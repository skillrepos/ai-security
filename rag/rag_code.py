#!/usr/bin/env python3
"""
Complete RAG (Retrieval-Augmented Generation) Implementation
────────────────────────────────────────────────────────────────────
"""

import logging
import os
from typing import List, Dict
from pathlib import Path
import requests
import json

# IMPORTANT: Use PersistentClient to connect to the disk-based database
from chromadb import PersistentClient
from chromadb.config import Settings, DEFAULT_TENANT, DEFAULT_DATABASE

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rag-system")

# ═══════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════

OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")  # Set via OLLAMA_MODEL env var

class RAGSystem:
    """Complete RAG system with retrieval and generation"""

    def __init__(self, chroma_path: str = "./chroma_db", collection_name: str = "pdf_documents"):
        """
        Initialize the RAG system.

        Parameters:
        -----------
        chroma_path : str
            Path to the ChromaDB directory created by index_pdfs.py
        collection_name : str
            Name of the collection created by index_pdfs.py
        """
        self.chroma_path = Path(chroma_path)
        self.collection_name = collection_name
        self.chroma_client = None
        self.collection = None
        self.connect_to_database()

    def connect_to_database(self):
        logger.info(f"Connecting to ChromaDB at {self.chroma_path}...")

        # VALIDATION: Check if database directory exists on disk
        # The database must be created first by running index_pdfs.py
        if not self.chroma_path.exists():
            logger.error(f"Database not found at {self.chroma_path.resolve()}")
            logger.error("Please run 'python tools/index_pdfs.py' first to create the database.")
            raise FileNotFoundError(f"ChromaDB not found at {self.chroma_path}")

        self.chroma_client = PersistentClient(
            path=str(self.chroma_path),
            settings=Settings(),
            tenant=DEFAULT_TENANT,
            database=DEFAULT_DATABASE,
        )

        try:

            # VERIFY: Get collection info to confirm it has data
            collection_data = self.collection.get()
            total_chunks = len(collection_data.get("documents", []))

            logger.info(f"Successfully connected to collection '{self.collection_name}'")
            logger.info(f"Collection contains {total_chunks} indexed chunks")

        except Exception as e:
            logger.error(f"Failed to access collection '{self.collection_name}': {e}")
            logger.error("Make sure you've run 'python tools/index_pdfs.py' to create the index.")
            raise

    def retrieve(self, query: str, max_results: int = 3) -> List[Dict]:
        """
        """
        try:
            logger.info(f"[RETRIEVE] Searching for relevant context...")

            results = self.collection.query(
                query_texts=[query],              # User's question
                n_results=max_results,            # How many chunks to retrieve
                include=["documents", "metadatas", "distances"]  # What to return
            )

            # FORMAT RESULTS: Convert ChromaDB response to our format
            retrieved_chunks = []

            if results['documents'] and len(results['documents'][0]) > 0:
                # Iterate through each result (chunk) returned
                for i in range(len(results['documents'][0])):
                    document = results['documents'][0][i]   # The actual text content
                    metadata = results['metadatas'][0][i]   # Source file, page, etc.
                    distance = results['distances'][0][i]   # Cosine distance (lower = more similar)


                    # Store all information about this chunk
                    retrieved_chunks.append({
                        "content": document,
                        "source": metadata.get('source', 'unknown'),
                        "page": metadata.get('page', 'unknown'),
                        "type": metadata.get('type', 'text'),  # 'text' or 'table'
                        "score": score
                    })

                    logger.info(f"  [RETRIEVE] Found: {metadata.get('source')} (page {metadata.get('page')}) - Score: {score:.3f}")

            return retrieved_chunks

        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            return []

    def build_prompt(self, query: str, context_chunks: List[Dict]) -> str:
        """
        """
        logger.info("[AUGMENT] Building prompt with context...")


        # BUILD FULL PROMPT: Create instructions + context + question for the LLM
        # This is the "Augmentation" step - we're augmenting the user's question
        # with relevant information from our knowledge base

        return prompt

    def generate(self, prompt: str) -> str:
        """
        """
        logger.info("[GENERATE] Querying Llama 3.2 via Ollama...")

        try:
            # PREPARE LLM REQUEST: Configure how the model should generate the answer
            payload = {
                }
            }

            # SEND REQUEST: Call Ollama's HTTP API
            # Ollama must be running locally (ollama serve)

            # PROCESS RESPONSE: Extract the generated answer
            if response.status_code == 200:
                result = response.json()
                answer = result.get('response', '').strip()

                logger.info("[GENERATE] Answer generated successfully")
                return answer
            else:
                error_msg = f"Ollama API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return f"Error: Failed to get response from Ollama. Is Ollama running? (ollama serve)"

        except requests.exceptions.ConnectionError:
            error_msg = "Could not connect to Ollama. Make sure Ollama is running:\n  ollama serve"
            logger.error(error_msg)
            return f"Error: {error_msg}"
        except requests.exceptions.Timeout:
            error_msg = "Ollama request timed out"
            logger.error(error_msg)
            return f"Error: {error_msg}"
        except Exception as e:
            error_msg = f"Generation failed: {e}"
            logger.error(error_msg)
            return f"Error: {error_msg}"

    def query(self, question: str, max_context_chunks: int = 3, show_sources: bool = True) -> Dict:
        """
        """
        logger.info("="*60)
        logger.info(f"RAG Query: {question}")
        logger.info("="*60)

        # ═══════════════════════════════════════════════════════════════
        # ═══════════════════════════════════════════════════════════════


        # EARLY EXIT: If no relevant content found, return immediately
        if not context_chunks:
            return {
                "answer": "I couldn't find any relevant information in the documentation to answer your question.",
                "sources": [],
                "context_used": []
            }



        # PREPARE RESPONSE: Package the answer with source citations
        response = {
            "answer": answer,
            "sources": [
                {
                    "source": chunk['source'],  # Which PDF file
                    "page": chunk['page'],      # What page number
                    "score": chunk['score']     # How relevant (0-1)
                }
                for chunk in context_chunks
            ] if show_sources else [],
            "context_used": context_chunks if show_sources else []
        }

        return response

    def get_statistics(self) -> Dict:
        """Get statistics about the knowledge base"""
        try:
            # GET ALL DATA: Retrieve all documents and metadata from the collection
            collection_data = self.collection.get()
            total_docs = len(collection_data.get("documents", []))
            metadatas = collection_data.get("metadatas", [])

            # COUNT BY SOURCE: Track how many chunks come from each PDF
            sources = {}
            content_types = {"text": 0, "table": 0}

            for meta in metadatas:
                # Count chunks per source file
                source = meta.get("source", "unknown")
                sources[source] = sources.get(source, 0) + 1

                # Count text vs table chunks
                content_type = meta.get("type", "text")
                if content_type in content_types:
                    content_types[content_type] += 1

            # RETURN SUMMARY: Useful information about the knowledge base
            return {
                "total_chunks": total_docs,
                "sources": sources,                      # Per-file chunk counts
                "content_types": content_types,          # Text vs table breakdown
                "database_path": str(self.chroma_path.resolve()),
                "collection_name": self.collection_name
            }

        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}


# ═══════════════════════════════════════════════════════════════════
# Main Interactive Loop
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("="*60)
    print("RAG System - Retrieval-Augmented Generation")
    print("Using ChromaDB + Llama 3.2 (Ollama)")
    print("="*60)

    try:
        # ═══════════════════════════════════════════════════════════════
        # INITIALIZE: Connect to database and validate setup
        # ═══════════════════════════════════════════════════════════════


        # Display knowledge base statistics
        stats = rag.get_statistics()
        print("\nKnowledge Base Statistics:")
        print(f"  Total Chunks: {stats.get('total_chunks', 0)}")
        print(f"  Database: {stats.get('database_path', 'N/A')}")

        print("\n  Content Types:")
        for content_type, count in stats.get('content_types', {}).items():
            print(f"    • {content_type}: {count}")

        print("\n  Source Documents:")
        for source, count in stats.get('sources', {}).items():
            print(f"    • {source}: {count} chunks")

        # ═══════════════════════════════════════════════════════════════
        # VALIDATE OLLAMA: Check that LLM service is running and ready
        # ═══════════════════════════════════════════════════════════════

        print("\n" + "="*60)
        print("Checking Ollama Connection...")
        print("="*60)
        try:
            # Try to connect to Ollama API to check if it's running
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code == 200:
                print("✅ Ollama is running")

                # Check if our specific model is available
                models = response.json().get('models', [])
                model_names = [m.get('name', '') for m in models]
                if OLLAMA_MODEL in model_names or any(OLLAMA_MODEL in name for name in model_names):
                    print(f"✅ Model '{OLLAMA_MODEL}' is available")
                else:
                    print(f"⚠️  Model '{OLLAMA_MODEL}' not found. Run: ollama pull {OLLAMA_MODEL}")
            else:
                print("⚠️  Ollama not responding properly")
        except:
            print("❌ Ollama not running. Start with: ollama serve")
            print("   Then pull model: ollama pull llama3.2")

        # Suggested queries
        print("\n" + "="*60)
        print("Suggested Questions to Try:")
        print("="*60)
        print("  • How can I return a product?")
        print("  • What are the shipping costs?")
        print("  • How do I reset my password?")
        print("  • What should I do if my device won't turn on?")
        print("  • Do you offer international shipping?")
        print("="*60)

        # ═══════════════════════════════════════════════════════════════
        # INTERACTIVE LOOP: Accept questions and generate answers
        # ═══════════════════════════════════════════════════════════════

        print("\nAsk your question (or 'quit' to exit):")

        while True:
            # GET USER INPUT: Read question from command line
            question = input("\n> ").strip()

            # EXIT: User wants to quit
            if question.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye!")
                break

            # SKIP: Empty input
            if not question:
                continue


            # DISPLAY ANSWER: Show the LLM-generated response
            print("\n" + "="*60)
            print("ANSWER:")
            print("="*60)
            print(result['answer'])

            # DISPLAY SOURCES: Show which documents were used as context
            # This provides transparency and allows users to verify answers
            if result['sources']:
                print("\n" + "-"*60)
                print("SOURCES:")
                print("-"*60)
                for i, source in enumerate(result['sources'], 1):
                    print(f"  [{i}] {source['source']} (Page {source['page']}) - Relevance: {source['score']:.3f}")

    except KeyboardInterrupt:
        print("\n\nInterrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure to:")
        print("  1. Run: python tools/index_pdfs.py")
        print("  2. Start Ollama: ollama serve")
        print("  3. Pull model: ollama pull llama3.2")
