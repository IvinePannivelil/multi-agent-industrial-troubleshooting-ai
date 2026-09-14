import logging
from typing import List, Dict, Any

from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

# Using the requested configuration
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100

_text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", " ", ""]
)


def chunk_parsed_document(parsed_units: List[Dict[str, Any]], filename: str) -> List[Dict[str, Any]]:
    """
    Takes the structured blocks from the parser and breaks them down into
    Langchain chunks ready for embedding.
    """
    logger.info(f"[DocumentChunker] Chunking {len(parsed_units)} raw units from '{filename}'")
    
    final_chunks = []
    global_chunk_idx = 0
    
    for unit in parsed_units:
        raw_text = unit["text"]
        page_num = unit["page_number"]
        section = unit["section"]
        
        # Split text using the configured splitter
        splits = _text_splitter.split_text(raw_text)
        
        for split in splits:
            final_chunks.append({
                "text": split,
                "document_name": filename,
                "page_number": page_num,
                "section": section,
                "chunk_index": global_chunk_idx
            })
            global_chunk_idx += 1
            
    logger.info(f"[DocumentChunker] Generated {len(final_chunks)} total chunks for '{filename}'")
    return final_chunks
