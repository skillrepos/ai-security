# AI Security + Prompting Lab Pack (Codespaces + Ollama)
This package contains the **actual code assets** referenced by the two lab markdown files:

- `ai-security-labs.md`
- `prompting-techniques-labs.md`

## Prereqs
- GitHub Codespace (recommended)
- Ollama running locally in the Codespace (or forwarded) with:
  - `llama3.2:3b`

## Quick start
From the repo root of this pack:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Pull model (if needed):

```bash
ollama pull llama3.2:3b
```

## Run a smoke test
```bash
python scripts/smoke_test.py
```

## Lab folders
- `security/` — security labs code
- `prompting/` — prompting labs code

## Notes
- The security labs include both **insecure** and **secure** implementations.
- The `extra/` folder contains **diff targets** (the “secure” versions) so learners can use:
  `code -d secure.txt insecure.py` then merge changes.
