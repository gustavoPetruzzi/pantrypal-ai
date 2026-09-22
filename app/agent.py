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

import datetime
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors.agent_engine_sandbox_code_executor import AgentEngineSandboxCodeExecutor
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

# Hardcoded Agent Engine reasoning engine resource name for Agent Platform code execution sandbox
AGENT_ENGINE_RESOURCE_NAME = (
    "projects/qwiklabs-gcp-01-b551540f472b/locations/us-central1/reasoningEngines/4097663782686294016"
)

code_executor = AgentEngineSandboxCodeExecutor(
    agent_engine_resource_name=AGENT_ENGINE_RESOURCE_NAME
)


def get_weather(query: str) -> str:
    """Simulates a web search. Use it get information on weather.

    Args:
        query: A string containing the location to get weather information for.

    Returns:
        A string with the simulated weather information for the queried location.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degrees and foggy."
    return "It's 90 degrees and sunny."


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        city: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager

from app.a2ui_utils import a2ui_callback
from app.tools.firestore_pantry_tools import (
    add_or_update_pantry_item,
    get_pantry_inventory,
    remove_pantry_item,
)
from app.tools.image_gen_tools import generate_dish_image
from app.tools.rag_retrieval_tools import query_herbal_rag_corpus
from app.tools.recipe_api_tools import search_free_recipes
from app.tools.recipe_tools import recommend_recipes

schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

instruction = schema_manager.generate_system_prompt(
    role_description=(
        "PantryPal AI, a Smart Pantry & Zero-Waste Chef assistant. You help home cooks "
        "minimize food waste, manage fridge/pantry inventory, and recommend recipes "
        "tailored to their cooking style (e.g., 15-min rush, lazy 3-ingredient meals, one-pot wonders). "
        "You remember dietary preferences, allergies, household size, staple items, and skill level across sessions.\n\n"
        "You have direct access to real-time tools:\n"
        "- `get_pantry_inventory`: check available ingredients & expiring items.\n"
        "- `generate_dish_image`: generate dish visual presentation photos and get a public https URL.\n"
        "- `query_herbal_rag_corpus`: consult Nicholas Culpeper's 'The Complete Herbal' (Gutenberg #49513) for botanical remedies.\n"
        "- `search_free_recipes`: query free external recipe APIs (RecipeAPI.io & free global database).\n"
        "- `recommend_recipes`: curated zero-waste recipes matching cooking style and pantry coverage.\n"
        "- `add_or_update_pantry_item`: update quantities or add pantry items.\n"
        "- `remove_pantry_item`: remove used-up pantry items.\n\n"
        "IMPORTANT RECIPE FALLBACK RULE:\n"
        "If `search_free_recipes` or `recommend_recipes` returns zero exact matches for the requested ingredients, "
        "NEVER state that no recipe exists. Immediately act as an expert zero-waste chef and generate a creative, step-by-step "
        "recipe using the user's specific ingredients (plus standard staples like oil, salt, lemon, or vinegar). "
        "Formulate your response in a clean A2UI card format."
    ),
    workflow_description="Analyze the user request, call tools when appropriate, and return structured UI when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        '{"Image": {"url": {"literalString": "https://..."}}}. Never point an '
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)


async def generate_memories_callback(callback_context: CallbackContext):
    """Write turn session events to Memory Bank for extraction."""
    try:
        await callback_context.add_session_to_memory()
    except Exception:
        pass
    return None


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    code_executor=code_executor,
    instruction=instruction,
    tools=[
        PreloadMemoryTool(),
        get_pantry_inventory,
        generate_dish_image,
        query_herbal_rag_corpus,
        search_free_recipes,
        recommend_recipes,
        add_or_update_pantry_item,
        remove_pantry_item,
        get_weather,
        get_current_time,
    ],
    after_model_callback=a2ui_callback,
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)

