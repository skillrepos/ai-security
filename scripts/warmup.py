#!/usr/bin/env python3
"""
warmup.py – Pre-loads BOTH Ollama models (qwen2.5:3b and llama3.2:1b) and
ChromaDB's default embedding model so that all lab operations feel fast.

Run from the repo root:
    python scripts/warmup.py

What it does
------------
1. Checks that the Ollama server is reachable; starts it automatically if not.
2. Pulls any missing models (qwen2.5:3b for RAG labs, llama3.2:1b for agent labs).
3. Warms up /api/generate for both models (used by RAG scripts via requests).
4. Warms up /api/chat for both models (used by mcp_client_agent, etc.).
5. Warms up langchain-ollama's ChatOllama for both models (used by
   supervisor_budget_agent.py and agent.py).
6. Warms up smolagents' LiteLLMModel for llama3.2:1b (used by enterprise agents).
7. Warms up ChromaDB's default embedding model (all-MiniLM-L6-v2 via onnxruntime)
   so the first RAG query doesn't stall on model download/load.
8. Reports total elapsed time so you know when it's safe to start labs.

Models warmed up
----------------
- qwen2.5:3b  : RAG labs (rag_vulnerable.py, rag_hardened.py, rag_code.py),
                  supervisor_budget_agent.py
- llama3.2:1b  : Agent labs (enterprise_agent_vulnerable.py,
                  enterprise_agent_secure.py)
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

# ── Resolve imports from the repo root ──────────────────────────────────────
ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))
import requests

# ── Config ──────────────────────────────────────────────────────────────────
HOST    = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
TIMEOUT = int(os.getenv("OLLAMA_WARMUP_TIMEOUT", "300"))   # seconds
AUTO_PULL = os.getenv("OLLAMA_WARMUP_AUTO_PULL", "1").lower() not in {"0", "false", "no"}

# Models used across the project
MODELS = [
    os.getenv("OLLAMA_MODEL", "qwen2.5:3b"),   # RAG + enterprise agent labs
    "llama3.2:1b",                               # Supervisor budget agent lab
]
# Deduplicate in case env var matches one of the above
MODELS = list(dict.fromkeys(MODELS))

WARMUP_PROMPT = "Reply with the single word: ready"
WARMUP_SYSTEM = "You are a helpful assistant."


# ── Helpers ─────────────────────────────────────────────────────────────────

def _is_server_up() -> bool:
    """Return True if the Ollama API is reachable."""
    try:
        r = requests.get(f"{HOST}/api/tags", timeout=5)
        r.raise_for_status()
        return True
    except Exception:
        return False


def _start_ollama_server() -> None:
    """Attempt to start the Ollama server in the background."""
    # If ollama binary isn't installed, try the installer script first
    if not shutil.which("ollama"):
        installer = ROOT / "scripts" / "startOllama.sh"
        if installer.exists():
            print("  Ollama not found on PATH. Running installer …")
            try:
                subprocess.run(["bash", str(installer)], check=True)
                if _is_server_up():
                    return  # startOllama.sh leaves the server running
            except subprocess.CalledProcessError:
                pass  # Fall through to the error below

        if not shutil.which("ollama"):
            sys.exit(
                "\n✗ Ollama is not installed and could not be installed automatically.\n"
                "  Install manually: curl -fsSL https://ollama.com/install.sh | sh\n"
            )

    # Binary exists but server isn't up — start it
    print("  Starting Ollama server …")
    subprocess.Popen(
        ["ollama", "serve"],
        stdout=open("/tmp/ollama-serve.log", "a"),
        stderr=subprocess.STDOUT,
    )

    # Wait up to 20 seconds for the server to become reachable
    for _ in range(100):
        if _is_server_up():
            return
        time.sleep(0.2)

    sys.exit(
        "\n✗ Ollama server failed to start within 20 s.\n"
        "  Check /tmp/ollama-serve.log for details.\n"
    )


def _ensure_server() -> set[str]:
    """Make sure Ollama is running (start it if needed) and return model tags."""
    if not _is_server_up():
        _start_ollama_server()

    r = requests.get(f"{HOST}/api/tags", timeout=10)
    r.raise_for_status()
    return {m.get("name", "") for m in r.json().get("models", [])}


def _pull_model(model: str, tags: set[str]) -> None:
    """Pull a model if it is not already available locally."""
    if any(model in t for t in tags):
        return

    if not AUTO_PULL:
        print(f"  ⚠  Model '{model}' not found locally and auto-pull is disabled. Skipping.")
        return

    print(f"  ⚠  Model '{model}' not found locally – pulling now …")

    # Prefer CLI for visible progress
    if shutil.which("ollama"):
        try:
            subprocess.run(["ollama", "pull", model], check=True)
            print(f"  ✓  Pull complete: {model}")
            return
        except subprocess.CalledProcessError:
            print(f"  ⚠  CLI pull failed for '{model}', trying API …")

    # Fallback to API
    try:
        with requests.post(
            f"{HOST}/api/pull",
            json={"name": model, "stream": False},
            timeout=(10, 3600),
        ) as pull:
            pull.raise_for_status()
        print(f"  ✓  Pull complete: {model}")
    except Exception as exc:
        print(f"  ✗  Failed to pull '{model}': {exc}")


def _warmup_generate(model: str) -> float:
    """Warm up /api/generate for a model (used by RAG scripts via requests)."""
    t0 = time.perf_counter()
    payload = {
        "model":  model,
        "prompt": WARMUP_PROMPT,
        "options": {"temperature": 0.0, "num_predict": 5},
        "stream": False,
    }
    r = requests.post(f"{HOST}/api/generate", json=payload, timeout=TIMEOUT)
    r.raise_for_status()
    return time.perf_counter() - t0


def _warmup_chat(model: str) -> float:
    """Warm up /api/chat for a model (used by mcp_client_agent, etc.)."""
    t0 = time.perf_counter()
    payload = {
        "model": model,
        "messages": [
            {"role": "system",  "content": WARMUP_SYSTEM},
            {"role": "user",    "content": WARMUP_PROMPT},
        ],
        "options": {"temperature": 0.0, "num_predict": 5},
        "stream": False,
    }
    r = requests.post(f"{HOST}/api/chat", json=payload, timeout=TIMEOUT)
    r.raise_for_status()
    return time.perf_counter() - t0


def _warmup_langchain(model: str) -> float:
    """Warm up langchain-ollama ChatOllama (used by supervisor_budget_agent, agent.py)."""
    try:
        from langchain_ollama import ChatOllama
    except ImportError:
        print("  ⚠  langchain-ollama not installed – skipping ChatOllama warmup.")
        return 0.0
    t0 = time.perf_counter()
    llm = ChatOllama(model=model, temperature=0.0)
    llm.invoke([{"role": "user", "content": WARMUP_PROMPT}])
    return time.perf_counter() - t0


def _warmup_litellm(model: str) -> float:
    """Warm up smolagents LiteLLMModel (used by enterprise agent scripts)."""
    try:
        from smolagents import LiteLLMModel
        from smolagents.models import ChatMessage
    except ImportError:
        print("  ⚠  smolagents not installed – skipping LiteLLMModel warmup.")
        return 0.0
    t0 = time.perf_counter()
    try:
        llm = LiteLLMModel(
            model_id=f"ollama/{model}",
            api_base="http://localhost:11434",
        )
        msg = ChatMessage(role="user", content=[{"type": "text", "text": WARMUP_PROMPT}])
        llm([msg])
    except Exception as exc:
        print(f"  ⚠  LiteLLMModel warmup failed: {exc}")
        return time.perf_counter() - t0
    return time.perf_counter() - t0


def _warmup_chromadb_embeddings() -> float:
    """Warm up ChromaDB's default embedding model (all-MiniLM-L6-v2 via onnxruntime).

    The first call to collection.add() or collection.query() downloads and loads
    the embedding model. Doing it here avoids a cold-start delay in the labs.
    """
    try:
        import chromadb
    except ImportError:
        print("  ⚠  chromadb not installed – skipping embedding warmup.")
        return 0.0
    t0 = time.perf_counter()
    try:
        # Use an ephemeral (in-memory) client so we don't leave files behind
        client = chromadb.Client()
        coll = client.get_or_create_collection("warmup-temp")
        coll.add(
            ids=["warmup_1"],
            documents=["This is a warmup document to pre-load the embedding model."],
        )
        # Also prime the query path
        coll.query(query_texts=["warmup"], n_results=1)
        # Clean up
        client.delete_collection("warmup-temp")
    except Exception as exc:
        print(f"  ⚠  ChromaDB embedding warmup failed: {exc}")
    return time.perf_counter() - t0


# ── Main ────────────────────────────────────────────────────────────────────

def main() -> None:
    model_list = ", ".join(MODELS)
    print(f"\n🔥  Warming up Ollama models [{model_list}] at {HOST} …\n")
    t_total = time.perf_counter()

    # ── Step 1: Server & model availability ─────────────────────────────
    step = 0
    total_steps = 2 + (4 * len(MODELS))  # chromadb + server + 4 per model

    step += 1
    print(f"  [{step}/{total_steps}] Ensuring Ollama is running & pulling models …", flush=True)
    tags = _ensure_server()
    for model in MODELS:
        _pull_model(model, tags)
    print(f"  [{step}/{total_steps}] ok")

    # ── Step 2: Warm up each model across all interaction patterns ──────
    for model in MODELS:
        # /api/generate
        step += 1
        print(f"  [{step}/{total_steps}] Priming /api/generate  ({model}) …", end=" ", flush=True)
        dt = _warmup_generate(model)
        print(f"done  ({dt:.1f}s)")

        # /api/chat
        step += 1
        print(f"  [{step}/{total_steps}] Priming /api/chat      ({model}) …", end=" ", flush=True)
        dt = _warmup_chat(model)
        print(f"done  ({dt:.1f}s)")

        # ChatOllama (langchain)
        step += 1
        print(f"  [{step}/{total_steps}] Priming ChatOllama     ({model}) …", end=" ", flush=True)
        dt = _warmup_langchain(model)
        print(f"done  ({dt:.1f}s)")

        # LiteLLMModel (smolagents)
        step += 1
        print(f"  [{step}/{total_steps}] Priming LiteLLMModel   ({model}) …", end=" ", flush=True)
        dt = _warmup_litellm(model)
        print(f"done  ({dt:.1f}s)")

    # ── Step 3: ChromaDB default embedding model ────────────────────────
    step += 1
    print(f"  [{step}/{total_steps}] Priming ChromaDB embeddings (all-MiniLM-L6-v2) …", end=" ", flush=True)
    dt = _warmup_chromadb_embeddings()
    print(f"done  ({dt:.1f}s)")

    elapsed = time.perf_counter() - t_total
    print(f"\n✅  Warmup complete in {elapsed:.1f}s. Models [{model_list}] are hot!\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("\n⚠ Warmup interrupted. Re-run scripts/post_attach_ollama.sh when ready.\n")
