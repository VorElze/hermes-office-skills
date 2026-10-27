---
name: state-divergence-diagnosis
description: "Use when two views of state disagree; trace each pipeline."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [debugging, state-sync, data-flow, frontend, root-cause]
    related_skills: [systematic-debugging, dogfood]
---

# State Divergence Diagnosis

## Overview

Diagnose why two displays of supposedly-shared state disagree (a dashboard vs its source of truth, a status board vs live presence, a list vs a detail view). The failure mode this skill prevents: assuming a shared live state exists when each view actually has its own pipeline — then "fixing" a symptom while the structural cause remains.

Work from pipelines, not from the visible symptom. Separate what you verified in code from what you hypothesize.

## When to Use

- User reports "screen A shows X but screen B shows Y" for the same entity
- Status appears stale, reverted, or reverted-then-corrected after edits
- Two panels that should mirror each other drift apart

## Procedure

Execute in order; each step narrows the hypothesis space before the next.

### 1. State the symptom precisely

Classify first: is the mismatch **persistent** (always wrong, never self-corrects) or **intermittent** (resolves after refresh/wait)? If unclear, observe across a refresh cycle before reading code — this single fact splits the cause space in half (see step 7).

### 2. Trace each view to its source independently

For EACH view, answer: where does its data come from — live runtime, persisted store, API snapshot, cache, derived state? Do not assume the two sources are the same. Write both down; two views fed by different origins are structurally unable to agree without an explicit sync path.

Use `search_files` for the view's data-access entry points, then `read_file` the derivation/mapping functions to the render call.

### 3. Locate every sync path and record its DIRECTION

Find the code that copies or derives state between the two sources. Sync is usually one-way; a missing reverse path means edits on the other side never propagate — that absence is the root cause, not a bug to patch per-symptom. Confirm no reverse path exists before theorizing about data corruption.

### 4. Compare identifier shapes at every lookup

IDs are routinely transformed across boundaries: namespaced prefixes, composite keys parsed into components, case or trim differences. Check that both sides of every lookup compare the same shape. A failed match that hits an early-return guard (`if (!match) return`) **silently skips** the sync for those records with no error logged — check ID shape before assuming the sync code ran.

### 5. Compare refresh cadence and triggers

Different polling intervals, or event-driven vs interval-driven updates, produce transient mismatch. Ask: does this mismatch ever resolve on its own?

### 6. Check overwrite precedence

Find which side wins on conflict. An automatic derivation that unconditionally re-derives on every cycle will clobber a manual edit made through the other view — the edit appears to "not stick."

### 7. Classify, rank, and report

- **Persistent mismatch** → structural: missing/broken sync path or identifier mismatch (steps 3–4).
- **Intermittent mismatch** → timing: align intervals or move both views to a shared trigger (step 5).
- **Manual edits revert** → overwrite precedence (step 6).

Rank hypotheses by which pipeline link is absent or broken. Present each with `file:line` evidence and an explicit label: **verified** (read in code) vs **assumption** (plausible, needs runtime check). Recommend one concrete verification step (repro command, log point, or probe) before suggesting any architecture change.

## Pitfalls

- **Never assume the state is shared.** Two views can have wholly independent sources; the shared-state model is a hypothesis to test in step 2, not a given — assuming it makes a missing sync path invisible.
- **A silently-skipped sync looks identical to a wrong sync.** Lookup guards early-return without logging when IDs don't match, so "the sync ran and produced bad data" and "the sync never ran for this record" are indistinguishable at the symptom — verify ID shape (step 4) before debugging sync logic.
- **Don't call plausible causes "root cause."** Several pipeline links can each explain the symptom; presenting them as confirmed misleads whoever implements the fix. Label verified vs assumed and give a verification step.
- **Don't fix the display when the sync is one-way.** Patching per-view symptoms (adding a refresh, forcing a re-render) treats a structural gap as a timing bug and the mismatch returns under different conditions.

## Reference

- `references/pipeline-audit.md` — the audit table template and persistent/intermittent decision table for step 7.
