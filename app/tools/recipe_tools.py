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

"""Recipe recommendation tool for PantryPal AI.

Hardcodes GCP Project ID as a string ('qwiklabs-gcp-01-b551540f472b') for
Firestore queries.
"""

import json
from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-01-b551540f472b"
RECIPES_COLLECTION = "recipes"
PANTRY_COLLECTION = "pantry_items"


def _get_firestore_client():
    return firestore.Client(project=PROJECT_ID)


def recommend_recipes(
    cooking_style: str = "",
    max_prep_time: int = 0,
    dietary_restriction: str = ""
) -> str:
    """Recommends recipes based on available pantry items, cooking style, and prep time limit.

    Args:
        cooking_style: Optional filter by style ('15-min rush', 'lazy 3-ingredient', 'one-pot wonder', 'batch prep').
        max_prep_time: Optional maximum prep time limit in minutes (e.g. 15, 20).
        dietary_restriction: Optional dietary tag filter (e.g. 'vegetarian', 'gluten-free', 'dairy-free', 'nut-free').

    Returns:
        A JSON string containing recommended recipes with ingredients you have vs missing ingredients.
    """
    try:
        db = _get_firestore_client()

        # 1. Fetch pantry items
        pantry_docs = db.collection(PANTRY_COLLECTION).stream()
        pantry_items = [doc.to_dict() for doc in pantry_docs]
        pantry_names_lower = {item["name"].lower(): item for item in pantry_items}

        # Identify expiring/use_soon items for score boosting
        urgent_items_lower = {
            item["name"].lower() for item in pantry_items
            if item.get("status") in ["expiring", "use_soon"]
        }

        # 2. Fetch recipes
        recipe_docs = db.collection(RECIPES_COLLECTION).stream()
        all_recipes = [doc.to_dict() for doc in recipe_docs]

        matched_recipes = []

        for recipe in all_recipes:
            # Filter by cooking style if requested
            if cooking_style and cooking_style.strip():
                req_style = cooking_style.strip().lower()
                rec_style = recipe.get("cooking_style", "").lower()
                if req_style not in rec_style and rec_style not in req_style:
                    continue

            # Filter by max prep time if requested
            if max_prep_time and max_prep_time > 0:
                if recipe.get("prep_time_minutes", 999) > max_prep_time:
                    continue

            # Filter by dietary restriction if requested
            if dietary_restriction and dietary_restriction.strip():
                req_diet = dietary_restriction.strip().lower()
                rec_diets = [d.lower() for d in recipe.get("dietary_tags", [])]
                if req_diet not in rec_diets:
                    continue

            # 3. Analyze ingredients match
            required_ingredients = recipe.get("ingredients", [])
            have_list = []
            missing_list = []
            uses_expiring_item = False

            for ing in required_ingredients:
                ing_name = ing["name"]
                ing_name_lower = ing_name.lower()

                # Check if pantry contains this item (fuzzy/substring match)
                found = False
                for p_name_lower, p_item in pantry_names_lower.items():
                    if ing_name_lower in p_name_lower or p_name_lower in ing_name_lower:
                        found = True
                        have_list.append({
                            "name": ing_name,
                            "in_pantry": p_item["name"],
                            "status": p_item.get("status", "fresh")
                        })
                        if p_name_lower in urgent_items_lower or ing_name_lower in urgent_items_lower:
                            uses_expiring_item = True
                        break

                if not found:
                    missing_list.append(ing_name)

            coverage_ratio = len(have_list) / max(len(required_ingredients), 1)

            matched_recipes.append({
                "recipe_id": recipe.get("recipe_id"),
                "title": recipe.get("title"),
                "cooking_style": recipe.get("cooking_style"),
                "prep_time_minutes": recipe.get("prep_time_minutes"),
                "difficulty": recipe.get("difficulty"),
                "dietary_tags": recipe.get("dietary_tags", []),
                "instructions": recipe.get("instructions", []),
                "ingredients_you_have": have_list,
                "missing_ingredients": missing_list,
                "pantry_coverage_percentage": round(coverage_ratio * 100, 1),
                "uses_expiring_ingredients": uses_expiring_item,
                "waste_prevention_score": "High" if uses_expiring_item else recipe.get("waste_prevention_score", "Medium")
            })

        # Sort matches: prioritize recipes using expiring items and higher pantry coverage
        matched_recipes.sort(key=lambda r: (r["uses_expiring_ingredients"], r["pantry_coverage_percentage"]), reverse=True)

        return json.dumps({
            "status": "success",
            "count": len(matched_recipes),
            "filters": {
                "cooking_style": cooking_style,
                "max_prep_time": max_prep_time,
                "dietary_restriction": dietary_restriction
            },
            "recommendations": matched_recipes
        })

    except Exception as e:
        return json.dumps({"status": "error", "message": f"Failed to fetch recipe recommendations: {str(e)}"})
