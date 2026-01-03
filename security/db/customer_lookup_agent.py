from __future__ import annotations

import sqlite3
from pathlib import Path

from common.ollama_client import chat

DB_PATH = Path(__file__).parent / "customers.db"

SYSTEM = """You are a customer support assistant.

Rules:
- Never reveal sensitive personal information.
- Use database results carefully. If the DB stores hashed/masked values, explain that they are protected.
"""

def lookup(customer_id: int) -> str:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    rows = cur.execute("SELECT * FROM customers WHERE id=?", (customer_id,)).fetchall()
    conn.close()
    return str(rows[0]) if rows else "No record found."

def main() -> None:
    print("Customer Lookup Agent. Type 'exit' to quit.\n")
    while True:
        user = input("Customer ID: ").strip()
        if user.lower() in {"exit","quit"}:
            break
        try:
            cid = int(user)
        except ValueError:
            print("Please enter an integer ID.\n")
            continue

        db_row = lookup(cid)
        messages = [
            {"role":"system","content": SYSTEM},
            {"role":"user","content": f"Database row: {db_row}\nExplain what you can safely share to a support agent user."},
        ]
        ans = chat(messages, temperature=0.2, num_predict=250)
        print(f"\nAssistant:\n{ans}\n")

if __name__ == "__main__":
    main()
