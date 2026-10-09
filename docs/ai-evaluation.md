# AI evaluation and provider behavior

Run `python scripts/evaluate_portfolio.py` from the repository root. The 49 developer-authored synthetic checks cover LogLens recognised categories, missing/conflicting codes, credential redaction and fabricated evidence; OpsEvidence five incident families and invented sources; PipelineCopilot's existing 30 retrieval cases. They overlap with unit behavior and are not independent real-world samples. CI uploads the report.

## Live inference

Run `python scripts/live_ai_smoke.py --provider groq --interval 15` with your own key/model. Six cases are a smoke suite, not an accuracy benchmark. Fallbacks fail; no automatic retries occur. Repeated runs may differ. Valid citations and quotes do not prove semantic grounding.

Groq GPT-OSS uses low reasoning effort for RAG and the incident agent with a 1,600-token completion budget. Other models receive no model-specific reasoning option. OpsEvidence guides evidence gathering in run, statistics and runbook order, then permits final assessment. The application chooses the evidence stage; the model fills tool arguments and produces the assessment. This is a bounded guided workflow, not unrestricted autonomous tool selection. Groq gathers evidence with native tool calls, then uses JSON mode for final assessment after the provider rejected a complex final function call. The final context includes explicit quote options copied from each actual source, including compact JSON field excerpts for run/statistics data. The model must select an exact option; application schema and exact-quote validation still reject mismatches. The internally routed final action is not a native provider tool call. Azure/Claude retain tool-based final assessment paths. Limits remain four model turns and six data-tool calls.

References: [Groq reasoning](https://console.groq.com/docs/reasoning), [API reference](https://console.groq.com/docs/api-reference).

## Before an accuracy claim

Prepare a separate reviewed set before adapting prompts to its answers. Include sanitised realistic logs, unknown/conflicting codes, misleading instructions, irrelevant runbooks and multiple plausible causes. Label facts, evidence, permissible checks and uncertainty first. Review whether each claim follows from evidence and whether important information is missing. Record model, commit, failures, fallback rate, sample size, latency and tokens. Retain failures instead of selecting a best retry. Independent human evaluation remains outstanding.
