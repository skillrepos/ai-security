from __future__ import annotations

import re
from pathlib import Path

from fastmcp import FastMCP

mcp = FastMCP("Secure MCP Server")

# Secure: whitelist tools + validate inputs.

ALLOWED_LOG_ROOT = Path(__file__).parent / "logs"
ALLOWED_LOG_ROOT.mkdir(parents=True, exist_ok=True)

DISALLOWED_SHELL = re.compile(r"(rm\s+-rf|;|&&|\|\|)", re.I)

@mcp.tool()
def read_log(filename: str) -> str:
    """
    Read a log file from ./logs only. Refuses path traversal.
    """
    if "/" in filename or "\\" in filename or ".." in filename:
        raise ValueError("Invalid filename.")
    p = ALLOWED_LOG_ROOT / filename
    if not p.exists():
        raise FileNotFoundError(f"{filename} not found.")
    return p.read_text(encoding="utf-8")[:8000]

@mcp.tool()
def echo(message: str) -> str:
    """
    Safe utility for demonstrating tool calls.
    """
    return message[:500]

if __name__ == "__main__":
    mcp.run(transport="streamable-http", port=8000)
