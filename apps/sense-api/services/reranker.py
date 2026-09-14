"""
Reranker Service
================
Pluggable reranker layer using the Strategy pattern.  Sorting candidates
by semantic relevance to the user query after the initial hybrid retrieval.

Pipeline position:
  ... -> Reciprocal Rank Fusion -> Reranker -> Top-N context -> LLM

Supported providers:
  - cohere  (default)  — Cohere Rerank v3 API, requires COHERE_API_KEY
  - score   (fallback) — Sort by rrf_score when no API key is present

Adding a new provider:
  1. Create a class that implements BaseReranker.rerank()
  2. Register it in PROVIDER_REGISTRY at the bottom of this file.
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any

from core.config import COHERE_API_KEY, RERANKER_PROVIDER

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Base Interface
# ---------------------------------------------------------------------------

class BaseReranker(ABC):
    """Strategy interface for reranking retrieved candidates."""

    @abstractmethod
    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_n: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Rerank a list of retrieved chunks given the user query.

        Args:
            query:      Original user query string.
            candidates: List of candidate dicts (must have 'text' and 'rrf_score').
            top_n:      How many results to return.

        Returns:
            Subset of candidates sorted by rerank_score descending, each with
            an added 'rerank_score' field.
        """


# ---------------------------------------------------------------------------
# Cohere Reranker
# ---------------------------------------------------------------------------

class CohereReranker(BaseReranker):
    """
    Reranks candidates using the Cohere Rerank v3 API.
    Falls back to ScoreReranker if API key is missing or call fails.
    """

    MODEL = "rerank-v3.5"

    def __init__(self):
        self._client = None
        if COHERE_API_KEY:
            try:
                import cohere          # type: ignore
                self._client = cohere.ClientV2(api_key=COHERE_API_KEY)
                logger.info("[Reranker] Cohere client initialized (model=%s).", self.MODEL)
            except Exception as e:
                logger.warning("[Reranker] Cohere init failed: %s — falling back to score sort.", e)
        else:
            logger.warning("[Reranker] COHERE_API_KEY not set — falling back to score sort.")

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_n: int = 5,
    ) -> List[Dict[str, Any]]:
        if not candidates:
            return []

        if self._client is None:
            logger.info("[Reranker] No Cohere client — using score fallback.")
            return _score_fallback(candidates, top_n)

        try:
            documents = [c["text"] for c in candidates]
            result = self._client.rerank(
                model=self.MODEL,
                query=query,
                documents=documents,
                top_n=top_n,
            )

            reranked = []
            for item in result.results:
                candidate = dict(candidates[item.index])
                candidate["rerank_score"] = float(item.relevance_score)
                reranked.append(candidate)

            logger.info(
                "[Reranker] Cohere reranked %d/%d candidates. Top score: %.4f",
                len(reranked),
                len(candidates),
                reranked[0]["rerank_score"] if reranked else 0.0,
            )
            return reranked

        except Exception as e:
            logger.error("[Reranker] Cohere API call failed: %s — using score fallback.", e)
            return _score_fallback(candidates, top_n)


# ---------------------------------------------------------------------------
# Score-based fallback (no external API)
# ---------------------------------------------------------------------------

class ScoreReranker(BaseReranker):
    """
    Fallback reranker — sorts candidates by their RRF score.
    No external API calls. Use when no API key is configured.
    """

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_n: int = 5,
    ) -> List[Dict[str, Any]]:
        if not candidates:
            return []
        logger.info("[Reranker] Using score-based fallback (no API key).")
        return _score_fallback(candidates, top_n)


# ---------------------------------------------------------------------------
# Shared helper
# ---------------------------------------------------------------------------

def _score_fallback(
    candidates: List[Dict[str, Any]],
    top_n: int,
) -> List[Dict[str, Any]]:
    """Sort by rrf_score and annotate with a synthetic rerank_score."""
    sorted_candidates = sorted(
        candidates, key=lambda x: x.get("rrf_score", 0.0), reverse=True
    )[:top_n]
    for rank, c in enumerate(sorted_candidates):
        c["rerank_score"] = c.get("rrf_score", 0.0)  # mirror RRF score
    return sorted_candidates


# ---------------------------------------------------------------------------
# Provider registry — add new providers here
# ---------------------------------------------------------------------------

PROVIDER_REGISTRY: Dict[str, type] = {
    "cohere": CohereReranker,
    "score":  ScoreReranker,
}


def get_reranker() -> BaseReranker:
    """Factory: return the configured reranker instance."""
    provider = (RERANKER_PROVIDER or "cohere").lower()
    cls = PROVIDER_REGISTRY.get(provider)
    if cls is None:
        logger.warning(
            "[Reranker] Unknown provider '%s'. Falling back to ScoreReranker.", provider
        )
        cls = ScoreReranker
    return cls()


# Module-level singleton
reranker = get_reranker()
