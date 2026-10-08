# OpsEvidence

A capstone study project that investigates synthetic Azure pipeline incidents with a bounded agent loop, read-only SQLite tools, lexical runbook retrieval and validated citations. Designed around data-engineering incidents you can explain in an interview.

## Run locally

Requires Python 3.11 or 3.12. The runtime uses the standard library; no package installation is required. Clone [MyProjects](https://github.com/Jaswanth-16/MyProjects), then:

```bash
cd MyProjects/opsevidence
python -m opsevidence demo
python -m opsevidence serve
```

Open http://127.0.0.1:8767. On Windows, use `py` instead of `python` if needed. Ctrl+C stops the server. Run all commands from this project folder so Python finds the package.

Offline mode is a deterministic learning demo, **not model inference**. Optional Azure OpenAI, Claude and free-plan Groq modes are implemented; [configure a provider](docs/providers.md) to make live calls with your credentials.

## What you can study

- A model requests tools; Python validates arguments and executes only allowed reads.
- 420 synthetic runs across five pipelines and eight curated Azure runbooks.
- Parameterised SQL statistics scoped to the selected pipeline and incident window.
- BM25 retrieval with error-code matching; retrieved scores are not confidence.
- Evidence IDs and exact quotations, four model turns and six data-tool calls maximum.
- Provider-specific tool-result messages, usage counters, timings and visible fallback.

## Verify

```bash
python -m unittest discover -s tests -v
python -m compileall -q opsevidence
```

24 tests cover offline behavior, validation, mocked provider protocols and real local HTTP requests. GitHub Actions runs both Python versions. Checked-in [demo output](docs/demo-results.json) shows synthetic/offline behavior, not an independent benchmark of AI accuracy.

[Study walkthrough](docs/study-guide.md) · [Certification mapping](docs/certification-map.md) · [Optional providers](docs/providers.md)

## Limits

Synthetic study project, not production monitoring. Credential redaction is best effort; use the supplied fictional data. Exact-quote validation proves a quote exists, not that the model's interpretation is correct. Review all suggested checks. The local server is intended for one user on loopback, without account authentication or production deployment hardening. No resources are changed by either project. Live provider tests require separate credentials and were not run during construction.
