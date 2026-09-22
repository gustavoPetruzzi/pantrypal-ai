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

"""Seed script to populate Firestore database for PantryPal AI.

Hardcodes project ID 'qwiklabs-gcp-01-b551540f472b' to avoid project number
resolution issues on deployed Agent Platform environments.
"""

from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-01-b551540f472b"
COLLECTION_NAME = "pantry_items"


def seed_firestore():
    print(f"Connecting to Firestore for project: '{PROJECT_ID}'...")
    db = firestore.Client(project=PROJECT_ID)

    items = [
        {
            "name": "Fresh Baby Spinach",
            "category": "Produce",
            "quantity": 1.0,
            "unit": "bag",
            "expiration_date": "2026-09-24",
            "status": "use_soon",
            "notes": "Organic baby spinach, unwashed",
        },
        {
            "name": "Large Grade A Eggs",
            "category": "Dairy",
            "quantity": 12.0,
            "unit": "count",
            "expiration_date": "2026-10-05",
            "status": "fresh",
            "notes": "Cage-free brown eggs",
        },
        {
            "name": "Corn Tortillas",
            "category": "Pantry",
            "quantity": 1.0,
            "unit": "pack",
            "expiration_date": "2026-10-01",
            "status": "fresh",
            "notes": "100% yellow corn tortillas",
        },
        {
            "name": "Whole Milk",
            "category": "Dairy",
            "quantity": 1.0,
            "unit": "carton",
            "expiration_date": "2026-09-23",
            "status": "expiring",
            "notes": "Half gallon whole milk",
        },
        {
            "name": "Chicken Breasts",
            "category": "Protein",
            "quantity": 500.0,
            "unit": "grams",
            "expiration_date": "2026-09-25",
            "status": "use_soon",
            "notes": "Boneless skinless chicken breasts",
        },
        {
            "name": "Cherry Tomatoes",
            "category": "Produce",
            "quantity": 250.0,
            "unit": "grams",
            "expiration_date": "2026-09-26",
            "status": "fresh",
            "notes": "Sweet vine-ripened cherry tomatoes",
        },
    ]

    print(f"Seeding {len(items)} items into collection '{COLLECTION_NAME}'...")
    collection_ref = db.collection(COLLECTION_NAME)

    for item in items:
        # Use lowercased item name as document ID for idempotency
        doc_id = item["name"].lower().replace(" ", "_")
        collection_ref.document(doc_id).set(item)
        print(f"  ✓ Seeded: {item['name']} ({item['quantity']} {item['unit']}) [{item['status']}]")

    print("\n✅ Firestore seeding completed successfully!")


if __name__ == "__main__":
    seed_firestore()
