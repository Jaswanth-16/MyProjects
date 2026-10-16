# Verification status

Updated 2026-10-16.

- Fourteen automated tests passed locally, including an actual localhost HTTP
  request through the provider adapter. The server returned controlled fixtures.
- Seven of seven developer-authored retrieval/abstention regression cases passed.
  [Retained result](retrieval-evaluation.json) labels the mode and source quotes.
- The CLI produced a cited offline answer for the retention-approval question.
- Live Groq inference was **not executed**. No secret was needed for these checks.

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

Source quote matching is not a factuality score. No claim of production
security, client deployment, vector search or live LLM answer quality is made.
