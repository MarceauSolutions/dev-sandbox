"""
Exercise Recognition Module

Detects exercise types from video using pose estimation.
Supports 20+ common exercises with rep counting and form recommendations.

Story 023: Implement exercise recognition
"""

import asyncio
import json
import logging
import math
import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Optional MediaPipe import
try:
    import mediapipe as mp
    import cv2
    import numpy as np
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False

logger = logging.getLogger(__name__)


class ExerciseCategory(str, Enum):
    """Exercise category classification"""
    LEGS = "legs"
    BACK = "back"
    CHEST = "chest"
    SHOULDERS = "shoulders"
    ARMS = "arms"
    CORE = "core"
    GLUTES = "glutes"
    FULL_BODY = "full_body"


class MovementPattern(str, Enum):
    """Movement pattern classification"""
    SQUAT = "squat"  # Hip and knee flexion
    HINGE = "hinge"  # Hip flexion, knees relatively straight
    PUSH_HORIZONTAL = "push_horizontal"  # Pushing away from chest
    PUSH_VERTICAL = "push_vertical"  # Pushing overhead
    PULL_HORIZONTAL = "pull_horizontal"  # Pulling toward chest
    PULL_VERTICAL = "pull_vertical"  # Pulling from overhead
    LUNGE = "lunge"  # Unilateral leg movement
    ROTATION = "rotation"  # Rotational movement
    ISOMETRIC = "isometric"  # Static hold
    DYNAMIC = "dynamic"  # Multi-movement pattern


@dataclass
class PoseLandmark:
    """Single pose landmark with coordinates and visibility"""
    x: float  # Normalized 0-1
    y: float  # Normalized 0-1
    z: float  # Depth relative to hip
    visibility: float  # 0-1 confidence


@dataclass
class JointAngle:
    """Calculated joint angle"""
    joint_name: str
    angle: float  # Degrees
    timestamp: float
    confidence: float


@dataclass
class RepetitionPhase:
    """Phase of a repetition"""
    phase_name: str  # e.g., "descent", "bottom", "ascent", "top"
    start_time: float
    end_time: float
    key_angles: Dict[str, float]


@dataclass
class ExerciseDetection:
    """Single exercise detection result"""
    exercise_id: str
    exercise_name: str
    confidence: float
    category: str
    movement_pattern: str
    timestamp: float
    duration: float
    landmarks_visible: int


@dataclass
class RepCount:
    """Rep counting result"""
    total_reps: int
    rep_phases: List[RepetitionPhase]
    avg_rep_duration: float
    tempo: str  # e.g., "2:1:2" (eccentric:pause:concentric)


@dataclass
class FormAnalysis:
    """Form analysis result"""
    overall_score: float  # 0-100
    key_observations: List[str]
    form_cues: List[str]  # From exercise library
    areas_for_improvement: List[str]


@dataclass
class ExerciseRecognitionConfig:
    """Configuration for exercise recognition"""
    min_confidence: float = 0.7
    sample_interval: int = 5  # Process every Nth frame
    min_duration: float = 1.0  # Minimum seconds for valid detection
    enable_rep_counting: bool = True
    enable_form_analysis: bool = True
    smoothing_window: int = 5  # Frames for smoothing
    model_complexity: int = 1  # MediaPipe model complexity (0, 1, 2)


@dataclass
class ExerciseRecognitionResult:
    """Complete exercise recognition result"""
    success: bool
    detected_exercise: Optional[str]
    exercise_name: Optional[str]
    confidence: float
    category: Optional[str]
    muscle_groups: List[str]
    rep_count_estimate: int
    avg_rep_duration: Optional[float]
    description: str
    recommendations: List[str]
    complementary_exercises: List[str]
    form_score: Optional[float]
    form_observations: List[str]
    all_detections: List[ExerciseDetection]
    processing_time: float
    frames_analyzed: int
    error: Optional[str] = None


class ExerciseLibrary:
    """Manages the exercise library and matching"""

    def __init__(self, library_path: Optional[str] = None):
        """Initialize with exercise library"""
        if library_path is None:
            library_path = Path(__file__).parent.parent / "data" / "exercise_library.json"

        self.library_path = Path(library_path)
        self.exercises = {}
        self.categories = {}
        self.movement_patterns = {}
        self._load_library()

    def _load_library(self):
        """Load exercise library from JSON"""
        if not self.library_path.exists():
            logger.warning(f"Exercise library not found at {self.library_path}")
            self._create_default_library()
            return

        try:
            with open(self.library_path) as f:
                data = json.load(f)

            self.exercises = {ex["id"]: ex for ex in data.get("exercises", [])}
            self.categories = data.get("categories", {})
            self.pose_landmarks = data.get("pose_landmarks", {})

            # Build alias lookup
            self.alias_lookup = {}
            for ex_id, ex in self.exercises.items():
                self.alias_lookup[ex["name"].lower()] = ex_id
                for alias in ex.get("aliases", []):
                    self.alias_lookup[alias.lower()] = ex_id

            logger.info(f"Loaded {len(self.exercises)} exercises from library")

        except Exception as e:
            logger.error(f"Error loading exercise library: {e}")
            self._create_default_library()

    def _create_default_library(self):
        """Create minimal default library"""
        self.exercises = {
            "squat": {
                "id": "squat",
                "name": "Squat",
                "category": "legs",
                "muscle_groups": ["quadriceps", "glutes", "hamstrings"],
                "description": "A compound lower body exercise.",
                "complementary_exercises": ["deadlift", "lunge"]
            },
            "pushup": {
                "id": "pushup",
                "name": "Push-Up",
                "category": "chest",
                "muscle_groups": ["chest", "triceps", "shoulders"],
                "description": "A fundamental bodyweight pushing exercise.",
                "complementary_exercises": ["bench_press", "dips"]
            }
        }
        self.alias_lookup = {"squat": "squat", "squats": "squat", "push-up": "pushup", "pushup": "pushup"}

    def get_exercise(self, exercise_id: str) -> Optional[Dict]:
        """Get exercise by ID or alias"""
        # Direct lookup
        if exercise_id in self.exercises:
            return self.exercises[exercise_id]

        # Alias lookup
        if exercise_id.lower() in self.alias_lookup:
            return self.exercises[self.alias_lookup[exercise_id.lower()]]

        return None

    def get_all_exercises(self) -> List[Dict]:
        """Get all exercises"""
        return list(self.exercises.values())

    def get_exercises_by_category(self, category: str) -> List[Dict]:
        """Get exercises in a category"""
        return [ex for ex in self.exercises.values() if ex.get("category") == category]

    def get_categories(self) -> List[str]:
        """Get all categories"""
        return list(self.categories.keys())


class PoseAnalyzer:
    """Analyzes pose landmarks for exercise detection"""

    # MediaPipe landmark indices
    LANDMARKS = {
        "nose": 0,
        "left_shoulder": 11, "right_shoulder": 12,
        "left_elbow": 13, "right_elbow": 14,
        "left_wrist": 15, "right_wrist": 16,
        "left_hip": 23, "right_hip": 24,
        "left_knee": 25, "right_knee": 26,
        "left_ankle": 27, "right_ankle": 28,
    }

    @staticmethod
    def calculate_angle(a: Tuple[float, float], b: Tuple[float, float], c: Tuple[float, float]) -> float:
        """Calculate angle at point b given three points"""
        ba = (a[0] - b[0], a[1] - b[1])
        bc = (c[0] - b[0], c[1] - b[1])

        # Dot product and magnitudes
        dot = ba[0] * bc[0] + ba[1] * bc[1]
        mag_ba = math.sqrt(ba[0]**2 + ba[1]**2)
        mag_bc = math.sqrt(bc[0]**2 + bc[1]**2)

        if mag_ba * mag_bc == 0:
            return 0.0

        cos_angle = dot / (mag_ba * mag_bc)
        cos_angle = max(-1, min(1, cos_angle))  # Clamp for numerical stability

        angle = math.degrees(math.acos(cos_angle))
        return angle

    @staticmethod
    def get_landmark_position(landmarks, idx: int) -> Tuple[float, float, float]:
        """Get (x, y, visibility) for a landmark"""
        lm = landmarks.landmark[idx]
        return (lm.x, lm.y, lm.visibility)

    @classmethod
    def calculate_key_angles(cls, landmarks) -> Dict[str, float]:
        """Calculate key joint angles from landmarks"""
        angles = {}

        try:
            # Left knee angle (hip-knee-ankle)
            left_hip = cls.get_landmark_position(landmarks, cls.LANDMARKS["left_hip"])
            left_knee = cls.get_landmark_position(landmarks, cls.LANDMARKS["left_knee"])
            left_ankle = cls.get_landmark_position(landmarks, cls.LANDMARKS["left_ankle"])

            if all(p[2] > 0.5 for p in [left_hip, left_knee, left_ankle]):
                angles["left_knee"] = cls.calculate_angle(
                    left_hip[:2], left_knee[:2], left_ankle[:2]
                )

            # Right knee angle
            right_hip = cls.get_landmark_position(landmarks, cls.LANDMARKS["right_hip"])
            right_knee = cls.get_landmark_position(landmarks, cls.LANDMARKS["right_knee"])
            right_ankle = cls.get_landmark_position(landmarks, cls.LANDMARKS["right_ankle"])

            if all(p[2] > 0.5 for p in [right_hip, right_knee, right_ankle]):
                angles["right_knee"] = cls.calculate_angle(
                    right_hip[:2], right_knee[:2], right_ankle[:2]
                )

            # Left elbow angle (shoulder-elbow-wrist)
            left_shoulder = cls.get_landmark_position(landmarks, cls.LANDMARKS["left_shoulder"])
            left_elbow = cls.get_landmark_position(landmarks, cls.LANDMARKS["left_elbow"])
            left_wrist = cls.get_landmark_position(landmarks, cls.LANDMARKS["left_wrist"])

            if all(p[2] > 0.5 for p in [left_shoulder, left_elbow, left_wrist]):
                angles["left_elbow"] = cls.calculate_angle(
                    left_shoulder[:2], left_elbow[:2], left_wrist[:2]
                )

            # Right elbow angle
            right_shoulder = cls.get_landmark_position(landmarks, cls.LANDMARKS["right_shoulder"])
            right_elbow = cls.get_landmark_position(landmarks, cls.LANDMARKS["right_elbow"])
            right_wrist = cls.get_landmark_position(landmarks, cls.LANDMARKS["right_wrist"])

            if all(p[2] > 0.5 for p in [right_shoulder, right_elbow, right_wrist]):
                angles["right_elbow"] = cls.calculate_angle(
                    right_shoulder[:2], right_elbow[:2], right_wrist[:2]
                )

            # Hip angle (shoulder-hip-knee)
            if all(p[2] > 0.5 for p in [left_shoulder, left_hip, left_knee]):
                angles["left_hip"] = cls.calculate_angle(
                    left_shoulder[:2], left_hip[:2], left_knee[:2]
                )

            if all(p[2] > 0.5 for p in [right_shoulder, right_hip, right_knee]):
                angles["right_hip"] = cls.calculate_angle(
                    right_shoulder[:2], right_hip[:2], right_knee[:2]
                )

            # Torso angle (vertical)
            mid_shoulder = ((left_shoulder[0] + right_shoulder[0]) / 2,
                           (left_shoulder[1] + right_shoulder[1]) / 2)
            mid_hip = ((left_hip[0] + right_hip[0]) / 2,
                      (left_hip[1] + right_hip[1]) / 2)

            # Angle from vertical (0 = upright, 90 = horizontal)
            dx = mid_shoulder[0] - mid_hip[0]
            dy = mid_shoulder[1] - mid_hip[1]
            angles["torso_vertical"] = 90 - abs(math.degrees(math.atan2(dx, -dy)))

        except Exception as e:
            logger.debug(f"Error calculating angles: {e}")

        return angles

    @classmethod
    def classify_movement_pattern(cls, angles_history: List[Dict[str, float]]) -> str:
        """Classify movement pattern from angle history"""
        if not angles_history:
            return MovementPattern.ISOMETRIC.value

        # Calculate angle ranges
        knee_range = cls._calculate_range([a.get("left_knee", 180) for a in angles_history])
        hip_range = cls._calculate_range([a.get("left_hip", 180) for a in angles_history])
        elbow_range = cls._calculate_range([a.get("left_elbow", 180) for a in angles_history])
        torso_range = cls._calculate_range([a.get("torso_vertical", 0) for a in angles_history])

        # Classification rules
        if knee_range > 40 and hip_range > 40:
            if torso_range < 20:
                return MovementPattern.SQUAT.value
            else:
                return MovementPattern.LUNGE.value

        if hip_range > 40 and knee_range < 30:
            return MovementPattern.HINGE.value

        if elbow_range > 40:
            avg_torso = sum(a.get("torso_vertical", 0) for a in angles_history) / len(angles_history)
            if avg_torso > 45:  # More horizontal
                return MovementPattern.PUSH_HORIZONTAL.value
            else:
                return MovementPattern.PUSH_VERTICAL.value

        if knee_range < 20 and hip_range < 20 and elbow_range < 20:
            return MovementPattern.ISOMETRIC.value

        return MovementPattern.DYNAMIC.value

    @staticmethod
    def _calculate_range(values: List[float]) -> float:
        """Calculate range of values"""
        if not values:
            return 0.0
        return max(values) - min(values)

    @classmethod
    def count_reps(cls, angles_history: List[Dict[str, float]],
                   joint: str = "left_knee",
                   threshold: float = 30) -> int:
        """Count repetitions based on joint angle oscillation"""
        if not angles_history or joint not in angles_history[0]:
            return 0

        values = [a.get(joint, 180) for a in angles_history]
        if not values:
            return 0

        # Smooth values
        smoothed = cls._smooth_values(values, window=5)

        # Find peaks and valleys
        avg = sum(smoothed) / len(smoothed)
        reps = 0
        above = smoothed[0] > avg

        for val in smoothed[1:]:
            curr_above = val > avg
            if curr_above != above:
                if not curr_above:  # Crossed below average (completed descent)
                    reps += 1
                above = curr_above

        return reps // 2  # Full rep = descent + ascent

    @staticmethod
    def _smooth_values(values: List[float], window: int = 5) -> List[float]:
        """Apply moving average smoothing"""
        if len(values) < window:
            return values

        smoothed = []
        for i in range(len(values)):
            start = max(0, i - window // 2)
            end = min(len(values), i + window // 2 + 1)
            smoothed.append(sum(values[start:end]) / (end - start))

        return smoothed


class ExerciseRecognizer:
    """Main exercise recognition engine"""

    def __init__(self, config: Optional[ExerciseRecognitionConfig] = None):
        """Initialize recognizer"""
        self.config = config or ExerciseRecognitionConfig()
        self.library = ExerciseLibrary()
        self.pose_analyzer = PoseAnalyzer()

        # Initialize MediaPipe if available
        self.pose = None
        if MEDIAPIPE_AVAILABLE:
            self.mp_pose = mp.solutions.pose
            self.pose = self.mp_pose.Pose(
                static_image_mode=False,
                model_complexity=self.config.model_complexity,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )

    async def detect_exercise(
        self,
        video_path: str,
        config: Optional[ExerciseRecognitionConfig] = None
    ) -> ExerciseRecognitionResult:
        """
        Detect exercise type from video

        Args:
            video_path: Path to video file
            config: Optional configuration override

        Returns:
            ExerciseRecognitionResult with detection details
        """
        import time
        start_time = time.time()

        config = config or self.config

        # Validate input
        if not os.path.exists(video_path):
            return ExerciseRecognitionResult(
                success=False,
                detected_exercise=None,
                exercise_name=None,
                confidence=0.0,
                category=None,
                muscle_groups=[],
                rep_count_estimate=0,
                avg_rep_duration=None,
                description="",
                recommendations=[],
                complementary_exercises=[],
                form_score=None,
                form_observations=[],
                all_detections=[],
                processing_time=0.0,
                frames_analyzed=0,
                error=f"Video file not found: {video_path}"
            )

        if not MEDIAPIPE_AVAILABLE:
            return await self._detect_without_mediapipe(video_path, config)

        try:
            # Process video frames
            angles_history = []
            detections = []
            frames_analyzed = 0

            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS) or 30
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps

            frame_idx = 0
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                # Sample frames
                if frame_idx % config.sample_interval != 0:
                    frame_idx += 1
                    continue

                frames_analyzed += 1
                timestamp = frame_idx / fps

                # Process with MediaPipe
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.pose.process(rgb_frame)

                if results.pose_landmarks:
                    # Calculate angles
                    angles = self.pose_analyzer.calculate_key_angles(results.pose_landmarks)
                    angles["timestamp"] = timestamp
                    angles_history.append(angles)

                frame_idx += 1

            cap.release()

            if not angles_history:
                return ExerciseRecognitionResult(
                    success=False,
                    detected_exercise=None,
                    exercise_name=None,
                    confidence=0.0,
                    category=None,
                    muscle_groups=[],
                    rep_count_estimate=0,
                    avg_rep_duration=None,
                    description="No pose detected in video",
                    recommendations=["Ensure person is clearly visible in frame"],
                    complementary_exercises=[],
                    form_score=None,
                    form_observations=[],
                    all_detections=[],
                    processing_time=time.time() - start_time,
                    frames_analyzed=frames_analyzed,
                    error="No pose landmarks detected"
                )

            # Classify movement pattern
            movement_pattern = self.pose_analyzer.classify_movement_pattern(angles_history)

            # Match to exercise
            matched_exercise, confidence = self._match_exercise(movement_pattern, angles_history)

            # Count reps if enabled
            rep_count = 0
            avg_rep_duration = None
            if config.enable_rep_counting and matched_exercise:
                rep_count = self._count_reps_for_exercise(matched_exercise, angles_history)
                if rep_count > 0:
                    avg_rep_duration = duration / rep_count

            # Get exercise details
            exercise_data = self.library.get_exercise(matched_exercise) if matched_exercise else None

            # Form analysis
            form_score = None
            form_observations = []
            if config.enable_form_analysis and exercise_data:
                form_score, form_observations = self._analyze_form(
                    matched_exercise, angles_history, exercise_data
                )

            # Generate description
            description = self._generate_description(
                matched_exercise, exercise_data, rep_count, duration
            )

            # Get recommendations
            recommendations = self._generate_recommendations(
                matched_exercise, form_observations, exercise_data
            )

            processing_time = time.time() - start_time

            return ExerciseRecognitionResult(
                success=True,
                detected_exercise=matched_exercise,
                exercise_name=exercise_data.get("name") if exercise_data else matched_exercise,
                confidence=confidence,
                category=exercise_data.get("category") if exercise_data else None,
                muscle_groups=exercise_data.get("muscle_groups", []) if exercise_data else [],
                rep_count_estimate=rep_count,
                avg_rep_duration=avg_rep_duration,
                description=description,
                recommendations=recommendations,
                complementary_exercises=exercise_data.get("complementary_exercises", []) if exercise_data else [],
                form_score=form_score,
                form_observations=form_observations,
                all_detections=detections,
                processing_time=processing_time,
                frames_analyzed=frames_analyzed
            )

        except Exception as e:
            logger.error(f"Error detecting exercise: {e}")
            return ExerciseRecognitionResult(
                success=False,
                detected_exercise=None,
                exercise_name=None,
                confidence=0.0,
                category=None,
                muscle_groups=[],
                rep_count_estimate=0,
                avg_rep_duration=None,
                description="",
                recommendations=[],
                complementary_exercises=[],
                form_score=None,
                form_observations=[],
                all_detections=[],
                processing_time=time.time() - start_time,
                frames_analyzed=0,
                error=str(e)
            )

    async def _detect_without_mediapipe(
        self,
        video_path: str,
        config: ExerciseRecognitionConfig
    ) -> ExerciseRecognitionResult:
        """Fallback detection without MediaPipe using motion analysis"""
        import time
        start_time = time.time()

        logger.warning("MediaPipe not available, using motion-based detection")

        # Use FFmpeg to extract motion statistics
        try:
            cmd = [
                "ffprobe", "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "json", video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            duration = float(json.loads(result.stdout)["format"]["duration"])

            # Simple heuristic based on duration
            if duration < 5:
                detected = "pushup"
                confidence = 0.4
            elif duration < 15:
                detected = "squat"
                confidence = 0.5
            else:
                detected = "burpee"
                confidence = 0.3

            exercise_data = self.library.get_exercise(detected)

            return ExerciseRecognitionResult(
                success=True,
                detected_exercise=detected,
                exercise_name=exercise_data.get("name") if exercise_data else detected,
                confidence=confidence,
                category=exercise_data.get("category") if exercise_data else "unknown",
                muscle_groups=exercise_data.get("muscle_groups", []) if exercise_data else [],
                rep_count_estimate=0,
                avg_rep_duration=None,
                description=f"Detected {detected} (low confidence - MediaPipe unavailable)",
                recommendations=["Install mediapipe for accurate detection"],
                complementary_exercises=exercise_data.get("complementary_exercises", []) if exercise_data else [],
                form_score=None,
                form_observations=[],
                all_detections=[],
                processing_time=time.time() - start_time,
                frames_analyzed=0,
                error="MediaPipe unavailable - using heuristic detection"
            )

        except Exception as e:
            return ExerciseRecognitionResult(
                success=False,
                detected_exercise=None,
                exercise_name=None,
                confidence=0.0,
                category=None,
                muscle_groups=[],
                rep_count_estimate=0,
                avg_rep_duration=None,
                description="",
                recommendations=["Install opencv-python and mediapipe for exercise detection"],
                complementary_exercises=[],
                form_score=None,
                form_observations=[],
                all_detections=[],
                processing_time=time.time() - start_time,
                frames_analyzed=0,
                error=f"Detection failed: {str(e)}"
            )

    def _match_exercise(
        self,
        movement_pattern: str,
        angles_history: List[Dict[str, float]]
    ) -> Tuple[Optional[str], float]:
        """Match movement pattern to exercise from library"""

        # Movement pattern to exercise mapping
        pattern_exercises = {
            MovementPattern.SQUAT.value: ["squat", "leg_press"],
            MovementPattern.HINGE.value: ["deadlift", "romanian_deadlift", "hip_thrust"],
            MovementPattern.PUSH_HORIZONTAL.value: ["pushup", "bench_press", "dips"],
            MovementPattern.PUSH_VERTICAL.value: ["overhead_press", "lateral_raise"],
            MovementPattern.PULL_HORIZONTAL.value: ["bent_over_row"],
            MovementPattern.PULL_VERTICAL.value: ["pullup", "lat_pulldown"],
            MovementPattern.LUNGE.value: ["lunge"],
            MovementPattern.ISOMETRIC.value: ["plank"],
            MovementPattern.DYNAMIC.value: ["burpee", "mountain_climber"]
        }

        candidates = pattern_exercises.get(movement_pattern, [])

        if not candidates:
            return None, 0.0

        # Score candidates based on angle patterns
        best_match = None
        best_score = 0.0

        for exercise_id in candidates:
            exercise = self.library.get_exercise(exercise_id)
            if not exercise:
                continue

            score = self._score_exercise_match(exercise_id, angles_history)
            if score > best_score:
                best_score = score
                best_match = exercise_id

        return best_match, best_score

    def _score_exercise_match(
        self,
        exercise_id: str,
        angles_history: List[Dict[str, float]]
    ) -> float:
        """Score how well angles match expected exercise pattern"""
        if not angles_history:
            return 0.0

        score = 0.5  # Base score for pattern match

        # Exercise-specific angle expectations
        exercise_angles = {
            "squat": {"knee_range": (40, 90), "hip_range": (40, 90)},
            "deadlift": {"hip_range": (40, 90), "knee_range": (0, 40)},
            "pushup": {"elbow_range": (40, 90)},
            "plank": {"torso_vertical": (0, 15)},
            "lunge": {"knee_range": (30, 80)},
            "pullup": {"elbow_range": (40, 100)},
            "bench_press": {"elbow_range": (50, 100)},
            "overhead_press": {"elbow_range": (40, 90)},
            "bicep_curl": {"elbow_range": (40, 100)},
            "hip_thrust": {"hip_range": (40, 90), "knee_range": (0, 30)},
        }

        expected = exercise_angles.get(exercise_id, {})

        for angle_key, (min_range, max_range) in expected.items():
            if "_range" in angle_key:
                # Check range of motion
                base_key = angle_key.replace("_range", "")
                left_key = f"left_{base_key}"
                right_key = f"right_{base_key}"

                for key in [left_key, right_key, base_key]:
                    if key in angles_history[0]:
                        values = [a.get(key, 180) for a in angles_history]
                        range_val = max(values) - min(values)
                        if min_range <= range_val <= max_range:
                            score += 0.2
                        elif range_val > max_range * 0.7:
                            score += 0.1
                        break
            else:
                # Check average angle
                if angle_key in angles_history[0]:
                    avg = sum(a.get(angle_key, 0) for a in angles_history) / len(angles_history)
                    if min_range <= avg <= max_range:
                        score += 0.2

        return min(1.0, score)

    def _count_reps_for_exercise(
        self,
        exercise_id: str,
        angles_history: List[Dict[str, float]]
    ) -> int:
        """Count reps for specific exercise"""

        # Exercise to joint mapping for rep counting
        exercise_joints = {
            "squat": "left_knee",
            "deadlift": "left_hip",
            "pushup": "left_elbow",
            "bench_press": "left_elbow",
            "pullup": "left_elbow",
            "lunge": "left_knee",
            "bicep_curl": "left_elbow",
            "overhead_press": "left_elbow",
            "hip_thrust": "left_hip",
            "leg_press": "left_knee",
        }

        joint = exercise_joints.get(exercise_id, "left_knee")
        return self.pose_analyzer.count_reps(angles_history, joint)

    def _analyze_form(
        self,
        exercise_id: str,
        angles_history: List[Dict[str, float]],
        exercise_data: Dict
    ) -> Tuple[float, List[str]]:
        """Analyze exercise form"""
        observations = []
        score = 70.0  # Base score

        form_cues = exercise_data.get("form_cues", [])

        # Check for common form issues

        # Asymmetry check
        for base in ["knee", "elbow", "hip"]:
            left_key = f"left_{base}"
            right_key = f"right_{base}"

            if left_key in angles_history[0] and right_key in angles_history[0]:
                left_avg = sum(a.get(left_key, 0) for a in angles_history) / len(angles_history)
                right_avg = sum(a.get(right_key, 0) for a in angles_history) / len(angles_history)

                asymmetry = abs(left_avg - right_avg)
                if asymmetry > 15:
                    observations.append(f"Significant {base} asymmetry detected ({asymmetry:.1f}°)")
                    score -= 10
                elif asymmetry > 8:
                    observations.append(f"Minor {base} asymmetry detected ({asymmetry:.1f}°)")
                    score -= 5

        # Depth check for squats
        if exercise_id == "squat":
            knee_angles = [a.get("left_knee", 180) for a in angles_history]
            min_knee = min(knee_angles)
            if min_knee > 100:
                observations.append("Squat depth could be deeper (knees not reaching 90°)")
                score -= 15
            elif min_knee < 60:
                observations.append("Excellent squat depth achieved")
                score += 10

        # Range of motion check
        if exercise_id in ["pushup", "bench_press"]:
            elbow_angles = [a.get("left_elbow", 180) for a in angles_history]
            min_elbow = min(elbow_angles)
            max_elbow = max(elbow_angles)

            if max_elbow - min_elbow < 50:
                observations.append("Limited range of motion - try going deeper")
                score -= 10
            elif min_elbow < 70:
                observations.append("Good depth on the descent")
                score += 5

        # Add form cues from library
        if form_cues:
            observations.append("Key form cues for this exercise:")
            observations.extend([f"  • {cue}" for cue in form_cues[:3]])

        return max(0, min(100, score)), observations

    def _generate_description(
        self,
        exercise_id: Optional[str],
        exercise_data: Optional[Dict],
        rep_count: int,
        duration: float
    ) -> str:
        """Generate caption-ready description"""
        if not exercise_id:
            return "Exercise type could not be determined from the video."

        name = exercise_data.get("name", exercise_id) if exercise_data else exercise_id
        category = exercise_data.get("category", "fitness") if exercise_data else "fitness"
        muscles = exercise_data.get("muscle_groups", []) if exercise_data else []

        parts = [f"Performing {name}"]

        if rep_count > 0:
            parts.append(f"for {rep_count} reps")

        if muscles:
            muscle_str = ", ".join(muscles[:3])
            parts.append(f"targeting the {muscle_str}")

        return " ".join(parts) + "."

    def _generate_recommendations(
        self,
        exercise_id: Optional[str],
        form_observations: List[str],
        exercise_data: Optional[Dict]
    ) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []

        # Form-based recommendations
        for obs in form_observations:
            if "asymmetry" in obs.lower():
                recommendations.append("Focus on even weight distribution between sides")
            if "depth" in obs.lower() and "deeper" in obs.lower():
                recommendations.append("Work on mobility to achieve full range of motion")
            if "range of motion" in obs.lower():
                recommendations.append("Control the movement through the full range")

        # Exercise-specific tips
        if exercise_data:
            category = exercise_data.get("category")
            if category == "legs":
                recommendations.append("Consider adding pause reps for increased time under tension")
            elif category == "chest":
                recommendations.append("Focus on the mind-muscle connection with the chest")
            elif category == "back":
                recommendations.append("Initiate pulls with the lats, not the arms")

        # Always include form cue reminder
        if exercise_data and exercise_data.get("form_cues"):
            recommendations.append(f"Key cue: {exercise_data['form_cues'][0]}")

        return recommendations[:5]  # Limit to 5 recommendations


# Convenience functions

async def detect_exercise(
    video_path: str,
    config: Optional[ExerciseRecognitionConfig] = None
) -> ExerciseRecognitionResult:
    """
    Detect exercise type from video

    Args:
        video_path: Path to video file
        config: Optional configuration

    Returns:
        ExerciseRecognitionResult
    """
    recognizer = ExerciseRecognizer(config)
    return await recognizer.detect_exercise(video_path, config)


def get_supported_exercises() -> List[Dict]:
    """Get list of all supported exercises"""
    library = ExerciseLibrary()
    return library.get_all_exercises()


def get_exercise_categories() -> List[str]:
    """Get list of exercise categories"""
    return [cat.value for cat in ExerciseCategory]


def get_exercise_by_id(exercise_id: str) -> Optional[Dict]:
    """Get exercise details by ID"""
    library = ExerciseLibrary()
    return library.get_exercise(exercise_id)


def get_exercises_by_category(category: str) -> List[Dict]:
    """Get exercises in a category"""
    library = ExerciseLibrary()
    return library.get_exercises_by_category(category)


# CLI for testing
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Exercise Recognition")
    parser.add_argument("video_path", help="Path to video file")
    parser.add_argument("--confidence", type=float, default=0.7, help="Minimum confidence")
    parser.add_argument("--no-reps", action="store_true", help="Disable rep counting")
    parser.add_argument("--no-form", action="store_true", help="Disable form analysis")

    args = parser.parse_args()

    config = ExerciseRecognitionConfig(
        min_confidence=args.confidence,
        enable_rep_counting=not args.no_reps,
        enable_form_analysis=not args.no_form
    )

    result = asyncio.run(detect_exercise(args.video_path, config))

    print(f"\n=== Exercise Recognition Result ===")
    print(f"Success: {result.success}")
    print(f"Detected: {result.exercise_name}")
    print(f"Confidence: {result.confidence:.2f}")
    print(f"Category: {result.category}")
    print(f"Muscles: {', '.join(result.muscle_groups)}")
    print(f"Rep Count: {result.rep_count_estimate}")
    print(f"Form Score: {result.form_score}")
    print(f"\nDescription: {result.description}")
    print(f"\nRecommendations:")
    for rec in result.recommendations:
        print(f"  - {rec}")
    print(f"\nComplementary Exercises: {', '.join(result.complementary_exercises)}")
    print(f"\nProcessing Time: {result.processing_time:.2f}s")
    print(f"Frames Analyzed: {result.frames_analyzed}")

    if result.error:
        print(f"\nError: {result.error}")
