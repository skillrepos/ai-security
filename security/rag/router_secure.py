from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, Any

from common.ollama_client import generate

PROMPT_PATH = Path(__file__).parent / "routing_prompt_canonical.txt"

ALLOWED_INTENTS = {"question","support","lookup","howto","unknown"}

def canonicalize(user_text: str) -> Dict[str, Any]:
    # Tiny, intentionally simple canonicalizer:
    t = user_text.strip()
    intent = "question"
    if re.search(r"\b(return|policy|refund)\b", t, re.I):
        intent = "support"
    elif re.search(r"\b(weather|forecast)\b", t, re.I):
        intent = "lookup"
    if intent not in ALLOWED_INTENTS:
        intent = "unknown"
    return {"intent": intent, "text": t[:500]}

def main() -> None:
    template = PROMPT_PATH.read_text(encoding="utf-8")
    print("Router (SECURE canonical query). Type 'exit' to quit.\n")
    while True:
        user = input("User: ").strip()
        if user.lower() in {"exit","quit"}:
            break

        cq = canonicalize(user)
        prompt = template.replace("{{CANONICAL_QUERY_JSON}}", json.dumps(cq, indent=2))

        out = generate(prompt, temperature=0.2, num_predict=160)
        print(f"\nCanonical query:\n{json.dumps(cq, indent=2)}\n")
        print(f"Model output:\n{out}\n")

if __name__ == "__main__":
    main()
