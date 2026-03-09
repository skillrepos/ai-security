#!/usr/bin/env python3
"""
warmup.py – Pre-loads the granite4:3b model into Ollama so that subsequent
lab operations (simple_prompt_runner, cot_runner, rag_prompt_runner,
react_weather_agent, agent.py, mcp_client_agent.py) feel fast.
Run from the repo root:
    python scripts/warmup.py
What it does
------------
1. Checks that the Ollama server is reachable.
2. Calls /api/generate with a trivial prompt – this forces Ollama to load the
   model weights into memory (GPU/CPU) and cache them.
3. Makes a second call via /api/chat (the endpoint used by common.ollama_client
   and mcp_client_agent.py) so both codepaths are primed.
4. Makes a third call via langchain-ollama's ChatOllama (used by agent.py) so
   that library's connection pool is also warmed up.
5. Reports total elapsed time so you know when it's safe to start labs.
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
# ── Config (mirrors common/ollama_client.py defaults) ───────────────────────
MODEL   = os.getenv("OLLAMA_MODEL", "granite4:3b")
HOST    = os.getenv("OLLAMA_HOST",  "http://127.0.0.1:11434")
TIMEOUT = int(os.getenv("OLLAMA_WARMUP_TIMEOUT", "300"))   # seconds
AUTO_PULL = os.getenv("OLLAMA_WARMUP_AUTO_PULL", "1").lower() not in {"0", "false", "no"}
WARMUP_PROMPT  = "Reply with the single word: ready"
WARMUP_SYSTEM  = "You are a helpful assistant."
# ── Helpers ──────────────────────────────────────────────────────────────────
def _check_server() -> set[str]:
    """Verify the Ollama server is up and return known model tags."""
    try:
        r = requests.get(f"{HOST}/api/tags", timeout=10)
        r.raise_for_status()
    except Exception as exc:
        sys.exit(
            f"\n✗ Cannot reach Ollama at {HOST}.\n"
            f"  Make sure Ollama is running (e.g. `ollama serve` or ./scripts/startOllama.sh).\n"
            f"  Error: {exc}\n"
        )
    return {m.get("name", "") for m in r.json().get("models", [])}


def _pull_model_with_cli() -> bool:
    """Pull model via CLI for visible progress and keepalive output."""
    if not shutil.which("ollama"):
        return False

    print(f"  ↳ Running: ollama pull {MODEL}")
    try:
        # Keep stdout/stderr attached so progress is visible in post-attach logs.
        subprocess.run(["ollama", "pull", MODEL], check=True)
    except subprocess.CalledProcessError as exc:
        sys.exit(f"\n✗ Failed to pull model '{MODEL}' via CLI. Exit code: {exc.returncode}\n")
    return True


def _pull_model_with_api() -> None:
    """Fallback model pull through API when CLI isn't available."""
    print("  ↳ Falling back to Ollama API pull")
    try:
        with requests.post(
            f"{HOST}/api/pull",
            json={"name": MODEL, "stream": False},
            timeout=(10, 3600),
        ) as pull:
            pull.raise_for_status()
    except Exception as exc:
        sys.exit(f"\n✗ Failed to pull model '{MODEL}' via API. Error: {exc}\n")


def _ensure_model_available(tags: set[str]) -> None:
    """Pull the configured model on first run, if needed."""
    if any(MODEL in t for t in tags):
        return

    if not AUTO_PULL:
        sys.exit(
            f"\n✗ Model '{MODEL}' is not available locally and auto-pull is disabled.\n"
            "  Set OLLAMA_WARMUP_AUTO_PULL=1 or pull manually with: ollama pull "
            f"{MODEL}\n"
        )

    print(f"  ⚠  Model '{MODEL}' not found locally – pulling now (this may take a while)…")
    if not _pull_model_with_cli():
        _pull_model_with_api()
    print("  ✓  Pull complete.\n")
def _warmup_generate() -> float:
    """Warm up the /api/generate endpoint (used by common.ollama_client.generate)."""
    t0 = time.perf_counter()
    payload = {
        "model":  MODEL,
        "prompt": WARMUP_PROMPT,
        "options": {"temperature": 0.0, "num_predict": 5},
        "stream": False,
    }
    r = requests.post(f"{HOST}/api/generate", json=payload, timeout=TIMEOUT)
    r.raise_for_status()
    return time.perf_counter() - t0
def _warmup_chat() -> float:
    """Warm up the /api/chat endpoint (used by common.ollama_client.chat
    and mcp_client_agent.py's call_ollama)."""
    t0 = time.perf_counter()
    payload = {
        "model": MODEL,
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
def _warmup_langchain() -> float:
    """Warm up langchain-ollama's ChatOllama (used by agent.py)."""
    try:
        from langchain_ollama import ChatOllama
    except ImportError:
        print("  ⚠  langchain-ollama not installed – skipping ChatOllama warmup.")
        return 0.0
    t0 = time.perf_counter()
    llm = ChatOllama(model=MODEL, temperature=0.0)
    llm.invoke([{"role": "user", "content": WARMUP_PROMPT}])
    return time.perf_counter() - t0
# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    print(f"\n🔥  Warming up Ollama model '{MODEL}' at {HOST} ...\n")
    t_total = time.perf_counter()
    # 1. Server / model availability
    print("  [1/4] Checking server & model availability …", end=" ", flush=True)
    tags = _check_server()
    _ensure_model_available(tags)
    print("ok")
    # 2. /api/generate  (simple_prompt_runner.py, cot_runner.py, rag_prompt_runner.py)
    print("  [2/4] Priming /api/generate  (generate-based scripts) …", end=" ", flush=True)
    dt = _warmup_generate()
    print(f"done  ({dt:.1f}s)")
    # 3. /api/chat  (react_weather_agent.py, mcp_client_agent.py)
    print("  [3/4] Priming /api/chat      (chat-based scripts)     …", end=" ", flush=True)
    dt = _warmup_chat()
    print(f"done  ({dt:.1f}s)")
    # 4. ChatOllama  (agent.py)
    print("  [4/4] Priming ChatOllama     (agent.py)               …", end=" ", flush=True)
    dt = _warmup_langchain()
    print(f"done  ({dt:.1f}s)")
    elapsed = time.perf_counter() - t_total
    print(f"\n✅  Warmup complete in {elapsed:.1f}s. Model '{MODEL}' is hot - lab scripts will be fast!\n")
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("\n⚠ Warmup interrupted. Re-run scripts/post_attach_ollama.sh when ready.\n")
