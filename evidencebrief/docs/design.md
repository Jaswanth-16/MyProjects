# Design and role alignment

EvidenceBrief complements ClientPulse: one project prepares and models tabular
data; the other uses NLP retrieval and an optional generative model to produce
auditable briefs from the resulting analysis and policy material.

The corpus loader reads top-level Markdown files only. It enforces size/chunk
bounds, performs basic redaction and excludes common instruction-injection
phrases. SHA-256 IDs include file name, paragraph index, offset and redacted
text, so changed evidence creates a changed citation.

TF-IDF unigrams/bigrams rank chunks with cosine similarity. Empty, suspicious or
out-of-vocabulary queries abstain. The default mode returns source extracts.
The optional Groq adapter sends bounded evidence and a strict JSON instruction.
Only approved endpoint URLs are allowed; redirects are refused to avoid leaking
authorization headers. Context/query values are treated as untrusted text.

Validation rejects unknown keys, invalid types, extra explanatory fields,
unknown source IDs, invented numbers and paraphrases that are not literal
substrings. Accepted claims include source file and paragraph references.
Faithfulness here means exact text provenance, not truth, entailment or safety
of the document's own recommendations.

Tests cover retrieval, abstention, schema/citation enforcement, redaction,
injection exclusion, empty corpus, provider failure, credentials/endpoints and
a real localhost HTTP round-trip. A synthetic regression set checks common
business questions. No test substitutes a fake provider response for proof of
live generative performance.

For the supplied PwC role this demonstrates Python, NLP, generative-AI
integration, data preparation, analytical automation, testing and documentation.
The CLI is intentionally small and inspectable; no web deployment is implied.
