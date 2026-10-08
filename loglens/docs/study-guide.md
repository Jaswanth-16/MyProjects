# LogLens walkthrough

## 1. Understand the problem

A failed pipeline can generate a long message. Start by extracting what the log actually says: pipeline, activity, error code and a short summary. An error code alone does not prove why the failure occurred.

Run `python -m loglens demo`, then `python -m loglens analyse examples/storage.log`. The sample AccountKey is fictional and gets redacted. Try the schema and unknown samples in the browser.

## 2. Follow the code

1. `core.numbered` limits input, redacts common credentials and creates line IDs such as L1.
2. Offline mode uses regular expressions and eight known codes. Two different known codes produce an unknown classification rather than choosing a diagnosis.
3. Live mode sends numbered lines and a system prompt to Azure or Claude. The model must call `emit_summary` with structured arguments.
4. `contracts.validate` checks types, required fields, allowed categories and extra fields.
5. `validate_summary` checks observed fields occur in the log, category matches code and every evidence quotation exists on its cited line.
6. Rejected responses visibly fall back to the deterministic parser. `server.py` provides the local browser interface; `app.js` renders text without inserting model HTML.

## 3. Exercises

- Remove the pipeline name: the result should use null.
- Add `LoginFailed` beside `SqlTimeout`: the offline result should be unknown.
- Put a fictional bearer token into the log and inspect sanitised lines.
- Read the mocked provider tests, then configure a provider and compare the same example.
- Add one new error code with a test. Explain why a parser cannot reliably diagnose every free-text error.

## 4. Explain it in an interview

“I built a structured log summariser with two provider adapters. It checks types and source quotations before accepting generated output, handles missing facts and falls back visibly when validation fails. Offline mode is deterministic, so the project runs without credentials.”

Do not claim measured accuracy, real production incidents, root-cause automation or savings without running an appropriate evaluation. The free-text summary still needs human review.
