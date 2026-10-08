# Certification study mapping

Prepared for **Microsoft AI-103: Azure AI Apps and Agents Developer Associate** and **Claude Certified Developer – Foundations**. These are hands-on study exercises, not official exam content or complete preparation courses. Follow the current exam guide provided by your employer/Anthropic partner portal for Claude.

| Topic | LogLens | OpsEvidence |
|---|---|---|
| Model/API configuration | Azure OpenAI v1 and Claude Messages | Same adapters in a multi-turn loop |
| Prompt and output contracts | Numbered logs, JSON schema, unknown values | Tool schemas, final answer schema, uncertainty |
| Tool use | One forced structured-output tool | Three read-only data tools plus final answer tool |
| Retrieval and grounding | Exact source-line evidence | BM25 runbooks, evidence registry, exact citations |
| Evaluation and failure handling | Offline cases, invalid-output rejection | Protocol tests, citation rejection, scope/budget tests |
| Monitoring and cost controls | Usage counters, input/output limits | Trace timings, tokens, turn/tool limits |

AI-103 also covers areas these projects do not implement: vision, speech, managed Azure AI Search, information extraction services, managed identities, Foundry deployment/evaluation and production monitoring. MCP, enterprise authorization, cloud deployment and production scale are also outside this implementation. The custom tool loop is not Azure Foundry Agent Service. Lexical BM25 is not vector search. Do additional labs against the actual exam objectives.

Official references: [AI-103 study guide](https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/AI-103), [Anthropic role-based certifications](https://claude.com/resources/articles/four-role-based-claude-certifications), [Claude Developer certification portal](https://anthropic-partners.skilljar.com/claude-certified-developer-foundations-certification).
