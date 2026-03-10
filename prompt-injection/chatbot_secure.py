#!/usr/bin/env python3
"""
Customer Service Chatbot - SECURE VERSION (Ollama / llama3.2:1b)
────────────────────────────────────────────────────────────────────
A security-hardened version of the customer service chatbot with
three defense layers:
  1. Input validation — regex-based injection detection
  2. Hardened system prompt — explicit security rules
  3. Output validation — response scanning for signs of compromise

Used in Lab 1: Prompt Injection & Guardrail Defense

INSTRUCTIONS: Use 'code -d ../extra/chatbot_secure_complete.txt chatbot_secure.py'
to open a diff view and merge the security code from the complete version.
"""

import os
import re
import requests
import json

OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:1b")

# ═══════════════════════════════════════════════════════════════════
# LAYER 1: Input Validation
# TODO: Add injection detection patterns and validate_input() function
# ═══════════════════════════════════════════════════════════════════

# Merge the INJECTION_PATTERNS list and validate_input() function
# from the complete version


# ═══════════════════════════════════════════════════════════════════
# LAYER 2: Hardened System Prompt
# TODO: Replace this weak prompt with the hardened version
# ═══════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = "You are a helpful customer service assistant for OmniTech Solutions."


# ═══════════════════════════════════════════════════════════════════
# LAYER 3: Output Validation
# TODO: Add validate_output() function
# ═══════════════════════════════════════════════════════════════════

# Merge the validate_output() function from the complete version


def chat(user_message: str, conversation_history: list) -> str:
    """Send a message to the LLM and return its response.

    TODO: Add input validation before sending to LLM
    TODO: Add output validation before returning response
    """
    # TODO: Add input validation here (call validate_input)

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
            # TODO: Add output validation here (call validate_output)
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
    print("  SECURE VERSION — Defense in Depth")
    print(f"  Model: {OLLAMA_MODEL} (via Ollama)")
    print("=" * 60)
    print()
    print("  This chatbot has three security layers:")
    print("    1. Input validation (injection detection)")
    print("    2. Hardened system prompt")
    print("    3. Output validation (response scanning)")
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
