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

import os
import google.cloud.aiplatform_v1 as gapic

PROJECT_ID = "qwiklabs-gcp-01-b551540f472b"
LOCATION = "us-south1"
CORPUS_NAME = f"projects/{PROJECT_ID}/locations/{LOCATION}/ragCorpora/7493989779944505344"

_rag_client = None

def _get_rag_client():
    global _rag_client
    if _rag_client is None:
        _rag_client = gapic.VertexRagServiceClient(
            client_options={"api_endpoint": f"{LOCATION}-aiplatform.googleapis.com"}
        )
    return _rag_client


def query_herbal_rag_corpus(query: str) -> str:
    """Queries the grounded Vertex AI RAG Corpus containing Nicholas Culpeper's 'The Complete Herbal' (Gutenberg eBook #49513).
    
    Use this tool when users ask about herbal remedies, natural medicinal plants, traditional herb usages, or botanical properties grounded in Culpeper's Herbal ebook corpus.

    Args:
        query: The search query or herbal topic (e.g., 'medicinal uses of mint', 'remedies for headache', 'rosemary benefits').

    Returns:
        A string containing relevant text snippets retrieved directly from the grounded RAG corpus.
    """
    try:
        client = _get_rag_client()
        req = gapic.RetrieveContextsRequest(
            parent=f"projects/{PROJECT_ID}/locations/{LOCATION}",
            vertex_rag_store=gapic.RetrieveContextsRequest.VertexRagStore(
                rag_resources=[
                    gapic.RetrieveContextsRequest.VertexRagStore.RagResource(
                        rag_corpus=CORPUS_NAME
                    )
                ]
            ),
            query=gapic.RagQuery(text=query)
        )
        res = client.retrieve_contexts(request=req)
        
        if not res.contexts or not res.contexts.contexts:
            return f"No grounded herbal passages found in the RAG corpus for query: '{query}'."

        snippets = []
        for idx, ctx in enumerate(res.contexts.contexts[:5]):
            clean_text = ctx.text.strip().replace("\n", " ")
            snippets.append(f"Passage {idx+1}: {clean_text}")

        return "\n\n".join(snippets)
    except Exception as e:
        return f"Error retrieving context from Vertex AI RAG corpus: {str(e)}"
