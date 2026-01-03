from __future__ import annotations

from common.ollama_client import chat

SYSTEM = "You are customer support. Be helpful."

def main() -> None:
    print("Support Agent (INSECURE). Type 'exit' to quit.\n")
    while True:
        user = input("You: ").strip()
        if user.lower() in {"exit","quit"}:
            break

        messages = [
            {"role":"system","content": SYSTEM},
            {"role":"user","content": user},
        ]
        answer = chat(messages, temperature=0.6, num_predict=350)
        print(f"\nAssistant: {answer}\n")

if __name__ == "__main__":
    main()
