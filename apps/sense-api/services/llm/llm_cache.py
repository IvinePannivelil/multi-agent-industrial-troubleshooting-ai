import hashlib
import sqlite3
import os
import json
import logging
from typing import Optional, List, Dict, Union
from core.config import SCRAPER_DB_PATH

logger = logging.getLogger(__name__)

class LLMCache:
    """
    Optional token-saving cache layer using SQLite.
    Stores exact prompt hashes to bypass API queries for identical duplicate requests.
    """
    
    def __init__(self):
        self.db_path = SCRAPER_DB_PATH
        self._init_db()

    def _init_db(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS llm_cache (
                        prompt_hash TEXT PRIMARY KEY,
                        response TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                conn.execute('PRAGMA journal_mode=WAL;')
        except Exception as e:
            logger.error(f"[LLMCache] Failed to initialize cache DB: {e}")

    def _hash_payload(self, payload: Union[str, List[Dict[str, str]]]) -> str:
        """Creates a stable hash of the prompt or multi-turn history."""
        if isinstance(payload, list):
            # Sort keys for consistent hashing of dicts
            payload_str = json.dumps(payload, sort_keys=True)
        else:
            payload_str = str(payload)
            
        return hashlib.sha256(payload_str.encode("utf-8")).hexdigest()

    def get(self, payload: Union[str, List[Dict[str, str]]]) -> Optional[str]:
        """Retrieves a cached response if it exists."""
        prompt_hash = self._hash_payload(payload)
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT response FROM llm_cache WHERE prompt_hash = ?", (prompt_hash,))
                result = cursor.fetchone()
                if result:
                    logger.debug(f"[LLMCache] Cache HIT for hash {prompt_hash[:8]}")
                    return result[0]
        except Exception as e:
            logger.warning(f"[LLMCache] Read error: {e}")
        return None

    def set(self, payload: Union[str, List[Dict[str, str]]], response: str) -> None:
        """Stores a successful LLM generation in the cache."""
        prompt_hash = self._hash_payload(payload)
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO llm_cache (prompt_hash, response) VALUES (?, ?)",
                    (prompt_hash, response)
                )
                logger.debug(f"[LLMCache] Cached response for hash {prompt_hash[:8]}")
        except Exception as e:
            logger.warning(f"[LLMCache] Write error: {e}")

# Singleton instance
llm_cache = LLMCache()
