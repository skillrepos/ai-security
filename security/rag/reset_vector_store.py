from __future__ import annotations

import shutil
from pathlib import Path

DB_DIR = Path(__file__).parent / "chroma_db"

def main() -> None:
    if DB_DIR.exists():
        shutil.rmtree(DB_DIR)
        print(f"Removed {DB_DIR}")
    else:
        print(f"No DB found at {DB_DIR}")

if __name__ == "__main__":
    main()
