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

"""Edamam Recipe Search API v2 integration for PantryPal AI.

Documentation: https://developer.edamam.com/edamam-docs-recipe-api

Queries Edamam's global recipe database based on available pantry items,
cooking style, maximum prep time, and health/dietary tags. Cross-references
returned recipes against Firestore 'pantry_items'.
"""

import json
import os
import httpx
from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-01-b551540f472b"
PANTRY_COLLECTION = "pantry_items"
EDAMAM_API_URL = "https://api.edamam.com/api/recipes/v2"


def _get_firestore_pantry_items():
    """Fetches pantry items from Firestore."""
    try:
        db = firestore.Client(project=PROJECT_ID)
        docs = db.collection(PANTRY_COLLECTION).stream()
        return [doc.to_dict() for doc in docs]
    except Exception:
        return []


def search_edamam_recipes(
    query: str = "",
    cooking_style: str = "",
    max_prep_time: int = 0,
    dietary_restriction: str = ""
) -> str:
    """Searches recipes via the Edamam Recipe Search API v2 and matches them against pantry inventory.

    Args:
        query: Specific search terms or ingredients (e.g. 'spinach eggs', 'chicken'). If empty, uses pantry items.
        cooking_style: Optional style filter ('15-min rush', 'lazy 3-ingredient', 'one-pot wonder', 'batch prep').
        max_prep_time: Maximum preparation/cooking time in minutes (e.g. 15, 20).
        dietary_restriction: Health/dietary label filter (e.g. 'vegetarian', 'vegan', 'gluten-free', 'dairy-free').

    Returns:
        A JSON string containing Edamam recipe recommendations, ingredient coverage, and source links.
    """
    app_id = os.environ.get("EDAMAM_APP_ID")
    app_key = os.environ.get("EDAMAM_APP_KEY")

    # Fetch current pantry items to cross-reference
    pantry_items = _get_firestore_pantry_items()
    pantry_names_lower = {item["name"].lower(): item for item in pantry_items}
    urgent_items_lower = {
        item["name"].lower() for item in pantry_items
        if item.get("status") in ["expiring", "use_soon"]
    }

    # If query is empty, build query string from pantry items
    if not query or not query.strip():
        if urgent_items_lower:
            query = " ".join(list(urgent_items_lower)[:3])
        elif pantry_names_lower:
            query = " ".join(list(pantry_names_lower.keys())[:3])
        else:
            query = "healthy quick meal"

    # If Edamam credentials are missing, notify user and provide fallback
    if not app_id or not app_key:
        return json.dumps({
            "status": "notice",
            "message": (
                "Edamam API credentials (EDAMAM_APP_ID and EDAMAM_APP_KEY) are not configured. "
                "Please set these environment variables to enable live Edamam searches. "
                "Falling back to Firestore recipe catalog."
            ),
            "edamam_docs": "https://developer.edamam.com/edamam-docs-recipe-api",
            "suggested_query": query
        })

    # Prepare Edamam API parameters
    params = {
        "type": "public",
        "q": query.strip(),
        "app_id": app_id.strip(),
        "app_key": app_key.strip(),
    }

    # Apply cooking style constraints
    if "15-min" in cooking_style.lower() or "rush" in cooking_style.lower():
        params["time"] = "1-15"
    elif max_prep_time and max_prep_time > 0:
        params["time"] = f"1-{max_prep_time}"

    if "3-ingredient" in cooking_style.lower() or "lazy" in cooking_style.lower():
        params["ingr"] = "1-5"

    # Apply health/dietary tags
    if dietary_restriction and dietary_restriction.strip():
        diet_clean = dietary_restriction.strip().lower().replace("_", "-")
        params["health"] = diet_clean

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(EDAMAM_API_URL, params=params)

        if response.status_code != 200:
            return json.dumps({
                "status": "error",
                "http_code": response.status_code,
                "message": f"Edamam API request failed: {response.text}"
            })

        data = response.json()
        hits = data.get("hits", [])

        recipes = []
        for hit in hits[:5]:  # Top 5 recommendations
            rec = hit.get("recipe", {})
            ing_lines = rec.get("ingredientLines", [])

            # Match ingredients against pantry
            have_list = []
            missing_list = []
            uses_expiring = False

            for line in ing_lines:
                line_lower = line.lower()
                found = False
                for p_name_lower, p_item in pantry_names_lower.items():
                    if p_name_lower in line_lower:
                        found = True
                        have_list.append(p_item["name"])
                        if p_name_lower in urgent_items_lower:
                            uses_expiring = True
                        break
                if not found:
                    missing_list.append(line)

            recipes.append({
                "title": rec.get("label"),
                "source": rec.get("source"),
                "url": rec.get("url"),
                "image": rec.get("image"),
                "prep_time_minutes": rec.get("totalTime", 0),
                "yield_servings": rec.get("yield", 1),
                "calories": round(rec.get("calories", 0)),
                "diet_labels": rec.get("dietLabels", []),
                "health_labels": rec.get("healthLabels", []),
                "ingredient_lines": ing_lines,
                "ingredients_you_have": list(set(have_list)),
                "missing_ingredients": missing_list[:5],
                "uses_expiring_ingredients": uses_expiring,
            })

        return json.dumps({
            "status": "success",
            "source": "Edamam Recipe API v2",
            "count": len(recipes),
            "query": query,
            "recipes": recipes
        })

    except Exception as e:
        return json.dumps({"status": "error", "message": f"Failed to call Edamam API: {str(e)}"})
