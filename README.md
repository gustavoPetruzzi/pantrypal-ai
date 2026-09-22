# PantryPal AI 🌱

An agentic AI Smart Pantry & Zero-Waste Chef built with Google's **Agent Development Kit (ADK)**, **Gemini 2.5 Flash**, **A2UI**, and **Google Cloud Platform**.

PantryPal AI helps home cooks manage fridge/pantry inventory, minimize food waste by prioritizing expiring ingredients, look up historical botanical remedies, search real-world recipe APIs, and generate dish images.

![PantryPal AI Demo](docs/demo.gif)

🎥 **[Watch High-Res WebM Video Demo](docs/demo_video.webm)**

---

## 🚀 Key Features & Implemented Capabilities

Every capability listed below is fully implemented in `app/` and wired into the agent runtime:

### 🥑 Smart Pantry & Zero-Waste Management
- **Firestore Pantry Inventory**: Tracks pantry items, quantities, and expiration statuses (`fresh`, `use_soon`, `expiring`).
- **Real-Time Inventory Tools**:
  - `get_pantry_inventory`: Fetches live inventory and flags urgent/expiring items.
  - `add_or_update_pantry_item`: Adds new items or updates quantities in Cloud Firestore.
  - `remove_pantry_item`: Removes consumed items from Firestore.
- **Zero-Waste Recipe Recommendation**:
  - `recommend_recipes`: Matches recipes against live pantry stock, boosting waste prevention scores for recipes that consume expiring ingredients.

### 🌐 Multi-Source Recipe Discovery
- **External Recipe APIs**:
  - `search_free_recipes`: Queries **TheMealDB** (and **RecipeAPI.io** if API key is provided) to fetch recipes dynamically, with multi-ingredient token fallback logic.
- **Generative Chef Fallback**:
  - Automatically creates custom, step-by-step zero-waste recipes when external APIs return zero matches for a combination of ingredients.

### 🖼️ AI Image Generation
- **Imagen 3 Integration**:
  - `generate_dish_image`: Generates photorealistic dish visual presentations using Vertex AI Imagen 3 (`imagen-3.0-generate-002`) and stores them in Google Cloud Storage (`pantrypal-ai-media-264376302197`) with public access.

### 📜 Herbal & Botanical RAG
- **Culpeper Herbal Knowledge Base**:
  - `query_herbal_rag_corpus`: Grounded RAG retrieval tool querying Nicholas Culpeper's *"The Complete Herbal"* (Project Gutenberg #49513) via Google GenAI Embeddings (`text-embedding-004`) for botanical health remedies.

### 🖥️ Dynamic A2UI & Agent Callback
- **A2UI Schema Manager (v0.8)**:
  - Formats agent outputs into rich, interactive micro-surfaces (Cards, Columns, Rows, Text, Images).
- **A2UI Callback**:
  - Integrated via `after_model_callback` (`a2ui_callback`) to parse A2UI data parts cleanly into structured UI.

### 🧠 Cross-Session Memory Bank
- **ADK PreloadMemoryTool & Event Callbacks**:
  - Uses `PreloadMemoryTool` and `after_agent_callback` (`generate_memories_callback`) to persist user dietary preferences, allergies, and cooking habits across sessions.

---

## 🏗️ Architecture & Stack

| Component | Technology |
|---|---|
| **Agent Framework** | Google Agent Development Kit (ADK) |
| **Model** | Gemini 2.5 Flash (`gemini-2.5-flash`) |
| **Database** | Google Cloud Firestore (`pantry_items`, `recipes`) |
| **Image Generation** | Vertex AI Imagen 3 (`imagen-3.0-generate-002`) |
| **Storage Bucket** | Google Cloud Storage (`pantrypal-ai-media-264376302197`) |
| **Embeddings & RAG** | Vertex AI Embeddings (`text-embedding-004`) |
| **Frontend Proxy** | FastAPI (`main.py`) + Custom Plain HTML/CSS Chat UI (`a2a-sdk`) |
| **Deployment Target** | Google Cloud Run / Agent Runtime |

---

## 📋 Planned Capabilities (Not Yet Implemented)

The following items were discussed in earlier project specs but are **not yet implemented in code**:
- ❌ **Barcode / Receipt Scanning**: OCR receipt upload for auto-filling pantry stock.
- ❌ **Automated Grocery Ordering**: Direct cart checkout integration with external delivery services.

---

## 🛠️ Local Setup & Running Instructions

### Prerequisites
- Python 3.11+
- Google Cloud SDK (`gcloud`)
- Google Agents CLI (`agents-cli`)

### 1. Environment Configuration

Clone the repository and navigate to the project directory:

```bash
cd pantrypal-ai
```

Set required environment variables:

```bash
export GOOGLE_CLOUD_PROJECT="<YOUR_GCP_PROJECT_ID>"
export GOOGLE_CLOUD_LOCATION="us-east1"
```

### 2. Running Local Agent & Playground

Install dependencies and test the agent interactively in the ADK CLI:

```bash
agents-cli playground
```

### 3. Running the Frontend Proxy Locally

Navigate to the `frontend/` directory, set up a virtual environment, install requirements, and run the server:

```bash
cd frontend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Set your deployed reasoning engine resource name and agent directory
export AGENT_ENGINE_RESOURCE_NAME="projects/<YOUR_PROJECT>/locations/us-east1/reasoningEngines/<REASONING_ENGINE_ID>"
export AGENT_DIRECTORY="app"

python3 main.py
```

Open your browser at local port `8080` to access the chat interface.

---

## 🚢 Deployment Instructions

### Deploying the Agent

Deploy the agent logic to Agent Runtime:

```bash
agents-cli deploy -d agent_runtime --project <YOUR_GCP_PROJECT_ID> --region us-east1
```

### Deploying the Frontend Proxy to Cloud Run

Deploy the containerized frontend to Google Cloud Run:

```bash
cd frontend
gcloud run deploy pantrypal-frontend \
  --project <YOUR_GCP_PROJECT_ID> \
  --region us-east1 \
  --source . \
  --allow-unauthenticated \
  --update-env-vars "AGENT_ENGINE_RESOURCE_NAME=projects/<YOUR_PROJECT>/locations/us-east1/reasoningEngines/<REASONING_ENGINE_ID>,AGENT_DIRECTORY=app"
```

Ensure the Cloud Run default compute service account has been granted the `roles/aiplatform.user` IAM role:

```bash
gcloud projects add-iam-policy-binding <YOUR_GCP_PROJECT_ID> \
  --member="serviceAccount:<PROJECT_NUMBER>-compute@developer.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```
