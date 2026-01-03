from __future__ import annotations

import re
from typing import Dict, Any

from common.ollama_client import chat


SYSTEM = """You are a helpful assistant. Answer the user's question."""
# Intentionally insecure: no mention of secrets policy, no refusal behavior, no input checks.


def get_weather_stub(location: str) -> str:
    # Stub tool; in real life you'd call a weather API.
    return f"Weather for {location}: 7C, light rain (stub)."


def main() -> None:
    print("Weather Agent (INSECURE). Type 'exit' to quit.\n")
    while True:
        user = input("You: ").strip()
        if user.lower() in {"exit", "quit"}:
            break

        # naive location extraction
        m = re.search(r"in ([A-Za-z\s]+)", user)
        location = (m.group(1).strip() if m else "your location")

        tool_result = get_weather_stub(location)

        messages = [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": f"User question: {user}\nTool result: {tool_result}\nAnswer:"},
        ]
        answer = chat(messages)
        print(f"\nAssistant: {answer}\n")


if __name__ == "__main__":
    main()
