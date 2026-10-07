# Portfolio and interview guide

## A 30-second explanation

“I built PipelineCopilot to help investigate Azure pipeline errors using relevant troubleshooting
runbooks. It combines BM25 and error-code retrieval with an optional Azure OpenAI generation
adapter. Answers include source links, unsupported questions abstain, and provider failures fall
back to curated checks. I tested the local retrieval and HTTP flows and mocked the provider
boundary. A live Azure deployment remains a separate validation step.”

## Resume wording supported by current evidence

**PipelineCopilot | Pipeline Troubleshooting Assistant | Python, BM25, optional Azure OpenAI**

- Built a source-cited troubleshooting assistant across eight Azure pipeline failure categories,
  with a local web interface and optional retrieval-augmented Azure OpenAI generation adapter.
- Implemented input limits, best-effort credential redaction, citation-ID validation and extractive
  fallback; passed 39 automated tests covering retrieval, mocked inference and HTTP boundaries.
- Evaluated 30 curated cases: correct top runbook on 24 supported questions and abstention on six
  unrelated questions; documented benchmark scope and pending live inference validation.

Do not claim deployed Azure AI Search, trained language models, live inference accuracy, production
usage or employer incident-resolution savings. Build evidence before adding those claims.

## Interview questions

**Why BM25?** Small corpus, no account/dependencies, repeatable behaviour and good exact-token
matching. It misses unfamiliar paraphrases; hybrid retrieval is a useful next step.

**Is the default demo AI-generated?** No. It is extractive retrieval. Enabling the configured Azure
OpenAI adapter adds LLM generation over retrieved evidence; that path is implemented and mocked
in tests but has not been live-validated.

**Do citations prevent hallucinations?** Citation-ID validation prevents references outside the
retrieved context. It does not verify semantic support. That needs claim-level evaluation.

**Why not let it fix pipelines?** Investigation is useful without granting write access. Automatic
remediation would require stronger authorization, change review, idempotency and rollback controls.

**What did you measure?** Local tests and a 30-case curated retrieval benchmark. Neither is proof
of broad AI diagnosis accuracy. Independent noisy data and live-model evaluations remain next steps.
