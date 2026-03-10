# hardened_client.py  –  Lab 5: Defense in Depth
# Tests the hardened MCP server's security controls.

import asyncio
import httpx
from fastmcp import Client

AUTH_SERVER   = "http://127.0.0.1:9000/token"
MCP_ENDPOINT  = "http://127.0.0.1:8000/mcp/"
CALL_TIMEOUT  = 5.0  # Timeout for tool calls (FastMCP client can hang)


async def get_token() -> str:
    """Obtain a JWT from the authorization server."""
    async with httpx.AsyncClient() as h:
        r = await h.post(AUTH_SERVER, data={
            "username": "demo-client",
            "password": "demopass"
        })
        r.raise_for_status()
        return r.json()["access_token"]


async def main():
    token = await get_token()
    print("Token acquired from auth server.\n")

    print("=" * 50)
    print("Lab 5: Defense in Depth - Security Controls Demo")
    print("=" * 50)

    # Use a single Client connection for Scenarios 1, 2, and 5
    # This avoids hitting rate limits from multiple connection initializations
    try:
        async with Client(MCP_ENDPOINT, auth=token) as c:
            # ── Scenario 1: Normal tool call ──
            print("\n" + "=" * 50)
            print("=" * 50)
            tools = await c.list_tools()
            print(f"Available tools: {[t.name for t in tools]}")

            try:
            except asyncio.TimeoutError:
                print("add(3, 4) -> TIMEOUT")

            print("\n" + "=" * 50)
            print("Scenario 2: Customer Lookup (Output Sanitization)")
            print("=" * 50)
            try:
            except asyncio.TimeoutError:
                print("Customer lookup -> TIMEOUT")

            # ── Scenario 5: View audit log ──
            print("\n" + "=" * 50)
            print("Scenario 5: Audit Log (Before Rate Limit Test)")
            print("=" * 50)
            try:
                result = await asyncio.wait_for(
                    c.call_tool("get_audit_log", {"count": 10}),
                    timeout=CALL_TIMEOUT
                )
                print(f"Recent audit entries:\n{result}")
            except asyncio.TimeoutError:
                print("get_audit_log -> TIMEOUT")

    except httpx.HTTPStatusError as e:
        # FastMCP client bug: errors during cleanup crash on context exit
        if e.response.status_code == 429:
            print(f"\n⚠️  Rate limit hit. The server limits requests to prevent abuse.")
            print("This is expected behavior - the defense is working!")
        elif e.response.status_code != 403:
            raise
    except Exception as e:
        print(f"Error: {e}")

    # ── Scenario 3: Rate limiting test (raw HTTP) ──
            status = "OK" if r.status_code == 200 else f"BLOCKED ({r.status_code})"
            print(f"  Request {i+1}: {status}")

    print("\n" + "=" * 50)
    print("Scenario 4: Input Validation (dangerous input)")
    print("=" * 50)
    async with httpx.AsyncClient() as h:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        if r.status_code == 400:
            print(f"  Server says: {r.json().get('detail', '')}")

        print(f"  SQL injection attempt: status {r.status_code}")
        if r.status_code == 400:
            print(f"  Server says: {r.json().get('detail', '')}")


    print("\n" + "=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
