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

"""Firestore tools for PantryPal AI pantry inventory management.

Hardcodes GCP Project ID as a string ('qwiklabs-gcp-01-b551540f472b') to avoid
project number resolution errors on Agent Platform deployments.
"""

import json
from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-01-b551540f472b"
COLLECTION_NAME = "pantry_items"


def _get_firestore_client():
    """Initializes and returns a Firestore client with hardcoded project ID."""
    return firestore.Client(project=PROJECT_ID)


def get_pantry_inventory(category: str = "", status: str = "") -> str:
    """Reads current pantry and fridge inventory items from Firestore.

    Args:
        category: Optional filter by category (e.g. 'Produce', 'Dairy', 'Pantry', 'Protein').
        status: Optional filter by status (e.g. 'fresh', 'use_soon', 'expiring').

    Returns:
        A JSON string containing the list of matching inventory items.
    """
    try:
        db = _get_firestore_client()
        query_ref = db.collection(COLLECTION_NAME)

        if category and category.strip():
            query_ref = query_ref.where("category", "==", category.strip())
        if status and status.strip():
            query_ref = query_ref.where("status", "==", status.strip())

        docs = query_ref.stream()
        items = []
        for doc in docs:
            item_data = doc.to_dict()
            item_data["doc_id"] = doc.id
            items.append(item_data)

        if not items:
            return json.dumps({"status": "success", "count": 0, "items": [], "message": "No pantry items found matching criteria."})

        return json.dumps({"status": "success", "count": len(items), "items": items})
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Failed to fetch pantry inventory: {str(e)}"})


def add_or_update_pantry_item(
    name: str,
    quantity: float,
    unit: str,
    category: str = "Pantry",
    expiration_date: str = "",
    status: str = "fresh",
    notes: str = ""
) -> str:
    """Adds a new ingredient to the pantry or updates an existing item's quantity and details.

    Args:
        name: Name of the item (e.g. 'Eggs', 'Fresh Baby Spinach', 'Whole Milk').
        quantity: Amount/quantity (e.g. 1.0, 12.0, 500.0).
        unit: Measurement unit (e.g. 'count', 'bag', 'carton', 'grams', 'pack').
        category: Category of the item ('Produce', 'Dairy', 'Pantry', 'Protein').
        expiration_date: Expiration date string (YYYY-MM-DD format).
        status: Item freshness status ('fresh', 'use_soon', 'expiring').
        notes: Optional extra details or notes (e.g. 'Organic').

    Returns:
        A JSON string confirming the item addition/update.
    """
    try:
        db = _get_firestore_client()
        doc_id = name.lower().strip().replace(" ", "_")
        item_data = {
            "name": name.strip(),
            "quantity": float(quantity),
            "unit": unit.strip(),
            "category": category.strip(),
            "expiration_date": expiration_date.strip(),
            "status": status.strip(),
            "notes": notes.strip(),
        }
        db.collection(COLLECTION_NAME).document(doc_id).set(item_data)
        return json.dumps({"status": "success", "message": f"Successfully updated '{name}' in pantry inventory.", "item": item_data})
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Failed to update pantry item '{name}': {str(e)}"})


def remove_pantry_item(name: str) -> str:
    """Removes an item from the pantry inventory when used up or discarded.

    Args:
        name: Name of the item to remove (e.g. 'Whole Milk').

    Returns:
        A JSON string confirming item removal.
    """
    try:
        db = _get_firestore_client()
        doc_id = name.lower().strip().replace(" ", "_")
        db.collection(COLLECTION_NAME).document(doc_id).delete()
        return json.dumps({"status": "success", "message": f"Successfully removed '{name}' from pantry inventory."})
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Failed to remove pantry item '{name}': {str(e)}"})
