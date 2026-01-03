from __future__ import annotations

import re
from pathlib import Path
from typing import List

import chromadb
from sentence_transformers import SentenceTransformer

DOCS_DIR = Path(__file__).parent / "docs"
DB_DIR = Path(__file__).parent / "chroma_db"
COLLECTION = "security_docs"

DANGEROUS_PATTERNS = [
    r"ignore (all|previous) instructions",
    r"share (your )?(password|mfa|token)",
    r"claim .* return .* 90",
]

def sanitize(text: str) -> str:
    # Example “cheap” defenses:
    # 1) remove obvious prompt-injection lines
    cleaned_lines = []
    for line in text.splitlines():
        low = line.lower()
        if any(re.search(p, low) for p in DANGEROUS_PATTERNS):
            continue
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines).strip()


def load_docs() -> List[tuple[str, str]]:
    docs = []
    for p in DOCS_DIR.glob("*.md"):
        raw = p.read_text(encoding="utf-8")
        docs.append((p.name, sanitize(raw)))
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

    print(f"Ingested {len(docs)} docs into {DB_DIR} (SECURE: sanitized ingestion).")


if __name__ == "__main__":
    main()
