"""
Subject Tracking for Fitness Influencer AI

Face and body detection using MediaPipe for intelligent video reframing.
Tracks subjects across frames with identity preservation and smoothing.

Story 012: Add face and body tracking for reframe

Usage:
    from backend.subject_tracker import SubjectTracker, TrackingConfig

    # Create tracker with config
    config = TrackingConfig(mode="face", smoothing_factor=0.8)
    tracker = SubjectTracker(config)

    # Track subjects in video
    results = await tracker.track_video("/path/to/video.mp4")

    # Get center of interest for each frame
    for frame in results.frames:
        print(f"Frame {frame.frame_number}: Center at {frame.center_of_interest}")
"""

import os
import cv2
import numpy as np
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any, Generator
from enum import Enum
import math
import tempfile
import asyncio
from collections import defaultdict

from backend.logging_config import get_logger

logger = get_logger(__name__)

# Check for MediaPipe availability
try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    logger.warning("MediaPipe not installed. Subject tracking will use fallback center detection.")


class DetectionMode(Enum):
    """Subject detection modes."""
    FACE = "face"          # Track faces only
    BODY = "body"          # Track full body/pose
    FACE_AND_BODY = "both" # Track both (use closest)
    AUTO = "auto"          # Auto-select based on content


class SubjectPriority(Enum):
    """How to handle multiple subjects."""
    LARGEST = "largest"    # Prioritize largest subject
    CLOSEST = "closest"    # Prioritize subject closest to center
    FIRST = "first"        # Prioritize first detected subject
    ALL = "all"            # Track all subjects (average center)


@dataclass
class Point:
    """2D coordinate."""
    x: float
    y: float

    def distance_to(self, other: 'Point') -> float:
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)

    def to_tuple(self) -> Tuple[float, float]:
        return (self.x, self.y)


@dataclass
class BoundingBox:
    """Bounding box for detected subject."""
    x: int
    y: int
    width: int
    height: int
    confidence: float = 1.0
    subject_id: Optional[str] = None
    detection_type: str = "unknown"

    @property
    def center(self) -> Point:
        return Point(
            self.x + self.width / 2,
            self.y + self.height / 2
        )

    @property
    def area(self) -> int:
        return self.width * self.height

    def to_dict(self) -> dict:
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "confidence": round(self.confidence, 2),
            "subject_id": self.subject_id,
            "detection_type": self.detection_type,
            "center": {"x": round(self.center.x, 1), "y": round(self.center.y, 1)}
        }


@dataclass
class TrackedFrame:
    """Tracking result for a single frame."""
    frame_number: int
    timestamp: float
    subjects: List[BoundingBox]
    center_of_interest: Point
    confidence: float

    def to_dict(self) -> dict:
        return {
            "frame_number": self.frame_number,
            "timestamp": round(self.timestamp, 3),
            "subjects_count": len(self.subjects),
            "subjects": [s.to_dict() for s in self.subjects],
            "center_of_interest": {
                "x": round(self.center_of_interest.x, 1),
                "y": round(self.center_of_interest.y, 1)
            },
            "confidence": round(self.confidence, 2)
        }


@dataclass
class TrackingResult:
    """Complete tracking result for a video."""
    success: bool
    video_path: str
    total_frames: int
    tracked_frames: int
    frames: List[TrackedFrame]
    frame_width: int
    frame_height: int
    fps: float
    duration: float
    detection_mode: str
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "video_path": self.video_path,
            "total_frames": self.total_frames,
            "tracked_frames": self.tracked_frames,
            "frame_dimensions": {"width": self.frame_width, "height": self.frame_height},
            "fps": round(self.fps, 2),
            "duration": round(self.duration, 2),
            "detection_mode": self.detection_mode,
            "error": self.error
        }

    def get_smoothed_trajectory(self, smoothing_factor: float = 0.8) -> List[Point]:
        """Get smoothed center of interest trajectory."""
        if not self.frames:
            return []

        centers = [f.center_of_interest for f in self.frames]
        return smooth_trajectory(centers, smoothing_factor)


@dataclass
class TrackingConfig:
    """Configuration for subject tracking."""
    mode: DetectionMode = DetectionMode.FACE
    priority: SubjectPriority = SubjectPriority.LARGEST
    smoothing_factor: float = 0.8
    min_confidence: float = 0.5
    sample_interval: int = 1  # Analyze every Nth frame
    max_subjects: int = 5  # Maximum subjects to track


def smooth_trajectory(
    points: List[Point],
    smoothing_factor: float = 0.8
) -> List[Point]:
    """
    Apply exponential smoothing to trajectory.

    Higher smoothing_factor = smoother but slower response.
    """
    if not points or smoothing_factor <= 0:
        return points

    smoothed = [points[0]]

    for i in range(1, len(points)):
        prev = smoothed[-1]
        curr = points[i]

        new_x = prev.x * smoothing_factor + curr.x * (1 - smoothing_factor)
        new_y = prev.y * smoothing_factor + curr.y * (1 - smoothing_factor)

        smoothed.append(Point(new_x, new_y))

    return smoothed


class SubjectTracker:
    """
    Track subjects (faces/bodies) across video frames.

    Uses MediaPipe for detection with fallback to center if unavailable.
    """

    def __init__(self, config: Optional[TrackingConfig] = None):
        self.config = config or TrackingConfig()
        self._face_detector = None
        self._pose_detector = None
        self._initialize_detectors()

    def _initialize_detectors(self):
        """Initialize MediaPipe detectors based on config."""
        if not MEDIAPIPE_AVAILABLE:
            logger.warning("MediaPipe not available, using center fallback")
            return

        mode = self.config.mode

        if mode in [DetectionMode.FACE, DetectionMode.FACE_AND_BODY, DetectionMode.AUTO]:
            self._face_detector = mp.solutions.face_detection.FaceDetection(
                model_selection=1,  # Full range detection
                min_detection_confidence=self.config.min_confidence
            )

        if mode in [DetectionMode.BODY, DetectionMode.FACE_AND_BODY, DetectionMode.AUTO]:
            self._pose_detector = mp.solutions.pose.Pose(
                model_complexity=1,
                min_detection_confidence=self.config.min_confidence,
                min_tracking_confidence=0.5
            )

    def _detect_faces(self, frame: np.ndarray) -> List[BoundingBox]:
        """Detect faces in a frame using MediaPipe."""
        if self._face_detector is None:
            return []

        height, width = frame.shape[:2]

        # Convert to RGB (MediaPipe expects RGB)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self._face_detector.process(rgb_frame)

        faces = []
        if results.detections:
            for i, detection in enumerate(results.detections):
                bbox = detection.location_data.relative_bounding_box

                x = int(bbox.xmin * width)
                y = int(bbox.ymin * height)
                w = int(bbox.width * width)
                h = int(bbox.height * height)

                # Clamp to frame bounds
                x = max(0, min(x, width - 1))
                y = max(0, min(y, height - 1))
                w = min(w, width - x)
                h = min(h, height - y)

                faces.append(BoundingBox(
                    x=x, y=y, width=w, height=h,
                    confidence=detection.score[0],
                    subject_id=f"face_{i}",
                    detection_type="face"
                ))

        return faces

    def _detect_bodies(self, frame: np.ndarray) -> List[BoundingBox]:
        """Detect body/pose in a frame using MediaPipe."""
        if self._pose_detector is None:
            return []

        height, width = frame.shape[:2]

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self._pose_detector.process(rgb_frame)

        bodies = []
        if results.pose_landmarks:
            # Get bounding box from pose landmarks
            landmarks = results.pose_landmarks.landmark

            # Find bounding box from all visible landmarks
            visible_x = []
            visible_y = []

            for lm in landmarks:
                if lm.visibility > 0.5:
                    visible_x.append(lm.x * width)
                    visible_y.append(lm.y * height)

            if visible_x and visible_y:
                x = int(min(visible_x))
                y = int(min(visible_y))
                w = int(max(visible_x) - x)
                h = int(max(visible_y) - y)

                # Add padding
                padding = 0.1
                x = max(0, int(x - w * padding))
                y = max(0, int(y - h * padding))
                w = min(width - x, int(w * (1 + 2 * padding)))
                h = min(height - y, int(h * (1 + 2 * padding)))

                avg_visibility = sum(lm.visibility for lm in landmarks) / len(landmarks)

                bodies.append(BoundingBox(
                    x=x, y=y, width=w, height=h,
                    confidence=avg_visibility,
                    subject_id="body_0",
                    detection_type="body"
                ))

        return bodies

    def _detect_subjects(self, frame: np.ndarray) -> List[BoundingBox]:
        """Detect all subjects in a frame based on config mode."""
        subjects = []

        if self.config.mode in [DetectionMode.FACE, DetectionMode.FACE_AND_BODY, DetectionMode.AUTO]:
            subjects.extend(self._detect_faces(frame))

        if self.config.mode in [DetectionMode.BODY, DetectionMode.FACE_AND_BODY, DetectionMode.AUTO]:
            subjects.extend(self._detect_bodies(frame))

        # Limit to max subjects
        if len(subjects) > self.config.max_subjects:
            subjects = sorted(subjects, key=lambda s: s.confidence, reverse=True)[:self.config.max_subjects]

        return subjects

    def _calculate_center_of_interest(
        self,
        subjects: List[BoundingBox],
        frame_width: int,
        frame_height: int
    ) -> Tuple[Point, float]:
        """
        Calculate center of interest from detected subjects.

        Returns (center_point, confidence).
        """
        frame_center = Point(frame_width / 2, frame_height / 2)

        if not subjects:
            return frame_center, 0.0

        priority = self.config.priority

        if priority == SubjectPriority.LARGEST:
            # Use center of largest subject
            largest = max(subjects, key=lambda s: s.area)
            return largest.center, largest.confidence

        elif priority == SubjectPriority.CLOSEST:
            # Use subject closest to frame center
            closest = min(subjects, key=lambda s: s.center.distance_to(frame_center))
            return closest.center, closest.confidence

        elif priority == SubjectPriority.FIRST:
            # Use first detected subject
            return subjects[0].center, subjects[0].confidence

        elif priority == SubjectPriority.ALL:
            # Average all subject centers (weighted by size)
            total_area = sum(s.area for s in subjects)
            if total_area == 0:
                return frame_center, 0.0

            avg_x = sum(s.center.x * s.area for s in subjects) / total_area
            avg_y = sum(s.center.y * s.area for s in subjects) / total_area
            avg_conf = sum(s.confidence for s in subjects) / len(subjects)

            return Point(avg_x, avg_y), avg_conf

        return frame_center, 0.0

    def track_frame(
        self,
        frame: np.ndarray,
        frame_number: int,
        timestamp: float
    ) -> TrackedFrame:
        """Track subjects in a single frame."""
        height, width = frame.shape[:2]

        # Detect subjects
        subjects = self._detect_subjects(frame)

        # Calculate center of interest
        center, confidence = self._calculate_center_of_interest(subjects, width, height)

        return TrackedFrame(
            frame_number=frame_number,
            timestamp=timestamp,
            subjects=subjects,
            center_of_interest=center,
            confidence=confidence
        )

    async def track_video(self, video_path: str) -> TrackingResult:
        """
        Track subjects across all frames of a video.

        Args:
            video_path: Path to video file

        Returns:
            TrackingResult with per-frame tracking data
        """
        if not os.path.exists(video_path):
            return TrackingResult(
                success=False,
                video_path=video_path,
                total_frames=0,
                tracked_frames=0,
                frames=[],
                frame_width=0,
                frame_height=0,
                fps=0,
                duration=0,
                detection_mode=self.config.mode.value,
                error=f"Video not found: {video_path}"
            )

        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            return TrackingResult(
                success=False,
                video_path=video_path,
                total_frames=0,
                tracked_frames=0,
                frames=[],
                frame_width=0,
                frame_height=0,
                fps=0,
                duration=0,
                detection_mode=self.config.mode.value,
                error="Failed to open video"
            )

        try:
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration = total_frames / fps if fps > 0 else 0

            tracked_frames = []
            frame_number = 0

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                # Sample based on interval
                if frame_number % self.config.sample_interval == 0:
                    timestamp = frame_number / fps
                    tracked = self.track_frame(frame, frame_number, timestamp)
                    tracked_frames.append(tracked)

                    # Log progress periodically
                    if frame_number % 100 == 0:
                        logger.debug(f"Tracking progress: frame {frame_number}/{total_frames}")

                frame_number += 1

            return TrackingResult(
                success=True,
                video_path=video_path,
                total_frames=total_frames,
                tracked_frames=len(tracked_frames),
                frames=tracked_frames,
                frame_width=width,
                frame_height=height,
                fps=fps,
                duration=duration,
                detection_mode=self.config.mode.value
            )

        except Exception as e:
            logger.error(f"Tracking failed: {e}", exc_info=True)
            return TrackingResult(
                success=False,
                video_path=video_path,
                total_frames=0,
                tracked_frames=0,
                frames=[],
                frame_width=0,
                frame_height=0,
                fps=0,
                duration=0,
                detection_mode=self.config.mode.value,
                error=str(e)
            )

        finally:
            cap.release()

    def __del__(self):
        """Clean up MediaPipe resources."""
        if self._face_detector:
            self._face_detector.close()
        if self._pose_detector:
            self._pose_detector.close()


async def track_subjects(
    video_path: str,
    mode: str = "face",
    priority: str = "largest",
    smoothing_factor: float = 0.8,
    sample_interval: int = 1
) -> TrackingResult:
    """
    Convenience function to track subjects in a video.

    Args:
        video_path: Path to video file
        mode: Detection mode ("face", "body", "both", "auto")
        priority: Subject priority ("largest", "closest", "first", "all")
        smoothing_factor: Motion smoothing (0.1-1.0)
        sample_interval: Analyze every Nth frame

    Returns:
        TrackingResult with tracking data
    """
    mode_map = {
        "face": DetectionMode.FACE,
        "body": DetectionMode.BODY,
        "both": DetectionMode.FACE_AND_BODY,
        "auto": DetectionMode.AUTO
    }

    priority_map = {
        "largest": SubjectPriority.LARGEST,
        "closest": SubjectPriority.CLOSEST,
        "first": SubjectPriority.FIRST,
        "all": SubjectPriority.ALL
    }

    config = TrackingConfig(
        mode=mode_map.get(mode.lower(), DetectionMode.FACE),
        priority=priority_map.get(priority.lower(), SubjectPriority.LARGEST),
        smoothing_factor=smoothing_factor,
        sample_interval=sample_interval
    )

    tracker = SubjectTracker(config)
    return await tracker.track_video(video_path)


def interpolate_trajectory(
    tracked_frames: List[TrackedFrame],
    target_fps: float,
    source_fps: float,
    sample_interval: int
) -> List[Point]:
    """
    Interpolate tracking data to full frame rate.

    Fills in frames between sampled frames with linear interpolation.
    """
    if not tracked_frames:
        return []

    # Get all centers
    sampled_centers = [f.center_of_interest for f in tracked_frames]

    # If sample_interval is 1, no interpolation needed
    if sample_interval == 1:
        return sampled_centers

    # Interpolate between sampled frames
    interpolated = []
    for i in range(len(sampled_centers) - 1):
        start = sampled_centers[i]
        end = sampled_centers[i + 1]

        # Add start point
        interpolated.append(start)

        # Add interpolated points
        for j in range(1, sample_interval):
            t = j / sample_interval
            x = start.x + (end.x - start.x) * t
            y = start.y + (end.y - start.y) * t
            interpolated.append(Point(x, y))

    # Add last point
    interpolated.append(sampled_centers[-1])

    return interpolated
