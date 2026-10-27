# Pipeline Audit: Divergent Views

Fill one row per view before forming hypotheses. Columns 1–4 are read from code; column 5 is observed at runtime.

## Audit table

| # | Question | View A (e.g. office floor) | View B (e.g. Kanban) |
|---|----------|---------------------------|----------------------|
| 1 | Render entry point (file:line) | | |
| 2 | Data source (live runtime / store / API / cache / derived) | | |
| 3 | Refresh trigger (event / interval Ns / on-edit only) | | |
| 4 | Entity ID shape at lookup (namespaced? composite? parsed?) | | |
| 5 | Persistent or intermittent? | | |

## Sync paths (between A and B)

One row per code path that copies or derives state across the boundary:

| Direction (A→B, B→A, none) | Function (file:line) | ID comparison used | Early-return guard? |
|----------------------------|----------------------|--------------------|---------------------|
| | | | |

- A row with **no reverse direction** → edits on that side never propagate (root cause: structural).
- An ID comparison that mixes shapes (e.g. `remote:<id>` vs `<id>`) → guard silently skips sync for those records.

## Decision table (step 7)

| Symptom class | Most likely link | First verification step |
|---------------|------------------|-------------------------|
| Persistent, no self-correction | Missing sync path (step 3) or ID mismatch (step 4) | Search for the reverse-direction function; print both ID shapes at the lookup |
| Intermittent, self-corrects after refresh | Divergent refresh cadence (step 5) | Align both to one trigger, or log timestamps of last update per view |
| Manual edit reverts automatically | Overwrite precedence (step 6) | Find the unconditional re-derivation cycle; check which side wins |
| Only some entities mis-sync | Identifier transformation (step 4) | Collect mismatched ID pairs; check prefix/parse/case differences |

## Report format

For each hypothesis:

```
[VERIFIED|ASSUMPTION] <claim>
Evidence: file:line (code) or observation (runtime)
Verification step: <one repro command, log point, or probe>
```

Never merge VERIFIED and ASSUMPTION claims into one conclusion. Recommend exactly one architecture change only after at least one hypothesis is VERIFIED.
