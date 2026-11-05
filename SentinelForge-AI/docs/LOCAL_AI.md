# Free, local AI investigation

SentinelForge supports a **no-key, opt-in local Ollama provider**. The deterministic investigator remains the default and requires no installation or network calls.

## Setup

Install Ollama from its official site, then run:

```bash
ollama pull llama3.2:3b
ollama serve
```

In another terminal:

```bash
export SENTINELFORGE_AI_PROVIDER=ollama
export SENTINELFORGE_OLLAMA_MODEL=llama3.2:3b
uvicorn sentinelforge.main:app --host 127.0.0.1 --port 8000
```

Create a synthetic finding with POST /findings, then GET /findings/{id}/investigation. If Ollama is unavailable or times out, the system returns the deterministic report instead.

## Security notes

- Local Ollama is only allowed at localhost:11434; arbitrary external endpoints are rejected.
- The model receives the title, resource, rule, evidence and remediation text, so **do not submit secrets or sensitive company information**.
- Model output is untrusted and not an authoritative verification or fix.
- This is a development-only API without authentication; never expose it publicly.
- Ollama model downloads require internet once; inference then runs locally.
- The provider is not Hinoki. No Hinoki key is required.
