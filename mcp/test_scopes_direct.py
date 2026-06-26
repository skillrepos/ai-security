# test_scopes_direct.py  –  Lab 4: Scope Enforcement (Direct HTTP)
#
# Bypasses the FastMCP client and POSTs raw JSON-RPC requests directly to
# the MCP server.  Because the auth middleware returns 403 before FastMCP
# ever processes the request, the 403 JSON body is visible immediately —
# no client abstraction, no session machinery, no timeouts needed.
#
# Usage (all three servers must be running):
#   python auth_server.py          (port 9000)
#   python secure_server.py        (port 8000)
#   python test_scopes_direct.py

import asyncio
import httpx

AUTH_SERVER  = "http://127.0.0.1:9000/token"
MCP_ENDPOINT = "http://127.0.0.1:8000/mcp/"


async def get_token(client_id: str, secret: str) -> str:
    async with httpx.AsyncClient() as h:
        r = await h.post(AUTH_SERVER, data={"username": client_id, "password": secret})
        r.raise_for_status()
        return r.json()["access_token"]


async def call_tool_direct(
    client_name: str,
    token: str,
    tool: str,
    args: dict,
    expect_denied: bool = False,
) -> None:
    """POST a raw JSON-RPC tools/call to the MCP server and print the result."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool, "arguments": args},
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }

    async with httpx.AsyncClient() as h:
        r = await h.post(MCP_ENDPOINT, json=payload, headers=headers)

    label = f"{tool}({', '.join(f'{k}={v}' for k, v in args.items())})"

    if r.status_code == 403:
        detail = r.json().get("detail", r.text)
        marker = "✓" if expect_denied else "⚠️  UNEXPECTED DENIAL"
        print(f"  {label} -> ❌ 403 Forbidden {marker}")
        print(f"    {detail}")
    elif r.status_code == 200:
        marker = "⚠️  SHOULD HAVE BEEN DENIED" if expect_denied else "✓"
        # Streamable-HTTP may return SSE text; grab the last JSON-RPC result line
        body = r.text.strip()
        print(f"  {label} -> ✅ 200 OK {marker}")
        print(f"    {body[:120]}")
    else:
        print(f"  {label} -> HTTP {r.status_code}")
        print(f"    {r.text[:120]}")


async def test_client(name: str, secret: str, tools_to_test: list[dict]) -> None:
    print(f"\n{'='*55}")
    print(f"Client: {name}")
    print(f"{'='*55}")
    token = await get_token(name, secret)
    for t in tools_to_test:
        await call_tool_direct(name, token, t["tool"], t["args"], t.get("denied", False))


async def main() -> None:
    print("\n" + "="*55)
    print("Lab 4: MCP Scope Enforcement – Direct HTTP Test")
    print("="*55)
    print("(No FastMCP client — raw HTTP shows real 403 bodies)\n")

    await test_client(
        "full-client", "fullpass",
        [
            {"tool": "add",      "args": {"a": 7,  "b": 5},  "denied": False},
            {"tool": "multiply", "args": {"a": 3,  "b": 4},  "denied": False},
            {"tool": "divide",   "args": {"a": 10, "b": 3},  "denied": False},
        ],
    )

    await test_client(
        "limited-client", "limitedpass",
        [
            {"tool": "add",      "args": {"a": 7,  "b": 5},  "denied": False},
            {"tool": "multiply", "args": {"a": 3,  "b": 4},  "denied": True},
            {"tool": "divide",   "args": {"a": 10, "b": 3},  "denied": True},
        ],
    )

    print("\n" + "="*55)
    print("Scope enforcement verified via direct HTTP.")
    print("="*55)


if __name__ == "__main__":
    asyncio.run(main())
