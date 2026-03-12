#!/usr/bin/env python3
"""
RAG System - HARDENED VERSION (Security Defenses Enabled)
────────────────────────────────────────────────────────────────────
"""

import logging
import os
import re
from typing import List, Dict, Tuple
from pathlib import Path
import requests
import json

from chromadb import PersistentClient
from chromadb.config import Settings, DEFAULT_TENANT, DEFAULT_DATABASE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rag-hardened")

# ═══════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════

OLLAMA_API_URL = "http://localhost:11434/api/generate"
# Hardcoded to match rag_vulnerable.py for apples-to-apples comparison
OLLAMA_MODEL = "llama3.2:1b"


# ═══════════════════════════════════════════════════════════════════
# SecurityGuard - RAG Security Defense Layer
# ═══════════════════════════════════════════════════════════════════

class SecurityGuard:
    """
    Defends RAG systems against document poisoning and prompt injection.

    Implements multiple security checks:
    - Prompt injection detection (regex pattern matching)
    - Source allowlist verification
    - Relevance score thresholds
    - Output scanning for suspicious URLs/emails
    """

    # ── Prompt injection patterns ──────────────────────────────────

    # ── Trusted document sources (allowlist) ───────────────────────
    # Only these documents are considered legitimate knowledge sources
    TRUSTED_SOURCES = [
    ]

    # ── Known legitimate domains ───────────────────────────────────
    # URLs/emails with these domains are considered safe in output
    TRUSTED_DOMAINS = [
    ]

    # ── Minimum relevance score ────────────────────────────────────
    # Chunks below this threshold are discarded (low confidence)

    def __init__(self):
        """Initialize SecurityGuard with empty security log"""
        self.security_log = []

    def scan_for_injection(self, text: str) -> Tuple[bool, List[str]]:
        """
        Scan text for prompt injection patterns.

        Parameters:
        -----------
        text : str
            The text content of a retrieved chunk

        Returns:
        --------
        Tuple[bool, List[str]]
            (is_safe, list_of_warnings)
            is_safe=True means no injection found
        """
        warnings = []

        for pattern, description in self.INJECTION_PATTERNS:
            if re.search(pattern, text):
                warnings.append(f"INJECTION: {description} — matched: '{pattern}'")

        is_safe = len(warnings) == 0

        if not is_safe:
            self.security_log.append({
                "check": "injection_scan",
                "result": "BLOCKED",
                "warnings": warnings,
                "text_preview": text[:100] + "..."
            })

        return is_safe, warnings

    def verify_source(self, source: str) -> bool:
        """

        Parameters:
        -----------
        source : str
            The source filename from chunk metadata

        Returns:
        --------
        bool
            True if the source is trusted
        """
        is_trusted = source in self.TRUSTED_SOURCES

        if not is_trusted:
            self.security_log.append({
                "check": "source_verification",
                "result": "BLOCKED",
                "source": source,
                "reason": f"Source '{source}' is not in the trusted allowlist"
            })

        return is_trusted

    def check_relevance(self, score: float) -> bool:
        """
        Parameters:
        -----------
        score : float
            The relevance score (0.0 to 1.0)

        Returns:
        --------
        bool
            True if the score is above the threshold
        """

        if not meets_threshold:
            self.security_log.append({
                "check": "relevance_threshold",
                "result": "BLOCKED",
                "score": score,
                "threshold": self.MIN_RELEVANCE_SCORE,
                "reason": f"Score {score:.3f} below threshold {self.MIN_RELEVANCE_SCORE}"
            })

        return meets_threshold

    def scan_output(self, text: str) -> Tuple[bool, List[str]]:
        """
        Parameters:
        -----------
        text : str
            The generated answer from the LLM

        Returns:
        --------
        Tuple[bool, List[str]]
            (is_safe, list_of_warnings)
        """
        warnings = []

        urls = re.findall(r'https?://([^\s/\)]+)', text)
        for url_domain in urls:
            is_trusted = any(url_domain.endswith(d) for d in self.TRUSTED_DOMAINS)
            if not is_trusted:
                warnings.append(f"UNTRUSTED URL: {url_domain}")

        emails = re.findall(r'[\w.+-]+@([\w.-]+)', text)
        for email_domain in emails:
            is_trusted = any(email_domain.endswith(d) for d in self.TRUSTED_DOMAINS)
            if not is_trusted:
                warnings.append(f"UNTRUSTED EMAIL DOMAIN: {email_domain}")

        sensitive_patterns = [
            (r'(?i)credit\s+card\s+number', "Asks for credit card number"),
            (r'(?i)full\s+credit\s+card', "Asks for credit card details"),
            (r'(?i)enter\s+(your|their)\s+(current\s+)?password', "Asks to enter password"),
            (r'(?i)social\s+security\s+number', "Asks for SSN"),
            (r'(?i)1-900-', "Premium rate phone number"),
        ]

        for pattern, description in sensitive_patterns:
            if re.search(pattern, text):
                warnings.append(f"SENSITIVE DATA REQUEST: {description}")

        is_safe = len(warnings) == 0

        if not is_safe:
            })

        return is_safe, warnings

    def filter_chunks(self, chunks: List[Dict]) -> List[Dict]:
        """

        Checks applied to each chunk:
        1. Source allowlist verification
        2. Relevance score threshold
        3. Prompt injection scanning

        Parameters:
        -----------
        chunks : List[Dict]
            Retrieved chunks from vector database

        Returns:
        --------
        List[Dict]
            Only chunks that pass all security checks
        """
        safe_chunks = []

        print("\n" + "=" * 60)
        print("SECURITY GUARD - Filtering Retrieved Chunks")
        print("=" * 60)


            # CHECK 1: Source allowlist

            # CHECK 2: Relevance threshold
            # CHECK 3: Injection scanning

            # Report result
            if blocked:
                print(f"\n  [BLOCKED] Chunk {i} from '{source}'")
                for reason in reasons:
                    print(f"    >> {reason}")
            else:
                print(f"\n  [  OK  ] Chunk {i} from '{source}' (score: {score:.3f})")
                safe_chunks.append(chunk)

        print(f"\n  Result: {len(safe_chunks)}/{len(chunks)} chunks passed security checks")
        print("=" * 60)

        return safe_chunks

    def get_security_report(self) -> str:
        """

        Returns:
        --------
        str
            Formatted security report
        """
        if not self.security_log:
            return "No security events recorded."

        report = "\nSECURITY REPORT\n"
        report += "=" * 60 + "\n"

        blocked = sum(1 for e in self.security_log if e.get('result') == 'BLOCKED')
        flagged = sum(1 for e in self.security_log if e.get('result') == 'FLAGGED')

        report += f"  Total events: {len(self.security_log)}\n"
        report += f"  Blocked: {blocked}\n"
        report += f"  Flagged: {flagged}\n"
        report += "-" * 60 + "\n"

        for i, event in enumerate(self.security_log, 1):
            report += f"\n  Event {i}: [{event.get('result')}] {event.get('check')}\n"
            if 'warnings' in event:
                for w in event['warnings']:
                    report += f"    - {w}\n"
            if 'reason' in event:
                report += f"    - {event['reason']}\n"
            if 'source' in event:
                report += f"    - Source: {event['source']}\n"

        report += "\n" + "=" * 60
        return report


# ═══════════════════════════════════════════════════════════════════
# Hardened RAG System
# ═══════════════════════════════════════════════════════════════════

class HardenedRAGSystem:
    """RAG system WITH security hardening via SecurityGuard"""

    def __init__(self, chroma_path: str = "./chroma_poisoned_db",
                 collection_name: str = "pdf_documents"):
        self.chroma_path = Path(chroma_path)
        self.collection_name = collection_name
        self.chroma_client = None
        self.collection = None
        # SECURITY: Initialize the SecurityGuard
        self.security_guard = SecurityGuard()
        self.connect_to_database()

    def connect_to_database(self):

        if not self.chroma_path.exists():
            logger.error(f"Database not found at {self.chroma_path.resolve()}")
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


    def retrieve(self, query: str, max_results: int = 5) -> List[Dict]:
        """Retrieve relevant chunks from vector database"""
        try:
            logger.info(f"[RETRIEVE] Searching for relevant context...")

            # Retrieve top chunks without deduplication by source.
            # Unlike the vulnerable version, the hardened pipeline allows
            # multiple chunks from the same trusted source — giving the
            # model more context after untrusted chunks are filtered out.
            results = self.collection.query(
                query_texts=[query],
                n_results=max_results,
                include=["documents", "metadatas", "distances"]
            )

            retrieved_chunks = []

            if results['documents'] and len(results['documents'][0]) > 0:
                for i in range(len(results['documents'][0])):
                    document = results['documents'][0][i]
                    metadata = results['metadatas'][0][i]
                    distance = results['distances'][0][i]
                    score = 1.0 / (1.0 + distance)
                    source = metadata.get('source', 'unknown')

                    retrieved_chunks.append({
                        "content": document,
                        "source": source,
                        "page": metadata.get('page', 'unknown'),
                        "type": metadata.get('type', 'text'),
                        "score": score
                    })

                    logger.info(f"  [RETRIEVE] Found: {source} "
                                f"(page {metadata.get('page')}) - Score: {score:.3f}")

            return retrieved_chunks

        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            return []

    def build_prompt(self, query: str, context_chunks: List[Dict]) -> str:
        """Build prompt with context"""
        logger.info("[AUGMENT] Building prompt with FILTERED context...")

        # Present chunks in reverse relevance order (matches the vulnerable
        # version's ordering so the comparison is apples-to-apples).
        ordered_chunks = list(reversed(context_chunks))

        context_text = ""
        for i, chunk in enumerate(ordered_chunks, 1):

        prompt = f"""You are a helpful assistant answering questions based on the provided documentation.

CONTEXT FROM DOCUMENTATION:
{context_text}

USER QUESTION:
{query}

INSTRUCTIONS:

ANSWER:"""

        return prompt

    def generate(self, prompt: str) -> str:
        """Generate answer via Ollama"""
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
    # HARDENED RAG Pipeline: Retrieve -> FILTER -> Augment -> Generate -> SCAN
    # ═══════════════════════════════════════════════════════════════

    def query(self, question: str, max_context_chunks: int = 5,
              show_sources: bool = True) -> Dict:
        """
        Hardened RAG pipeline with security checks at two points:
          1. AFTER retrieval  - filter out poisoned/untrusted chunks
          2. AFTER generation - scan output for suspicious content
        """
        logger.info("=" * 60)
        logger.info(f"HARDENED RAG Query: {question}")
        logger.info("=" * 60)

        # STEP 1: RETRIEVE (fetch extra chunks since some may be filtered)
        context_chunks = self.retrieve(question, max_results=max_context_chunks)

        if not context_chunks:
            return {
                "answer": "I couldn't find any relevant information.",
                "sources": [],
                "context_used": [],
                "security_events": []
            }


        # If ALL chunks were filtered out, the query may be under attack
        if not safe_chunks:
            return {
                "answer": "[SECURITY] All retrieved context was flagged as "
                          "potentially compromised. Cannot provide a safe answer. "
                          "Please verify the knowledge base integrity.",
                "sources": [],
                "context_used": [],
                "security_events": self.security_guard.security_log
            }

        # STEP 2: AUGMENT (using only safe chunks)

        # STEP 3: GENERATE

        if not output_safe:
            print("\n" + "!" * 60)
            print("SECURITY WARNING - Suspicious content in LLM output:")
            for w in output_warnings:
                print(f"  >> {w}")
            print("!" * 60)

            answer = (
                "[SECURITY WARNING] The generated response contains "
                "potentially suspicious content:\n"
                + "\n".join(f"  - {w}" for w in output_warnings)
                + "\n\n--- Original Response (review with caution) ---\n"
                + answer
                + "\n--- End of flagged response ---\n"
                "\nPlease verify this information through official channels."
            )

        # Package response
        response = {
            "answer": answer,
            "sources": [
                {
                    "source": chunk['source'],
                    "page": chunk['page'],
                    "score": chunk['score']
                }
                for chunk in safe_chunks
            ] if show_sources else [],
            "context_used": safe_chunks if show_sources else [],
            "security_events": self.security_guard.security_log
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
    print("  RAG System - HARDENED VERSION")
    print("  (Security Defenses ENABLED)")
    print(f"  Using ChromaDB + {OLLAMA_MODEL} (Local Ollama)")
    print("=" * 60)
    print("\n  DEFENSES ACTIVE:")
    print("    - Prompt injection detection")
    print("    - Source allowlist verification")
    print("    - Relevance score thresholds")
    print("    - Output scanning for suspicious content\n")

    try:
        rag = HardenedRAGSystem(chroma_path="./chroma_poisoned_db",
                                collection_name="pdf_documents")

        stats = rag.get_statistics()
        print("Knowledge Base Statistics:")
        print(f"  Total Chunks: {stats.get('total_chunks', 0)}")
        print(f"  Database: {stats.get('database_path', 'N/A')}")
        print("\n  Source Documents:")
        for source, count in stats.get('sources', {}).items():
            marker = "[TRUSTED]" if source in SecurityGuard.TRUSTED_SOURCES else "[UNKNOWN]"
            print(f"    {marker} {source}: {count} chunks")

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
        print("Try the Same Questions — Watch Security Guards Activate:")
        print("=" * 60)
        print("  - How do I reset my password?")
        print("  - How do I get a refund?")
        print("  - What is the return policy?")
        print("=" * 60)

        print("\nAsk your question (or 'quit'/'report' to exit/see security log):")

        while True:
            question = input("\n> ").strip()

            if question.lower() in ['quit', 'exit', 'q']:
                # Show security report on exit
                report = rag.security_guard.get_security_report()
                print(report)
                print("\nGoodbye!")
                break

            if question.lower() == 'report':
                report = rag.security_guard.get_security_report()
                print(report)
                continue

            if not question:
                continue

            result = rag.query(question, max_context_chunks=5)

            print("\n" + "=" * 60)
            print("ANSWER:")
            print("=" * 60)
            print(result['answer'])

            if result['sources']:
                print("\n" + "-" * 60)
                print("SOURCES (verified safe):")
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
