# Artifact-based progress audit

Use this bounded audit when an owner asks whether a card has real progress or is merely `running`.

1. **Read live orchestration state** from the canonical board DB: card status/assignee/block reason, newest run outcome and start time, and current worker PID. Confirm the PID/process is live, but treat that only as liveness. Check prerequisites and dependency/gate state; never infer that a downstream card has started or passed because its predecessor appears complete in an old report.
2. **Inspect repository/workspace changes** against the card's baseline: latest commits, dirty diff, and files/artifacts modified during the current run window. Attribute changes to the task where possible. A commit, line count, file count, mtime, or tool activity proves activity only—not acceptance progress.
3. **Enumerate deliverables and validate representative evidence independently.** For code, run the smallest relevant test/lint or smoke check. For evidence bundles, verify expected file count and types, parse structured output, recompute headline counts from raw rows, inspect sample screenshots, validate PDFs by signature and preferably a parser, and compare reported metrics with the underlying artifact. Do not accept a worker's summary as validation.
4. **Map each check to acceptance criteria.** Mark each criterion PASS, FAIL, or NOT MEASURED. Investigate apparent failures against the actual route/method/parameters and test intent; a 404 may be an expected negative probe or a required route defect, so verify the router and request contract before classifying it. Keep failures visible; do not treat partial evidence as a pass.
5. **State the gate chain explicitly.** Separate implementation activity, functional evidence, independent review/verdict, and formal Kanban completion. Do not label a phase complete or allow its successor until the required predecessor state and reviewer gate are verified live.
6. **Report concisely:** answer the user's question first; say whether progress is real, cite the strongest directly checked artifacts/results, name outstanding acceptance/gate gaps, and give the next concrete step. Distinguish observed facts from worker-reported facts and unknowns. Do not continue polling or broaden the audit after the answer unless new evidence or an actionable anomaly warrants it.

## Evidence interpretation

| Evidence | Supports | Does not establish |
|---|---|---|
| `running`, heartbeat, PID | Worker/process liveness | Work advancing or acceptance passed |
| New tool calls or read-heavy activity | Activity | Product change; repeated reads can be a loop |
| New/changed source files or commit | Implementation activity | Runtime behavior or feature correctness |
| Lint/build success | Syntax/buildability at checked revision | Functional acceptance or independent gate |
| Test artifact with raw cases and recomputed totals | Measured behavior for those cases | Untested routes, viewport states, or full milestone completion |
| Screenshot/PDF existence or valid signature | Artifact is present and structurally plausible | Correct content/rendering; inspect or parse it |
| Explicit reviewer APPROVE + required board transition | Gate disposition/completion at that scope | Unlisted downstream gates or deployment |

A report can contain many artifacts yet remain incomplete: check provenance, recency (artifact timestamp vs current run), raw-to-summary arithmetic, scope coverage, and whether the result maps to a stated acceptance criterion. A percentage is optional; if no fixed, evidence-backed denominator exists, report measured criterion counts and say the completion percentage is not measurable.
