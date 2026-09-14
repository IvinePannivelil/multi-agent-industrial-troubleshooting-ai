"""
Hybrid Retrieval Pipeline
==========================
Combines Pinecone vector search and BM25 keyword search, merges results
using Reciprocal Rank Fusion (RRF), deduplicates, then reranks.

Full pipeline:
┌─────────────────────────────────────────────────────────────┐
│  User Query                                                  │
│      │                                                       │
│      ▼  embed_query()  [Gemini text-embedding-004]           │
│  ┌────────────────┐   ┌──────────────────────┐              │
│  │  Pinecone Vector│   │  BM25 Keyword Search  │             │
│  │  Search (top-K) │   │  (rank-bm25, top-K)  │             │
│  └───────┬─────────┘   └──────────┬───────────┘             │
│          │                        │                          │
│          └──────────┬─────────────┘                         │
│                     ▼                                        │
│        Reciprocal Rank Fusion (RRF)                          │
│         vector_weight=0.6 / bm25_weight=0.4                 │
│                     │                                        │
│                     ▼                                        │
│        Deduplicate by chunk_index                            │
│                     │                                        │
│                     ▼                                        │
│        Reranker (Cohere / score fallback)                    │
│                     │                                        │
│                     ▼                                        │
│        Top-N chunks -> LLM context                           │
└─────────────────────────────────────────────────────────────┘

Returned chunk schema:
  {
    "text":          str,
    "document_name": str,
    "section":       str,
    "page_number":   int,
    "chunk_index":   int,
    "rrf_score":     float,
    "rerank_score":  float,
  }
"""

import logging
from typing import List, Dict, Any, Optional

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pinecone import Pinecone

from core.config import (
    PINECONE_API_KEY,
    PINECONE_INDEX_NAME,
    GEMINI_API_KEY,
    VECTOR_WEIGHT,
    BM25_WEIGHT,
    RETRIEVAL_TOP_K,
    RERANKER_TOP_N,
)
from services.bm25_index import bm25_index
from services.reranker import reranker

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Client initialization
# ---------------------------------------------------------------------------

_pc = Pinecone(api_key=PINECONE_API_KEY)
_index = _pc.Index(PINECONE_INDEX_NAME)

_embeddings_model = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-2-preview",
    google_api_key=GEMINI_API_KEY,
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _pinecone_search(
    query_embedding: List[float],
    top_k: int,
) -> List[Dict[str, Any]]:
    """Query Pinecone and normalise results to our metadata schema."""
    try:
        result = _index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
        )
        matches = getattr(result, "matches", [])
    except Exception as e:
        logger.error("[HybridRetrieval] Pinecone query failed: %s", e)
        return []

    candidates = []
    for match in matches:
        meta = match.metadata or {}
        candidates.append({
            "text":          str(meta.get("text", "")),
            "document_name": str(meta.get("document_name", meta.get("source", "Unknown"))),
            "section":       str(meta.get("section", "")),
            "page_number":   int(meta.get("page_number", 0)),
            "chunk_index":   int(meta.get("chunkIndex", meta.get("chunk_index", 0))),
            "score":         float(match.score or 0.0),
        })

    logger.info(
        "[HybridRetrieval] Pinecone returned %d results (top score: %.4f).",
        len(candidates),
        candidates[0]["score"] if candidates else 0.0,
    )
    return candidates


def _reciprocal_rank_fusion(
    vector_results: List[Dict[str, Any]],
    bm25_results: List[Dict[str, Any]],
    vector_weight: float,
    bm25_weight: float,
    k: int = 60,
) -> List[Dict[str, Any]]:
    """
    Weighted Reciprocal Rank Fusion.

    RRF score = vector_weight * (1 / (k + rank_v)) +
                bm25_weight   * (1 / (k + rank_b))

    k=60 is the standard RRF constant that prevents high ranks from dominating.
    """
    # Map chunk_index -> rrf accumulator
    rrf_scores: Dict[str, float] = {}
    index_to_candidate: Dict[str, Dict[str, Any]] = {}

    for rank, candidate in enumerate(vector_results, start=1):
        key = f"{candidate['document_name']}::{candidate['chunk_index']}"
        rrf_scores[key] = rrf_scores.get(key, 0.0) + vector_weight * (1.0 / (k + rank))
        index_to_candidate[key] = candidate

    for rank, candidate in enumerate(bm25_results, start=1):
        key = f"{candidate['document_name']}::{candidate['chunk_index']}"
        rrf_scores[key] = rrf_scores.get(key, 0.0) + bm25_weight * (1.0 / (k + rank))
        if key not in index_to_candidate:
            index_to_candidate[key] = candidate

    # Sort by RRF score descending
    merged = []
    for key, rrf_score in sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True):
        entry = dict(index_to_candidate[key])
        entry["rrf_score"] = rrf_score
        merged.append(entry)

    logger.info(
        "[HybridRetrieval] RRF merged %d unique chunks (vector=%d, bm25=%d).",
        len(merged),
        len(vector_results),
        len(bm25_results),
    )
    return merged


# ---------------------------------------------------------------------------
# Public retrieve() function
# ---------------------------------------------------------------------------

def retrieve(
    query: str,
    top_k: Optional[int] = None,
    reranker_top_n: Optional[int] = None,
    vector_weight: float = VECTOR_WEIGHT,
    bm25_weight: float = BM25_WEIGHT,
) -> List[Dict[str, Any]]:
    """
    Full hybrid retrieval pipeline.

    Args:
        query:          User query string.
        top_k:          Candidates to fetch from each source (default: RETRIEVAL_TOP_K).
        reranker_top_n: Final results after reranking (default: RERANKER_TOP_N).
        vector_weight:  RRF weight for vector results (0–1).
        bm25_weight:    RRF weight for BM25 results (0–1).

    Returns:
        List of chunk dicts with full metadata + rrf_score + rerank_score.
    """
    top_k          = top_k          or RETRIEVAL_TOP_K
    reranker_top_n = reranker_top_n or RERANKER_TOP_N

    logger.info(
        "[HybridRetrieval] Starting hybrid retrieval for query: '%s' "
        "(top_k=%d, reranker_top_n=%d, v_weight=%.2f, bm25_weight=%.2f)",
        query, top_k, reranker_top_n, vector_weight, bm25_weight,
    )

    # Step 1 — Embed query
    query_embedding = _embeddings_model.embed_query(query)
    if len(query_embedding) > 768:
        query_embedding = query_embedding[:768]

    # Step 2 — Parallel retrieval
    vector_results = _pinecone_search(query_embedding, top_k)
    bm25_results   = bm25_index.search(query, top_k)

    logger.info(
        "[HybridRetrieval] Retrieved %d vector, %d BM25 candidates.",
        len(vector_results),
        len(bm25_results),
    )

    # Step 3 — Merge via Reciprocal Rank Fusion
    merged = _reciprocal_rank_fusion(
        vector_results,
        bm25_results,
        vector_weight=vector_weight,
        bm25_weight=bm25_weight,
    )

    if not merged:
        logger.warning("[HybridRetrieval] No results after RRF merge.")
        return []

    # Step 4 — Rerank
    final_results = reranker.rerank(query, merged, top_n=reranker_top_n)

    logger.info(
        "[HybridRetrieval] Final %d chunks selected. Scores: %s",
        len(final_results),
        [(round(r.get("rerank_score", 0), 4)) for r in final_results],
    )

    return final_results
