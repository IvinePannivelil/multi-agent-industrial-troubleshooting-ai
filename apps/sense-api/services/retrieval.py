"""
RAG Retrieval Service
======================
Orchestrates the full hybrid retrieval -> LLM generation pipeline.

Pipeline:
  User Query
    -> hybrid_retrieval.retrieve()       ← Vector + BM25 + RRF + Rerank
    -> Format context string
    -> Gemini Flash LLM
    -> Parse JSON response
    -> Return structured result
"""

import json
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from core.config import GEMINI_API_KEY
from services.hybrid_retrieval import retrieve as hybrid_retrieve

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# LLM initialization
# ---------------------------------------------------------------------------

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=GEMINI_API_KEY,
    temperature=0.2,   # low temp for analytical grounding
)

# ---------------------------------------------------------------------------
# Master System Prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """# MISSION
You are the "Senior Maintenance Engineer" for the Goose Ecosystem (Dairy Operations). You act as a strict state-machine for industrial diagnostics. 

# CRITICAL CONSTRAINTS (NO EXCEPTIONS)
1. ONLY OUTPUT VALID JSON. Do not include any introductory text, markdown prose, or "Here is the result" commentary.
2. DO NOT SOLVE ON TURN 1. You are strictly forbidden from providing a resolution until the fault is confirmed via user inquiry.
3. BOLD SAFETY WARNINGS. Every resolution must start with a bold safety warning regarding heat, pressure, or electricity.

# DIAGNOSTIC STATE LOGIC
- STATE: CLARIFYING (Use when intent is not 100% confirmed)
    - Identify 2-3 root causes from RAG context.
    - Select EXACTLY ONE simple physical question to ask the user.
    - Output: {"state": "CLARIFYING", "chatResponse": "Safety Warning... [Question]"}

- STATE: RESOLVED (Use ONLY after user confirms the specific fault)
    - Provide the multimodal resolution.
    - Output: {
        "state": "RESOLVED",
        "chatResponse": "**SAFETY WARNING**...",
        "media": {"image": "/path/to/img", "video": "/path/to/vid"},
        "steps": ["Step 1", "Step 2"],
        "ecosystem_escalation": {"goose_mart": "parts_link"}
      }

# ESCALATION MAPPING
- Replacement Parts -> Goose Mart
- Training/Upskilling -> Goose Elevate
- Engineering Consultation -> Goose Solutions
- Technical Hiring -> Hire My Engineer
- Upgrades/Maintenance -> Goose Service Shield

# INPUT CONTEXT
User Query: {{user_query}}
Retrieved Manual Data: {{rag_context}}
"""


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def generate_rag_response(user_query: str, history=None):
    """
    Full hybrid RAG pipeline:
      1. Hybrid retrieval (vector + BM25 + rerank)
      2. Format context
      3. LLM generation
      4. Parse and return structured JSON

    Args:
        user_query: Natural-language user question.
        history:    Conversation history (reserved for future use).

    Returns:
        Parsed JSON dict with keys: state, intent, chatResponse, searchQuery, sources.
    """
    logger.info("[RAG] Received query: '%s'", user_query)

    # Step 1 — Hybrid retrieval
    retrieved = hybrid_retrieve(user_query)

    logger.info("[RAG] Retrieved %d final chunks after hybrid pipeline.", len(retrieved))

    # Step 2 — Format context and sources
    context_parts: list = []
    sources: list = []

    for chunk in retrieved:
        text          = chunk.get("text", "")
        document_name = chunk.get("document_name", "Unknown")
        section       = chunk.get("section", "")
        page_number   = chunk.get("page_number", 0)
        chunk_index   = chunk.get("chunk_index", 0)
        rerank_score  = chunk.get("rerank_score", 0.0)

        # Build readable context block
        header = f"[Source: {document_name}"
        if section:
            header += f" | Section: {section}"
        if page_number:
            header += f" | Page: {page_number}"
        header += f" | Chunk: {chunk_index} | Relevance: {rerank_score:.3f}]"

        context_parts.append(f"{header}\n{text}")
        sources.append({
            "document_name": document_name,
            "section":       section,
            "page_number":   page_number,
            "chunk_index":   chunk_index,
        })

    context_str = "\n\n---\n\n".join(context_parts) if context_parts else "No relevant documents found."

    # Step 3 — Build and send prompt
    history_str = "\n".join(f"{msg['role'].capitalize()}: {msg['content']}" for msg in history) if history else "None"
    full_prompt = SYSTEM_PROMPT.replace("{{rag_context}}", context_str).replace("{{user_query}}", user_query)
    full_prompt += f"\n\n### Previous Conversation Context\n{history_str}"

    try:
        from services.intent_classifier import INTENT_GENERAL_QA
        raw_text = llm_client.generate(full_prompt, intent=INTENT_GENERAL_QA)

        # Strip markdown code fences if present
        if raw_text.startswith("```json"):
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1].split("```")[0].strip()

        parsed_res = json.loads(raw_text)

        # Override with pipeline-computed sources (richer metadata)
        parsed_res["sources"] = sources

        logger.info(
            "[RAG] LLM responded (state=%s, intent=%s, sources=%d).",
            parsed_res.get("state"),
            parsed_res.get("intent"),
            len(sources),
        )
        return parsed_res

    except Exception as e:
        logger.error("[RAG] LLM generation or parsing error: %s", e)
        return {
            "state":        "RESOLVED",
            "intent":       "GENERAL_CHAT",
            "chatResponse": "I am experiencing temporary technical difficulties accessing the AI engine. Please try again later.",
            "searchQuery":  "",
            "sources":      [],
        }
