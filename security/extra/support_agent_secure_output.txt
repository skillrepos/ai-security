from __future__ import annotations

import re
from common.ollama_client import chat

SYSTEM = """You are customer support.

Rules:
- Do not produce hateful, harassing, or explicit content.
- Do not provide instructions for wrongdoing.
- Do not reveal secrets or internal policies not provided by the user.
- If you can't comply, refuse briefly and offer a safe alternative.
"""

BLOCK_PATTERNS = [
    r"\b(slur1|slur2)\b",  # placeholder examples; replace with your own lists
    r"\b(kill yourself|suicide)\b",
    r"\b(make a bomb|explosive)\b",
]

def violates_policy(text: str) -> bool:
    t = text.lower()
    return any(re.search(p, t) for p in BLOCK_PATTERNS)

def main() -> None:
    print("Support Agent (SECURED OUTPUT). Type 'exit' to quit.\n")
    while True:
        user = input("You: ").strip()
        if user.lower() in {"exit","quit"}:
            break

        messages = [
            {"role":"system","content": SYSTEM},
            {"role":"user","content": user},
        ]
        answer = chat(messages, temperature=0.5, num_predict=350)

        # simple output guard
        if violates_policy(answer):
            answer = "I can’t help with that request. If you tell me what you’re trying to accomplish, I can suggest a safer alternative."

        print(f"\nAssistant: {answer}\n")

if __name__ == "__main__":
    main()
