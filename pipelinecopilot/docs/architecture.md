# Design decisions and code walkthrough

## Retrieval

`retrieval.py` normalises words and a short explicit synonym list, removes stop words, and scores
runbooks with BM25 (k1=1.5, b=0.75). Exact error-code matches receive a 15-point boost. Results are
ordered by descending score then ID, so ties are deterministic. The best result must have an exact
code match or score at least 3.5. This threshold is a heuristic selected for this corpus; it is not a
probability or confidence estimate. Generic or adversarial questions may still match incorrectly.

The complete corpus is small enough to index at startup. Each runbook acts as one chunk. A larger
system needs document chunking, revisions, ACL metadata and hybrid retrieval. Error identifiers
help preserve exact matches that embeddings alone might blur.

## Answer generation

`core.py` validates the request, sanitises question/log text, retrieves evidence and abstains when
matching evidence is weak. Default checks are copied from the top runbook. With LLM mode enabled,
`llm.py` sends the top three passages and the user's redacted text to Azure OpenAI. The response
must contain `summary`, `checks`, and `citation_ids`; unknown IDs and empty citations are rejected.

Validation is structural and checks membership only. It does not independently verify each claim
against evidence. A valid-looking hallucination remains possible. Errors fall back to extractive
checks, and provider error bodies are not exposed. No retries are made automatically, avoiding
unexpected repeat costs. No model response is cached or persisted.

## Local HTTP boundary

`server.py` exposes a page, two static assets, and `POST /api/ask`. It binds only to 127.0.0.1.
POSTs must use JSON and the page's origin. Host checking blocks basic DNS-rebinding access.
Requests are limited to 20,000 bytes; questions to 2,000 characters; logs to 16,000 characters.
The UI places model text in text nodes and restricts outbound source links to Microsoft Learn.

This remains a demo: localhost malware could access it, authenticated multi-user access is absent,
and the threaded server has no production concurrency quota. Do not bind it publicly.

## Test evidence

`tests/test_assistant.py` covers retrieval, exact codes, unknown topics, corpus integrity, secret
formats, input limits, offline network isolation, model request format, endpoint restrictions,
redirect refusal, invalid outputs, fallback and real HTTP boundaries. Provider transport is mocked;
no Azure subscription or paid inference request is needed for CI.

`evaluate.py` compares each top answer ID with the 30 bundled expected IDs. These cases were authored
for the portfolio, not sampled from independent operational traffic. The JSON report exposes each
case's prediction so failures remain reviewable. CI gates supported accuracy at >=85% and unknown
abstention at 100% on this tiny fixture. It does not evaluate LLM semantics or diagnosis correctness.

## Roadmap

1. Run opt-in inference against a real deployment and manually score correctness and citation support.
2. Add challenging independent queries, ambiguous incidents, noisy logs and adversarial evaluation.
3. Move runbooks to access-controlled Azure AI Search for hybrid retrieval when the corpus grows.
4. Integrate read-only monitoring APIs with scoped identity and resource-level authorization.
5. Track groundedness, fallback rate, provider latency, token usage and cost without logging secrets.
