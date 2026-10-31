# Card progress diagnostics: workspaces, read-loops, dispatch slots, gate verdicts

Use when a card says `running` but progress is unproven, when a dispatch
reports nothing spawned, or when a chain reports finished while its gate said
otherwise. The board DB is authoritative; stdout of the worker is not.

## 1. Where the work actually is

```bash
sqlite3 "file:<board>/kanban.db?mode=ro" \
  "select id,status,assignee,workspace_kind,workspace_path,branch_name,worker_pid,current_run_id,max_runtime_seconds,consecutive_failures,block_kind from tasks where id='<id>'"
```

- `workspace_kind=worktree` → the worker edits `<board>/workspaces/<task_id>/repo`
  on `branch_name`. Measuring `git status` in the project checkout reports
  "nothing changed" while real edits pile up on the card branch.
- `workspace_kind=dir` → edits land in place in the project path; backups matter
  because there is no branch to roll back to.
- Evidence of progress = commit + artifact (size, mtime) in that path + non-zero
  write calls in the profile's `state.db`. Status, PID, and heartbeat prove none
  of it.

Tool mix over the last N minutes for the card's assignee profile:

```bash
sqlite3 "file:~/.hermes/profiles/<profile>/state.db?mode=ro" \
  "select coalesce(tool_name,'(msg)'),count(*) from messages where timestamp>=<epoch> group by 1 order by 2 desc"
```

## 2. Read-loop signature

| Signal | Healthy | Looping |
|---|---|---|
| writes (`write_file`/`patch`) | several per 5 min | 0 |
| messages per 30 min | tens | hundreds |
| one read tool repeated | no | `skill_view` dozens of times |
| run outcome | `completed` with `kanban_complete` | `crashed` at `rc=0`, no completion |
| context growth | stable | ~120k tokens → compaction → turn budget gone |

Corroborate with the profile log line `Blocked skill_view: returned the same
result 5 times` and with `find . -newermt '-8 minutes'` in the card workspace.

Remedy ladder: comment a bounded next step → `reclaim` + kill the PID →
`reassign` to a profile with a write record → verify write counts after 4–5 min.
Do not dispatch the loop-prone profile a fourth time.

## 3. Dispatch slots and orphans

- `dispatch --dry-run` says 1, real `dispatch` says `Spawned: 0`:
  orphaned `kanban_worker_client` processes from finished cards are holding the
  `--max` slot. Kill them by explicit PID, then dispatch.
- `pkill -f '<pattern>'` where the pattern text appears in your own command
  line kills the shell running it (exit -15). Use `ps -eo pid,args | awk` to
  collect PIDs, then `kill -TERM <pid> ...`.
- A watcher that restarts an orchestrator must re-apply the same slot hygiene,
  otherwise it retries into a phantom queue.

## 4. Gate verdict chain (FIX → RE-AUDIT)

When a gate card finishes with REVISE/BLOCKED, the release is not done even
though its status is `done`:

1. Write the FIX body to a scratch file: each finding, the measured BEFORE
   number, the required AFTER number, and the exact evidence file path.
2. `hermes kanban --board <b> create "<FIX title>" --assignee <producer> --parent <gate-id> \
   --body-file <scratch> --workspace worktree:<repo> --priority 10 \
   --max-runtime 5400 --skill request-token-efficiency --completion-contract local-only --json`
   (`--priority` takes an integer; a non-numeric value silently fails the create.
   `--skill` gives the card a skill allowlist — use it to starve a read-loop.
   `--initial-status blocked` parks a child until its parent is done.)
3. Create the RE-AUDIT card for `code-analyst`, `--parent <fix-id>`,
   `--initial-status blocked`, body = "measure it yourself, verdict in the
   first line, no code edits".
4. Watcher loop: FIX `done` → `unblock` RE-AUDIT + comment + dispatch, then
   stop when RE-AUDIT is `done` or `blocked`, or when a deadline passes and the
   card is escalated to the owner.
5. Confirm the chain ids in the board DB — the create JSON id and the `parent`
   edge — before dispatching.

Percentage accounting while this runs: the gate card keeps weight 0, FIX and
RE-AUDIT each carry their own weight, and the report labels the gate
`done (REVISE)` rather than crediting it.
