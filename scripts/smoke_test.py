from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]

def run(cmd: list[str]) -> None:
    print(f"$ {' '.join(cmd)}")
    subprocess.check_call(cmd, cwd=str(ROOT))

def main() -> None:
    # Quick check: can we import ollama helper?
    run([sys.executable, "-c", "from common.ollama_client import generate; print('ollama_client ok')"])
    print("Smoke test complete. Next: run labs from security/ and prompting/ folders.")

if __name__ == "__main__":
    main()
