# Education Scenarios: Workout Plan Generator

*Tool: `generate_workout_plan`*
*Module: workout_plan_generator.py*
*Category: 1 (FREE)*

## Persona

**Sarah M., Personal Trainer**
- Has 50+ clients with varying fitness levels
- Needs to quickly create customized workout plans
- Clients range from complete beginners to competitive athletes
- Equipment varies: home gym, full gym, minimal equipment

---

## Scenario 1: Beginner Client - Home Workout

**Goal:** Create a beginner-friendly plan for a client with minimal equipment at home

**Input:**
```python
{
    "goal": "muscle_gain",
    "experience": "beginner",
    "days_per_week": 3,
    "equipment": "minimal"
}
```

**Expected Output:**
- 3-day split (e.g., Full Body x3)
- Bodyweight exercises + resistance bands
- Clear rep ranges (higher for beginners: 12-15)
- Proper warm-up and cool-down included
- Exercise alternatives provided

**Test Command:**
```bash
python -c "
from src.workout_plan_generator import WorkoutPlanGenerator
gen = WorkoutPlanGenerator()
plan = gen.generate_plan('muscle_gain', 'beginner', 3, 'minimal')
print('Days:', len(plan.get('days', [])))
for day in plan.get('days', []):
    print(f'  {day[\"name\"]}: {len(day.get(\"exercises\", []))} exercises')
"
```

**Pass Criteria:**
- [ ] Returns 3 training days
- [ ] Exercises are appropriate for minimal equipment
- [ ] Rep ranges are beginner-appropriate (10-15)
- [ ] No advanced movements (Olympic lifts, etc.)

---

## Scenario 2: Intermediate Client - Full Gym

**Goal:** Create a muscle-building program for someone with gym access

**Input:**
```python
{
    "goal": "muscle_gain",
    "experience": "intermediate",
    "days_per_week": 5,
    "equipment": "full_gym"
}
```

**Expected Output:**
- 5-day split (e.g., PPL + Upper/Lower or Bro Split)
- Compound movements prioritized
- Progressive overload guidance
- Moderate rep ranges (8-12)

**Test Command:**
```bash
python -c "
from src.workout_plan_generator import WorkoutPlanGenerator
gen = WorkoutPlanGenerator()
plan = gen.generate_plan('muscle_gain', 'intermediate', 5, 'full_gym')
print('Days:', len(plan.get('days', [])))
print('Goal:', plan.get('goal'))
print('Split type:', plan.get('split_type', 'Not specified'))
"
```

**Pass Criteria:**
- [ ] Returns 5 training days
- [ ] Includes barbell/dumbbell compound movements
- [ ] Split makes logical sense (not random exercises)
- [ ] Volume is appropriate for intermediate

---

## Scenario 3: Advanced Client - Strength Focus

**Goal:** Create a strength-focused program for an experienced lifter

**Input:**
```python
{
    "goal": "strength",
    "experience": "advanced",
    "days_per_week": 4,
    "equipment": "full_gym"
}
```

**Expected Output:**
- 4-day split optimized for strength
- Focus on big 3 (squat, bench, deadlift)
- Lower rep ranges (3-6)
- Adequate rest between sets guidance
- Periodization suggestions

**Test Command:**
```bash
python -c "
from src.workout_plan_generator import WorkoutPlanGenerator
gen = WorkoutPlanGenerator()
plan = gen.generate_plan('strength', 'advanced', 4, 'full_gym')
exercises = []
for day in plan.get('days', []):
    exercises.extend([e['name'] for e in day.get('exercises', [])])
print('Total exercises:', len(exercises))
has_compounds = any(e in str(exercises).lower() for e in ['squat', 'deadlift', 'bench', 'press'])
print('Has compound lifts:', has_compounds)
"
```

**Pass Criteria:**
- [ ] Returns 4 training days
- [ ] Includes squat, bench, deadlift variations
- [ ] Rep ranges are strength-appropriate (3-6)
- [ ] Rest periods are longer (3-5 min for main lifts)

---

## Scenario 4: Endurance Goal - Home Gym

**Goal:** Create a plan for cardiovascular endurance with limited equipment

**Input:**
```python
{
    "goal": "endurance",
    "experience": "intermediate",
    "days_per_week": 4,
    "equipment": "home_gym"
}
```

**Expected Output:**
- Circuit-style training
- Higher rep ranges (15-20+)
- Cardio integration
- Minimal rest between exercises
- Heart rate guidance

**Test Command:**
```bash
python -c "
from src.workout_plan_generator import WorkoutPlanGenerator
gen = WorkoutPlanGenerator()
plan = gen.generate_plan('endurance', 'intermediate', 4, 'home_gym')
print('Plan generated:', bool(plan))
print('Goal:', plan.get('goal'))
"
```

**Pass Criteria:**
- [ ] Returns valid plan
- [ ] Exercises suit endurance goals
- [ ] Can be done with home gym equipment

---

## Edge Case 1: Invalid Fitness Level

**Goal:** Test error handling for invalid input

**Input:**
```python
{
    "goal": "muscle_gain",
    "experience": "expert_master",  # Invalid
    "days_per_week": 4,
    "equipment": "full_gym"
}
```

**Expected Output:**
- Graceful error OR defaults to closest valid level

**Test Command:**
```bash
python -c "
from src.workout_plan_generator import WorkoutPlanGenerator
gen = WorkoutPlanGenerator()
try:
    plan = gen.generate_plan('muscle_gain', 'expert_master', 4, 'full_gym')
    print('Result:', 'Accepted invalid input' if plan else 'Rejected')
except Exception as e:
    print('Error handled:', str(e)[:50])
"
```

**Pass Criteria:**
- [ ] Does not crash
- [ ] Either rejects with helpful error OR defaults gracefully

---

## Edge Case 2: Minimum Days (3)

**Input:**
```python
{
    "goal": "muscle_gain",
    "experience": "beginner",
    "days_per_week": 3,  # Minimum
    "equipment": "minimal"
}
```

**Pass Criteria:**
- [ ] Returns exactly 3 days
- [ ] Full body or appropriate split for 3 days

---

## Edge Case 3: Maximum Days (6)

**Input:**
```python
{
    "goal": "muscle_gain",
    "experience": "advanced",
    "days_per_week": 6,  # Maximum
    "equipment": "full_gym"
}
```

**Pass Criteria:**
- [ ] Returns exactly 6 days
- [ ] Includes appropriate rest/recovery guidance
- [ ] Split allows muscle recovery (not same muscles daily)

---

## Batch Test Script

Run all scenarios:
```bash
cd /Users/williammarceaujr./dev-sandbox/projects/fitness-influencer

python -c "
from src.workout_plan_generator import WorkoutPlanGenerator
gen = WorkoutPlanGenerator()

scenarios = [
    ('muscle_gain', 'beginner', 3, 'minimal'),
    ('muscle_gain', 'intermediate', 5, 'full_gym'),
    ('strength', 'advanced', 4, 'full_gym'),
    ('endurance', 'intermediate', 4, 'home_gym'),
]

print('Running workout plan scenarios...')
for goal, exp, days, equip in scenarios:
    try:
        plan = gen.generate_plan(goal, exp, days, equip)
        status = '✅' if plan and len(plan.get('days', [])) == days else '❌'
        print(f'{status} {goal}/{exp}/{days}days/{equip}')
    except Exception as e:
        print(f'❌ {goal}/{exp}/{days}days/{equip} - Error: {e}')
print('Done!')
"
```

---

## Success Criteria Summary

| Scenario | Expected Days | Key Check |
|----------|---------------|-----------|
| Beginner Home | 3 | Minimal equipment exercises |
| Intermediate Gym | 5 | Compound movements |
| Advanced Strength | 4 | Big 3 lifts, low reps |
| Endurance Home | 4 | Circuit/cardio focus |
| Edge: Invalid level | - | No crash |
| Edge: Min days | 3 | Full body split |
| Edge: Max days | 6 | Recovery guidance |
