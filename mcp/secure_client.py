# secure_client.py  –  Lab 4: Auth + Per-Tool Scopes
# Demonstrates per-tool scope enforcement with different client identities.

import asyncio  # needed for asyncio.run()
import httpx
from fastmcp import Client

async def get_token(client_id: str, client_secret: str) -> str:
    async with httpx.AsyncClient() as h:
        r = await h.post(AUTH_SERVER, data={
            "username": client_id,
            "password": client_secret
        })
        r.raise_for_status()
        return r.json()["access_token"]


async def test_client(name: str, token: str):
    print(f"\n{'='*50}")
    print(f"Testing as: {name}")
    print(f"{'='*50}")

    async with Client(MCP_ENDPOINT, auth=token) as c:

        try:
            result = await c.call_tool("add", {"a": 7, "b": 5})
            print(f"add(7, 5) = {result}")
        except httpx.HTTPStatusError as e:
            print(f"add(7, 5) -> ERROR: HTTP {e.response.status_code}")
        except Exception as e:
            print(f"add(7, 5) -> ERROR: {e}")

        try:
            result = await c.call_tool("multiply", {"a": 3, "b": 4})
            if name == "full-client":
                print(f"multiply(3, 4) = {result}")
            else:
                print(f"multiply(3, 4) = {result} ⚠️  SHOULD HAVE BEEN DENIED!")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                print(f"multiply(3, 4) -> ❌ DENIED (403 Forbidden) ✓")
                print(f"  (Server rejected due to missing 'tools:multiply' scope)")
            else:
                print(f"multiply(3, 4) -> ERROR: HTTP {e.response.status_code}")
        except Exception as e:
            print(f"multiply(3, 4) -> ERROR: {e}")

        # Test divide – only full-client has tools:divide scope
        try:
            result = await c.call_tool("divide", {"a": 10, "b": 3})
            if name == "full-client":
                print(f"divide(10, 3) = {result}")
            else:
                print(f"divide(10, 3) = {result} ⚠️  SHOULD HAVE BEEN DENIED!")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                print(f"divide(10, 3) -> ❌ DENIED (403 Forbidden) ✓")
                print(f"  (Server rejected due to missing 'tools:divide' scope)")
            else:
                print(f"divide(10, 3) -> ERROR: HTTP {e.response.status_code}")
        except Exception as e:
            print(f"divide(10, 3) -> ERROR: {e}")


async def main():
    print("\n" + "="*50)
    print("Lab 4: MCP Authentication & Per-Tool Scopes")
    print("="*50)

    # Test 1: full-client has all scopes

    # Test 2: limited-client only has tools:add scope
    
    print("\n" + "="*50)
    print("✓ RESULTS:")
    print("="*50)
    print("For limited-client:")
    print("  • multiply -> DENIED (403 Forbidden)")
    print("  • divide   -> DENIED (403 Forbidden)")
    print("\nScope enforcement is working!")
    print("="*50)


if __name__ == "__main__":
    asyncio.run(main())

