from __future__ import annotations

import re
from typing import Dict, Any, Tuple

from common.ollama_client import chat

SYSTEM = """You are a tool-using assistant.

Use this format:

Thought: ...
Action: tool_name(location="...")
Observation: tool output
Final: final answer

Rules:
- Keep tool calls to a minimum.
- Stop when you have enough information.
"""

MAX_STEPS = 6
MAX_TOOL_CALLS = 2

def tool_weather(location: str) -> str:
    return f"Weather for {location}: 7C, light rain (stub)."

TOOLS = {"weather": tool_weather}

def parse_action(text: str) -> Tuple[str, Dict[str, Any]] | None:
    m = re.search(r"Action:\s*(\w+)\((.*)\)", text)
    if not m:
        return None
    name = m.group(1)
    args_str = m.group(2).strip()
    args: Dict[str, Any] = {}
    if args_str:
        m2 = re.search(r"location\s*=\s*['\"]([^'\"]+)['\"]", args_str)
        if m2:
            args["location"] = m2.group(1)
    return name, args

def main() -> None:
    print("ReAct Agent (SECURED with budgets). Type 'exit' to quit.\n")
    while True:
        user = input("You: ").strip()
        if user.lower() in {"exit","quit"}:
            break

        transcript = [{"role":"system","content": SYSTEM}]
        transcript.append({"role":"user","content": user})

        tool_calls = 0
        for step in range(1, MAX_STEPS + 1):
            out = chat(transcript, temperature=0.2, num_predict=300)
            transcript.append({"role":"assistant","content": out})
            print(out)

            if "Final:" in out:
                break

            parsed = parse_action(out)
            if not parsed:
                transcript.append({"role":"user","content":"Observation: (no tool call parsed). Provide Final if possible."})
                continue

            if tool_calls >= MAX_TOOL_CALLS:
                transcript.append({"role":"user","content":"Observation: Tool-call budget exceeded. Provide Final using what you have."})
                continue

            tool_name, args = parsed
            tool = TOOLS.get(tool_name)
            if not tool:
                obs = f"Observation: tool '{tool_name}' not available."
            else:
                tool_calls += 1
                loc = args.get("location","your location")
                obs = f"Observation: {tool(loc)}"

            transcript.append({"role":"user","content": obs})

        else:
            print("\nFinal: I’m stopping because the step budget was reached.\n")

        print()

if __name__ == "__main__":
    main()
