import os
import logging
from typing import List, Dict
from services.llm.providers.base_provider import BaseLLMProvider

try:
    from langchain_openai import ChatOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)

class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI implementation of the LLM Provider interface.
    Requires langchain-openai package.
    """
    def __init__(self, model_name: str = "gpt-4o-mini", temperature: float = 0.0):
        if not OPENAI_AVAILABLE:
            raise ImportError("langchain-openai is required for OpenAIProvider. Run `pip install langchain-openai`")
            
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set.")
            
        self.llm = ChatOpenAI(
            model=model_name,
            api_key=api_key,
            temperature=temperature
        )
        # Dedicated JSON mode instance
        self.llm_json = ChatOpenAI(
            model=model_name,
            api_key=api_key,
            temperature=temperature,
            model_kwargs={"response_format": {"type": "json_object"}}
        )
        logger.info(f"[OpenAIProvider] Initialized with model {model_name}")

    def generate(self, prompt: str, format: str = "") -> str:
        try:
            llm = self.llm_json if format == "json" else self.llm
            response = llm.invoke(prompt)
            return response.content
        except Exception as e:
            logger.error(f"[OpenAIProvider] Generate error: {e}")
            raise

    def chat(self, messages: List[Dict[str, str]], json_mode: bool = False) -> str:
        try:
            llm = self.llm_json if json_mode else self.llm
            formatted_messages = [(m["role"], m["content"]) for m in messages]
            response = llm.invoke(formatted_messages)
            return response.content
        except Exception as e:
            logger.error(f"[OpenAIProvider] Chat error: {e}")
            raise
