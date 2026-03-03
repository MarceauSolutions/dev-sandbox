#!/usr/bin/env python3
"""
Test script for Branded PDF Engine.
Generates one sample PDF per template with realistic mock data.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from branded_pdf_engine import BrandedPDFEngine

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", ".tmp", "pdf_test")
os.makedirs(OUTPUT_DIR, exist_ok=True)

engine = BrandedPDFEngine()


def test_workout():
    data = {
        "client_name": "Sarah Mitchell",
        "program_name": "4-Week Hypertrophy Program",
        "start_date": "March 10, 2026",
        "goal": "Muscle Gain + Body Recomposition",
        "experience_level": "Intermediate",
        "equipment": "Full Gym",
        "days_per_week": 4,
        "coach_note": "Sarah, this program is built around progressive overload with a focus on compound movements. We'll reassess after Week 2 and adjust volume based on your recovery.",
        "program_notes": {
            "progression": "Add 5 lbs to compounds weekly, or increase reps by 1-2 if weight increase stalls",
            "warm_up": "5 min cardio + dynamic stretching + 2 warm-up sets per first exercise",
            "cool_down": "5 min light cardio + static stretching for worked muscle groups",
            "rest_days": "Wednesday and weekends. Active recovery (walking, yoga) encouraged.",
        },
        "schedule": [
            {
                "day_number": 1, "day_name": "Monday", "focus": "Push / Chest & Shoulders",
                "warmup": "5 min incline walk + arm circles + 2x12 light bench press",
                "cooldown": "Chest and shoulder stretches, 5 min walk",
                "exercises": [
                    {"name": "Barbell Bench Press", "muscle_group": "Chest", "sets": 4, "reps": "6-8", "rest_seconds": 120, "notes": "Focus on bar path"},
                    {"name": "Incline Dumbbell Press", "muscle_group": "Chest", "sets": 3, "reps": "8-10", "rest_seconds": 90},
                    {"name": "Overhead Press", "muscle_group": "Shoulders", "sets": 3, "reps": "8-10", "rest_seconds": 90},
                    {"name": "Cable Lateral Raises", "muscle_group": "Shoulders", "sets": 3, "reps": "12-15", "rest_seconds": 60},
                    {"name": "Tricep Pushdowns", "muscle_group": "Arms", "sets": 3, "reps": "10-12", "rest_seconds": 60},
                ],
            },
            {
                "day_number": 2, "day_name": "Tuesday", "focus": "Pull / Back & Biceps",
                "warmup": "5 min row machine + band pull-aparts",
                "exercises": [
                    {"name": "Barbell Rows", "muscle_group": "Back", "sets": 4, "reps": "6-8", "rest_seconds": 120},
                    {"name": "Lat Pulldowns", "muscle_group": "Back", "sets": 3, "reps": "8-10", "rest_seconds": 90},
                    {"name": "Seated Cable Rows", "muscle_group": "Back", "sets": 3, "reps": "10-12", "rest_seconds": 90},
                    {"name": "Face Pulls", "muscle_group": "Shoulders", "sets": 3, "reps": "15-20", "rest_seconds": 60, "notes": "Rear delt focus"},
                    {"name": "Barbell Curls", "muscle_group": "Arms", "sets": 3, "reps": "10-12", "rest_seconds": 60},
                ],
            },
            {
                "day_number": 4, "day_name": "Thursday", "focus": "Legs / Quads & Glutes",
                "warmup": "5 min bike + bodyweight squats + hip circles",
                "exercises": [
                    {"name": "Barbell Back Squats", "muscle_group": "Legs", "sets": 4, "reps": "6-8", "rest_seconds": 150, "notes": "Below parallel"},
                    {"name": "Romanian Deadlifts", "muscle_group": "Legs", "sets": 3, "reps": "8-10", "rest_seconds": 120},
                    {"name": "Leg Press", "muscle_group": "Legs", "sets": 3, "reps": "10-12", "rest_seconds": 90},
                    {"name": "Walking Lunges", "muscle_group": "Legs", "sets": 3, "reps": "12 each", "rest_seconds": 90},
                    {"name": "Calf Raises", "muscle_group": "Legs", "sets": 4, "reps": "15-20", "rest_seconds": 60},
                ],
            },
            {
                "day_number": 5, "day_name": "Friday", "focus": "Upper / Full Upper Body",
                "exercises": [
                    {"name": "Dumbbell Shoulder Press", "muscle_group": "Shoulders", "sets": 3, "reps": "8-10", "rest_seconds": 90},
                    {"name": "Weighted Pull-ups", "muscle_group": "Back", "sets": 3, "reps": "6-8", "rest_seconds": 120},
                    {"name": "Dumbbell Bench Press", "muscle_group": "Chest", "sets": 3, "reps": "10-12", "rest_seconds": 90},
                    {"name": "Cable Rows", "muscle_group": "Back", "sets": 3, "reps": "10-12", "rest_seconds": 90},
                    {"name": "Hammer Curls + Overhead Tricep Ext", "muscle_group": "Arms", "sets": 3, "reps": "12 each", "rest_seconds": 60, "notes": "Superset"},
                ],
            },
        ],
    }
    path = os.path.join(OUTPUT_DIR, "sample_workout.pdf")
    engine.generate_to_file("workout_program", data, path)
    print(f"  Workout: {path}")
    return path


def test_nutrition():
    data = {
        "client_name": "Sarah Mitchell",
        "goal": "Body Recomposition",
        "weight_lbs": 155,
        "daily_targets": {"calories": 1850, "protein_g": 155, "carbs_g": 162, "fats_g": 62},
        "coach_note": "Focus on hitting your protein target first — it's the most important macro for recomp. Meal timing around workouts will help maximize muscle protein synthesis.",
        "meal_plan": [
            {"meal_name": "Meal 1 — Breakfast", "time": "7:00 AM", "foods": ["3 whole eggs scrambled", "1 cup spinach", "1 slice sourdough toast", "1/2 avocado"], "macros": {"calories": 450, "protein_g": 28, "carbs_g": 22, "fats_g": 30}},
            {"meal_name": "Meal 2 — Pre-Workout", "time": "11:00 AM", "foods": ["Greek yogurt (200g)", "1 scoop whey protein", "1/2 cup granola", "1 banana"], "macros": {"calories": 480, "protein_g": 45, "carbs_g": 55, "fats_g": 8}},
            {"meal_name": "Meal 3 — Post-Workout", "time": "2:00 PM", "foods": ["6 oz chicken breast", "1 cup white rice", "Mixed vegetables", "1 tbsp olive oil"], "macros": {"calories": 520, "protein_g": 45, "carbs_g": 52, "fats_g": 14}},
            {"meal_name": "Meal 4 — Dinner", "time": "7:00 PM", "foods": ["6 oz salmon fillet", "Sweet potato (medium)", "Broccoli (1 cup)", "Side salad with vinaigrette"], "macros": {"calories": 400, "protein_g": 37, "carbs_g": 33, "fats_g": 10}},
        ],
        "food_lists": {
            "protein_sources": ["Chicken breast", "Salmon", "Eggs", "Greek yogurt", "Whey protein", "Lean ground turkey", "Shrimp"],
            "carb_sources": ["White rice", "Sweet potatoes", "Oats", "Sourdough bread", "Bananas", "Berries", "Quinoa"],
            "fat_sources": ["Avocado", "Olive oil", "Almonds", "Eggs", "Salmon", "Nut butter"],
            "vegetables": ["Spinach", "Broccoli", "Bell peppers", "Asparagus", "Zucchini", "Mixed greens"],
        },
        "supplements": {
            "essential": ["Creatine monohydrate (5g/day)", "Vitamin D3 (2000 IU/day)", "Fish oil (2g/day)"],
            "performance": ["Whey protein (post-workout)", "Caffeine (pre-workout, 200mg)"],
            "optional": ["Magnesium glycinate (before bed)", "Zinc (25mg/day)"],
        },
        "hydration_oz": 100,
        "tips": [
            "Prep meals Sunday and Wednesday to stay consistent",
            "Eat protein within 2 hours of training",
            "If you miss a meal, don't skip — adjust portions to hit daily totals",
            "Track everything in MyFitnessPal for the first 2 weeks until portions feel intuitive",
        ],
    }
    path = os.path.join(OUTPUT_DIR, "sample_nutrition.pdf")
    engine.generate_to_file("nutrition_guide", data, path)
    print(f"  Nutrition: {path}")
    return path


def test_progress():
    data = {
        "client_name": "Mike Rodriguez",
        "report_period": "February 1 — February 28, 2026",
        "adherence_pct": 87.5,
        "coach_note": "Mike, outstanding month. Your consistency is paying off — the strength gains across the board show the program is working. Let's push the deadlift next month.",
        "metrics_history": [
            {"date": "Feb 1", "weight_lbs": 192.4, "body_fat_pct": 22.1},
            {"date": "Feb 8", "weight_lbs": 191.0, "body_fat_pct": 21.8},
            {"date": "Feb 15", "weight_lbs": 189.6, "body_fat_pct": 21.3},
            {"date": "Feb 22", "weight_lbs": 188.2, "body_fat_pct": 20.9},
            {"date": "Feb 28", "weight_lbs": 187.5, "body_fat_pct": 20.5},
        ],
        "strength_gains": [
            {"exercise": "Bench Press", "previous": "185 x 5", "current": "205 x 5", "change_pct": 10.8},
            {"exercise": "Squat", "previous": "225 x 5", "current": "245 x 5", "change_pct": 8.9},
            {"exercise": "Deadlift", "previous": "275 x 3", "current": "285 x 3", "change_pct": 3.6},
            {"exercise": "Overhead Press", "previous": "115 x 6", "current": "125 x 6", "change_pct": 8.7},
            {"exercise": "Barbell Row", "previous": "155 x 8", "current": "175 x 8", "change_pct": 12.9},
        ],
        "highlights": [
            "Hit first 205 lb bench press — lifetime PR",
            "Lost 4.9 lbs while getting stronger across all lifts",
            "87.5% workout adherence (7 of 8 sessions per 2-week block)",
            "Consistent meal prep — only 2 off-plan days all month",
        ],
        "areas_to_improve": [
            "Sleep consistency — aim for 7+ hours, lights out by 10:30 PM",
            "Deadlift lagging relative to other lifts — adding 1 extra accessory set",
            "Water intake dropped below target on 5 days",
        ],
        "next_phase": "Moving into a 4-week strength block with heavier loads (3-5 rep range on compounds). We'll drop volume slightly and focus on progressive overload. Nutrition stays the same — the recomp is working.",
    }
    path = os.path.join(OUTPUT_DIR, "sample_progress.pdf")
    engine.generate_to_file("progress_report", data, path)
    print(f"  Progress: {path}")
    return path


def test_onboarding():
    data = {
        "client_name": "Jessica Chen",
        "start_date": "March 10, 2026",
        "coach_name": "William Marceau",
        "welcome_message": "Jessica, welcome to coaching! I'm excited to work with you. This packet covers everything you need to know about how we'll work together over the coming weeks. Read through it before our kickoff call — it'll save us time and let us dive right into your plan.",
        "what_to_expect": [
            "Within 48 hours of our kickoff call, you'll receive your custom training program and nutrition protocol",
            "Every Monday, you'll get a check-in message — reply with your weekly update (weight, energy, any concerns)",
            "Your program gets updated monthly based on your progress data",
            "You have unlimited messaging access for questions between check-ins",
            "Monthly progress reports track your body composition, strength, and adherence",
        ],
        "communication_guidelines": {
            "check_ins": "Every Monday via SMS — reply with your weekly update",
            "response_time": "I respond within 12 hours on weekdays, 24 hours on weekends",
            "urgent_questions": "Text me directly. If it's training-related, include a video if possible",
            "form_checks": "Film from the side at hip height. Upload to our shared folder or send via text",
        },
        "weekly_schedule": {
            "Monday": "Check-in message (you send: weight, energy level, wins, concerns)",
            "Tuesday": "Program review + response from me",
            "Wednesday": "Mid-week motivation or training tip",
            "Thursday-Saturday": "Training days — reach out anytime for form checks",
            "Sunday": "Rest + meal prep. New week's focus sent in the evening",
        },
        "app_setup_steps": [
            "Join our Skool community at skool.com/unbreakable-9502",
            "Download MyFitnessPal and add me as a friend (wmarceau)",
            "Complete the intake form (link in your welcome email)",
            "Book your kickoff call at calendly.com/wmarceau/kickoff-call",
            "Take Day 1 progress photos (front, side, back — same lighting each time)",
        ],
        "faq": [
            {"q": "Can I cancel anytime?", "a": "Yes. $197/month, no contract, no cancellation fees. Just let me know."},
            {"q": "What if I travel or miss a workout?", "a": "We'll adjust your program. Travel workouts, hotel gym alternatives, or modified split — I've got you covered."},
            {"q": "Do I need to be interested in peptides?", "a": "Not at all. Peptide knowledge informs how I design programs, but it's not required. Your plan works with or without peptides."},
            {"q": "How often do I need to train?", "a": "Most clients train 3-5 days per week, 45-75 minutes per session. We'll design around your schedule."},
        ],
        "important_links": {
            "stripe_billing": "buy.stripe.com (manage your subscription)",
            "calendly": "calendly.com/wmarceau/30min",
            "skool_community": "skool.com/unbreakable-9502",
            "website": "marceausolutions.com",
        },
    }
    path = os.path.join(OUTPUT_DIR, "sample_onboarding.pdf")
    engine.generate_to_file("onboarding_packet", data, path)
    print(f"  Onboarding: {path}")
    return path


def test_peptide():
    data = {
        "client_name": "David Park",
        "title": "Evidence-Based Peptide Guide",
        "intro_text": "This guide provides an overview of peptides relevant to fitness and body composition goals. All information is evidence-based, and any protocols involving peptide use require physician oversight. This is education, not medical advice.",
        "coach_note": "David, based on our conversation about your recovery and body comp goals, I've put together profiles on the compounds most relevant to you. Read through this before our next check-in and we can discuss questions.",
        "compounds": [
            {
                "name": "Tesamorelin (Egrifta)",
                "category": "GHRH Analog",
                "evidence_rating": "Strong",
                "mechanism": "Stimulates pituitary gland to release growth hormone naturally. FDA-approved for HIV-associated lipodystrophy. The most clinically studied GHRH analog available.",
                "benefits": ["Visceral fat reduction (clinically proven)", "Improved body composition without muscle loss", "Better lipid profiles in studies", "Natural GH pulsatility preserved"],
                "side_effects": ["Injection site reactions", "Joint pain (arthralgia)", "Peripheral edema", "Increased insulin resistance in some individuals"],
                "notes": "Most relevant for your fat loss goals. Requires prescription and lab monitoring.",
            },
            {
                "name": "Ipamorelin + CJC-1295",
                "category": "GH Secretagogue Combo",
                "evidence_rating": "Moderate",
                "mechanism": "Ipamorelin is a selective GH secretagogue (mimics ghrelin). CJC-1295 extends GH release duration. Together they create a sustained, natural-pattern GH elevation.",
                "benefits": ["Enhanced recovery between training sessions", "Improved sleep quality", "Moderate fat loss effects", "Synergistic with training adaptations"],
                "side_effects": ["Water retention (transient)", "Increased hunger (from ghrelin mimicry)", "Tingling/numbness (paresthesia)", "Headache"],
                "notes": "Often used as an alternative to Tesamorelin. Less clinical data but widely used in anti-aging medicine.",
            },
            {
                "name": "BPC-157",
                "category": "Body Protection Compound",
                "evidence_rating": "Emerging",
                "mechanism": "A pentadecapeptide (15 amino acids) derived from gastric juice. Studied primarily in animal models for tissue repair, gut healing, and angiogenesis.",
                "benefits": ["Accelerated soft tissue healing (animal studies)", "Gut lining repair", "Anti-inflammatory properties", "Tendon and ligament support"],
                "side_effects": ["Limited human safety data", "Unknown long-term effects", "Quality control issues with compounded sources"],
                "notes": "Promising but lacks human clinical trials. I include it for awareness, not recommendation. Always discuss with your physician.",
            },
        ],
        "decision_framework": {
            "consider_if": [
                "You've already optimized sleep, nutrition, and training",
                "You're over 30 and noticing recovery decline",
                "You want to work with physicians, not gray market sources",
                "You're committed to regular lab work and monitoring",
                "You have realistic expectations about outcomes",
            ],
            "hold_off_if": [
                "Your sleep, nutrition, or training are still inconsistent",
                "You're looking for a shortcut or magic solution",
                "You're under 25-30 with naturally optimized hormones",
                "You have unaddressed health conditions",
                "You're not willing to invest in proper medical oversight",
            ],
        },
    }
    path = os.path.join(OUTPUT_DIR, "sample_peptide.pdf")
    engine.generate_to_file("peptide_guide", data, path)
    print(f"  Peptide: {path}")
    return path


def test_challenge():
    data = {
        "challenge_name": "7-Day Body Recomp Challenge",
        "duration_days": 7,
        "difficulty": "Beginner-Intermediate",
        "equipment_needed": "Dumbbells + Bodyweight",
        "coach_note": "This challenge is designed to build a foundation. Don't skip the rest days — recovery is where the gains happen. Text me anytime if you need help with form.",
        "rules": [
            "Complete each day's workout within the day",
            "Hit your protein target (1g per lb of bodyweight)",
            "Drink at least 80 oz of water daily",
            "Post your workout completion in the Skool community",
            "Take a Day 1 and Day 7 progress photo",
        ],
        "days": [
            {
                "day_number": 1, "title": "Foundation — Full Body Baseline",
                "motivation_quote": "The secret of getting ahead is getting started.",
                "exercises": [
                    {"name": "Goblet Squats", "sets": 3, "reps": "12", "rest_seconds": 60},
                    {"name": "Push-ups", "sets": 3, "reps": "AMRAP", "rest_seconds": 60},
                    {"name": "Dumbbell Rows", "sets": 3, "reps": "10 each", "rest_seconds": 60},
                    {"name": "Plank Hold", "sets": 3, "reps": "30 sec", "rest_seconds": 45},
                ],
                "tip": "Record your reps and weights — we'll compare on Day 7.",
            },
            {
                "day_number": 2, "title": "Nutrition Lock-In",
                "motivation_quote": "You can't out-train a bad diet.",
                "exercises": [
                    {"name": "Romanian Deadlifts", "sets": 3, "reps": "10", "rest_seconds": 90},
                    {"name": "Overhead Press", "sets": 3, "reps": "10", "rest_seconds": 60},
                    {"name": "Lunges", "sets": 3, "reps": "10 each", "rest_seconds": 60},
                    {"name": "Face Pulls (band)", "sets": 3, "reps": "15", "rest_seconds": 45},
                ],
                "tip": "Focus on protein timing: eat within 2 hours of your workout.",
            },
            {
                "day_number": 3, "title": "Progressive Overload",
                "motivation_quote": "Small daily improvements lead to stunning results.",
                "exercises": [
                    {"name": "Goblet Squats", "sets": 3, "reps": "12", "rest_seconds": 60, "notes": "+5 lbs from Day 1"},
                    {"name": "Push-ups", "sets": 3, "reps": "AMRAP +2", "rest_seconds": 60, "notes": "Beat Day 1 count"},
                    {"name": "Dumbbell Rows", "sets": 3, "reps": "10 each", "rest_seconds": 60, "notes": "+5 lbs from Day 1"},
                    {"name": "Plank Hold", "sets": 3, "reps": "40 sec", "rest_seconds": 45, "notes": "+10 sec from Day 1"},
                ],
                "tip": "Progressive overload = doing slightly more than last time. This is how muscles grow.",
            },
            {
                "day_number": 4, "title": "Nutrition Check",
                "exercises": [],
                "motivation_quote": "Rest is not laziness. It's preparation for the next push.",
                "tip": "Active recovery day. Take a 30-minute walk. Review your protein intake — are you hitting your target? Adjust meals if needed.",
            },
            {
                "day_number": 5, "title": "Active Recovery",
                "exercises": [
                    {"name": "30-Minute Walk", "sets": 1, "reps": "30 min", "rest_seconds": 0},
                    {"name": "Foam Rolling", "sets": 1, "reps": "10 min", "rest_seconds": 0},
                    {"name": "Stretching Routine", "sets": 1, "reps": "15 min", "rest_seconds": 0},
                ],
                "tip": "Hydration check: are you at 80+ oz today? Your muscles are 75% water.",
            },
            {
                "day_number": 6, "title": "Final Push — Full Body Blast",
                "motivation_quote": "One more day. Give it everything.",
                "exercises": [
                    {"name": "Dumbbell Squats", "sets": 4, "reps": "12", "rest_seconds": 60},
                    {"name": "Push-up Variations", "sets": 4, "reps": "AMRAP", "rest_seconds": 60},
                    {"name": "Bent Over Rows", "sets": 4, "reps": "10", "rest_seconds": 60},
                    {"name": "Shoulder Press", "sets": 3, "reps": "10", "rest_seconds": 60},
                    {"name": "Plank Hold", "sets": 3, "reps": "45 sec", "rest_seconds": 45},
                ],
                "tip": "Extra set on everything today. You're stronger than Day 1 — prove it.",
            },
            {
                "day_number": 7, "title": "Results Day",
                "exercises": [],
                "motivation_quote": "You just did what most people quit after Day 2.",
                "tip": "Take your Day 7 photo. Compare with Day 1. Share your results in the community. Ready to keep going? Talk to me about coaching.",
            },
        ],
    }
    path = os.path.join(OUTPUT_DIR, "sample_challenge.pdf")
    engine.generate_to_file("challenge_workout", data, path)
    print(f"  Challenge: {path}")
    return path


def test_generic():
    data = {
        "title": "Welcome to the Unbreakable Community",
        "subtitle": "Everything you need to know",
        "author": "William Marceau",
        "date": "March 2026",
        "content_markdown": """## What Is Unbreakable?

Unbreakable is a **private fitness community** for people committed to evidence-based training, real accountability, and long-term results. No bro science. No gatekeeping. Just a group of people helping each other get better.

## Community Rules

- **Be respectful** — we're all at different stages. Lift others up.
- **Stay evidence-based** — cite sources when making claims about training or nutrition.
- **No spam or self-promotion** — this is a coaching community, not a marketplace.
- **Show up consistently** — post your workouts, share your wins, ask for help.

## What You'll Find Inside

- Weekly workout challenges
- Live Q&A sessions with Coach William
- Peer accountability groups
- Peptide education modules (for those interested)
- Exclusive discounts on coaching and digital programs

## How to Get the Most Out of It

1. Introduce yourself in the Welcome thread
2. Set your weekly training goal
3. Post at least 3 times per week (workouts, meals, questions)
4. Engage with other members — comment, encourage, share tips

---

*This community is your support system. Use it. The people who engage the most get the best results.*
""",
    }
    path = os.path.join(OUTPUT_DIR, "sample_generic.pdf")
    engine.generate_to_file("generic_document", data, path)
    print(f"  Generic: {path}")
    return path


if __name__ == "__main__":
    print("Generating sample PDFs...\n")
    print(f"Available templates: {engine.list_templates()}\n")

    paths = []
    tests = [
        ("Workout Program", test_workout),
        ("Nutrition Guide", test_nutrition),
        ("Progress Report", test_progress),
        ("Onboarding Packet", test_onboarding),
        ("Peptide Guide", test_peptide),
        ("Challenge Workout", test_challenge),
        ("Generic Document", test_generic),
    ]

    for name, fn in tests:
        try:
            p = fn()
            paths.append(p)
            # Verify it's a valid PDF
            with open(p, "rb") as f:
                header = f.read(5)
                assert header == b"%PDF-", f"{name}: Invalid PDF header"
            print(f"    Valid PDF ({os.path.getsize(p):,} bytes)")
        except Exception as e:
            print(f"  FAILED: {name} — {e}")
            import traceback
            traceback.print_exc()

    print(f"\nAll {len(paths)} PDFs generated in: {OUTPUT_DIR}")
    print("Opening all PDFs for review...")

    for p in paths:
        os.system(f'open "{p}"')
