# secure_server.py  –  Lab 3: Auth + Per-Tool Scopes
# FastMCP server with JWT auth and per-tool scope enforcement.

import json
import warnings
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
# ─────────────────────────────────────────────────────────────────

# 1) Create the MCP server
mcp = FastMCP("Secure Calc")

# 2) Mount on /mcp with streamable-http transport
app = mcp.http_app(path="/mcp", transport="streamable-http")


# 3) Auth middleware – verify JWT and enforce per-tool scopes
class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/mcp"):
            auth = request.headers.get("authorization", "")
            if not auth.startswith("Bearer "):
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Missing token"}
                )

            token = auth.removeprefix("Bearer ").strip()
            try:
                claims = jwt.decode(token, SECRET_KEY,
                                    algorithms=[ALGORITHM], audience=AUDIENCE)
            except JWTError as exc:
                return JSONResponse(
                    status_code=401,
                    content={"detail": f"Token invalid: {exc}"}
                )

            # Per-tool scope enforcement
            # (scope checking logic goes here)

        return await call_next(request)


# 4) Register the middleware


# 5) Secure tools
@mcp.tool(description="Add two numbers")
async def add(a: int, b: int) -> int:
    return a + b


# 6) Run
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
