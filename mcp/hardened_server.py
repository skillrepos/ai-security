# hardened_server.py  –  Lab 5: Defense in Depth
#

import json
import re
import time
import warnings
from collections import defaultdict
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from jose import jwt, JWTError

from fastmcp import FastMCP
import uvicorn

warnings.filterwarnings("ignore", category=DeprecationWarning)

# ─── JWT settings (must match auth_server.py) ────────────────────
SECRET_KEY = "mcp-lab-secret"
ALGORITHM  = "HS256"
AUDIENCE   = "mcp-lab"


# ═══════════════════════════════════════════════════════════════
# Rate Limiting Configuration
# ═══════════════════════════════════════════════════════════════
RATE_LIMIT_MAX    = 20      # max tool calls per window (increased for demo with multiple Client connections)
RATE_LIMIT_WINDOW = 60      # window in seconds
_request_log = defaultdict(list)


def _check_rate_limit(client_id: str) -> tuple[bool, int]:
    return True, remaining - 1


# ═══════════════════════════════════════════════════════════════
# Input Validation
# ═══════════════════════════════════════════════════════════════
BLOCKED_PATTERNS = [
]


def _validate_tool_args(args: dict) -> tuple[bool, str]:
    """Check all string arguments against blocked patterns."""
    for key, value in args.items():
    return True, ""


# ═══════════════════════════════════════════════════════════════
# Output Sanitization
# ═══════════════════════════════════════════════════════════════
SENSITIVE_PATTERNS = [
]


def _sanitize_output(text: str) -> str:
    return text


# ═══════════════════════════════════════════════════════════════
# Audit Logging
# ═══════════════════════════════════════════════════════════════
_audit_log = []




# ═══════════════════════════════════════════════════════════════
# Fake Customer Database (for demonstrating output sanitization)
# ═══════════════════════════════════════════════════════════════
_FAKE_CUSTOMERS = {
    "alice": {
        "name": "Alice Johnson",
        "email": "alice@example.com",
        "phone": "555-0101",
        "ssn": "123-45-6789",
        "card": "4111111111111111",
        "notes": "Premium customer since 2019"
    },
    "bob": {
        "name": "Bob Smith",
        "email": "bob@example.com",
        "phone": "555-0102",
        "ssn": "987-65-4321",
        "card": "5500000000000004",
        "notes": "Temp credentials – password: bob_secret_123"
    }
}


# ═══════════════════════════════════════════════════════════════
# MCP Server + Middleware
# ═══════════════════════════════════════════════════════════════
mcp = FastMCP("Hardened Server")
app = mcp.http_app(path="/mcp", transport="streamable-http")


class HardenedMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not request.url.path.startswith("/mcp"):
            return await call_next(request)

        auth = request.headers.get("authorization", "")
        if not auth.startswith("Bearer "):
            return JSONResponse(status_code=401,
                                content={"detail": "Missing token"})

        token_str = auth.removeprefix("Bearer ").strip()
        try:
            claims = jwt.decode(token_str, SECRET_KEY,
                                algorithms=[ALGORITHM], audience=AUDIENCE)
        except JWTError as exc:
            return JSONResponse(status_code=401,
                                content={"detail": f"Token invalid: {exc}"})

        client_id = claims.get("sub", "unknown")

        allowed, remaining = _check_rate_limit(client_id)
        if not allowed:
            _audit(client_id, "RATE_LIMITED")
            return JSONResponse(
                status_code=429,
                content={"detail": f"Rate limit exceeded. "
                                   f"Max {RATE_LIMIT_MAX} tool calls "
                                   f"per {RATE_LIMIT_WINDOW}s."},
                headers={"Retry-After": str(RATE_LIMIT_WINDOW)}
            )
        if request.method == "POST":
            body = await request.body()
            try:
                rpc = json.loads(body)
                if rpc.get("method") == "tools/call":
                    tool_name = rpc.get("params", {}).get("name", "")
                    args = rpc.get("params", {}).get("arguments", {})

                    ok, msg = _validate_tool_args(args)
                    if not ok:
                        _audit(client_id, "INPUT_BLOCKED",
                               f"{tool_name}: {msg}")
                        return JSONResponse(
                            status_code=400,
                            content={"detail": msg}
                        )

                    _audit(client_id, "TOOL_CALL", tool_name)
            except (json.JSONDecodeError, KeyError):
                pass

        response = await call_next(request)
        return response


app.add_middleware(HardenedMiddleware)


# ═══════════════════════════════════════════════════════════════
# Tools
# ═══════════════════════════════════════════════════════════════
@mcp.tool(description="Add two numbers")
async def add(a: int, b: int) -> int:
    return a + b


@mcp.tool(description="Look up customer information by name")
async def lookup_customer(name: str) -> str:
    """Returns customer info. Sensitive data is automatically sanitized."""
    customer = _FAKE_CUSTOMERS.get(name.lower())
    if not customer:
        return f"No customer found: {name}"
    raw = (
        f"Name: {customer['name']}\n"
        f"Email: {customer['email']}\n"
        f"Phone: {customer['phone']}\n"
        f"SSN: {customer['ssn']}\n"
        f"Card: {customer['card']}\n"
        f"Notes: {customer['notes']}"
    )
    return _sanitize_output(raw)


@mcp.tool(description="Search customer notes")
async def search_notes(query: str) -> str:
    """Search through customer notes for matching text."""
    results = []
    for cid, cust in _FAKE_CUSTOMERS.items():
        if query.lower() in cust["notes"].lower():
            results.append(f"{cust['name']}: {cust['notes']}")
    if not results:
        return f"No notes matching: {query}"
    return _sanitize_output("\n".join(results))




if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
