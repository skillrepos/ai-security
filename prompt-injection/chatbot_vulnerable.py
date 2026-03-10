#!/usr/bin/env python3
"""
Customer Service Chatbot - VULNERABLE VERSION (Ollama / llama3.2:1b)
────────────────────────────────────────────────────────────────────
A simple LLM-powered customer service chatbot with NO security controls.
Demonstrates how prompt injection attacks can override the system prompt.

This chatbot has three critical vulnerabilities:
  1. Weak system prompt — no security rules or boundaries
  2. No input validation — user messages go directly to the LLM
  3. No output validation — LLM responses are returned as-is

Used in Lab 1: Prompt Injection & Guardrail Defense
"""

import os
import requests
import json

OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:1b")

# ═══════════════════════════════════════════════════════════════════
# VULNERABILITY: Weak system prompt with no security guidance
# ═══════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = "You are a helpful customer service assistant for OmniTech Solutions."


def chat(user_message: str, conversation_history: list) -> str:
    """Send a message to the LLM and return its response.

    VULNERABLE: No input validation, no output validation.
    Whatever the user types goes straight to the LLM, and whatever
    the LLM generates comes straight back.
    """
    conversation_history.append({"role": "user", "content": user_message})

    # Build the full prompt from conversation history
    full_prompt = f"System: {SYSTEM_PROMPT}\n\n"
    for msg in conversation_history:
        if msg["role"] == "user":
            full_prompt += f"User: {msg['content']}\n"
        else:
            full_prompt += f"Assistant: {msg['content']}\n"
    full_prompt += "Assistant:"

    try:
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "num_predict": 300,
            },
        }
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=120)

        if response.status_code == 200:
            answer = response.json().get("response", "").strip()
            conversation_history.append({"role": "assistant", "content": answer})
            return answer
        else:
            return f"Error: Ollama returned status {response.status_code}"

    except requests.exceptions.ConnectionError:
        return "Error: Could not connect to Ollama. Make sure Ollama is running: ollama serve"
    except requests.exceptions.Timeout:
        return "Error: Request timed out."
    except Exception as e:
        return f"Error: {e}"


def main():
    print("=" * 60)
    print("  OmniTech Customer Service Chatbot")
    print("  VULNERABLE VERSION — No Security Controls")
    print(f"  Model: {OLLAMA_MODEL} (via Ollama)")
    print("=" * 60)
    print()
    print("  WARNING: This chatbot has NO defenses against")
    print("  prompt injection attacks. Try to break it!")
    print()
    print("  Type 'quit' to exit.")
    print("=" * 60)

    # Verify Ollama is running
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=3)
        if resp.status_code == 200:
            print(f"\n[OK] Ollama is running. Model: {OLLAMA_MODEL}")
        else:
            print("\n[WARNING] Ollama responded but may have issues.")
    except Exception:
        print("\n[ERROR] Cannot connect to Ollama. Run: ollama serve")
        print(f"        Then ensure model is pulled: ollama pull {OLLAMA_MODEL}")
        return

    conversation_history = []

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if user_input.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        if not user_input:
            continue

        response = chat(user_input, conversation_history)
        print(f"\nAssistant: {response}")


if __name__ == "__main__":
    main()
