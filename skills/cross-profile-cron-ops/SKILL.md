---
name: cross-profile-cron-ops
description: Use when inspecting cron jobs of another Hermes profile.
version: 1.0.0
author: codi
license: MIT
metadata:
  hermes:
    tags: [hermes, cron, cross-profile, scheduling, verification]
    related_skills: [hermes-agent, hermes-profile-hygiene]
---

# Cross-Profile Cron Operations

## When to Use

Use when the user asks about, needs verifying, or wants edits to scheduled
jobs that belong to a DIFFERENT Hermes profile than this session's active one
(e.g. codi checking amanda's Threads posting slots) — "is X scheduled
right", "will it fire tomorrow", "alert me if this fails".

Cron jobs are per-profile: the `cronjob` tool only sees the ACTIVE profile's
jobs, and every other profile's schedules live under its own `$HERMES_HOME`.

## Procedure

1. Locate the target profile home: `ls ~/.hermes/profiles/`
2. List its jobs (always list before acting — never guess job IDs):
   `HERMES_HOME=~/.hermes/profiles/<name> hermes cron list`
3. Edit via the same env prefix, e.g. alert-on-failure wiring:
   `HERMES_HOME=... hermes cron edit <job_id> --failure-deliver telegram:<chat_id>`
   Check `hermes cron --help` for verbs — there is **no** `hermes cron show`;
   use `list`, or step 4 for per-job detail.
4. Verify the change by reading `<home>/cron/jobs.json` directly (Python/jq).
   The CLI echoes the requested values back, but jobs.json is the ground
   truth the scheduler actually loads.

## Verifikasi "laporan cron tidak masuk" (user-facing send failures)

When the user says a scheduled report never arrived, job `last_status=ok`
and `delivery_outcome=delivered` do NOT prove the user received anything —
prove each artifact before answering. Per-job ground truth lives in the
profile's cron DBs (CLI verbs like `hermes cron show/logs` do NOT exist):

```bash
H=~/.hermes/profiles/<profile>/cron
# 1. execution + timing + delivery verdict (recent runs):
sqlite3 -header -line $H/executions.db "SELECT id,status,claimed_at,finished_at,error,delivery_outcome FROM executions WHERE job_id='<id>' ORDER BY claimed_at DESC LIMIT 3"
# 2. delivery payload (execution_id = id from step 1):
sqlite3 -header -line $H/deliveries.db "SELECT status,length(content) AS len,created_at,finished_at FROM deliveries WHERE execution_id='<id>'"
# 3. send-side proof in the log:
grep -a 'delivered to' ~/.hermes/profiles/<profile>/logs/agent.log | tail
```

Interpretation:
- `len=0` in deliveries.db is NORMAL — content is not stored there; it is not
  evidence of an empty reply.
- `cron/output/<job_id>/<ts>.md` contains ONLY the prompt echo (job metadata),
  never the agent's answer — don't mistake it for a missing report.
- `delivered ... message_id=N` in agent.log proves the send call returned
  success, not that the user saw it — but combined with the run timeline it
  usually means the user asked BEFORE the run finished (multi-minute runs
  deliver after the user's "mana laporan?" message). Quote run-finish time
  vs ask time; if the send really did fail, fall back to
  `chat-silence-diagnosis` step 5.
- Artifacts (PDF produced, Drive uploaded) can be healthy even when the user
  never saw a chat message — verify outputs independently via the filesystem
  and Drive API before declaring failure.

## Pitfalls

- Using the in-session `cronjob` tool against another profile returns a
  generic "job not found" — it never hints that the job lives elsewhere. A
  not-found error on a job ID you just saw in a profile's `cron list` means
  wrong profile context, not a missing job.
- `--failure-deliver` grammar is `platform:chat_id` (e.g.
  `telegram:<CHAT_ID_ANDA>`); `local` suppresses failure notices entirely.
- Job list `Next run` timestamps are profile-local and already tz-aware;
  don't re-convert them against your own `date` output.

Threads posting slots owned by profile amanda (job IDs, scripts, queue,
failure modes).
