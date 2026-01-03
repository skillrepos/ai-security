from __future__ import annotations

import asyncio

from fastmcp import Client

async def main() -> None:
    client = Client("http://127.0.0.1:8000/mcp")
    async with client:
        tools = await client.list_tools()
        print("Available tools:")
        for t in tools:
            print(f"  - {t.name}: {t.description}")

if __name__ == "__main__":
    asyncio.run(main())
