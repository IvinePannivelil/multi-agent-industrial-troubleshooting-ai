"""
BM25 Keyword Search Index
=========================
Provides an in-memory BM25 index over ingested document chunks,
persisted to disk via pickle so it survives server restarts.

Architecture:
  BM25Index (singleton via module-level instance)
    ├── corpus: List[str]          — tokenized raw texts
    ├── metadata: List[dict]       — parallel metadata list
    └── bm25: BM25Okapi | None     — rank-bm25 model

Public API:
  add_documents(chunks, metadata_list)  — add new chunks to index
  search(query, top_k)                  — keyword search, returns ranked results
  save()                                — persist to BM25_INDEX_PATH
  load()                                — restore from BM25_INDEX_PATH
"""

import re
import pickle
import logging
import os
from typing import List, Dict, Any, Optional

from rank_bm25 import BM25Okapi

from core.config import BM25_INDEX_PATH

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Text normalization helpers
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> List[str]:
    """Lowercase, strip punctuation, split into tokens."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)   # remove punctuation
    tokens = text.split()
    return tokens if tokens else ["<empty>"]


# ---------------------------------------------------------------------------
# BM25 Index class
# ---------------------------------------------------------------------------

class BM25Index:
    """
    Thread-safe BM25 keyword search index with disk persistence.

    Metadata schema per chunk:
      {
        "text":          str,
        "document_name": str,
        "section":       str,
        "page_number":   int,
        "chunk_index":   int,
      }
    """

    def __init__(self):
        self._corpus_tokens: List[List[str]] = []   # tokenized texts
        self._metadata: List[Dict[str, Any]] = []   # parallel metadata
        self._bm25: Optional[BM25Okapi] = None

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def add_documents(
        self,
        chunks: List[str],
        metadata_list: List[Dict[str, Any]],
    ) -> None:
        """
        Add new document chunks to the BM25 index.

        Args:
            chunks:        List of raw text strings.
            metadata_list: Parallel list of metadata dicts.
                           Must contain keys: document_name, section,
                           page_number, chunk_index.
        """
        if len(chunks) != len(metadata_list):
            raise ValueError(
                f"chunks ({len(chunks)}) and metadata_list ({len(metadata_list)}) "
                "must be the same length."
            )

        for chunk, meta in zip(chunks, metadata_list):
            tokens = _tokenize(chunk)
            self._corpus_tokens.append(tokens)
            self._metadata.append({
                "text":          chunk,
                "document_name": meta.get("document_name", "Unknown"),
                "section":       meta.get("section", ""),
                "page_number":   meta.get("page_number", 0),
                "chunk_index":   meta.get("chunk_index", 0),
            })

        # Rebuild BM25 model — O(n) but acceptable for typical corp sizes
        self._bm25 = BM25Okapi(self._corpus_tokens)
        logger.info(
            "[BM25] Added %d chunks. Total corpus size: %d",
            len(chunks),
            len(self._corpus_tokens),
        )

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Perform BM25 keyword search.

        Args:
            query:  Natural-language query string.
            top_k:  Maximum number of results to return.

        Returns:
            List of result dicts sorted by BM25 score descending:
              {text, document_name, section, page_number, chunk_index, score}
        """
        if self._bm25 is None or not self._corpus_tokens:
            logger.warning("[BM25] Index is empty — returning no results.")
            return []

        query_tokens = _tokenize(query)
        scores = self._bm25.get_scores(query_tokens)

        # Pair scores with indices, sort descending
        indexed_scores = sorted(
            enumerate(scores), key=lambda x: x[1], reverse=True
        )

        results: List[Dict[str, Any]] = []
        for idx, score in indexed_scores[:top_k]:
            # Include all top_k results; score=0 can happen in small corpora
            entry = dict(self._metadata[idx])
            entry["score"] = float(score)
            results.append(entry)

        logger.info(
            "[BM25] Query '%s' -> %d results (top score: %.4f)",
            query,
            len(results),
            results[0]["score"] if results else 0.0,
        )
        return results

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self) -> None:
        """Persist corpus tokens and metadata to disk (pickle)."""
        try:
            os.makedirs(os.path.dirname(BM25_INDEX_PATH) or ".", exist_ok=True)
            payload = {
                "corpus_tokens": self._corpus_tokens,
                "metadata":      self._metadata,
            }
            with open(BM25_INDEX_PATH, "wb") as f:
                pickle.dump(payload, f)
            logger.info("[BM25] Index saved to %s (%d docs).", BM25_INDEX_PATH, len(self._corpus_tokens))
        except Exception as e:
            logger.error("[BM25] Failed to save index: %s", e)

    def load(self) -> None:
        """Restore corpus tokens and metadata from disk and rebuild BM25 model."""
        if not os.path.exists(BM25_INDEX_PATH):
            logger.info("[BM25] No existing index found at %s — starting fresh.", BM25_INDEX_PATH)
            return
        try:
            with open(BM25_INDEX_PATH, "rb") as f:
                payload = pickle.load(f)
            self._corpus_tokens = payload["corpus_tokens"]
            self._metadata      = payload["metadata"]
            if self._corpus_tokens:
                self._bm25 = BM25Okapi(self._corpus_tokens)
            logger.info("[BM25] Index loaded from %s (%d docs).", BM25_INDEX_PATH, len(self._corpus_tokens))
        except Exception as e:
            logger.error("[BM25] Failed to load index: %s — starting fresh.", e)
            self._corpus_tokens = []
            self._metadata      = []
            self._bm25          = None

    @property
    def size(self) -> int:
        return len(self._corpus_tokens)


# ---------------------------------------------------------------------------
# Module-level singleton — import and use directly
# ---------------------------------------------------------------------------

bm25_index = BM25Index()
bm25_index.load()   # restore state on startup
