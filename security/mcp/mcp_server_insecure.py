from __future__ import annotations

import os
import subprocess
from pathlib import Path

from fastmcp import FastMCP

mcp = FastMCP("Insecure MCP Server")

# Insecure: exposes file read + shell exec with minimal validation.

@mcp.tool()
def read_file(path: str) -> str:
    p = Path(path)
    return p.read_text(encoding="utf-8")

@mcp.tool()
def run_shell(cmd: str) -> str:
    out = subprocess.check_output(cmd, shell=True, text=True)
    return out

if __name__ == "__main__":
    # Streamable HTTP endpoint at http://127.0.0.1:8000/mcp by default (per FastMCP docs).
    mcp.run(transport="streamable-http", port=8000)
