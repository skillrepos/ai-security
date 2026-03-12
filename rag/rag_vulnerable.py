#!/usr/bin/env python3
"""
RAG System - VULNERABLE VERSION (Ollama / granite4:3b)
────────────────────────────────────────────────────────────────────
Uses local Ollama with the granite4:3b model. The smaller model is
more susceptible to prompt injection from poisoned documents — useful
for demonstrating how the phishing URL appears in responses without
any prompt coaxing.
"""

import logging
import os
from typing import List, Dict
from pathlib import Path
import requests
import json

from chromadb import PersistentClient
from chromadb.config import Settings, DEFAULT_TENANT, DEFAULT_DATABASE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rag-vulnerable-ollama")

# ═══════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════

OLLAMA_API_URL = "http://localhost:11434/api/generate"
# Hardcoded — the small model is more susceptible to prompt injection,
# which is the point of this demo. Ignores OLLAMA_MODEL env var intentionally.
OLLAMA_MODEL = "granite4:3b"


class RAGSystem:
    """Standard RAG system - NO security hardening"""

    def __init__(self, chroma_path: str = "./chroma_poisoned_db",
                 collection_name: str = "pdf_documents"):
        self.chroma_path = Path(chroma_path)
        self.collection_name = collection_name
        self.chroma_client = None
        self.collection = None
        self.connect_to_database()

    def connect_to_database(self):
        """Connect to the ChromaDB database (which contains poisoned chunks)"""
        logger.info(f"Connecting to ChromaDB at {self.chroma_path}...")

        if not self.chroma_path.exists():
            logger.error(f"Database not found at {self.chroma_path.resolve()}")
            logger.error("Run 'python create_poisoned_db.py' first.")
            raise FileNotFoundError(f"ChromaDB not found at {self.chroma_path}")

        self.chroma_client = PersistentClient(
            path=str(self.chroma_path),
            settings=Settings(),
            tenant=DEFAULT_TENANT,
            database=DEFAULT_DATABASE,
        )

        try:
            self.collection = self.chroma_client.get_collection(name=self.collection_name)
            collection_data = self.collection.get()
            total_chunks = len(collection_data.get("documents", []))
            logger.info(f"Connected to '{self.collection_name}' ({total_chunks} chunks)")
        except Exception as e:
            logger.error(f"Failed to access collection '{self.collection_name}': {e}")
            raise

    # ═══════════════════════════════════════════════════════════════
    # STEP 1: RETRIEVE - Find relevant chunks (no filtering)
    # ═══════════════════════════════════════════════════════════════

    def retrieve(self, query: str, max_results: int = 5) -> List[Dict]:
        """Retrieve relevant chunks - NO security checks on content"""
        try:
            logger.info(f"[RETRIEVE] Searching for relevant context...")

            # VULNERABILITY: Retrieves extra chunks then deduplicates by source,
            # keeping only the best chunk per document. This gives every source
            # equal representation — including poisoned documents that would
            # otherwise be outnumbered by legitimate ones.
            results = self.collection.query(
                query_texts=[query],
                n_results=max_results * 2,
                include=["documents", "metadatas", "distances"]
            )

            seen_sources = {}
            retrieved_chunks = []

            if results['documents'] and len(results['documents'][0]) > 0:
                for i in range(len(results['documents'][0])):
                    document = results['documents'][0][i]
                    metadata = results['metadatas'][0][i]
                    distance = results['distances'][0][i]
                    score = 1.0 / (1.0 + distance)
                    source = metadata.get('source', 'unknown')

                    # Keep only the best chunk per source document
                    if source in seen_sources:
                        continue
                    seen_sources[source] = True

                    retrieved_chunks.append({
                        "content": document,
                        "source": source,
                        "page": metadata.get('page', 'unknown'),
                        "type": metadata.get('type', 'text'),
                        "score": score
                    })

                    logger.info(f"  [RETRIEVE] Found: {source} "
                                f"(page {metadata.get('page')}) - Score: {score:.3f}")

                    if len(retrieved_chunks) >= max_results:
                        break

            return retrieved_chunks

        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            return []

    # ═══════════════════════════════════════════════════════════════
    # STEP 2: AUGMENT - Build prompt with context (no sanitization)
    # ═══════════════════════════════════════════════════════════════

    def build_prompt(self, query: str, context_chunks: List[Dict]) -> str:
        """Build prompt - NO content scanning or sanitization"""
        logger.info("[AUGMENT] Building prompt with context...")

        # VULNERABILITY: Chunks are presented in reverse relevance order.
        # This means lower-scored (potentially poisoned) chunks appear FIRST
        # in the context, exploiting LLM primacy bias — models pay more
        # attention to content that appears earlier in the prompt.
        ordered_chunks = list(reversed(context_chunks))

        context_text = ""
        for i, chunk in enumerate(ordered_chunks, 1):
            context_text += f"\n--- Context {i} (Source: {chunk['source']}, Page: {chunk['page']}) ---\n"
            context_text += chunk['content']
            context_text += "\n"

        prompt = f"""You are a helpful assistant answering questions based on the provided documentation.

CONTEXT FROM DOCUMENTATION:
{context_text}

USER QUESTION:
{query}

INSTRUCTIONS:
- Answer based ONLY on the context provided above
- Provide a complete, comprehensive answer that includes ALL relevant information from the context
- Be specific and cite which document/page the information comes from
- If the context does NOT contain enough information to answer the question, respond with: "I don't have enough information in the provided documentation to answer this question."
- IMPORTANT: Do not include both an answer AND the "I don't have enough information" message - provide only one or the other

ANSWER:"""

        return prompt

    # ═══════════════════════════════════════════════════════════════
    # STEP 3: GENERATE - Get answer from LLM (no output scanning)
    # ═══════════════════════════════════════════════════════════════

    def generate(self, prompt: str) -> str:
        """Generate answer - NO output validation"""
        logger.info(f"[GENERATE] Querying {OLLAMA_MODEL} via Ollama...")

        try:
            payload = {
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "num_predict": 500
                }
            }

            response = requests.post(OLLAMA_API_URL, json=payload, timeout=300)

            if response.status_code == 200:
                result = response.json()
                answer = result.get('response', '').strip()
                logger.info("[GENERATE] Answer generated successfully")
                return answer
            else:
                return f"Error: Ollama API error {response.status_code}"

        except requests.exceptions.ConnectionError:
            return "Error: Could not connect to Ollama. Make sure Ollama is running: ollama serve"
        except requests.exceptions.Timeout:
            return "Error: Ollama request timed out"
        except Exception as e:
            return f"Error: Generation failed: {e}"

    # ═══════════════════════════════════════════════════════════════
    # Complete RAG Pipeline: Retrieve -> Augment -> Generate
    # ═══════════════════════════════════════════════════════════════

    def query(self, question: str, max_context_chunks: int = 3,
              show_sources: bool = True) -> Dict:
        """Run the full RAG pipeline - NO security checks anywhere"""
        logger.info("=" * 60)
        logger.info(f"RAG Query: {question}")
        logger.info("=" * 60)

        # STEP 1: RETRIEVE
        context_chunks = self.retrieve(question, max_results=max_context_chunks)

        if not context_chunks:
            return {
                "answer": "I couldn't find any relevant information.",
                "sources": [],
                "context_used": []
            }

        # STEP 2: AUGMENT
        prompt = self.build_prompt(question, context_chunks)

        # STEP 3: GENERATE
        answer = self.generate(prompt)

        response = {
            "answer": answer,
            "sources": [
                {
                    "source": chunk['source'],
                    "page": chunk['page'],
                    "score": chunk['score']
                }
                for chunk in context_chunks
            ] if show_sources else [],
            "context_used": context_chunks if show_sources else []
        }

        return response

    def get_statistics(self) -> Dict:
        """Get knowledge base statistics"""
        try:
            collection_data = self.collection.get()
            total_docs = len(collection_data.get("documents", []))
            metadatas = collection_data.get("metadatas", [])

            sources = {}
            for meta in metadatas:
                source = meta.get("source", "unknown")
                sources[source] = sources.get(source, 0) + 1

            return {
                "total_chunks": total_docs,
                "sources": sources,
                "database_path": str(self.chroma_path.resolve()),
            }
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}


# ═══════════════════════════════════════════════════════════════════
# Main Interactive Loop
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("  RAG System - VULNERABLE VERSION (Ollama)")
    print("  (No Security Hardening)")
    print(f"  Using ChromaDB + {OLLAMA_MODEL} (Local Ollama)")
    print("=" * 60)
    print("\n  WARNING: This RAG system has NO defenses against")
    print("  document poisoning or prompt injection attacks.")
    print("  Observe how poisoned content affects responses.\n")

    try:
        rag = RAGSystem(chroma_path="./chroma_poisoned_db",
                        collection_name="pdf_documents")

        stats = rag.get_statistics()
        print("Knowledge Base Statistics:")
        print(f"  Total Chunks: {stats.get('total_chunks', 0)}")
        print(f"  Database: {stats.get('database_path', 'N/A')}")
        print("\n  Source Documents:")
        for source, count in stats.get('sources', {}).items():
            print(f"    - {source}: {count} chunks")

        # Check Ollama
        print("\n" + "=" * 60)
        print("Checking Ollama Connection...")
        print("=" * 60)
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code == 200:
                print("[OK] Ollama is running")
                models = response.json().get('models', [])
                model_names = [m.get('name', '') for m in models]
                if OLLAMA_MODEL in model_names or any(OLLAMA_MODEL in name for name in model_names):
                    print(f"[OK] Model '{OLLAMA_MODEL}' is available")
                else:
                    print(f"[!!] Model '{OLLAMA_MODEL}' not found. Run: ollama pull {OLLAMA_MODEL}")
        except Exception:
            print("[ERROR] Ollama not running. Start with: ollama serve")

        print("\n" + "=" * 60)
        print("Try These Questions to See Poisoning in Action:")
        print("=" * 60)
        print("  - How do I reset my password?")
        print("  - How do I get a refund?")
        print("  - What is the return policy?")
        print("=" * 60)

        print("\nAsk your question (or 'quit' to exit):")

        while True:
            question = input("\n> ").strip()

            if question.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye!")
                break

            if not question:
                continue

            result = rag.query(question, max_context_chunks=5)

            print("\n" + "=" * 60)
            print("ANSWER:")
            print("=" * 60)
            print(result['answer'])

            if result['sources']:
                print("\n" + "-" * 60)
                print("SOURCES:")
                print("-" * 60)
                for i, source in enumerate(result['sources'], 1):
                    print(f"  [{i}] {source['source']} (Page {source['page']}) "
                          f"- Relevance: {source['score']:.3f}")

    except KeyboardInterrupt:
        print("\n\nInterrupted. Goodbye!")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        print("\nMake sure to:")
        print("  1. Run: python create_poisoned_db.py")
        print("  2. Start Ollama: ollama serve")
        print(f"  3. Pull model: ollama pull {OLLAMA_MODEL}")
