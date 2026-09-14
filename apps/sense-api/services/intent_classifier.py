"""
Intent Classifier
==================
Two-pass hybrid classifier for user query intent.

Pass 1 — Fast keyword/regex rules (no API call).
          Handles obvious patterns instantly.

Pass 2 — Gemini Flash LLM fallback for ambiguous queries.
          Only triggered when rules don't produce a confident match.

Supported intents (stored as module-level constants):
  INTENT_TROUBLESHOOTING      — fault diagnosis, alarms, failures
  INTENT_PRODUCT_SEARCH       — parts, catalog, pricing, vendors
  INTENT_TRAINING_REQUEST     — courses, certifications, learning
  INTENT_ENGINEERING_TALENT   — hire, expert, contractor search
  INTENT_GENERAL_QA           — everything else / RAG fallback

Configuration:
  INTENT_CLASSIFIER_MODE env var controls which passes run:
    "rules"  — pass 1 only
    "llm"    — pass 2 only
    "hybrid" — pass 1 then pass 2 (default)
"""

import re
import json
import logging
from typing import Optional

from core.config import INTENT_CLASSIFIER_MODE

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Intent constants
# ---------------------------------------------------------------------------

INTENT_TROUBLESHOOTING    = "TROUBLESHOOTING"
INTENT_PRODUCT_SEARCH     = "PRODUCT_SEARCH"
INTENT_TRAINING_REQUEST   = "TRAINING_REQUEST"
INTENT_ENGINEERING_TALENT = "ENGINEERING_TALENT"
INTENT_GENERAL_QA         = "GENERAL_QA"

ALL_INTENTS = [
    INTENT_TROUBLESHOOTING,
    INTENT_PRODUCT_SEARCH,
    INTENT_TRAINING_REQUEST,
    INTENT_ENGINEERING_TALENT,
    INTENT_GENERAL_QA,
]

# ---------------------------------------------------------------------------
# Rule-based keyword patterns (Pass 1)
# ---------------------------------------------------------------------------

_RULES: list = [
    (
        INTENT_TROUBLESHOOTING,
        re.compile(
            r"\b(fault|error|alarm|failure|broken|leak|overheat|vibrat|diagnos"
            r"|troubleshoot|not working|malfunction|trip|shutdown|defect|repair"
            r"|fix|issue|problem|warning|critical|unsafe|pasteuriz|homogeniz|separator"
            r"|clarifier|chiller|pump|valve|temp|pressure|milk|vat)\b",
            re.IGNORECASE,
        ),
    ),
    (
        INTENT_PRODUCT_SEARCH,
        re.compile(
            r"\b(buy|purchase|order|price|cost|catalog|part\s*number|sku|vendor"
            r"|supplier|recommend\w*\s+product|spare\s+part|hardware|component"
            r"|equipment\s+model|datasheet|spec\w*\s+sheet)\b",
            re.IGNORECASE,
        ),
    ),
    (
        INTENT_TRAINING_REQUEST,
        re.compile(
            r"\b(course|training|certif\w*|workshop|learn|tutorial|bootcamp"
            r"|program|upskill|skill|goose\s+elevate|e-?learn)\b",
            re.IGNORECASE,
        ),
    ),
    (
        INTENT_ENGINEERING_TALENT,
        re.compile(
            r"\b(hire|recruit|engineer\s+for\s+hire|contractor|freelance|talent"
            r"|expert\s+needed|find\s+(an?\s+)?engineer|staffing|resource"
            r"|hire\s+my\s+engineer)\b",
            re.IGNORECASE,
        ),
    ),
]

# ---------------------------------------------------------------------------
# History-stickiness patterns (Pass 0)
# ---------------------------------------------------------------------------
# If the assistant's most recent reply was a CLARIFYING troubleshooting
# question, any follow-up from the user is almost certainly still
# TROUBLESHOOTING — even if it lacks keywords (e.g. "It's a Tetra Pak").

_CLARIFYING_MARKERS = re.compile(
    r"\b(which\s+brand|which\s+model|what\s+(model|brand|type)|what\s+kind"
    r"|please\s+provide|can\s+you\s+tell\s+me|could\s+you\s+specify"
    r"|more\s+details|clarif|specify|let\s+me\s+know\s+the"
    r"|what\s+pasteuriz|what\s+equipment|model\s+number|serial\s+number)\b",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# LLM classification prompt (Pass 2)
# ---------------------------------------------------------------------------

_LLM_PROMPT = """You are an intent classification engine for a Dairy Plant AI assistant.

Based on the recent conversation history:
{history}

And the user's latest query: "{query}"

Classify the query into EXACTLY ONE of these intent categories:
- TROUBLESHOOTING: diagnosing dairy equipment issues, faults, errors, alarms (e.g., pasteurizers, homogenizers)
- PRODUCT_SEARCH: looking for parts, products, vendors, pricing
- TRAINING_REQUEST: requesting courses, certifications, or training materials
- ENGINEERING_TALENT: seeking to hire engineers or technical experts
- GENERAL_QA: any other industrial question or general knowledge query

Respond with ONLY a JSON object in this exact format, no markdown:
{{"intent": "<ONE_OF_THE_ABOVE>", "confidence": <0.0-1.0>}}"""


# ---------------------------------------------------------------------------
# Classifier class
# ---------------------------------------------------------------------------

from services.llm.llm_client import llm_client

class IntentClassifier:
    """
    Two-pass intent classifier.

    Pass 1: Rule-based regex matching (fast, no API).
    Pass 2: LLM Client (triggered on no rule match or in llm-only mode).
    """

    def __init__(self):
        self._mode = (INTENT_CLASSIFIER_MODE or "hybrid").lower()
        if self._mode in ("llm", "hybrid"):
            logger.info("[IntentClassifier] LLM mode ready.")

    def classify(self, query: str, history: list = None) -> str:
        """
        Classify a user query into one of the supported intents.

        Args:
            query: Raw user query string.
            history: Session history list.

        Returns:
            One of: TROUBLESHOOTING, PRODUCT_SEARCH, TRAINING_REQUEST,
                    ENGINEERING_TALENT, GENERAL_QA
        """
        history = history or []
        intent = INTENT_GENERAL_QA  # safe default

        # Pass 0 — History-awareness: if the agent was just clarifying a
        # troubleshooting issue, keep routing to TroubleshootingAgent.
        intent = self._classify_history_sticky(history)
        if intent != INTENT_GENERAL_QA:
            logger.info(
                "[IntentClassifier] Pass 0 (history-sticky) -> %s for query: '%s'",
                intent, query,
            )
            return intent

        if self._mode in ("rules", "hybrid"):
            intent = self._classify_rules(query)
            if intent != INTENT_GENERAL_QA:
                logger.info(
                    "[IntentClassifier] Pass 1 (rules) -> %s for query: '%s'",
                    intent, query,
                )
                return intent

        if self._mode in ("llm", "hybrid"):
            intent = self._classify_llm(query, history)
            logger.info(
                "[IntentClassifier] Pass 2 (LLM) -> %s for query: '%s'",
                intent, query,
            )
            return intent

        logger.info("[IntentClassifier] Default -> %s for query: '%s'", intent, query)
        return intent

    # ------------------------------------------------------------------
    # Internal passes
    # ------------------------------------------------------------------

    def _classify_history_sticky(self, history: list) -> str:
        """
        Pass 0: If the most recent assistant message in history looks like a
        CLARIFYING troubleshooting question, the current user reply is still
        part of that troubleshooting conversation.
        """
        if not history:
            return INTENT_GENERAL_QA
        # Walk backwards to find the last assistant message
        for msg in reversed(history):
            if msg.get("role") == "assistant":
                content = msg.get("content", "")
                if _CLARIFYING_MARKERS.search(content):
                    return INTENT_TROUBLESHOOTING
                break  # Only check the most recent assistant turn
        return INTENT_GENERAL_QA

    def _classify_rules(self, query: str) -> str:
        """Rule-based pass — returns first matching intent, else GENERAL_QA."""
        for intent, pattern in _RULES:
            if pattern.search(query):
                return intent
        return INTENT_GENERAL_QA

    def _classify_llm(self, query: str, history: list) -> str:
        """LLM pass — asks the configured LLM to classify the query."""
        try:
            recent_context = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in history[-4:]]) if history else "No previous history."
            prompt  = _LLM_PROMPT.format(history=recent_context, query=query)
            raw     = llm_client.generate(prompt).strip()

            # Strip markdown if present
            if raw.startswith("```"):
                raw = raw.split("```")[1].split("```")[0].strip()
                if raw.startswith("json"):
                    raw = raw[4:].strip()

            parsed = json.loads(raw)
            intent = parsed.get("intent", INTENT_GENERAL_QA).upper()

            if intent not in ALL_INTENTS:
                logger.warning("[IntentClassifier] LLM returned unknown intent '%s'. Defaulting to GENERAL_QA.", intent)
                return INTENT_GENERAL_QA

            return intent

        except Exception as e:
            logger.error("[IntentClassifier] LLM classification failed: %s. Defaulting to GENERAL_QA.", e)
            return INTENT_GENERAL_QA


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

intent_classifier = IntentClassifier()
