from __future__ import annotations

import json
from pathlib import Path

from common.ollama_client import generate

PROMPT_PATH = Path(__file__).parent / "routing_prompt_insecure.txt"

def main() -> None:
    template = PROMPT_PATH.read_text(encoding="utf-8")
    print("Router (INSECURE). Type 'exit' to quit.\n")
    while True:
        user = input("User: ").strip()
        if user.lower() in {"exit","quit"}:
            break
        prompt = template.replace("{{USER_TEXT}}", user)
        out = generate(prompt, temperature=0.2, num_predict=120)
        print(f"\nModel output:\n{out}\n")

if __name__ == "__main__":
    main()
