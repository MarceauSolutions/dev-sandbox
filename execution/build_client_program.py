#!/usr/bin/env python3
"""
build_client_program.py — Generate branded workout + nutrition PDFs for a coaching client.

Combines the workout plan generator and nutrition guide generator into a single CLI
that outputs two professionally branded PDFs ready to deliver.

Usage:
    python execution/build_client_program.py --client "John Doe" --goal "muscle gain" --days 4 --experience intermediate
    python execution/build_client_program.py --client "Jane" --goal "fat loss" --days 3 --experience beginner --weight 150 --equipment home_gym
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from workout_plan_generator import WorkoutPlanGenerator
from nutrition_guide_generator import NutritionGuideGenerator


def build_program(client_name: str, goal: str, days: int, experience: str,
                  equipment: str = "full_gym", weight: int = 180,
                  activity: str = "moderate", diet: str = "flexible",
                  output_dir: str = None) -> dict:
    """Generate both workout and nutrition PDFs for a client.

    Returns dict with paths to generated PDFs.
    """
    out_dir = Path(output_dir) if output_dir else Path(".tmp/client_programs")
    out_dir.mkdir(parents=True, exist_ok=True)

    safe_name = client_name.lower().replace(" ", "_")
    date_str = datetime.now().strftime("%Y%m%d")

    results = {}

    # --- Workout Plan ---
    print(f"Generating workout plan for {client_name}...")
    workout_gen = WorkoutPlanGenerator()
    workout_gen.output_dir = out_dir
    plan = workout_gen.generate_plan(goal, experience, days, equipment)

    workout_filename = f"workout_{safe_name}_{date_str}"
    workout_pdf = workout_gen.export_pdf(plan, workout_filename, client_name)
    results["workout_pdf"] = str(workout_pdf)
    print(f"  Workout PDF: {workout_pdf}")

    # --- Nutrition Guide ---
    print(f"Generating nutrition guide for {client_name}...")
    nutrition_gen = NutritionGuideGenerator()
    nutrition_gen.output_dir = out_dir

    # Map goal for nutrition generator
    nutrition_goal = goal.lower()
    if "muscle" in nutrition_goal or "bulk" in nutrition_goal:
        nutrition_goal = "lean_bulk"
    elif "fat" in nutrition_goal or "cut" in nutrition_goal or "loss" in nutrition_goal:
        nutrition_goal = "cut"
    elif "strength" in nutrition_goal:
        nutrition_goal = "lean_bulk"
    elif "recomp" in nutrition_goal:
        nutrition_goal = "recomp"
    else:
        nutrition_goal = "maintain"

    guide = nutrition_gen.generate_guide(weight, activity, nutrition_goal, diet)

    nutrition_filename = f"nutrition_{safe_name}_{date_str}"
    nutrition_pdf = nutrition_gen.export_pdf(guide, nutrition_filename, client_name)
    results["nutrition_pdf"] = str(nutrition_pdf)
    print(f"  Nutrition PDF: {nutrition_pdf}")

    print(f"\nProgram complete for {client_name}:")
    print(f"  Workout: {results['workout_pdf']}")
    print(f"  Nutrition: {results['nutrition_pdf']}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Generate branded workout + nutrition program for coaching client")
    parser.add_argument("--client", required=True, help="Client's full name")
    parser.add_argument("--goal", required=True, help="Fitness goal (muscle gain, fat loss, strength, recomp)")
    parser.add_argument("--days", type=int, required=True, choices=[3, 4, 5, 6], help="Training days per week")
    parser.add_argument("--experience", required=True, choices=["beginner", "intermediate", "advanced"])
    parser.add_argument("--equipment", default="full_gym", choices=["full_gym", "home_gym", "minimal"])
    parser.add_argument("--weight", type=int, default=180, help="Client weight in lbs")
    parser.add_argument("--activity", default="moderate",
                        choices=["sedentary", "light", "moderate", "active", "very_active"])
    parser.add_argument("--diet", default="flexible",
                        choices=["flexible", "keto", "vegan", "vegetarian", "paleo", "mediterranean"])
    parser.add_argument("--output-dir", "-o", help="Output directory for PDFs")
    args = parser.parse_args()

    results = build_program(
        client_name=args.client,
        goal=args.goal,
        days=args.days,
        experience=args.experience,
        equipment=args.equipment,
        weight=args.weight,
        activity=args.activity,
        diet=args.diet,
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    main()
