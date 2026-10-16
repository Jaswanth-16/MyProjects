# Verification status

Updated 2026-10-16.

- Fourteen automated tests passed locally, including an actual localhost HTTP
  request through the provider adapter. The server returned controlled fixtures.
- Seven of seven developer-authored retrieval/abstention regression cases passed.
  [Retained result](retrieval-evaluation.json) labels the mode and source quotes.
- The CLI produced a cited offline answer for the retention-approval question.
- Live Groq inference was executed on 2026-10-16 with `openai/gpt-oss-120b`.
  Five of five live answer cases passed JSON, exact-quote and citation checks.
  Two additional queries abstained locally before an API call (not live passes).
- [Successful live evidence](live-smoke-results.json) retains accepted outputs.
  [Initial failed run](live-smoke-initial.json) is retained rather than rewritten.
  The fixes added explicit HTTP headers, safe error-status diagnostics and quote
  length/full-paragraph requirements matching the existing strict validator.
- The key was entered through a non-echoing terminal prompt and is not in code,
  reports, test fixtures or GitHub Actions. CI still uses local HTTP fixtures;
  the live smoke test is manual and explicitly authorized.

The initial seven-case run passed five cases. It exposed that first-sentence
extraction could hide the relevant second sentence, and that one method paragraph
described observation months ambiguously. Offline output now retains the bounded
source paragraph, and the method document states the actual feature periods
explicitly. The regression cases themselves were not relaxed. This small,
developer-authored corpus remains a regression fixture, not an independent
retrieval accuracy benchmark.

ClientPulse has seven additional tests, making 21 across the two projects.
GitHub Actions runs both suites and both CLI demonstrations on Python 3.11.
Local development used Python 3.12.14 and scikit-learn 1.5.2. Dependency versions
are pinned for repeatable clean CI; inspect Actions for the actual latest result.

Source quote matching is not a factuality score. This small synthetic run does not establish general live LLM accuracy,
production security, client deployment or vector search capability.
