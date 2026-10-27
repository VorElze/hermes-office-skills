# Card health probe — jalan, maju, atau macet?

Recipe for answering "progres kartu X sudah sampai mana? adakah maju dan tidak
stuck?". Run the rungs in order. Each rung answers a DIFFERENT question — do
not collapse "alive" into "advancing", which is the error that turns a healthy
report into a false stall (or a false all-clear).

## Rung 0 — overview, seconds

```bash
date '+%Y-%m-%d %H:%M:%S %Z'          # fix your clock reference first
hermes kanban list --status running
hermes kanban list --status blocked
```

`list` is paginated and partial — a card absent from it is not proof of
deletion. Confirm against the DB.

## Rung 1 — the card row, and which of its columns LIE

```bash
sqlite3 ~/.hermes/kanban/boards/<board>/kanban.db \
  "SELECT status,assignee,current_run_id,consecutive_failures,
          last_failure_error,started_at,max_runtime_seconds,
          last_heartbeat_at,worker_pid
   FROM tasks WHERE id='<id>';"
```

Read these as history, never as current state:

| Column | Why it misleads |
|---|---|
| `last_failure_error` | persists verbatim after a successful recovery |
| `consecutive_failures` | not reset the moment the next run turns healthy |
| `started_at` | timestamp of the FIRST run; wall-clock since then includes blocked/queued idle and is not consumed budget |
| `completed_at` | survives requeue on some paths |

Current truth lives in the newest `task_runs` row and the heartbeat stream.
Quote a stale error column and you announce a failure that already resolved.

## Rung 2 — run history: this is where "was it stuck?" gets answered

```sql
SELECT id,status,started_at,ended_at,error
FROM task_runs WHERE task_id='<id>' ORDER BY id DESC LIMIT 8;
```

A run-status sequence across ids (`rate_limited`, `crashed`, `crashed`, then
`running` with `ended_at NULL`) is the whole story in one read: it names the
failure window, its cause text, and the exact moment of recovery. A card that
is healthy NOW may have crashed repeatedly an hour ago — say so, with the run
ids, rather than reporting a flat "berjalan normal". The current run's age is
`now - started_at` of the NEWEST row only; compare it to
`max_runtime_seconds` for budget headroom.

## Rung 3 — liveness: process and heartbeat cadence

```bash
ps -p <worker_pid> -o pid,ppid,etime,stat,cmd --no-headers
```

`etime` should be at least as long as the current run's elapsed time — a
process younger than the run means it is a respawn, not the run you are
reading. Then read heartbeat AGES AND GAPS from `task_events`:

```sql
SELECT created_at FROM task_events
WHERE task_id='<id>' AND kind='heartbeat' ORDER BY rowid DESC LIMIT 10;
```

Judge the gap distribution (steady ~60–100s = healthy), not merely "the last
one was recent". A single recent heartbeat next to widening gaps is decay.

## Rung 4 — advancement: the only rung that proves PROGRESS

Heartbeat proves the process is alive and doing *something*. Advancement is
proven by a fresh artifact scoped to the CURRENT run's window:

```bash
find <project_dir> -type f -newermt '<current run start time>' \
  -not -path '*/node_modules/*' -not -path '*/.git/*' \
  -printf '%TY-%Tm-%Td %TH:%TM  %p\n' | sort | tail -30
```

Then map the newest files to a KNOWN defect or acceptance criterion (the last
gate report, the previous review's findings). A new script plus a regenerated
asset that targets a defect named in the prior gate = **maju**. Unmapped file
churn = **activity**; report it as activity and say the acceptance mapping is
missing. Never translate file count or byte growth into a completion
percentage.

Distinguish the classes explicitly in the answer:

| Evidence | Claim you may make |
|---|---|
| heartbeat recent + process alive | hidup |
| artifact in run window mapped to a defect | maju |
| artifact present, no acceptance mapping | aktif, kemajuan belum terukur |
| no artifact + no process + widening gaps | macet — reclaim/steer |

## Rung 5 — failure texture since the recovery

```bash
grep -c '429' <profile>/logs/errors.log      # or the provider's signature
tail -20 <profile>/logs/errors.log
```

A zero count across the current run's window is what makes "clean since the
recovery" a measured claim instead of a hope.

## Fallback when `state.db` yields nothing

The usual liveness metric — message-count growth in the profile's `state.db` —
is sometimes UNAVAILABLE for a kanban worker profile: its `sessions/` dir may
hold only stale `request_dump_*.json` and no reachable message table, because
the worker's session lives in a different store. Absence of data is NOT a stall
signal. Do not report "no message growth" when you never had a source to
measure. Drop to rungs 3 and 4 (process, heartbeat gaps, workspace mtimes),
which carry the diagnosis on their own, and state plainly which metric was
unavailable.

## Shaping the answer

Lead with the verdict (maju / macet) and the rung-4 evidence, then position
(run id, elapsed vs budget), then the recovery history from rung 2 if there is
one, then what is queued next and why its waiting is correct ordering rather
than a stall. Pair "sudah sampai mana" with what changed since the last report
and what remains — a bare status word does not answer it.
