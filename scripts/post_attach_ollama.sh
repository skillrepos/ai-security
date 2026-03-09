#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WARMUP_STAMP_FILE="${OLLAMA_WARMUP_STAMP_FILE:-/tmp/ollama-warmup.stamp}"
WARMUP_MAX_AGE_SEC="${OLLAMA_WARMUP_MAX_AGE_SEC:-21600}"

is_ollama_up() {
  curl -fsS --max-time 2 "http://127.0.0.1:11434/api/tags" >/dev/null 2>&1
}

start_ollama_if_needed() {
  if ! command -v ollama >/dev/null 2>&1; then
    echo "Ollama not found on PATH. Running installer script..."
    bash "$REPO_ROOT/scripts/startOllama.sh"
  fi

  if is_ollama_up; then
    echo "Ollama server already running."
    return
  fi

  echo "Starting Ollama server..."
  nohup ollama serve >/tmp/ollama-serve.log 2>&1 &

  for _ in {1..100}; do
    if is_ollama_up; then
      echo "Ollama server is ready."
      return
    fi
    sleep 0.2
  done

  echo "ERROR: Ollama server failed to start."
  echo "Tail of /tmp/ollama-serve.log:"
  tail -n 100 /tmp/ollama-serve.log || true
  exit 1
}

warmup_is_recent() {
  if [[ ! -f "$WARMUP_STAMP_FILE" ]]; then
    return 1
  fi

  local now stamp age
  now="$(date +%s)"
  stamp="$(date -r "$WARMUP_STAMP_FILE" +%s 2>/dev/null || echo 0)"
  age="$((now - stamp))"

  [[ "$age" -lt "$WARMUP_MAX_AGE_SEC" ]]
}

run_warmup_if_stale() {
  if warmup_is_recent; then
    echo "Warmup is recent. Skipping."
    return
  fi

  echo "Running Ollama warmup..."
  local py_cmd="python3"
  if [[ -x "$REPO_ROOT/py_env/bin/python" ]]; then
    py_cmd="$REPO_ROOT/py_env/bin/python"
  fi

  if ! (cd "$REPO_ROOT" && "$py_cmd" scripts/warmup.py); then
    echo "WARNING: Warmup did not complete successfully."
    echo "You can retry later with: bash scripts/post_attach_ollama.sh"
    return
  fi

  touch "$WARMUP_STAMP_FILE"
  echo "Warmup complete; updated $WARMUP_STAMP_FILE"
}

start_ollama_if_needed
run_warmup_if_stale
