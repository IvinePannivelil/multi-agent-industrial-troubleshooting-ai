import os
import time
import logging
from typing import List, Dict, Union

from services.llm.providers.base_provider import BaseLLMProvider
from services.llm.llm_cache import llm_cache
from services.llm.llm_router import select_provider_for_intent
from services.intent_classifier import INTENT_GENERAL_QA

logger = logging.getLogger(__name__)

class LLMClient:
    """
    Singleton Router/Abstraction for all LLM calls in Goose Sense.
    Automatically instantiates the correct provider based on the intent
    passed from the AgentRouter.
    """
    def __init__(self):
        # We now lazily instantiate providers to avoid loading models
        # we don't end up needing for a particular request path.
        self._providers: Dict[str, BaseLLMProvider] = {}
        self.use_cache = os.getenv("LLM_USE_CACHE", "true").lower() == "true"

    def _get_provider(self, provider_name: str) -> BaseLLMProvider:
        if provider_name not in self._providers:
            if provider_name == "gemini":
                from services.llm.providers.gemini_provider import GeminiProvider
                self._providers[provider_name] = GeminiProvider()
            elif provider_name == "openai":
                from services.llm.providers.openai_provider import OpenAIProvider
                self._providers[provider_name] = OpenAIProvider()
            elif provider_name == "local":
                from services.llm.providers.local_provider import LocalProvider
                self._providers[provider_name] = LocalProvider()
            else:
                logger.warning(f"Unknown LLM_PROVIDER '{provider_name}', falling back to gemini.")
                from services.llm.providers.gemini_provider import GeminiProvider
                self._providers[provider_name] = GeminiProvider()
                
        return self._providers[provider_name]

    def generate(self, prompt: str, intent: str = INTENT_GENERAL_QA, format: str = "") -> str:
        """Route raw text generation through cache and selected provider."""
        if self.use_cache:
            cached = llm_cache.get(prompt)
            if cached:
                return cached
                
        provider_name = select_provider_for_intent(intent)
        provider = self._get_provider(provider_name)

        start_t = time.time()
        result = provider.generate(prompt, format=format)
        duration = time.time() - start_t
        
        logger.info(f"[LLMClient] [{provider_name}] generate() took {duration:.2f}s")
        
        if self.use_cache and result:
             llm_cache.set(prompt, result)
             
        return result

    def chat(self, messages: List[Dict[str, str]], intent: str = INTENT_GENERAL_QA, json_mode: bool = False) -> str:
        """Route chat conversation through cache and selected provider."""
        if self.use_cache:
            cached = llm_cache.get(messages)
            if cached:
                return cached
                
        provider_name = select_provider_for_intent(intent)
        provider = self._get_provider(provider_name)

        start_t = time.time()
        result = provider.chat(messages, json_mode=json_mode)
        duration = time.time() - start_t
        
        logger.info(f"[LLMClient] [{provider_name}] chat() took {duration:.2f}s")
        
        if self.use_cache and result:
             llm_cache.set(messages, result)
             
        return result

# Expose a singleton to the rest of the application
llm_client = LLMClient()
