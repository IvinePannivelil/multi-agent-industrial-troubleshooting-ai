import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables (check local sense-api .env first, then optional shared packages .env)
local_env = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=local_env)

shared_env = Path(__file__).parent.parent.parent.parent / "packages" / "database" / ".env"
if shared_env.exists():
    load_dotenv(dotenv_path=shared_env)

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# API Keys & LLM Configuration
# ---------------------------------------------------------------------------
LLM_PROVIDER     = os.getenv("LLM_PROVIDER", "gemini")
GEMINI_API_KEY   = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY   = os.getenv("OPENAI_API_KEY")
LOCAL_LLM_ENDPOINT = os.getenv("LOCAL_LLM_ENDPOINT", "http://localhost:11434")

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
COHERE_API_KEY   = os.getenv("COHERE_API_KEY")   # Optional — for Cohere reranker

# ---------------------------------------------------------------------------
# Pinecone
# ---------------------------------------------------------------------------
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "goose-manuals")

# ---------------------------------------------------------------------------
# BM25 Index
# ---------------------------------------------------------------------------
# Path to the pickle file that persists the BM25 corpus across restarts.
# Change to any absolute path if you want to store it elsewhere.
BM25_INDEX_PATH = os.getenv(
    "BM25_INDEX_PATH",
    str(Path(__file__).parent.parent / "bm25_corpus.pkl"),
)

# ---------------------------------------------------------------------------
# Reranker
# ---------------------------------------------------------------------------
# Provider choices: "cohere" (default) | "score" (no-API fallback)
# Add new providers to services/reranker.py PROVIDER_REGISTRY.
RERANKER_PROVIDER = os.getenv("RERANKER_PROVIDER", "cohere")

# ---------------------------------------------------------------------------
# Hybrid Retrieval weights & sizes
# ---------------------------------------------------------------------------
# Must sum to ≤ 1.0 (remainder is ignored in RRF).
VECTOR_WEIGHT   = float(os.getenv("VECTOR_WEIGHT",   "0.6"))
BM25_WEIGHT     = float(os.getenv("BM25_WEIGHT",     "0.4"))
RETRIEVAL_TOP_K = int(os.getenv("RETRIEVAL_TOP_K",   "10"))   # candidates per source
RERANKER_TOP_N  = int(os.getenv("RERANKER_TOP_N",    "5"))    # final context chunks

# ---------------------------------------------------------------------------
# Agent Layer
# ---------------------------------------------------------------------------
# Controls which pass(es) the intent classifier uses:
#   "rules"  — keyword regex only (fast, no API)
#   "llm"    — Gemini LLM only
#   "hybrid" — rules first, LLM fallback (default)
INTENT_CLASSIFIER_MODE = os.getenv("INTENT_CLASSIFIER_MODE", "hybrid")

# LLM temperature for all specialist agents (lower = more deterministic)
AGENT_LLM_TEMPERATURE = float(os.getenv("AGENT_LLM_TEMPERATURE", "0.3"))

# ---------------------------------------------------------------------------
# Scraper / Data Ingestion
# ---------------------------------------------------------------------------
# Local SQLite database path for scraped ecosystem data
SCRAPER_DB_PATH = os.getenv(
    "SCRAPER_DB_PATH",
    str(Path(__file__).parent.parent / "goose_scraped_data.db"),
)

# Base URLs for each Goose Ecosystem app (local dev servers)
GOOSE_MART_URL       = os.getenv("GOOSE_MART_URL",       "http://localhost:3000")
GOOSE_SOLUTIONS_URL  = os.getenv("GOOSE_SOLUTIONS_URL",  "http://localhost:3001")
GOOSE_ELEVATE_URL    = os.getenv("GOOSE_ELEVATE_URL",    "http://localhost:3002")
HIREMYENGINEER_URL   = os.getenv("HIREMYENGINEER_URL",   "http://localhost:3003")

# HTTP request timeout in seconds for scrapers
SCRAPER_REQUEST_TIMEOUT = int(os.getenv("SCRAPER_REQUEST_TIMEOUT", "8"))

# ---------------------------------------------------------------------------
# Startup validation
# ---------------------------------------------------------------------------
if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY is not set.")
if not PINECONE_API_KEY:
    print("WARNING: PINECONE_API_KEY is not set.")
if not COHERE_API_KEY:
    print("INFO: COHERE_API_KEY not set — Reranker will use score-based fallback.")
