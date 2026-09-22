# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Seed script to populate Firestore 'recipes' collection for PantryPal AI.

Hardcodes GCP project ID 'qwiklabs-gcp-01-b551540f472b'.
"""

from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-01-b551540f472b"
COLLECTION_NAME = "recipes"


def seed_recipes():
    print(f"Connecting to Firestore for project: '{PROJECT_ID}'...")
    db = firestore.Client(project=PROJECT_ID)

    recipes = [
        {
            "recipe_id": "spinach_egg_tacos",
            "title": "10-Minute Spinach & Egg Breakfast Tacos",
            "cooking_style": "15-min rush",
            "prep_time_minutes": 10,
            "difficulty": "Easy",
            "dietary_tags": ["vegetarian", "nut-free"],
            "ingredients": [
                {"name": "Corn Tortillas", "quantity": 2, "unit": "pack"},
                {"name": "Large Grade A Eggs", "quantity": 2, "unit": "count"},
                {"name": "Fresh Baby Spinach", "quantity": 0.5, "unit": "bag"},
            ],
            "instructions": [
                "Scramble eggs in a skillet over medium heat for 3 minutes.",
                "Toss in fresh baby spinach until wilted (1 minute).",
                "Warm corn tortillas on pan, fill with spinach & egg mixture, and serve immediately."
            ],
            "waste_prevention_score": "High",
            "notes": "Great for using up expiring spinach and milk/eggs!"
        },
        {
            "recipe_id": "one_pan_chicken_tomatoes",
            "title": "One-Pan Chicken Breast & Cherry Tomato Skillet",
            "cooking_style": "one-pot wonder",
            "prep_time_minutes": 20,
            "difficulty": "Medium",
            "dietary_tags": ["gluten-free", "dairy-free", "nut-free"],
            "ingredients": [
                {"name": "Chicken Breasts", "quantity": 300, "unit": "grams"},
                {"name": "Cherry Tomatoes", "quantity": 150, "unit": "grams"},
                {"name": "Fresh Baby Spinach", "quantity": 0.5, "unit": "bag"},
            ],
            "instructions": [
                "Season chicken breasts with salt, pepper, and olive oil.",
                "Sear chicken in a skillet for 6 minutes per side until golden.",
                "Add cherry tomatoes and spinach around chicken, cover pan, and simmer for 5 minutes until tomatoes burst."
            ],
            "waste_prevention_score": "High",
            "notes": "Minimal cleanup! Uses perishable protein and produce."
        },
        {
            "recipe_id": "creamy_spinach_milk_soup",
            "title": "Lazy 3-Ingredient Creamy Spinach Soup",
            "cooking_style": "lazy 3-ingredient",
            "prep_time_minutes": 12,
            "difficulty": "Beginner",
            "dietary_tags": ["vegetarian", "nut-free"],
            "ingredients": [
                {"name": "Fresh Baby Spinach", "quantity": 1.0, "unit": "bag"},
                {"name": "Whole Milk", "quantity": 0.5, "unit": "carton"},
                {"name": "Large Grade A Eggs", "quantity": 1, "unit": "count"},
            ],
            "instructions": [
                "Saute spinach in pot with butter or olive oil for 2 minutes.",
                "Add whole milk and gently simmer for 5 minutes.",
                "Blend until smooth, swirl in a poached or soft-boiled egg on top."
            ],
            "waste_prevention_score": "High",
            "notes": "Designed to finish expiring milk and spinach in one quick meal."
        },
        {
            "recipe_id": "batch_chicken_meal_prep",
            "title": "Weekly Batch-Prep Seasoned Chicken & Veggies",
            "cooking_style": "batch prep",
            "prep_time_minutes": 30,
            "difficulty": "Easy",
            "dietary_tags": ["gluten-free", "dairy-free", "nut-free"],
            "ingredients": [
                {"name": "Chicken Breasts", "quantity": 500, "unit": "grams"},
                {"name": "Cherry Tomatoes", "quantity": 250, "unit": "grams"},
            ],
            "instructions": [
                "Dice chicken breasts and toss with cherry tomatoes and herbs.",
                "Roast on sheet pan at 400°F (200°C) for 22 minutes.",
                "Divide into container portions for quick weekday lunches."
            ],
            "waste_prevention_score": "Medium",
            "notes": "Saves prep time for the entire week."
        },
        {
            "recipe_id": "crispy_egg_tortilla_quesadilla",
            "title": "5-Minute Lazy Egg & Cheese Tortilla Melt",
            "cooking_style": "lazy 3-ingredient",
            "prep_time_minutes": 5,
            "difficulty": "Beginner",
            "dietary_tags": ["vegetarian", "nut-free"],
            "ingredients": [
                {"name": "Corn Tortillas", "quantity": 1, "unit": "pack"},
                {"name": "Large Grade A Eggs", "quantity": 1, "unit": "count"},
            ],
            "instructions": [
                "Crack an egg into a hot pan, sprinkle salt, and press tortilla directly on top of raw egg.",
                "Flip after 2 minutes so tortilla gets crispy while egg finishes cooking.",
                "Fold in half and enjoy!"
            ],
            "waste_prevention_score": "Medium",
            "notes": "Ultra quick breakfast or late-night snack."
        }
    ]

    print(f"Seeding {len(recipes)} recipes into collection '{COLLECTION_NAME}'...")
    collection_ref = db.collection(COLLECTION_NAME)

    for recipe in recipes:
        doc_id = recipe["recipe_id"]
        collection_ref.document(doc_id).set(recipe)
        print(f"  ✓ Seeded recipe: {recipe['title']} [{recipe['cooking_style']}]")

    print("\n✅ Firestore recipe seeding completed successfully!")


if __name__ == "__main__":
    seed_recipes()
