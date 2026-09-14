import logging
from typing import Dict

from core.config import LLM_PROVIDER
from services.intent_classifier import (
    INTENT_TROUBLESHOOTING,
    INTENT_PRODUCT_SEARCH,
    INTENT_TRAINING_REQUEST,
    INTENT_ENGINEERING_TALENT,
    INTENT_GENERAL_QA
)

logger = logging.getLogger(__name__)

def select_provider_for_intent(intent: str) -> str:
    """
    LLM Router: Determines the best provider based on the task intent.
    Defaults to the configured LLM_PROVIDER (defaults to 'gemini')
    so the project works out of the box with cloud APIs without
    requiring a local Ollama daemon.
    """
    default_provider = LLM_PROVIDER or "gemini"
    routing_map: Dict[str, str] = {
        INTENT_TROUBLESHOOTING: default_provider,
        INTENT_PRODUCT_SEARCH: default_provider,
        INTENT_GENERAL_QA: default_provider,
        INTENT_TRAINING_REQUEST: default_provider,
        INTENT_ENGINEERING_TALENT: default_provider,
    }
    
    selected = routing_map.get(intent, default_provider)
    logger.info(f"[LLMRouter] Routed intent '{intent}' -> '{selected}' provider")
    return selected

