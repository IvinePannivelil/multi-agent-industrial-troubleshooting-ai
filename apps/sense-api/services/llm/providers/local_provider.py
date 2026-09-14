import os
import json
import logging
import requests
from typing import List, Dict
from services.llm.providers.base_provider import BaseLLMProvider

logger = logging.getLogger(__name__)

class LocalProvider(BaseLLMProvider):
    """
    Local Model implementation (e.g. Ollama) using raw HTTP requests.
    Agnostic to langchain dependencies.
    """
    def __init__(self, model_name: str = "llama3", temperature: float = 0.0):
        self.endpoint = os.getenv("LOCAL_LLM_ENDPOINT", "http://localhost:11434")
        self.model_name = os.getenv("LOCAL_LLM_MODEL", model_name)
        self.temperature = temperature
        
        logger.info(f"[LocalProvider] Initialized targeting {self.endpoint} with model {self.model_name}")

    def generate(self, prompt: str, format: str = "") -> str:
        url = f"{self.endpoint}/api/generate"
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature
            }
        }
        if format == "json":
            payload["format"] = "json"
        
        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")
        except Exception as e:
            logger.error(f"[LocalProvider] Generate error: {e}")
            raise

    def chat(self, messages: List[Dict[str, str]], json_mode: bool = False) -> str:
        url = f"{self.endpoint}/api/chat"
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.temperature
            }
        }
        if json_mode:
            payload["format"] = "json"
        
        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            return data.get("message", {}).get("content", "")
        except Exception as e:
            logger.error(f"[LocalProvider] Chat error: {e}")
            raise
