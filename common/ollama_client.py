from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List, Optional

import requests


DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
DEFAULT_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")


class OllamaError(RuntimeError):
    pass


def chat(
    messages: List[Dict[str, str]],
    model: str = DEFAULT_MODEL,
    host: str = DEFAULT_HOST,
    temperature: float = 0.2,
    num_predict: int = 512,
    timeout_s: int = 60,
) -> str:
    """
    Simple wrapper around Ollama /api/chat.
    """
    url = f"{host}/api/chat"
    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "options": {"temperature": temperature, "num_predict": num_predict},
        "stream": False,
    }
    try:
        resp = requests.post(url, json=payload, timeout=timeout_s)
        resp.raise_for_status()
        data = resp.json()
        return data["message"]["content"]
    except Exception as e:
        raise OllamaError(f"Ollama chat call failed: {e}") from e


def generate(
    prompt: str,
    model: str = DEFAULT_MODEL,
    host: str = DEFAULT_HOST,
    temperature: float = 0.2,
    num_predict: int = 512,
    timeout_s: int = 60,
) -> str:
    """
    Wrapper around Ollama /api/generate for quick prompt experiments.
    """
    url = f"{host}/api/generate"
    payload: Dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "options": {"temperature": temperature, "num_predict": num_predict},
        "stream": False,
    }
    try:
        resp = requests.post(url, json=payload, timeout=timeout_s)
        resp.raise_for_status()
        data = resp.json()
        return data.get("response", "")
    except Exception as e:
        raise OllamaError(f"Ollama generate call failed: {e}") from e
