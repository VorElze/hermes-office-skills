---
name: release-gate-scan
version: 1.0.0
description: Verify spec/content deliverables with numeric gates.
author: office
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [planning, specs, verification, kanban, gates]
    related_skills: [measurable-acceptance-criteria]
---

# Release Gate Scan

Distilled from <PROYEK> M1 (Oct 2026), where the coordinator needed proof, not prose: every "complete" claim had to survive one numeric scan before the card could close.

## When to Use

- A spec/doc task defines gates (file counts, minimum entries, marker consistency).
- Closing a milestone where a coordinator will re-verify independently.
- Don't use for: code tasks with real test suites — use those instead.

## Procedure

1. Count deliverables with `search_files(target='files', path=...)` or a terminal `ls | wc -l`; compare to the required minimum. Completion: actual >= required, number reported.
2. Count in-document entries (routes, tables, sections) with one `search_files` regex over the file, e.g. `^## [0-9]+\. \`` for numbered sections or `^\| P[0-9]+ \|` for sitemap rows. Completion: count >= gate threshold.
3. Verify no empty file: `find <dirs> -name '*.md' -size 0` must return 0.
4. Scan for stray non-target-script characters (CJK/fullwidth/soft-hyphen) with `search_files` pattern `[\x{4e00}-\x{9fff}\x{3000}-\x{303f}\x{ff00}-\x{ffef}\x{00ad}]`; patch every hit until count = 0. AI drafts accumulate these silently.
5. Verify marker consistency: every draft file contains `[DRAF-REVIEW]`; every hard fact is `[PLACEHOLDER: ...]`; zero invented names/dates/contacts (grep specific words like founder names to prove absence).
6. Commit locally per batch (never push/merge in gated tasks), then post one comment with a table: gate -> required -> measured -> status.

## Pitfalls

- `execute_code` may be blocked in some kanban workers; use `search_files` regex directly.
- `patch`/`write_file` calls fail with 'path required' if the path field is omitted — always include it.
- Operator note distinction: budget (report every <=15 min, e.g. 120m estimate) is NOT the same as kanban max-runtime cap; report the budget, not the cap.
- Untracked files at repo root (owner's plan doc, zip) may be untracked deliberately — do not add them in your spec commit without instruction.

## Verification

- The final comment contains a numeric row per gate, derived from tool output, not memory.
- Zero empty files, zero stray-character hits, all marker counts shown.