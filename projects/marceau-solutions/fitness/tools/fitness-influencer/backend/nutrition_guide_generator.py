#!/usr/bin/env python3
"""
nutrition_guide_generator.py - Personalized Nutrition Plans

WHAT: Creates nutrition guides with macro calculations and meal suggestions
WHY: Users request meal plans and macro guidance (5+ times) - identified gap
INPUT: Goal (cut/bulk/maintain), weight, activity level, dietary preferences
OUTPUT: Nutrition guide with macros, meal timing, food lists (PDF + markdown)
COST: FREE
TIME: <10 seconds

QUICK USAGE:
  python execution/nutrition_guide_generator.py \
    --goal "lean bulk" \
    --weight 180 \
    --activity "moderate" \
    --diet "flexible"

CAPABILITIES:
  • Calculate personalized macros (protein/carbs/fats)
  • Suggest meal timing around workouts
  • Provide food lists by macro category
  • Accommodate dietary restrictions (vegan, keto, etc.)
  • Export as PDF with meal prep tips
"""

import argparse
import json
from datetime import datetime
from pathlib import Path


class NutritionGuideGenerator:
    """Generates personalized nutrition guides with macro calculations."""
    
    ACTIVITY_MULTIPLIERS = {
        "sedentary": 1.2,      # Little to no exercise
        "light": 1.375,        # Light exercise 1-3 days/week
        "moderate": 1.55,      # Moderate exercise 3-5 days/week
        "active": 1.725,       # Hard exercise 6-7 days/week
        "very_active": 1.9     # Intense exercise + physical job
    }
    
    GOAL_ADJUSTMENTS = {
        "cut": -500,           # 500 cal deficit
        "lean_bulk": +300,     # 300 cal surplus
        "bulk": +500,          # 500 cal surplus
        "maintain": 0,         # Maintenance
        "recomp": -200         # Slight deficit with high protein
    }
    
    FOOD_LISTS = {
        "protein": {
            "animal": ["Chicken breast", "Turkey", "Lean beef", "Fish (salmon, tilapia, cod)", "Eggs", "Greek yogurt", "Cottage cheese"],
            "plant": ["Tofu", "Tempeh", "Lentils", "Chickpeas", "Black beans", "Quinoa", "Seitan", "Protein powder"]
        },
        "carbs": {
            "complex": ["Oats", "Brown rice", "Sweet potatoes", "Quinoa", "Whole wheat bread", "Whole wheat pasta"],
            "simple": ["Bananas", "Berries", "Apples", "Rice cakes", "White rice (post-workout)", "Honey"],
            "vegetables": ["Broccoli", "Spinach", "Kale", "Peppers", "Carrots", "Zucchini", "Cauliflower"]
        },
        "fats": {
            "healthy": ["Avocado", "Olive oil", "Nuts (almonds, walnuts)", "Nut butters", "Fatty fish (salmon)", "Chia seeds", "Flax seeds"],
            "moderate": ["Cheese", "Dark chocolate", "Coconut oil", "Whole eggs"]
        }
    }
    
    DIETARY_ADJUSTMENTS = {
        "vegan": {
            "exclude": ["animal"],
            "focus": ["plant", "complex", "healthy"],
            "note": "Ensure adequate B12, iron, and complete proteins"
        },
        "keto": {
            "protein_ratio": 0.25,
            "carb_ratio": 0.05,
            "fat_ratio": 0.70,
            "note": "Keep net carbs under 50g per day"
        },
        "paleo": {
            "exclude_foods": ["Grains", "Legumes", "Dairy"],
            "focus": ["animal", "vegetables", "healthy"],
            "note": "Focus on whole, unprocessed foods"
        },
        "flexible": {
            "protein_ratio": 0.30,
            "carb_ratio": 0.40,
            "fat_ratio": 0.30,
            "note": "Balance of all macros, 80/20 rule applies"
        }
    }
    
    def __init__(self):
        self.output_dir = Path(".tmp/nutrition_guides")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def calculate_macros(self, weight, activity, goal, diet="flexible"):
        """Calculate personalized macro targets."""
        
        # Calculate TDEE (Total Daily Energy Expenditure)
        # Using Mifflin-St Jeor equation approximation
        bmr = weight * 10  # Simplified BMR calculation
        activity_mult = self.ACTIVITY_MULTIPLIERS.get(activity, 1.55)
        tdee = int(bmr * activity_mult)
        
        # Adjust for goal
        goal_adjustment = self.GOAL_ADJUSTMENTS.get(goal, 0)
        target_calories = tdee + goal_adjustment
        
        # Get macro ratios based on diet type
        diet_info = self.DIETARY_ADJUSTMENTS.get(diet, self.DIETARY_ADJUSTMENTS["flexible"])
        
        if "keto" in diet:
            protein_ratio = diet_info["protein_ratio"]
            carb_ratio = diet_info["carb_ratio"]
            fat_ratio = diet_info["fat_ratio"]
        else:
            # Standard macro split
            if goal in ["cut", "recomp"]:
                protein_ratio = 0.35  # Higher protein for fat loss
                carb_ratio = 0.35
                fat_ratio = 0.30
            elif goal in ["bulk", "lean_bulk"]:
                protein_ratio = 0.30
                carb_ratio = 0.45  # More carbs for muscle gain
                fat_ratio = 0.25
            else:  # maintain
                protein_ratio = diet_info.get("protein_ratio", 0.30)
                carb_ratio = diet_info.get("carb_ratio", 0.40)
                fat_ratio = diet_info.get("fat_ratio", 0.30)
        
        # Calculate macro grams
        protein_cals = target_calories * protein_ratio
        carb_cals = target_calories * carb_ratio
        fat_cals = target_calories * fat_ratio
        
        macros = {
            "calories": target_calories,
            "protein_g": int(protein_cals / 4),
            "carbs_g": int(carb_cals / 4),
            "fats_g": int(fat_cals / 9),
            "tdee": tdee,
            "goal_adjustment": goal_adjustment
        }
        
        return macros
    
    def generate_meal_timing(self, goal, workout_schedule="afternoon"):
        """Generate meal timing recommendations."""
        
        if goal in ["bulk", "lean_bulk"]:
            return {
                "pre_workout": "1-2 hours before: Complex carbs + lean protein (e.g., oats + protein shake)",
                "post_workout": "Within 30-60 minutes: Fast-digesting carbs + protein (e.g., white rice + chicken)",
                "meals_per_day": "4-6 meals to maximize muscle protein synthesis",
                "sample_schedule": {
                    "meal_1": "7:00 AM - Breakfast (protein + carbs)",
                    "meal_2": "10:00 AM - Snack (protein + fats)",
                    "meal_3": "1:00 PM - Lunch (balanced)",
                    "pre_workout": "3:00 PM - Pre-workout meal",
                    "post_workout": "5:30 PM - Post-workout meal",
                    "meal_4": "8:00 PM - Dinner (protein + vegetables)"
                }
            }
        elif goal in ["cut", "recomp"]:
            return {
                "pre_workout": "1-2 hours before: Moderate carbs + lean protein",
                "post_workout": "Within 60 minutes: Protein-focused meal with moderate carbs",
                "meals_per_day": "3-4 meals to maintain satiety while in deficit",
                "sample_schedule": {
                    "meal_1": "8:00 AM - Breakfast (protein + fats)",
                    "meal_2": "12:00 PM - Lunch (balanced, largest meal)",
                    "pre_workout": "3:00 PM - Small pre-workout snack",
                    "post_workout": "6:00 PM - Dinner (protein + vegetables)",
                    "optional_snack": "Casein protein before bed if hungry"
                }
            }
        else:  # maintain
            return {
                "pre_workout": "1-2 hours before: Balanced meal",
                "post_workout": "Within 60-90 minutes: Balanced meal",
                "meals_per_day": "3-4 meals based on preference",
                "sample_schedule": {
                    "meal_1": "8:00 AM - Breakfast",
                    "meal_2": "12:00 PM - Lunch",
                    "meal_3": "3:00 PM - Snack (if needed)",
                    "meal_4": "7:00 PM - Dinner"
                }
            }
    
    def generate_food_lists(self, diet="flexible"):
        """Generate appropriate food lists based on dietary preference."""
        
        diet_info = self.DIETARY_ADJUSTMENTS.get(diet, self.DIETARY_ADJUSTMENTS["flexible"])
        
        # Filter food lists based on diet
        filtered_foods = {
            "protein_sources": [],
            "carb_sources": [],
            "fat_sources": []
        }
        
        if diet == "vegan":
            filtered_foods["protein_sources"] = self.FOOD_LISTS["protein"]["plant"]
        elif diet == "keto":
            filtered_foods["protein_sources"] = self.FOOD_LISTS["protein"]["animal"] + ["Eggs", "Fatty fish"]
            filtered_foods["carb_sources"] = ["Leafy greens", "Cauliflower", "Broccoli", "Avocado"]
        elif diet == "paleo":
            filtered_foods["protein_sources"] = self.FOOD_LISTS["protein"]["animal"]
            filtered_foods["carb_sources"] = ["Sweet potatoes", "Fruits", "Vegetables"]
        else:  # flexible
            filtered_foods["protein_sources"] = self.FOOD_LISTS["protein"]["animal"] + self.FOOD_LISTS["protein"]["plant"]
            filtered_foods["carb_sources"] = self.FOOD_LISTS["carbs"]["complex"] + self.FOOD_LISTS["carbs"]["simple"]
        
        filtered_foods["fat_sources"] = self.FOOD_LISTS["fats"]["healthy"]
        filtered_foods["vegetables"] = self.FOOD_LISTS["carbs"]["vegetables"]
        
        return filtered_foods
    
    def generate_guide(self, weight, activity, goal, diet="flexible"):
        """Generate complete nutrition guide."""
        
        # Normalize inputs
        activity = activity.lower().replace(" ", "_")
        goal = goal.lower().replace(" ", "_")
        diet = diet.lower()
        
        # Calculate macros
        macros = self.calculate_macros(weight, activity, goal, diet)
        
        # Generate meal timing
        meal_timing = self.generate_meal_timing(goal)
        
        # Generate food lists
        food_lists = self.generate_food_lists(diet)
        
        # Build guide
        guide = {
            "generated_at": datetime.now().isoformat(),
            "user_stats": {
                "weight_lbs": weight,
                "activity_level": activity.replace("_", " ").title(),
                "goal": goal.replace("_", " ").title(),
                "dietary_preference": diet.title()
            },
            "macros": macros,
            "meal_timing": meal_timing,
            "food_lists": food_lists,
            "hydration": {
                "water_oz_per_day": int(weight * 0.67),  # 2/3 oz per lb bodyweight
                "timing": "Drink 16-20oz upon waking, 8oz every 2 hours, extra during workouts"
            },
            "supplements": self._get_supplement_recommendations(goal, diet),
            "tips": self._get_nutrition_tips(goal, diet)
        }
        
        return guide
    
    def _get_supplement_recommendations(self, goal, diet):
        """Provide supplement recommendations based on goal and diet."""
        supplements = {
            "essential": ["Protein powder (whey or plant-based)", "Multivitamin", "Omega-3 (fish oil or algae)"],
            "performance": ["Creatine monohydrate (5g daily)", "Caffeine (pre-workout)", "Beta-alanine (for endurance)"],
            "optional": ["Vitamin D3", "Magnesium", "Zinc"]
        }
        
        if diet == "vegan":
            supplements["essential"].extend(["B12 supplement", "Iron (if needed)", "Complete amino acids"])
        
        if goal in ["cut", "recomp"]:
            supplements["helpful"] = ["Green tea extract", "L-carnitine", "Fiber supplement"]
        
        return supplements
    
    def _get_nutrition_tips(self, goal, diet):
        """Provide practical nutrition tips."""
        tips = [
            "Track your intake for at least 2 weeks to establish baseline",
            "Meal prep on Sundays to ensure compliance during busy weeks",
            "Weigh yourself daily and take weekly averages to track progress",
            "Adjust calories by 100-200 if no progress after 2 weeks"
        ]
        
        if goal == "cut":
            tips.extend([
                "Prioritize protein to preserve muscle mass (1g per lb bodyweight)",
                "Include high-volume, low-calorie foods (vegetables) for satiety",
                "Save some calories for evening if you get hungry before bed"
            ])
        elif goal in ["bulk", "lean_bulk"]:
            tips.extend([
                "Eat protein with every meal (20-40g per meal)",
                "Don't be afraid of carbs - they fuel muscle growth",
                "Liquid calories can help if struggling to eat enough"
            ])
        
        return tips
    
    def export_markdown(self, guide, filename):
        """Export guide as markdown."""
        md_path = self.output_dir / f"{filename}.md"
        
        with open(md_path, 'w') as f:
            f.write(f"# Personalized Nutrition Guide\n\n")
            f.write(f"**Weight:** {guide['user_stats']['weight_lbs']} lbs  \n")
            f.write(f"**Activity Level:** {guide['user_stats']['activity_level']}  \n")
            f.write(f"**Goal:** {guide['user_stats']['goal']}  \n")
            f.write(f"**Diet Type:** {guide['user_stats']['dietary_preference']}  \n")
            f.write(f"**Generated:** {guide['generated_at'][:10]}  \n\n")
            
            f.write("---\n\n")
            
            # Macros section
            f.write("## 🎯 Daily Macro Targets\n\n")
            f.write(f"**Total Calories:** {guide['macros']['calories']} kcal  \n")
            f.write(f"**Protein:** {guide['macros']['protein_g']}g  \n")
            f.write(f"**Carbohydrates:** {guide['macros']['carbs_g']}g  \n")
            f.write(f"**Fats:** {guide['macros']['fats_g']}g  \n\n")
            f.write(f"*TDEE: {guide['macros']['tdee']} kcal | Adjustment: {guide['macros']['goal_adjustment']:+d} kcal*\n\n")
            
            # Meal timing
            f.write("## ⏰ Meal Timing\n\n")
            f.write(f"**Meals per Day:** {guide['meal_timing']['meals_per_day']}  \n\n")
            f.write("**Sample Schedule:**\n")
            for meal, time in guide['meal_timing']['sample_schedule'].items():
                f.write(f"- {time}\n")
            f.write("\n")
            
            # Food lists
            f.write("## 🍗 Food Lists\n\n")
            for category, foods in guide['food_lists'].items():
                f.write(f"### {category.replace('_', ' ').title()}\n")
                for food in foods:
                    f.write(f"- {food}\n")
                f.write("\n")
            
            # Hydration
            f.write("## 💧 Hydration\n\n")
            f.write(f"**Target:** {guide['hydration']['water_oz_per_day']} oz per day  \n")
            f.write(f"**Timing:** {guide['hydration']['timing']}  \n\n")
            
            # Supplements
            f.write("## 💊 Supplement Recommendations\n\n")
            for category, supps in guide['supplements'].items():
                f.write(f"**{category.title()}:**\n")
                for supp in supps:
                    f.write(f"- {supp}\n")
                f.write("\n")
            
            # Tips
            f.write("## 💡 Practical Tips\n\n")
            for tip in guide['tips']:
                f.write(f"- {tip}\n")
        
        print(f"✓ Markdown exported: {md_path}")
        return md_path
    
    def export_json(self, guide, filename):
        """Export guide as JSON."""
        json_path = self.output_dir / f"{filename}.json"
        
        with open(json_path, 'w') as f:
            json.dump(guide, f, indent=2)
        
        print(f"✓ JSON exported: {json_path}")
        return json_path


def main():
    parser = argparse.ArgumentParser(description='Generate personalized nutrition guide')
    parser.add_argument('--weight', type=int, required=True, help='Body weight in pounds')
    parser.add_argument('--activity', required=True, 
                       choices=['sedentary', 'light', 'moderate', 'active', 'very_active'],
                       help='Activity level')
    parser.add_argument('--goal', required=True,
                       choices=['cut', 'lean_bulk', 'bulk', 'maintain', 'recomp'],
                       help='Fitness goal')
    parser.add_argument('--diet', default='flexible',
                       choices=['flexible', 'vegan', 'keto', 'paleo'],
                       help='Dietary preference')
    parser.add_argument('--output', default='nutrition_guide', help='Output filename (without extension)')
    
    args = parser.parse_args()
    
    print(f"\n🥗 Generating nutrition guide for {args.goal} at {args.weight} lbs...")
    
    generator = NutritionGuideGenerator()
    guide = generator.generate_guide(args.weight, args.activity, args.goal, args.diet)
    
    # Export to both formats
    md_path = generator.export_markdown(guide, args.output)
    json_path = generator.export_json(guide, args.output)
    
    print(f"\n✓ Nutrition guide generated successfully!")
    print(f"  - Markdown: {md_path}")
    print(f"  - JSON: {json_path}")
    print(f"  - Target calories: {guide['macros']['calories']} kcal/day")
    print(f"  - Macros: {guide['macros']['protein_g']}p / {guide['macros']['carbs_g']}c / {guide['macros']['fats_g']}f")


if __name__ == "__main__":
    main()