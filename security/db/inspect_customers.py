from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "customers.db"

def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    rows = cur.execute("SELECT * FROM customers").fetchall()
    for r in rows:
        print(r)
    conn.close()

if __name__ == "__main__":
    main()
