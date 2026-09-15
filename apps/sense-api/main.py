"""
Goose Sense Coordination Layer — FastAPI Entry Point
v3.0.0 — AI Agent Layer on top of Hybrid RAG
"""
import logging
import sys
import uuid
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from services.agents import AgentRouter
from services.conversation_memory import get_history, save_message

# ---------------------------------------------------------------------------
# Structured logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Industrial AI Coordination Layer",
    description=(
        "AI Agent Layer + Hybrid RAG pipeline: "
        "Intent Classification -> Agent Routing -> Vector/BM25/RRF/Rerank"
    ),
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:3003",
        "http://localhost:3004",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lazy-instantiated router (agents + intent classifier loaded on first request)
_router = AgentRouter()


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    query:      str
    session_id: Optional[str] = None
    history:    list = []


class ChatResponse(BaseModel):
    response_text:   str
    intent:          str
    agent_used:      str
    session_id:      str
    sources:         list = []
    state:           str  = "RESOLVED"
    search_query:    str  = ""
    tool_calls_made: list = []
    media:           Optional[dict] = None
    steps:           Optional[list] = None
    ecosystem_escalation: Optional[dict] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------




@app.post("/chat", response_model=ChatResponse)
async def chat_interaction(request: ChatRequest):
    """
    AI Agent pipeline with Conversation Memory:
      query -> fetch memory -> IntentClassifier -> AgentRouter -> Specialist Agent
            -> save memory -> Response
    """
    session_id = request.session_id or str(uuid.uuid4())
    logger.info("[API] /chat — session: %s | query: '%s'", session_id, request.query)

    try:
        # Load conversation history
        history = get_history(session_id, limit=6)
        logger.info("[API] /chat — loaded %d previous turns for context", len(history) // 2)

        # Run agent router with history
        response_dict = _router.run(request.query, history=history)

        # Save the new turn to DB
        save_message(
            session_id=session_id,
            user_message=request.query,
            ai_response=response_dict["response_text"],
            intent=response_dict["intent"],
            agent_used=response_dict["agent_used"],
        )

        response_dict["session_id"] = session_id
        return response_dict

    except Exception as e:
        logger.error("[API] /chat error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload-document")
async def upload_document(
    file: UploadFile = File(...),
    session_id: str = Form(None)
):
    from services.doc_ingestion.document_ingestor import ingest_document
    
    logger.info("[API] /upload-document — received %s for session %s", file.filename, session_id)
    try:
        content = await file.read()
        result = ingest_document(content, file.filename)
        return result
    except Exception as e:
        logger.error("[API] /upload-document error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

class TitleRequest(BaseModel):
    query: str

class TitleResponse(BaseModel):
    title: str

@app.post("/generate-title", response_model=TitleResponse)
async def generate_title(request: TitleRequest):
    """Generates a short, witty industrial title for a chat session."""
    from services.llm.llm_client import llm_client
    try:
        prompt = f"Based on this user query, generate a short (2-4 words) title for the chat session context. Query: '{request.query}'. Respond ONLY with the title. No quotes."
        title = llm_client.generate(prompt).strip(' \n"')
        return TitleResponse(title=title)
    except Exception as e:
        logger.error(f"[API] /generate-title error: {e}")
        return TitleResponse(title="Industrial Session")


@app.get("/health")
def health_check():
    from services.bm25_index import bm25_index
    from services.intent_classifier import ALL_INTENTS
    return {
        "status":            "ok",
        "service":           "Industrial AI Coordination Layer",
        "version":           "3.0.0",
        "bm25_doc_count":    bm25_index.size,
        "supported_intents": ALL_INTENTS,
    }


@app.get("/agents")
def list_agents():
    """List all registered agents and their required tools."""
    from services.agents.agent_router import AGENT_REGISTRY
    return {
        intent: {
            "agent": cls.__name__,
            "tools": cls().get_required_tools(),
        }
        for intent, cls in AGENT_REGISTRY.items()
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
