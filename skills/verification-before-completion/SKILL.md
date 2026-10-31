---
name: verification-before-completion
description: Use when about to claim work is complete, fixed, or passing, before committing or creating PRs - requires running verification commands and confirming output before making any success claims; evidence before assertions always
---

# Verification Before Completion

## Overview

**Core principle:** Evidence before claims, always.

**Violating the letter of this rule is violating the spirit of this rule.**

## The Iron Law

```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

If you haven't run the verification command in this message, you cannot claim it passes.

## The Gate Function

```
BEFORE claiming any status or expressing satisfaction:

1. IDENTIFY: What command proves this claim?
2. RUN: Execute the FULL command (fresh, complete)
3. READ: Full output, check exit code, count failures
4. VERIFY: Does output confirm the claim?
   - If NO: State actual status with evidence
   - If YES: State claim WITH evidence
5. ONLY THEN: Make the claim

Skip any step = lying, not verifying
```

## Common Failures

| Claim | Requires | Not Sufficient |
|-------|----------|----------------|
| Tests pass | Test command output: 0 failures | Previous run, "should pass" |
| Linter clean | Linter output: 0 errors | Partial check, extrapolation |
| Build succeeds | Build command: exit 0 | Linter passing, logs look good |
| Bug fixed | Test original symptom: passes | Code changed, assumed fixed |
| Regression test works | Red-green cycle verified | Test passes once |
| Agent completed | VCS diff shows changes | Agent reports "success" |
| Requirements met | Line-by-line checklist | Tests passing |

## Red Flags - STOP

- Using "should", "probably", "seems to"
- Expressing satisfaction before verification ("Great!", "Perfect!", "Done!", etc.)
- About to commit/push/PR without verification
- Trusting agent success reports
- Relying on partial verification
- Thinking "just this once"
- Tired and wanting work over
- **ANY wording implying success without having run verification**

## Rationalization Prevention

| Excuse | Reality |
|--------|---------|
| "Should work now" | RUN the verification |
| "I'm confident" | Confidence ≠ evidence |
| "Just this once" | No exceptions |
| "Linter passed" | Linter ≠ compiler |
| "Agent said success" | Verify independently |
| "I'm tired" | Exhaustion ≠ excuse |
| "Partial check is enough" | Partial proves nothing |
| "Different words so rule doesn't apply" | Spirit over letter |

## Key Patterns

**Tests:**
```
✅ [Run test command] [See: 34/34 pass] "All tests pass"
❌ "Should pass now" / "Looks correct"
```

**Regression tests (TDD Red-Green):**
```
✅ Write → Run (pass) → Revert fix → Run (MUST FAIL) → Restore → Run (pass)
❌ "I've written a regression test" (without red-green verification)
```

**Build:**
```
✅ [Run build] [See: exit 0] "Build passes"
❌ "Linter passed" (linter doesn't check compilation)
```

**Requirements:**
```
✅ Re-read plan → Create checklist → Verify each → Report gaps or completion
❌ "Tests pass, phase complete"
```

**Agent delegation:**
```
✅ Agent reports success → Check VCS diff → Verify changes → Report actual state
❌ Trust agent report
```

## Defects Need Evidence Too

The Iron Law cuts both ways: a claim that something is BROKEN also needs a fresh
measurement. Jumping to "ada bug" costs the team a fix cycle on a non-defect.

- **Reproduce before you report.** A single observed glitch (dropped session, one
timeout, one flash of wrong text) is an observation, not a defect. Re-run the
condition under a timed probe and report the measured outcome — "session held at
60 s, could not reproduce" is a finding; "sesi putus" from one sample is a false
bug report.
- **Read both sides for a data defect.** "Dashboard shows 0" only becomes a bug
when the same scope and time window is quoted from the second view AND from the
source rows (report page = 2 pemeriksaan, DB `exams` = 2 rows, dashboard = 0).
A mismatch between two views is the defect; a lone number is not.
- **Verify identifiers against the real schema before blaming the data.** Run
`SHOW COLUMNS FROM <table>` (MySQL) or `PRAGMA table_info(<table>)` first;
column names in storage rarely match route/JS naming, and a guessed column
(`exam_date` where the column is `tanggal`) throws a stack trace that proves
nothing about the rows.
- **Quantify a visual/UX gap, never adjective it.** Compare the reference and the
live build at the same viewport with counts you can re-measure: `<svg>` nodes,
`box-shadow`, `transition`, gradient, distinct font sizes, dark-mode variants,
paired screenshots. "Terlihat lebih modern" is taste; "0 transition vs 49 hover
states" is a finding a worker can close.
- **Measure layout overflow the way a user causes it, not as a snapshot.** Read
`scrollWidth - clientWidth` **after** `window.scrollTo(9999, 0)` plus two
`requestAnimationFrame`, and also read `window.scrollX`: a single instantaneous
snapshot reports 0 whenever the responsive branch is inactive (a wide table
becomes a card list below its breakpoint, so the overflowing wrapper does not
exist yet) while the live page really pans 150–570 px. Pair the number with the
name/class of the widest element — a bare "0 px" cannot be audited.
- **A claimed 0 you cannot reproduce indicts the harness, not just the code.**
When the producer's evidence file says "overflow 0 px" and your independent
re-measure finds three-digit values, write two findings: the layout defect and
the harness that measured it. Require the raw matrix (screen × width ×
`scrollWidth`/`clientWidth`/delta/`scrollX`/widest element) as the deliverable,
so the gate can rerun the same script instead of trusting prose.
- **Routing a value through the view can hide a live row, and routing a
soft-deleted parent through a detail page can throw.** Probe the detail route of
an archived/soft-deleted owner record: the join returns NULL and the view
dereferences it — a 500 that a list-only sweep never sees. Include archived-owner
IDs in the route matrix, not only the happy-path IDs.

## When To Apply

**ALWAYS before:**
- ANY variation of success/completion claims
- ANY expression of satisfaction
- ANY positive statement about work state
- Committing, PR creation, task completion
- Moving to next task
- Delegating to agents

**Rule applies to:**
- Exact phrases
- Paraphrases and synonyms
- Implications of success
- ANY communication suggesting completion/correctness
