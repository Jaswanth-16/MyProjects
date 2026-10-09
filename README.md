# Azure data engineering and applied AI portfolio

I am Jaswanth, an Azure Data and BI Engineer at Accenture. This portfolio connects incremental processing and reporting with source-cited AI troubleshooting. Synthetic project data is separate from production work.

[GitHub](https://github.com/Jaswanth-16) · [LinkedIn](https://www.linkedin.com/in/jaswanth-cheedella-a3b591200) · [Credentials](https://www.credly.com/users/jaswanth-pavan-kumar-cheedella)

| Project | Capability | Demonstration |
|---|---|---|
| [TransitPulse](transitpulse/) | Incremental Python/SQL, corrections, quarantine, optional Azure assets | 10,000 initial trips become 10,200; replay skips |
| [OpsEvidence](opsevidence/) | Read-only tool agent, scoped statistics and evidence validation | Five incident families over 420 synthetic runs |
| [PipelineCopilot](pipelinecopilot/) | RAG, BM25 retrieval, citations, redaction and abstention | Eight runbooks, 30 curated retrieval cases |
| [LogLens](loglens/) | Structured extraction and source-line validation | Beginner offline/live comparison lab |

## Evidence before claims

[Verification](TESTING.md) distinguishes unit/HTTP, Blob SDK/Azurite, browser and live checks. [49 regression cases](docs/portfolio-evaluation.json) include the existing 30 retrieval examples; this developer-authored synthetic set is not a held-out accuracy benchmark.

Live Azure deployment, Azure OpenAI and Claude execution remain unverified. [Groq results](docs/groq-live-smoke-results.json) retain accepted outputs and failures; fallback is never a live pass.

## Run the evidence

Python 3.11 or 3.12:

```powershell
git clone https://github.com/Jaswanth-16/MyProjects.git
cd MyProjects
python scripts/evaluate_portfolio.py
cd transitpulse
python -m transitpulse demo --workspace workspace-demo --count 10000
```

Use a fresh TransitPulse workspace for each demo. AI READMEs contain serve commands and ports. Offline demos need no provider account.

## Engineering decisions

- [TransitPulse architecture](transitpulse/docs/architecture.md): transactions and immutable snapshots through HEAD.
- [Azure operations](transitpulse/docs/operations.md): optional monitoring and deployment acceptance.
- [PipelineCopilot architecture](pipelinecopilot/docs/architecture.md): abstention and citation limitations.
- [AI evaluation](docs/ai-evaluation.md): regression, live smoke and human review.
- [Interview guide](docs/portfolio-review.md): a five-minute demonstration and implementation questions.

![TransitPulse synthetic dashboard](transitpulse/docs/preview.svg)
