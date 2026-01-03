from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "customers.db"

def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS customers")
    cur.execute("""
        CREATE TABLE customers (
            id INTEGER PRIMARY KEY,
            email TEXT,
            phone TEXT,
            notes TEXT
        )
    """)
    cur.execute("INSERT INTO customers (id,email,phone,notes) VALUES (?,?,?,?)",
                (12345, "alice@example.com", "555-0101", "VIP customer"))
    conn.commit()
    conn.close()
    print(f"Created {DB_PATH} with clear-text PII (INSECURE).")

if __name__ == "__main__":
    main()
