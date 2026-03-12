#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WARMUP_STAMP_FILE="${OLLAMA_WARMUP_STAMP_FILE:-/tmp/ollama-warmup.stamp}"
WARMUP_MAX_AGE_SEC="${OLLAMA_WARMUP_MAX_AGE_SEC:-21600}"
WARMUP_LOG_FILE="${OLLAMA_WARMUP_LOG_FILE:-/tmp/ollama-warmup.log}"
WARMUP_PID_FILE="${OLLAMA_WARMUP_PID_FILE:-/tmp/ollama-warmup.pid}"

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

warmup_is_running() {
  if [[ ! -f "$WARMUP_PID_FILE" ]]; then
    return 1
  fi

  local pid
  pid="$(cat "$WARMUP_PID_FILE" 2>/dev/null || true)"
  if [[ -z "$pid" ]]; then
    rm -f "$WARMUP_PID_FILE"
    return 1
  fi

  if kill -0 "$pid" >/dev/null 2>&1; then
    return 0
  fi

  rm -f "$WARMUP_PID_FILE"
  return 1
}

run_warmup_if_stale() {
  if warmup_is_recent; then
    echo "Warmup is recent. Skipping."
    return
  fi

  if warmup_is_running; then
    local active_pid
    active_pid="$(cat "$WARMUP_PID_FILE")"
    echo "Warmup already in progress (pid $active_pid)."
    echo "Follow progress with: tail -f $WARMUP_LOG_FILE"
    return
  fi

  echo "Starting Ollama warmup in background..."
  local py_cmd="python3"
  if [[ -x "$REPO_ROOT/py_env/bin/python" ]]; then
    py_cmd="$REPO_ROOT/py_env/bin/python"
  fi

  {
    printf "\n[%s] Starting warmup...\n" "$(date -Is)"
    cd "$REPO_ROOT"
    OLLAMA_WARMUP_STAMP_FILE="$WARMUP_STAMP_FILE" "$py_cmd" scripts/warmup.py
  } >>"$WARMUP_LOG_FILE" 2>&1 &

  local warmup_pid=$!
  echo "$warmup_pid" >"$WARMUP_PID_FILE"
  disown "$warmup_pid" 2>/dev/null || true

  echo "Warmup started (pid $warmup_pid)."
  echo "Logs: $WARMUP_LOG_FILE"
  echo "A success run will update: $WARMUP_STAMP_FILE"
}

start_ollama_if_needed
run_warmup_if_stale
