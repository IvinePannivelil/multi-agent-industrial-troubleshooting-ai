"""
Document Ingestion Pipeline
============================
Handles extraction, chunking, embedding, and dual-indexing of uploaded documents.

On each upload:
  1. Extract text (PDF page-by-page, CSV/Excel, images, plain text)
  2. Chunk using RecursiveCharacterTextSplitter
  3. Embed each chunk with Gemini text-embedding-004
  4. Upsert to Pinecone with rich metadata
  5. Add to BM25 index for keyword search

Rich metadata stored per chunk:
  {
    "document_name": str,   # original filename
    "section":       str,   # heuristic section heading (or "")
    "page_number":   int,   # 1-indexed; 0 for non-PDF
    "chunk_index":   int,   # position within document
    "text":          str,   # raw chunk content
  }
"""

import os
import re
import logging
import pandas as pd
import PyPDF2
from PIL import Image
from io import BytesIO
from typing import List, Tuple, Dict, Any

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pinecone import Pinecone

from core.config import PINECONE_API_KEY, PINECONE_INDEX_NAME, GEMINI_API_KEY
from services.bm25_index import bm25_index

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Client initialization
# ---------------------------------------------------------------------------

pc    = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX_NAME)

embeddings_model = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001",
    google_api_key=GEMINI_API_KEY,
)

# Text Splitter for Industrial Context
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=100,
    separators=["\n\n", "\n", " ", ""],
)

# ---------------------------------------------------------------------------
# Section heading heuristic
# ---------------------------------------------------------------------------

_SECTION_RE = re.compile(r"^(?:section|chapter|part|§)\s+[\d\w.]+[:\s]", re.IGNORECASE)


def _extract_section_heading(text: str) -> str:
    """
    Best-effort extract a section heading from the start of a chunk.
    Returns empty string if no clear heading detected.
    """
    first_line = text.strip().split("\n")[0].strip()
    if _SECTION_RE.match(first_line) or (len(first_line) < 100 and first_line.endswith(":")):
        return first_line
    return ""


# ---------------------------------------------------------------------------
# Per-format text extraction
# ---------------------------------------------------------------------------

def _extract_pdf_pages(file_content: bytes) -> List[Tuple[str, int]]:
    """
    Extract (text, page_number) pairs from a PDF.
    page_number is 1-indexed.
    """
    reader = PyPDF2.PdfReader(BytesIO(file_content))
    pages = []
    for page_num, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            pages.append((text, page_num))
    return pages


def extract_text_from_file(file_content: bytes, filename: str) -> List[Tuple[str, int]]:
    """
    Adaptive parsing based on file extension.

    Returns:
        List of (text_segment, page_number) tuples.
        page_number is 1 for non-paginated formats, actual page for PDFs.
    """
    ext = os.path.splitext(filename)[1].lower()

    if ext == ".pdf":
        return _extract_pdf_pages(file_content)

    elif ext in [".csv", ".xlsx", ".xls"]:
        if ext == ".csv":
            df = pd.read_csv(BytesIO(file_content))
        else:
            df = pd.read_excel(BytesIO(file_content))
        return [(df.to_string(index=False), 1)]

    elif ext in [".png", ".jpg", ".jpeg", ".webp"]:
        # Downstream Gemini vision parsing can replace this placeholder
        return [(
            f"[Image uploaded: {filename}] Visual telemetry or P&ID diagram to be parsed downstream.",
            1,
        )]

    else:
        # Fallback text decoding
        text = file_content.decode("utf-8", errors="ignore")
        return [(text, 1)]


# ---------------------------------------------------------------------------
# Main ingestion function
# ---------------------------------------------------------------------------

def process_and_store_document(file_content: bytes, filename: str) -> Dict[str, Any]:
    """
    Full E2E ingestion:
      Extract -> Chunk -> Embed -> Upsert Pinecone -> Add to BM25 Index

    Args:
        file_content: Raw bytes of the uploaded file.
        filename:     Original filename (used as document_name).

    Returns:
        {"status": "success", "chunks_processed": N}  |  {"status": "error", ...}
    """
    document_name = filename

    # 1 — Extract (with page numbers for PDFs)
    page_segments = extract_text_from_file(file_content, filename)
    if not page_segments or all(not seg.strip() for seg, _ in page_segments):
        return {"status": "error", "message": "No text could be extracted from the file."}

    # 2 — Chunk each page segment independently to preserve page provenance
    all_chunks: List[str]            = []
    all_metadata: List[Dict[str, Any]] = []
    global_chunk_idx = 0

    for page_text, page_number in page_segments:
        if not page_text.strip():
            continue
        page_chunks = text_splitter.split_text(page_text)
        for chunk in page_chunks:
            section = _extract_section_heading(chunk)
            all_chunks.append(chunk)
            all_metadata.append({
                "document_name": document_name,
                "section":       section,
                "page_number":   page_number,
                "chunk_index":   global_chunk_idx,
                "text":          chunk,
            })
            global_chunk_idx += 1

    if not all_chunks:
        return {"status": "error", "message": "Text extracted but no valid chunks produced."}

    logger.info(
        "[Ingestion] '%s' -> %d pages, %d chunks.",
        document_name, len(page_segments), len(all_chunks),
    )

    # 3 — Embed & Upsert to Pinecone in batches
    batch_size = 50
    upsert_data = []

    for i, (chunk, meta) in enumerate(zip(all_chunks, all_metadata)):
        try:
            embedding = embeddings_model.embed_query(chunk)
        except Exception as e:
            logger.error("[Ingestion] Embedding failed for chunk %d: %s", i, e)
            continue

        upsert_data.append({
            "id": f"{document_name}-chunk-{meta['chunk_index']}",
            "values": embedding,
            "metadata": {
                "document_name": meta["document_name"],
                "section":       meta["section"],
                "page_number":   meta["page_number"],
                "chunk_index":   meta["chunk_index"],
                "text":          chunk,
                # backward-compat alias
                "source":        document_name,
                "chunkIndex":    meta["chunk_index"],
            },
        })

        if len(upsert_data) >= batch_size or i == len(all_chunks) - 1:
            try:
                index.upsert(vectors=upsert_data)
                logger.info("[Ingestion] Upserted batch of %d vectors to Pinecone.", len(upsert_data))
                upsert_data = []
            except Exception as e:
                logger.error("[Ingestion] Pinecone upsert failed: %s", e)
                return {"status": "error", "message": f"Pinecone upsert failed: {str(e)}"}

    # 4 — Add to BM25 Index
    try:
        bm25_index.add_documents(all_chunks, all_metadata)
        bm25_index.save()
        logger.info("[Ingestion] BM25 index updated and persisted (%d total docs).", bm25_index.size)
    except Exception as e:
        # Non-fatal — vector search will still work
        logger.warning("[Ingestion] BM25 index update failed: %s", e)

    return {"status": "success", "chunks_processed": len(all_chunks)}
