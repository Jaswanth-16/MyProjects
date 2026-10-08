# Verification report — 8 October 2026

There are four projects. Their local tests pass, but **not every integration has been tested live**. This report distinguishes executed checks from mocked checks and remaining gaps. Passing tests do not prove general AI accuracy, complete security, cloud deployment success or certification readiness.

## Executed checks

| Project | Automated suite | Other executed checks | Remaining live checks |
|---|---:|---|---|
| TransitPulse | 31 passed, with cloud SDK dependencies installed | Full 10,000-trip demo reconciled to 10,200 unique trips; four real Azure Blob SDK/Azurite integration tests; Chromium dashboard/filter checks; ADF/JSON/link validation | Azure deployment, managed identity/RBAC, ADLS behavior, ADF orchestration, Synapse queries, Power BI imports/DAX/RLS |
| PipelineCopilot | 41 passed | 30/30 developer-authored retrieval cases; real local HTTP tests; Chromium samples, abstention and source links; mocked Azure and Groq response handling | Real model output and semantic grounding, Azure configuration and service errors |
| LogLens | 19 passed | Real local HTTP tests; Chromium structured output, unknown input, invalid input and HTML-as-text checks; valid/rejected Azure, Claude and Groq protocol fixtures | Real model extraction, provider availability and quotas |
| OpsEvidence | 24 passed | Real local HTTP tests; Chromium incident switching, trace/evidence rendering and input recovery; mocked three-provider multi-tool loop; read-only scope, citations and budget rejection | Real model tool selection, answer quality, latency and live provider errors |

**115 unit/HTTP tests + 4 emulator tests + 12 browser checks = 131 passing checks.** Browser checks include mobile layout and an uncaught JavaScript-error assertion. Fixtures are synthetic; retrieval cases are small and developer-authored. These counts are checks, not independent real-world examples.

The emulator requests used Azure Storage Blob SDK 12.31.0 and Azurite 3.37.0 on loopback, with telemetry disabled. The browser run used Playwright 1.64.0 and packaged Chromium 153. Standard Playwright browser download was unavailable in this environment, so a packaged local Chromium was used; web security remained enabled. GitHub Actions additionally installs and tests Playwright's matched browser.

The local cached Bicep executable could not run because its bundle was corrupt. The existing TransitPulse GitHub workflow compiles Bicep on a fresh runner without deploying resources. Check its current CI result before treating infrastructure compilation as passed for a new revision.

## Free options and what they validate

| Option | Account or prerequisite | Useful coverage | Limits |
|---|---|---|---|
| [Groq Free plan](https://console.groq.com/docs/rate-limits) | Your own account/key and an available model | Real JSON extraction, RAG and tool-loop inference in all three AI projects | Model/account rate limits; does not test Claude or Azure-specific behavior |
| [Azurite](https://learn.microsoft.com/en-us/azure/storage/common/storage-use-azurite) | Node.js and optional Azure Python dependencies; no Azure subscription | Actual Blob SDK HTTP requests, immutable writes, ETag conflicts, snapshots and replay | Emulator behavior is not Azure RBAC/managed identity/ADLS/ADF deployment validation |
| [Power BI Desktop](https://learn.microsoft.com/en-us/power-bi/fundamentals/desktop-get-the-desktop) | Windows and free Desktop installation | Local CSV imports, model relationships, DAX and View as role | Not available in this Linux environment; no completed PBIX is supplied; sharing/licensing differs |
| [Gemini Developer API](https://ai.google.dev/gemini-api/docs/pricing) | Own account/key and an eligible free-tier model | Another possible free model evaluation route | Not integrated here; model/region quotas apply; cannot substitute for provider-specific Azure/Claude tests |

A user-supplied key was used transiently for the strict Groq smoke suite with `openai/gpt-oss-20b`. Six cases attempted real requests, but none passed live inference: responses fell back, and a separate models-endpoint diagnostic returned **HTTP 403**. The account/provider/network cause is not established. No live AI success is claimed. The key was not committed, saved in this report or embedded in the presentation. See [sanitised live results](docs/groq-live-smoke-results.json). Trial/promotional cloud credits may depend on eligibility; no paid subscription was created or upgraded.

## Run the free-plan AI smoke suite

Create your key at https://console.groq.com/keys and remain on the Free plan. Choose a current model supporting tool calls and JSON mode from https://console.groq.com/docs/models. Set the key locally or as a GitHub Actions secret, never in source code or a chat message.

PowerShell:

```powershell
$env:GROQ_API_KEY = "YOUR_KEY"
$env:GROQ_MODEL = "YOUR_AVAILABLE_MODEL"
python scripts/live_ai_smoke.py --provider groq --interval 15
```

macOS/Linux:

```bash
export GROQ_API_KEY="YOUR_KEY"
export GROQ_MODEL="YOUR_AVAILABLE_MODEL"
python scripts/live_ai_smoke.py --provider groq --interval 15
```

Run from the repository root. Six synthetic smoke cases cover two examples per AI project. The script exits **2 for missing configuration**, **1 for rejected output/provider failure/fallback**, and **0 only when all live checks pass**. No retries occur. Six cases are a smoke test, not a full semantic evaluation. OpsEvidence permits at most four model requests per case. Increase the interval if your account's limits require it; a failed network call may still use quota.

Alternatively, add `GROQ_API_KEY` to repository **Settings → Secrets and variables → Actions**, then manually run **Opt-in live Groq smoke tests** and enter the model name. This workflow never runs automatically on pushes or PRs and does not expose the key. API plan/billing settings remain under your account's control.

## Reproduce emulator and browser tests

From `transitpulse`, install `requirements.txt`. In one terminal:

```bash
npx --yes --package azurite@3.37.0 azurite-blob --blobHost 127.0.0.1 --blobPort 10000 --location ./workspace-azurite --silent --skipApiVersionCheck --disableTelemetry
```

In another terminal, from the same project directory:

```bash
TRANSITPULSE_TEST_AZURITE=1 python -m unittest discover -s integration -v
```

PowerShell: set `$env:TRANSITPULSE_TEST_AZURITE = "1"` before the Python command. Integration tests use the documented public emulator key, create uniquely named test containers and delete them afterward. They do not request managed identity credentials. Stop the emulator with Ctrl+C.

From the repository root:

```bash
npm ci --ignore-scripts --no-audit --no-fund
npx playwright install chromium
npm run test:browser
```

On Linux, `npx playwright install --with-deps chromium` may be required. Browser tests start/stop all three local AI servers and generate/remove a temporary TransitPulse dataset. GitHub's **Free integration verification** workflow executes browser and emulator checks without cloud credentials.

## Issues found and addressed

- Added Groq's fixed HTTPS endpoint and bearer authentication to all three AI projects; retained the existing Azure/Claude paths and default offline behavior.
- PipelineCopilot now rejects responses whose finish reason is not `stop`, including truncated JSON-shaped output.
- Live smoke tests fail on fallback instead of counting offline results as real inference.
- Added actual Blob SDK/emulator tests and browser interaction tests, beyond the existing transport mocks and HTTP checks.
- Kept token counters and fallback warnings visible; they do not constitute a billing guarantee or semantic quality measurement.

## Work still needed before a production claim

Run the live suite with an account-owned key, evaluate outputs against a reviewed held-out set, and test actual Azure and Claude services when credentials are available. For TransitPulse, execute the Azure deployment with identity/access checks and validate the Power BI model on Windows. Production load testing, cross-user authorization, durable telemetry and independent security review are not covered by this portfolio suite.
