---
name: hermes-profile-hygiene
description: "Use when cleaning finished Kanban cards and dead jobs."
version: 1.0.0
author: codi
license: MIT
metadata:
  hermes:
    tags: [kanban, cleanup, hygiene, cron, cache, maintenance]
    related_skills: [kanban-rate-limit-resilience, codi-team-dispatch]
---

# Hermes profile hygiene

Clear finished cards and dead artifacts from a profile so the board and job
list show only live work — without touching anything a worker is actively
using. The goal is a board where every visible card is a real next task.

## When to Use

- "Bersihkan sampah / kartu yang sudah terpakai / perintah menumpuk" — the
  board is buried in done cards and the cron list confuses new work.
- After a project closes, before onboarding the next one.
- The operator reports difficulty finding current work among old results.

## Procedure

### 1. Inventory and classify before deleting anything

Batch these reads in one turn:

```bash
hermes kanban boards list       # counts per status per board
hermes kanban list              # card lines: ✓ done, ◻ todo, ● running
hermes cron list --all          # every job including paused/disabled
```

Classify each artifact into: **live** (leave), **finished** (archive/prune),
**orphan** (candidate for deletion after verification in step 4). Report the
inventory before mutating — the operator should see the same numbers you do.

### 2. Cards: archive done cards, never purge

- Only `✓ done` cards qualify. `todo`/`running`/`blocked` cards are live work
  even when their titles look obsolete — a decomposer chain (parent + auto-
  children) is one unit; if any member is active, leave the whole chain.
- Confirm liveness before touching non-done cards: `hermes kanban show <id>`
  and look for recent heartbeat/claim timestamps (minutes-old = running now).
- Archive in one batch, ids parsed from the `✓` lines of `hermes kanban list`:

```bash
hermes kanban archive t_id1 t_id2 ...   # hides from board, history kept
hermes kanban gc                        # prunes events/logs past retention
```

- `archive` keeps comments and run history readable via `hermes kanban show`
  — that is the point: out of sight, still auditable. `archive --rm` is
  irreversible; only run it when the operator explicitly asks for purge.
- `gc` clears task events and worker logs (30-day defaults), not cards.

### 3. Services and routes: decommission as a unit

A project service usually has three coupling points; all three must be handled
in one pass or it resurrects or leaves error paths:

```bash
systemctl --user stop <svc>.service && systemctl --user disable <svc>.service
ss -ltnp | grep ':<port>'          # confirm the listener is gone
a2dissite <vhost> && apache2ctl configtest && systemctl reload apache2  # drop reverse-proxy route
```
- Verify each with a read-back (`is-active` → `inactive`, `is-enabled` →
  `disabled`, no listener, vhost symlink absent) and state the distinction:
  *stopped/disabled* (recoverable, survives reboot) vs *deleted* (source
  removed) — report exactly which was done, never blur them.
- Leaving the proxy vhost in place after the backend dies is what turns a
  deliberate shutdown into recurring 502s for anyone hitting the URL.
- Preserve source/config backups when decommissioning unless deletion was
  explicitly requested; removing test scripts, probe scripts, and session
  login files belonging to the project is part of the pass.

### 4. Cron: justify every job; pause instead of delete when unsure

- Walk `hermes cron list --all` and give each job a one-line reason it still
  earns its keep (standing absensi reports, credential watchdogs, guards).
  Jobs with no reason and no owner project are deletion candidates.
- Prefer `hermes cron pause <id>` over `hermes cron remove <id>`: pause stops
  the quota burn but stays reversible for a revision round; remove is for
  jobs whose project is verifiably closed AND the operator approved.
- Edit jobs through the CLI (`hermes cron edit`), never by hand-editing
  `cron/jobs.json` under a live gateway.

### 5. Scripts and backups: verify orphanhood on multiple signals

A filename that looks stale proves nothing. A script is an orphan only when
ALL hold:

1. no reference in `cron/jobs.json` (grep the live config, not logs/history),
2. no reference in `config.yaml` or other live config,
3. no running process (`pgrep -af <name>` returns nothing).

Then delete. Same rule for `jobs.json.bak-*`: keep the newest backup, drop
older ones — one recovery point is enough.

### 6. Caches and logs

- `cache/scratch/*`: files idle ≥24h are auto-pruned by the scheduled prune
  cycle — do not force-delete merely because they are old; act only under
  disk pressure or for obviously dead artifacts (checked with `ls -la`).
- `cache/terminal-output/*`: session command logs, safe to delete past a few
  days.
- Never truncate active runtime logs (`agent.log`, `gateway.log`,
  `errors.log`) — they are the diagnostic trail for live incidents.

### 7. Verify and report

Re-run `hermes kanban boards list` and `hermes cron list --all`; the board
should show only live cards and the cron list only justified jobs. Report
with measured numbers: cards archived, files deleted, MB freed, jobs
removed/paused — plus an explicit "what was NOT touched and why" line for
anything live. This matches the operator's standing expectation of evidence
over assertions.

## Pitfalls

- **Don't judge card liveness by status or title alone** — a `running` card
  with heartbeats seconds ago is live even if its task sounds finished, and
  a `todo` card can be a child of an active chain. Check `show` timestamps.
- **Don't `archive --rm` during routine cleanup** — purge destroys the audit
  trail (comments, run evidence) the operator uses to reconstruct decisions;
  archive achieves the clutter goal with zero data loss.
- **Don't delete a script on filename intuition** — the reference may live in
  a cron job or a live card; grep the live configs and pgrep first.
- **Don't treat `gc` reporting 0 rows as "nothing to clean"** — gc covers
  events/logs only; card clutter is a separate `archive` action.
- **Don't delete cron jobs just because they are quiet** — quiet standing
  jobs (weekly guards, hourly watchdogs) may fire rarely by design; classify
  by ownership, not activity.
- **Don't skip the verify pass** — archiving in batch can leave stragglers
  (cards that changed status mid-run), and the final counts are the proof
  the operator asked for.
