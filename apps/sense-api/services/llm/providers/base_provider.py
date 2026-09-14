from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseLLMProvider(ABC):
    """
    Abstract base class for all LLM providers in the Goose Sense system.
    Ensures a consistent interface whether the backend is Gemini, OpenAI, Claude, or a local model.
    """

    @abstractmethod
    def generate(self, prompt: str, format: str = "") -> str:
        """
        Generates a string response from a raw text prompt.
        
        Args:
            prompt (str): The raw text prompt.
            format (str): Optional output format hint (e.g. 'json' for Ollama JSON mode).
            
        Returns:
            str: The text response from the LLM.
        """
        pass

    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], json_mode: bool = False) -> str:
        """
        Generates a string response from a conversational message array.
        
        Args:
            messages (List[Dict[str, str]]): A list of message dictionaries 
                                             e.g. [{"role": "user", "content": "hello"}]
            json_mode (bool): If True, enforce JSON-only output where supported.
                                             
        Returns:
            str: The text response from the LLM.
        """
        pass
