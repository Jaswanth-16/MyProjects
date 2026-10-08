# LogLens

A beginner project that converts a pipeline failure log into a validated JSON summary. Learn prompts, structured output, provider APIs, redaction and evidence checks before building an agent.

## Run locally

Requires Python 3.11 or 3.12. The runtime uses the standard library; no package installation is required. Clone [MyProjects](https://github.com/Jaswanth-16/MyProjects), then:

```bash
cd MyProjects/loglens
python -m loglens demo
python -m loglens serve
```

Open http://127.0.0.1:8766. On Windows, use `py` instead of `python` if needed. Ctrl+C stops the server. Run all commands from this project folder so Python finds the package.

Offline mode is a deterministic learning demo, **not model inference**. Optional Azure OpenAI and Claude modes are implemented; [configure a provider](docs/providers.md) to make live calls with your credentials.

## What you can study

- Numbered input lines and an explicit JSON output contract.
- Eight recognised error categories, unknown-code handling and ambiguous-log handling.
- Forced function/tool output with Azure and Claude adapters.
- Evidence quotes checked against the sanitised log and labelled fallback on rejected output.

## Verify

```bash
python -m unittest discover -s tests -v
python -m compileall -q loglens
```

18 tests cover offline behavior, validation, mocked provider protocols and real local HTTP requests. GitHub Actions runs both Python versions. Checked-in [demo output](docs/demo-results.json) shows synthetic/offline behavior, not an independent benchmark of AI accuracy.

[Study walkthrough](docs/study-guide.md) · [Certification mapping](docs/certification-map.md) · [Optional providers](docs/providers.md)

## Limits

Synthetic study project, not production monitoring. Credential redaction is best effort; use the supplied fictional data. Exact-quote validation proves a quote exists, not that the model's interpretation is correct. Review all suggested checks. The local server is intended for one user on loopback, without account authentication or production deployment hardening. No resources are changed by either project. Live provider tests require separate credentials and were not run during construction.
