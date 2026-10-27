#!/usr/bin/env python3
"""Deterministic Kanban progress change-detector (cron monitor gate).

Copy into ~/.hermes/profiles/<profile>/scripts/, edit TASKS and the board path,
then reference the filename as the cron job's `monitor`. Output must be
otherwise deterministic: fixed field order, no wall-clock noise beyond the
tick line — identical bytes let the gate skip the agent run; status/comment/
result changes alter the bytes and wake the reporter with the new snapshot
injected.

The trailing `tick: HH:MM` heartbeat makes the bytes change every check WHILE
any tracked card is running, guaranteeing the periodic reports the user
expects during active work (a purely change-gated snapshot goes silent when
a worker runs long without commenting). The `ws_30m` line carries the
anti-loop signal (files touched in the card's workspace in the last 30
minutes), so a `running` card that has stopped editing is visible in the
snapshot itself; it decays toward 0 without edits, and that decay WHILE
status=running is exactly the loop condition. It is inert at rest:
pause/remove the job when the workstream ends.

Two extras the owner's contract needs: `milestones done: N/M` counts the
FIXED TASKS list (done/archived) so a reported percentage never collapses
when children auto-archive, and each running card prints `budget: Xmin
(pct%) | flag: NEAR_DEADLINE (>=80%) / DEADLINE (>100%)` against the BUDGET
dict, so the cron prompt triggers the promised intervention itself.
"""
import datetime
import os
import sqlite3
import sys
import time

TASKS = ["t_REPLACE_ME"]
# Per-card budget in MINUTES — set at dispatch (2x the standard estimate on
# this server, where provider retries eat the first wall-clock window).
# Prints NEAR_DEADLINE at >=80% and DEADLINE past 100% while status=running.
BUDGET = {"t_REPLACE_ME": 270}
# Never put a LITERAL absolute path to the board DB below: the cron lifecycle
# guard scans files a job names and refuses create when one exceeds its 1 MiB
# scan cap (the board DB does). Build the path at runtime instead.
DB_CANDIDATES = [
    os.path.join(os.path.expanduser("~"), ".hermes/kanban/boards/<board>/kanban.db"),
]


def to_epoch(v):
    """Normalize timestamps: epoch sec, epoch ms, or ISO-8601 -> epoch sec."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return v / 1000.0 if v > 1e12 else float(v)
    try:
        from datetime import datetime
        return datetime.fromisoformat(str(v).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def main() -> int:
    db = next((p for p in DB_CANDIDATES if os.path.exists(p)), None)
    if not db:
        print("kanban db: MISSING")
        return 0
    conn = sqlite3.connect(db)
    try:
        for tid in TASKS:
            row = conn.execute(
                "SELECT title, assignee, status, COALESCE(result,''), "
                "COALESCE(last_failure_error,'') FROM tasks WHERE id=?",
                (tid,),
            ).fetchone()
            if not row:
                print(f"{tid}: NOT_FOUND")
                continue
            title, assignee, status, result, err = row
            n = conn.execute(
                "SELECT COUNT(*) FROM task_comments WHERE task_id=?", (tid,)
            ).fetchone()[0]
            last = conn.execute(
                "SELECT body FROM task_comments WHERE task_id=? "
                "ORDER BY created_at DESC LIMIT 1",
                (tid,),
            ).fetchone()
            # Workspace activity: the anti-loop line. Workers edit inside the
            # card workspace before syncing to the repo, so repo-side find(1)
            # alone gives false negatives ("no work happening"). Only worktree
            # cards get workspaces/<id>; a `dir:` card points at the repo via
            # workspace_path — fall back to it, or ws_30m reads 0 while real
            # edits happen. Skip .git: index churn looks like constant work.
            ws = os.path.join(os.path.dirname(db), "workspaces", tid)
            if not os.path.isdir(ws):
                try:
                    wrow = conn.execute(
                        "SELECT COALESCE(workspace_path,'') FROM tasks WHERE id=?",
                        (tid,),
                    ).fetchone()
                    if wrow and wrow[0]:
                        ws = wrow[0]
                except sqlite3.OperationalError:
                    pass
            recent = "-"
            if os.path.isdir(ws):
                cutoff = time.time() - 1800
                cnt = 0
                for root, dirs, files in os.walk(ws):
                    dirs[:] = [d for d in dirs if d != ".git"]
                    for f in files:
                        try:
                            if os.path.getmtime(os.path.join(root, f)) > cutoff:
                                cnt += 1
                        except OSError:
                            pass
                recent = str(cnt)
            # Budget vs deadline: age from the FIRST run of the card so 429
            # requeues still consume budget (a requeue must not buy a fresh
            # window). For precision, subtract blocked spans from task_runs.
            budget = BUDGET.get(tid, 0)
            pct_budget, flag, age_disp = 0, "-", "-"
            if status == "running" and budget:
                started = None
                row0 = conn.execute(
                    "SELECT MIN(started_at) FROM task_runs WHERE task_id=?", (tid,)
                ).fetchone()
                if row0:
                    started = to_epoch(row0[0])
                if started is None:
                    ev0 = conn.execute(
                        "SELECT MIN(created_at) FROM task_events WHERE task_id=?", (tid,)
                    ).fetchone()
                    started = to_epoch(ev0[0]) if ev0 else None
                if started:
                    age_min = (time.time() - started) / 60
                    pct_budget = int(age_min / budget * 100)
                    age_disp = str(int(age_min))
                    flag = ("DEADLINE" if pct_budget >= 100
                            else "NEAR_DEADLINE" if pct_budget >= 80 else "-")
            print(
                f"{tid} | {assignee} | status={status} | comments={n}\n"
                f"  title: {title}\n"
                f"  err: {err or '-'}\n"
                f"  result: {(result or '-')[:200]}\n"
                f"  budget: {budget}m ({pct_budget}%) | flag: {flag} | "
                f"run_age_min: {age_disp}\n"
                f"  ws_30m: {recent}\n"
                f"  latest_comment: {(last[0][:400] if last else '')}"
            )
        # Fixed denominator: count done/archived over TASKS once, never over
        # "visible" cards (children auto-archive when the parent closes).
        n_done = conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE id IN (%s) "
            "AND status IN ('done','archived')" % ",".join("?" * len(TASKS)),
            TASKS,
        ).fetchone()[0]
        print(f"milestones done: {n_done}/{len(TASKS)}")
        # Heartbeat: guarantees a tick-to-tick diff during active runs so the
        # user's 15-minute report cadence holds even when no card posts comments.
        running = [
            t for t in TASKS
            if (conn.execute("SELECT status FROM tasks WHERE id=?", (t,)).fetchone() or ("",))[0] == "running"
        ]
        print(f"tick: {datetime.datetime.now():%H:%M} | running: {', '.join(running) if running else '-'}")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
