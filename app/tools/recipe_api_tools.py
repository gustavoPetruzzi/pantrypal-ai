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

"""Free Recipe API integration for PantryPal AI.

Supports:
1. RecipeAPI.io (https://recipeapi.io/) - Free tier (500 requests/month) when RECIPEAPI_KEY is provided.
2. TheMealDB API (https://www.themealdb.com/api.php) - 100% Free, zero API key required fallback.
"""

import json
import os
import httpx
from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-01-b551540f472b"
PANTRY_COLLECTION = "pantry_items"


def _get_firestore_pantry_items():
    """Fetches pantry items from Firestore."""
    try:
        db = firestore.Client(project=PROJECT_ID)
        docs = db.collection(PANTRY_COLLECTION).stream()
        return [doc.to_dict() for doc in docs]
    except Exception:
        return []


def search_free_recipes(query: str = "") -> str:
    """Searches for recipes using free external recipe APIs (RecipeAPI.io or TheMealDB) and matches against pantry inventory.

    Args:
        query: Search term or ingredient name (e.g. 'chicken', 'spinach', 'egg', 'pasta'). If empty, uses pantry items.

    Returns:
        A JSON string containing recipe details, ingredients list, and pantry matching analysis.
    """
    pantry_items = _get_firestore_pantry_items()
    pantry_names_lower = {item["name"].lower(): item for item in pantry_items}
    urgent_items_lower = {
        item["name"].lower() for item in pantry_items
        if item.get("status") in ["expiring", "use_soon"]
    }

    # Default query if empty
    if not query or not query.strip():
        if urgent_items_lower:
            query = list(urgent_items_lower)[0]
        elif pantry_names_lower:
            query = list(pantry_names_lower.keys())[0]
        else:
            query = "chicken"

    query_clean = query.strip()
    recipeapi_key = os.environ.get("RECIPEAPI_KEY")

    # Option A: If RECIPEAPI_KEY is provided, query recipeapi.io
    if recipeapi_key and recipeapi_key.strip():
        try:
            headers = {"Authorization": f"Bearer {recipeapi_key.strip()}"}
            url = f"https://recipeapi.io/api/v1/recipes?search={query_clean}"
            with httpx.Client(timeout=10.0) as client:
                res = client.get(url, headers=headers)
            if res.status_code == 200:
                data = res.json()
                raw_recipes = data.get("data", [])
                results = []
                for item in raw_recipes[:5]:
                    rec_ings = item.get("ingredients", [])
                    have = []
                    missing = []
                    for ing in rec_ings:
                        ing_name = ing.get("name", "")
                        ing_lower = ing_name.lower()
                        found = False
                        for p_lower, p_obj in pantry_names_lower.items():
                            if p_lower in ing_lower or ing_lower in p_lower:
                                found = True
                                have.append(p_obj["name"])
                                break
                        if not found:
                            missing.append(ing_name)

                    results.append({
                        "title": item.get("name"),
                        "description": item.get("description"),
                        "difficulty": item.get("difficulty"),
                        "meal_type": item.get("meal_type"),
                        "prep_time_minutes": item.get("prep_time"),
                        "cook_time_minutes": item.get("cook_time"),
                        "instructions": item.get("instructions", []),
                        "ingredients_you_have": list(set(have)),
                        "missing_ingredients": missing,
                        "source_api": "RecipeAPI.io"
                    })
                return json.dumps({"status": "success", "source": "RecipeAPI.io", "count": len(results), "recipes": results})
        except Exception as e:
            pass  # Fall through to TheMealDB

    # Option B: TheMealDB (100% Free, zero API key required)
    try:
        url = f"https://www.themealdb.com/api/json/v1/1/search.php?s={query_clean}"
        with httpx.Client(timeout=10.0) as client:
            res = client.get(url)

        if res.status_code != 200:
            return json.dumps({"status": "error", "message": f"Recipe search failed with HTTP {res.status_code}"})

        data = res.json()
        meals = data.get("meals") or []

        # If search returned no results, try searching by main ingredients individually
        if not meals:
            # Extract individual words/ingredients (e.g. "tomato, lettuce, carrot" -> ["tomato", "lettuce", "carrot"])
            raw_tokens = [t.strip(",. ") for t.strip() in query_clean.replace("and", ",").split(",") if t.strip()]
            if not raw_tokens:
                raw_tokens = query_clean.split()
            
            for token in raw_tokens:
                if len(token) < 3:
                    continue
                filter_url = f"https://www.themealdb.com/api/json/v1/1/filter.php?i={token}"
                with httpx.Client(timeout=5.0) as client:
                    res_f = client.get(filter_url)
                if res_f.status_code == 200:
                    f_data = res_f.json()
                    f_meals = f_data.get("meals") or []
                    if f_meals:
                        # Fetch details for first 3 meals matching this ingredient
                        for fm in f_meals[:3]:
                            d_url = f"https://www.themealdb.com/api/json/v1/1/lookup.php?i={fm['idMeal']}"
                            with httpx.Client(timeout=5.0) as client:
                                d_res = client.get(d_url)
                            if d_res.status_code == 200:
                                d_meals = d_res.json().get("meals") or []
                                if d_meals:
                                    meals.append(d_meals[0])
                        if meals:
                            break

        results = []
        for meal in meals[:5]:
            title = meal.get("strMeal")
            category = meal.get("strCategory")
            area = meal.get("strArea")
            instructions = meal.get("strInstructions", "").split("\r\n")
            instructions_clean = [s.strip() for s in instructions if s.strip()]

            # Extract up to 20 ingredients from TheMealDB fields strIngredient1..20
            meal_ings = []
            for i in range(1, 21):
                ing_val = meal.get(f"strIngredient{i}")
                measure_val = meal.get(f"strMeasure{i}")
                if ing_val and ing_val.strip():
                    meal_ings.append({
                        "name": ing_val.strip(),
                        "measure": measure_val.strip() if measure_val else ""
                    })

            have = []
            missing = []
            uses_expiring = False

            for ing_obj in meal_ings:
                ing_name = ing_obj["name"]
                ing_lower = ing_name.lower()
                found = False
                for p_lower, p_obj in pantry_names_lower.items():
                    if p_lower in ing_lower or ing_lower in p_lower:
                        found = True
                        have.append(p_obj["name"])
                        if p_lower in urgent_items_lower:
                            uses_expiring = True
                        break
                if not found:
                    missing.append(ing_name)

            results.append({
                "title": title,
                "category": category,
                "cuisine_area": area,
                "image_url": meal.get("strMealThumb"),
                "instructions": instructions_clean[:8],
                "ingredients_you_have": list(set(have)),
                "missing_ingredients": missing[:8],
                "uses_expiring_ingredients": uses_expiring,
                "source_api": "TheMealDB (100% Free Public API)"
            })

        return json.dumps({
            "status": "success",
            "source": "Free Recipe API",
            "count": len(results),
            "query": query_clean,
            "recipes": results
        })

    except Exception as e:
        return json.dumps({"status": "error", "message": f"Failed to fetch free recipes: {str(e)}"})
