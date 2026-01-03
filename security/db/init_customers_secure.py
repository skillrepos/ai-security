from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "customers.db"

def mask_phone(phone: str) -> str:
    # Keep last 2 digits only
    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) < 2:
        return "***"
    return "***-**" + digits[-2:]

def hash_email(email: str) -> str:
    return hashlib.sha256(email.strip().lower().encode("utf-8")).hexdigest()

def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS customers")
    cur.execute("""
        CREATE TABLE customers (
            id INTEGER PRIMARY KEY,
            email_sha256 TEXT,
            phone_masked TEXT,
            notes TEXT
        )
    """)
    cur.execute("INSERT INTO customers (id,email_sha256,phone_masked,notes) VALUES (?,?,?,?)",
                (12345, hash_email("alice@example.com"), mask_phone("555-0101"), "VIP customer"))
    conn.commit()
    conn.close()
    print(f"Created {DB_PATH} with hashed/masked PII (SECURE).")

if __name__ == "__main__":
    main()
