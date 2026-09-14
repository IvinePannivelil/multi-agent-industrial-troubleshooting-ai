import logging
import os
import requests
from typing import Dict, Any, List

from services.doc_ingestion.document_parser import parse_document
from services.doc_ingestion.document_chunker import chunk_parsed_document

# Import existing indexing infrastructure
from core.config import PINECONE_INDEX_NAME, PINECONE_API_KEY
from pinecone import Pinecone
from services.bm25_index import bm25_index

logger = logging.getLogger(__name__)

# Initialize connections
_pc = Pinecone(api_key=PINECONE_API_KEY)
_index = _pc.Index(PINECONE_INDEX_NAME)

_OLLAMA_ENDPOINT = os.getenv("LOCAL_LLM_ENDPOINT", "http://localhost:11434")
_EMBED_MODEL = "nomic-embed-text"

def _embed_texts(texts: List[str]) -> List[List[float]]:
    """Generate embeddings using Ollama's nomic-embed-text model."""
    vectors = []
    for text in texts:
        resp = requests.post(
            f"{_OLLAMA_ENDPOINT}/api/embeddings",
            json={"model": _EMBED_MODEL, "prompt": text},
            timeout=30,
        )
        resp.raise_for_status()
        vectors.append(resp.json()["embedding"])
    return vectors


def ingest_document(file_content: bytes, filename: str) -> Dict[str, Any]:
    """
    End-to-end ingestion pipeline:
      1. Parse document text & structure
      2. Chunk text into 800 token slices
      3. Generate embeddings for each chunk
      4. Upsert vectors to Pinecone
      5. Add raw text to local BM25 index
    """
    logger.info(f"[DocumentIngestor] Starting ingestion for '{filename}'")
    
    # 1. Parse
    parsed_units = parse_document(file_content, filename)
    if not parsed_units:
        logger.warning(f"[DocumentIngestor] No text extracted from '{filename}'")
        return {"status": "failed", "chunks_added": 0, "error": "Empty document"}
        
    # 2. Chunk
    chunks = chunk_parsed_document(parsed_units, filename)
    if not chunks:
        return {"status": "failed", "chunks_added": 0, "error": "No chunks generated"}
        
    # 3. Generate Embeddings & 4. Upsert
    batch_size = 100
    total_upserted = 0
    
    # Collect texts for bm25
    bm25_documents = []
    
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        texts = [c["text"] for c in batch]
        
        # Add to BM25 holding array
        bm25_documents.extend(texts)
        
        # Generate embeddings in batch
        try:
            vectors = _embed_texts(texts)
        except Exception as e:
            logger.error(f"[DocumentIngestor] Embedding generation failed: {e}")
            raise
            
        pinecone_records = []
        for j, chunk_meta in enumerate(batch):
            doc_id = f"{filename}_{chunk_meta['chunk_index']}"
            
            pinecone_records.append({
                "id": doc_id,
                "values": vectors[j],
                "metadata": {
                    "text": chunk_meta["text"],
                    "document_name": chunk_meta["document_name"],
                    "page_number": chunk_meta["page_number"],
                    "section": chunk_meta["section"],
                    "chunk_index": chunk_meta["chunk_index"]
                }
            })
            
        # Upsert batch to Pinecone
        try:
            _index.upsert(vectors=pinecone_records)
            total_upserted += len(pinecone_records)
        except Exception as e:
            logger.error(f"[DocumentIngestor] Pinecone upsert failed: {e}")
            raise
            
    # 5. Add to BM25 Index & Save
    logger.info(f"[DocumentIngestor] Pushing {len(bm25_documents)} chunks to BM25")
    metadata_for_bm25 = [
        {
            "document_name": chunk["document_name"],
            "section": chunk["section"],
            "page_number": chunk["page_number"],
            "chunk_index": chunk["chunk_index"],
        }
        for chunk in chunks[:len(bm25_documents)]
    ]
    bm25_index.add_documents(bm25_documents, metadata_for_bm25)
        
    return {
        "status": "indexed",
        "chunks_added": total_upserted
    }
