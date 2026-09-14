"""
Conversation Memory Service
===========================
Stores and retrieves multi-turn chat history for the AI Agent Layer.
Uses the shared SQLite database located at SCRAPER_DB_PATH.

Table: conversations
  id           — Primary Key
  session_id   — UUID representing the user session
  user_message — The raw input query
  ai_response  — The final response text
  intent       — The classified intent
  agent_used   — The agent name that handled the query
  timestamp    — UTC ISO timestamp
"""

import sqlite3
import logging
from typing import List, Dict, Any

from services.scrapers.db import _conn, _now
from core.config import SCRAPER_DB_PATH

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Schema DDL
# ---------------------------------------------------------------------------

_DDL = """
CREATE TABLE IF NOT EXISTS conversations (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id     TEXT    NOT NULL,
    user_message   TEXT    NOT NULL,
    ai_response    TEXT    NOT NULL,
    intent         TEXT    DEFAULT '',
    agent_used     TEXT    DEFAULT '',
    timestamp      TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_conversations_session 
    ON conversations(session_id, timestamp DESC);
"""

# Auto-initialise table
try:
    with _conn() as con:
        con.executescript(_DDL)
except Exception as e:
    logger.error("[Memory] Failed to initialise conversations table: %s", e)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def save_message(
    session_id: str, 
    user_message: str, 
    ai_response: str, 
    intent: str, 
    agent_used: str
) -> None:
    """Save a single conversation turn to the database."""
    sql = """
    INSERT INTO conversations (session_id, user_message, ai_response, intent, agent_used, timestamp)
    VALUES (?, ?, ?, ?, ?, ?)
    """
    try:
        with _conn() as con:
            con.execute(sql, (
                session_id, 
                user_message, 
                ai_response, 
                intent, 
                agent_used, 
                _now()
            ))
        logger.info("[Memory] Saved turn for session: %s", session_id)
    except Exception as e:
        logger.error("[Memory] Failed to save message: %s", e)


def get_history(session_id: str, limit: int = 5) -> List[Dict[str, str]]:
    """
    Retrieve the last N turns for a session, formatted for the LLM.
    
    Returns:
        List of dicts: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
        Ordered chronologically (oldest first).
    """
    if not session_id:
        return []

    sql = """
    SELECT user_message, ai_response 
    FROM conversations
    WHERE session_id = ?
    ORDER BY timestamp DESC
    LIMIT ?
    """
    try:
        with _conn() as con:
            rows = con.execute(sql, (session_id, limit)).fetchall()
            
        history = []
        # DB returns newest first (DESC). We want chronological order for the prompt.
        for row in reversed(rows):
            history.append({"role": "user", "content": row["user_message"]})
            history.append({"role": "assistant", "content": row["ai_response"]})
            
        logger.info("[Memory] Retrieved %d recent turns for session: %s", len(rows), session_id)
        return history
    except Exception as e:
        logger.error("[Memory] Failed to retrieve history: %s", e)
        return []
