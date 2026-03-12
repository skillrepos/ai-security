#!/usr/bin/env python3
"""
create_poisoned_db.py
────────────────────────────────────────────────────────────────────
Creates a ChromaDB vector database containing BOTH legitimate OmniTech
documents AND a poisoned document to demonstrate RAG security risks.

This simulates a realistic attack scenario where an adversary has
managed to insert a malicious document into the knowledge base —
a common threat vector in enterprise RAG systems.

Attack Vectors Demonstrated:
  1. Prompt Injection via Document  - hidden LLM instructions in text
  2. Data Poisoning                 - false/malicious info that looks real
  3. Social Engineering             - tricks users into revealing credentials

Usage:
  python create_poisoned_db.py
"""

import subprocess
import sys
import re
import logging
from pathlib import Path

# ───────────────────── 3rd-party imports ───────────────────────────
try:
    from chromadb import PersistentClient
    from chromadb.config import Settings, DEFAULT_TENANT, DEFAULT_DATABASE
except ImportError:
    print("ERROR: chromadb not installed. Install with: pip install chromadb")
    exit(1)

# ───────────────────── logging ─────────────────────────────────────
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ───────────────────── configuration ───────────────────────────────

# Paths (relative to security_lab/ directory)
TOOLS_DIR = Path("../tools")
PDF_DIR = Path("../rag/knowledge_base_pdfs")
POISONED_DOC = Path("../docs/OmniTech_Special_Bulletin.txt")
CHROMA_PATH = Path("./chroma_poisoned_db")
COLLECTION_NAME = "pdf_documents"


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 200):
    """Split text into overlapping chunks at sentence boundaries."""
    if not text or len(text) <= chunk_size:
        return [text] if text else []

    chunks = []
    sentences = re.split(r'(?<=[.!?])\s+', text)
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
            current_chunk = overlap_text + " " + sentence
        else:
            current_chunk += (" " if current_chunk else "") + sentence

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


def inject_poisoned_chunks():
    """Read the poisoned document, chunk it, and inject into the vector DB."""

    # ── 1. Read poisoned document ──────────────────────────────────
    if not POISONED_DOC.exists():
        logger.error(f"Poisoned document not found: {POISONED_DOC}")
        return

    poisoned_text = POISONED_DOC.read_text()
    logger.info(f"Read poisoned document: {POISONED_DOC.name} ({len(poisoned_text)} chars)")

    # ── 2. Chunk the poisoned text ─────────────────────────────────
    chunks = chunk_text(poisoned_text)
    logger.info(f"Created {len(chunks)} poisoned chunks")

    # ── 3. Connect to the existing ChromaDB ────────────────────────
    client = PersistentClient(
        path=str(CHROMA_PATH),
        settings=Settings(),
        tenant=DEFAULT_TENANT,
        database=DEFAULT_DATABASE,
    )
    collection = client.get_collection(name=COLLECTION_NAME)

    # ── 4. Inject poisoned chunks with realistic-looking metadata ──
    # An attacker would set metadata to blend in with legitimate docs
    ids = [f"poisoned_chunk_{i}" for i in range(len(chunks))]
    metadatas = [
        {
            "source": "OmniTech_Security_Bulletin_2026.pdf",  # Fake PDF name
            "page": i + 1,
            "type": "text",
            "chunk_index": i,
        }
        for i in range(len(chunks))
    ]

    collection.add(
        ids=ids,
        documents=chunks,
        metadatas=metadatas,
    )

    logger.info(f"Injected {len(chunks)} poisoned chunks into {COLLECTION_NAME}")

    # ── 5. Show final stats ────────────────────────────────────────
    total = collection.count()
    logger.info(f"Database now contains {total} total chunks (legitimate + poisoned)")


def main():
    print("=" * 60)
    print("  VECTOR DATABASE CREATOR")
    print("=" * 60)

    # ── Step 1: Validate paths ─────────────────────────────────────
    index_script = TOOLS_DIR / "index_pdfs.py"
    if not index_script.exists():
        print(f"\n[ERROR] index_pdfs.py not found at {index_script.resolve()}")
        return

    if not PDF_DIR.exists():
        print(f"\n[ERROR] PDF directory not found at {PDF_DIR.resolve()}")
        return

    if not POISONED_DOC.exists():
        print(f"\n[ERROR] Poisoned document not found at {POISONED_DOC.resolve()}")
        return

    # ── Step 2: Index legitimate PDFs using existing tool ──────────
    print("\n[1/2] Indexing legitimate OmniTech PDFs...")
    print("-" * 60)

    result = subprocess.run(
        [
            sys.executable, str(index_script),
            "--pdf-dir", str(PDF_DIR),
            "--chroma-path", str(CHROMA_PATH),
            "--collection", COLLECTION_NAME,
        ],
        capture_output=False,
    )

    if result.returncode != 0:
        print("[ERROR] Failed to index legitimate PDFs")
        return

    # ── Step 3: Inject poisoned chunks ─────────────────────────────
    print("\n[2/2] Injecting poisoned document chunks...")
    print("-" * 60)
    inject_poisoned_chunks()

    # ── Done ───────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  DATABASE READY")
    print(f"  Location: {CHROMA_PATH.resolve()}")
    print("=" * 60)



if __name__ == "__main__":
    main()

