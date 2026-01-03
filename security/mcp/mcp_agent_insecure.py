from __future__ import annotations

import asyncio

from common.ollama_client import chat
from fastmcp import Client

SYSTEM = """You are an assistant that can use MCP tools.
If a tool can help, you may call it.

When you want to call a tool, respond with:
TOOL: <tool_name>
ARGS: <json>

Otherwise respond normally.
"""

def parse_tool_call(text: str):
    if "TOOL:" not in text or "ARGS:" not in text:
        return None
    try:
        tool = text.split("TOOL:",1)[1].splitlines()[0].strip()
        args_line = text.split("ARGS:",1)[1].strip()
        import json
        args = json.loads(args_line)
        return tool, args
    except Exception:
        return None

async def main() -> None:
    client = Client("http://127.0.0.1:8000/mcp")
    async with client:
        print("MCP Agent. Type 'exit' to quit.\n")
        while True:
            user = input("You: ").strip()
            if user.lower() in {"exit","quit"}:
                break

            messages = [{"role":"system","content": SYSTEM},
                        {"role":"user","content": user}]
            model_out = chat(messages, temperature=0.2, num_predict=220)
            tc = parse_tool_call(model_out)

            if not tc:
                print(f"\nAssistant: {model_out}\n")
                continue

            tool, args = tc
            try:
                result = await client.call_tool(tool, args)
                tool_text = result[0].text if result else ""
            except Exception as e:
                tool_text = f"Tool call failed: {e}"

            followup = chat(
                [{"role":"system","content": SYSTEM},
                 {"role":"user","content": f"User: {user}\nTool result: {tool_text}\nAnswer safely:"}],
                temperature=0.2,
                num_predict=220,
            )
            print(f"\nAssistant: {followup}\n")

if __name__ == "__main__":
    asyncio.run(main())
