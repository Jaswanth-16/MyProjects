# Optional live providers

Offline mode is the default and makes no model requests. Live modes send the sanitised input and, for OpsEvidence, synthetic tool evidence to your chosen provider. Calls may incur charges. You need a deployment/model with tool calling and access through your own account. No credentials are committed.

Set environment variables in your terminal. `.env.example` is a reference only: the application does **not** automatically load `.env` files. On PowerShell use `$env:NAME = "value"`; on macOS/Linux use `export NAME="value"`.

| Provider | Variables |
|---|---|
| Azure OpenAI | `AZURE_OPENAI_BASE_URL=https://YOUR-RESOURCE.openai.azure.com/openai/v1/`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_DEPLOYMENT` |
| Claude | `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL` |

Start `python -m loglens serve --provider azure` or `--provider claude` from the project directory. Set the exact deployment/model name available to your account. The server never sends keys to the browser. If configuration, transport, output validation or budgets fail, the response explicitly labels a deterministic offline fallback. Reported usage only reflects tokens supplied in received responses; failed network calls may have incurred unreported usage. There is no automatic retry.

The Azure adapter uses the v1 chat-completions endpoint, `tools`, `tool_choice` and tool-result messages. The Claude adapter uses Messages, `input_schema`, `tool_use` and matching `tool_result` blocks. Tests inject transport responses to verify both protocols; live inference has not been tested with paid credentials.

Sources: [Azure function calling](https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/function-calling), [Claude handling tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls).

## Free-plan alternative: Groq

Create your own account and API key at https://console.groq.com/keys, stay on the Free plan, and choose a currently available tool-capable model from https://console.groq.com/docs/models. Set `GROQ_API_KEY` and `GROQ_MODEL`, then run `python -m loglens serve --provider groq`. The adapter uses the fixed `https://api.groq.com/openai/v1/chat/completions` endpoint and bearer authentication. No SDK installation is needed.

[Free-plan rate limits](https://console.groq.com/docs/rate-limits) vary by model and account. Quota failures are visibly labelled; there are no automatic retries. A successful Groq test checks the application flow with a Groq-hosted model. It does not validate Claude model quality, Azure deployment access, Azure identity or either provider's service behavior. Never use someone else's published key.

Run the strict live smoke suite from the repository root with `python scripts/live_ai_smoke.py --provider groq`. Missing credentials are reported as blocked; fallbacks fail the live check instead of being counted as successful inference.
