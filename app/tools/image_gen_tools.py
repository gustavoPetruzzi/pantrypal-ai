# ruff: noqa
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

import time
import uuid
from google import genai
from google.cloud import storage
from google.adk.tools import ToolContext
from google.genai import types

PROJECT_ID = "qwiklabs-gcp-01-b551540f472b"
BUCKET_NAME = "pantrypal-ai-media-264376302197"
MODEL_ID = "gemini-3.1-flash-lite-image"
LOCATION = "global"

_genai_client = None
_storage_client = None


def _get_genai_client():
    global _genai_client
    if _genai_client is None:
        _genai_client = genai.Client(
            vertexai=True,
            project=PROJECT_ID,
            location=LOCATION,
        )
    return _genai_client


def _get_storage_client():
    global _storage_client
    if _storage_client is None:
        _storage_client = storage.Client(project=PROJECT_ID)
    return _storage_client


def generate_dish_image(tool_context: ToolContext, prompt: str) -> str:
    """Generates an image for a food item, recipe dish presentation, plating idea, or pantry item.

    Uses gemini-3.1-flash-lite-image in the global region to generate dish presentation images,
    saves the image as an ADK artifact for Playground display, and uploads it to public GCS.

    Args:
        tool_context: The ADK ToolContext instance provided automatically during tool invocation.
        prompt: Detailed description of the dish, food item, or plating presentation to generate.

    Returns:
        The public HTTPS URL (https://storage.googleapis.com/<bucket>/<object>) of the generated image.
    """
    try:
        client = _get_genai_client()
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=prompt,
        )

        image_bytes = None
        mime_type = "image/jpeg"

        if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    image_bytes = part.inline_data.data
                    if part.inline_data.mime_type:
                        mime_type = part.inline_data.mime_type
                    break

        if not image_bytes:
            return f"Failed to generate image bytes for prompt: '{prompt}'."

        # 1. Save artifact to ADK context so it shows up in Playground's Artifacts panel
        filename = f"generated_dish_{int(time.time())}_{uuid.uuid4().hex[:6]}.jpg"
        artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        tool_context.save_artifact(filename=filename, artifact=artifact_part)

        # 2. Upload image bytes directly to public GCS bucket (no local file path return)
        storage_client = _get_storage_client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blob_name = f"generated_dishes/{filename}"
        blob = bucket.blob(blob_name)
        blob.upload_from_string(image_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{blob_name}"
        return public_url

    except Exception as e:
        return f"Error generating dish image: {str(e)}"
