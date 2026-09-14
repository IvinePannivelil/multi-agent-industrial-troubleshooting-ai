import os
import logging
from typing import List, Dict
from langchain_google_genai import ChatGoogleGenerativeAI
from services.llm.providers.base_provider import BaseLLMProvider

logger = logging.getLogger(__name__)

class GeminiProvider(BaseLLMProvider):
    """
    Google Gemini implementation of the LLM Provider interface.
    """
    def __init__(self, model_name: str = "gemini-1.5-flash", temperature: float = 0.0):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set.")
            
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=temperature
        )
        # Separate instance configured to return strict JSON only
        self.llm_json = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=temperature,
            response_mime_type="application/json"
        )
        logger.info(f"[GeminiProvider] Initialized with model {model_name}")

    def generate(self, prompt: str, format: str = "") -> str:
        try:
            llm = self.llm_json if format == "json" else self.llm
            response = llm.invoke(prompt)
            return response.content
        except Exception as e:
            logger.error(f"[GeminiProvider] Generate error: {e}")
            raise

    def chat(self, messages: List[Dict[str, str]], json_mode: bool = False) -> str:
        try:
            llm = self.llm_json if json_mode else self.llm
            # For Langchain ChatGoogleGenerativeAI, it prefers specific message object types,
            # but usually accepts list of dicts. We convert to standard tuple format:
            formatted_messages = [(m["role"], m["content"]) for m in messages]
            response = llm.invoke(formatted_messages)
            return response.content
        except Exception as e:
            logger.error(f"[GeminiProvider] Chat error: {e}")
            raise
