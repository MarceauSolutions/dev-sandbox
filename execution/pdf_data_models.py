"""
Pydantic data models for the Branded PDF Engine.
Shared between CLI usage, FastAPI endpoints, and n8n integrations.
"""

from pydantic import BaseModel
from typing import Optional, List, Dict


# --- Workout Program ---

class ExerciseDetail(BaseModel):
    name: str
    muscle_group: str = ""
    sets: int = 3
    reps: str = "8-12"
    rest_seconds: int = 90
    notes: Optional[str] = None

class WorkoutDay(BaseModel):
    day_number: int
    day_name: str
    focus: str
    exercises: List[ExerciseDetail]
    warmup: Optional[str] = None
    cooldown: Optional[str] = None

class WorkoutProgramData(BaseModel):
    client_name: str
    program_name: str
    start_date: str = ""
    goal: str = ""
    experience_level: str = ""
    equipment: str = ""
    days_per_week: int = 4
    schedule: List[WorkoutDay]
    program_notes: Optional[Dict[str, str]] = None
    coach_note: Optional[str] = None


# --- Nutrition Guide ---

class MacroTargets(BaseModel):
    calories: int
    protein_g: int
    carbs_g: int
    fats_g: int

class MealPlanEntry(BaseModel):
    meal_name: str
    time: str = ""
    foods: List[str]
    macros: Optional[MacroTargets] = None

class NutritionGuideData(BaseModel):
    client_name: str
    goal: str = ""
    weight_lbs: int = 0
    daily_targets: MacroTargets
    meal_plan: List[MealPlanEntry] = []
    food_lists: Optional[Dict[str, List[str]]] = None
    supplements: Optional[Dict[str, List[str]]] = None
    hydration_oz: int = 100
    tips: List[str] = []
    coach_note: Optional[str] = None


# --- Progress Report ---

class BodyMetrics(BaseModel):
    date: str
    weight_lbs: float
    body_fat_pct: Optional[float] = None
    measurements: Optional[Dict[str, float]] = None

class StrengthMetric(BaseModel):
    exercise: str
    previous: str
    current: str
    change_pct: float = 0.0

class ProgressReportData(BaseModel):
    client_name: str
    report_period: str
    metrics_history: List[BodyMetrics] = []
    strength_gains: List[StrengthMetric] = []
    adherence_pct: float = 0.0
    highlights: List[str] = []
    areas_to_improve: List[str] = []
    next_phase: str = ""
    coach_note: Optional[str] = None


# --- Onboarding Packet ---

class OnboardingPacketData(BaseModel):
    client_name: str
    start_date: str = ""
    coach_name: str = "William Marceau"
    welcome_message: str = ""
    what_to_expect: List[str] = []
    communication_guidelines: Optional[Dict[str, str]] = None
    faq: List[Dict[str, str]] = []
    app_setup_steps: List[str] = []
    weekly_schedule: Optional[Dict[str, str]] = None
    important_links: Optional[Dict[str, str]] = None


# --- Peptide Guide ---

class PeptideProfile(BaseModel):
    name: str
    category: str = ""
    evidence_rating: str = "Moderate"
    mechanism: str = ""
    benefits: List[str] = []
    side_effects: List[str] = []
    notes: Optional[str] = None

class PeptideGuideData(BaseModel):
    client_name: Optional[str] = None
    title: str = "Evidence-Based Peptide Guide"
    intro_text: str = ""
    disclaimer: str = "This guide is for educational purposes only. Always consult with a licensed healthcare provider before starting any peptide protocol."
    compounds: List[PeptideProfile] = []
    decision_framework: Optional[Dict[str, List[str]]] = None
    coach_note: Optional[str] = None


# --- Challenge Workout ---

class ChallengeDay(BaseModel):
    day_number: int
    title: str
    exercises: List[ExerciseDetail] = []
    motivation_quote: Optional[str] = None
    tip: Optional[str] = None

class ChallengeWorkoutData(BaseModel):
    challenge_name: str = "7-Day Body Recomp Challenge"
    duration_days: int = 7
    difficulty: str = "Beginner"
    equipment_needed: str = "Dumbbells + bodyweight"
    days: List[ChallengeDay] = []
    rules: List[str] = []
    coach_note: Optional[str] = None


# --- Generic Document ---

class GenericDocData(BaseModel):
    title: str
    subtitle: Optional[str] = None
    content_markdown: str = ""
    author: str = "William Marceau"
    date: Optional[str] = None
    include_toc: bool = False
