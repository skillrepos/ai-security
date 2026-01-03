from __future__ import annotations

import os
from pathlib import Path
from typing import List

import chromadb
from sentence_transformers import SentenceTransformer

DOCS_DIR = Path(__file__).parent / "docs"
DB_DIR = Path(__file__).parent / "chroma_db"
COLLECTION = "security_docs"


def load_docs() -> List[tuple[str, str]]:
    docs = []
    for p in DOCS_DIR.glob("*.md"):
        docs.append((p.name, p.read_text(encoding="utf-8")))
    return docs


def main() -> None:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(DB_DIR))
    col = client.get_or_create_collection(COLLECTION)

    model = SentenceTransformer("all-MiniLM-L6-v2")

    docs = load_docs()
    ids = [d[0] for d in docs]
    texts = [d[1] for d in docs]
    embeds = model.encode(texts).tolist()

    col.add(ids=ids, documents=texts, embeddings=embeds)

    print(f"Ingested {len(docs)} docs into {DB_DIR} (INSECURE: no sanitization).")


if __name__ == "__main__":
    main()
