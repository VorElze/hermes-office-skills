---
name: task-progress-reporting
description: 'Report dispatched worker tasks to the user automatically.'
version: 1.0.0
author: codi
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [kanban, cron, monitoring, reporting, delivery]
---

# Task Progress Reporting

## When to Use

Use as soon as substantive work is dispatched to a worker (Kanban card,
background run) and the user will not babysit the board: set up automated
reports so completion (and failures) reach the user **without them asking**.
Standing user preference — requests like "laporkan kalau sudah selesai tanpa
saya minta" apply to every dispatched task going forward.

## Report format contract (user standing standard)

For this owner, active-project updates are expected every 15 minutes and at
stage transitions. The report must state an evidence-based overall percentage,
which milestone/stage is active, concrete work completed since the prior
update, what remains, and any blocker with its cause and remediation. When the user asks for a lightweight status demonstration, perform a real, bounded smoke check (service state, HTTP response, and a few key asset endpoints) and report those measured results separately from project completion; do not inflate the test into a full QA or imply HTTP 200 proves visual acceptance. Keep
percentages anchored to acceptance evidence; do not imply a fixed milestone
count captures within-stage progress. If progress appears stalled, compare
workspace diff, latest substantive comments, and message growth before saying
so; report a measured stall and the corrective action. The owner explicitly
prefers coordinator-authored, real-time reports over raw status-only monitor
output.

When replacing a raw monitor with a recurring agent report, pause the old job,
create the new job using the exact supported schedule syntax, then
verify the job name, enabled state, next-run timestamp, delivery destination,
and prompt containing the full reporting contract (cron runs without chat
history). Never claim recurring reports are active based only on command exit
status; read the job list. Keep any independent no-agent recovery watchdog
separate from the narrative report job. Before promising 15-minute progress,
verify the job's first actual delivery and inspect its text; an enabled
schedule or a successful create response proves only configuration, not that
the user received a useful report. On an explicit "mana laporanmu?" ask, send
a measured on-demand status NOW — do not defer the answer to the next tick —
and keep the recurring monitor running separately. When the owner quotes an
earlier cron report back, treat that text as history, not evidence: re-read the
board in the same turn before repeating any of its claims — a tick that said
"running" minutes earlier can already be a parked review lane whose respawn
guard blocks every spawn, so answering from the quoted text reports a project
state that no longer exists.

If a performance gate has no fresh measurement after a code change, report the
last measured value with its age and state plainly that no post-change result
exists. A diff proves edits, not improved performance. Require each bounded
optimization round to end with a reproducible benchmark result (duration,
sample count, min/avg, workload/moving-agent count); if the result is still
below the acceptance floor, use the measured profile to choose one next change
rather than listing speculative optimizations. After two measured rounds still
below the floor, stop blind iteration and report the blocker with evidence and
a decision request. Add a stale-result alert to recurring reports, but ensure
it measures the age of the last actual benchmark result, not the age of a
comment or heartbeat.

Every report — 15-minute ticks, stage updates, completion summaries — must be
**rapi (heading/table structure), jelas, terukur (only measured numbers),
solutif (problem + remediation in the same message), detail tapi ringkas. For a short request, keep the response proportionate: lead with the measured outcome and only the minimum context needed; reserve detailed milestone narratives for a genuinely complex handoff or explicit request.**
When something is wrong, state it immediately WITH its fix/next step; never
wait for the user to ask. Quote only numbers present in evidence; label unverified claims as unverified.

When a parent/root task is `done` but a deploy/preflight child remains `blocked`, report the two scopes separately: implementation/package completion is not live release completion. Include the blocked card's current recorded reason and exact remaining gate; do not imply that local QA, ZIP creation, or a successful preview resolves deployment blockers.

For a multi-card report, include each card's measured completion estimate and the overall chain completion separately. Derive estimates from acceptance evidence/diff, not lane status or elapsed time; if only two of four cards are done and one is running, report the verified 2/4 milestone count and label any per-card estimate as not yet measurable rather than inventing precision. State what evidence is missing before calling the chain released. When the owner delegates an entire multi-step chain and asks not to be the one chasing progress, deliver the schedule and the guard TOGETHER at handoff: publish one per-step table (step, scope, budget minutes, estimated completion time) and embed the same budgets in the monitor script as thresholds — at ≥80% of a step's budget emit `NEAR_DEADLINE` (coordinator inspects the card and worker liveness immediately), over 100% emit `DEADLINE` (coordinator intervenes: nudge, or reclaim+dispatch if dead). `templates/kanban_progress_monitor.py` already carries the `BUDGET` dict, the flags, and the `milestones done: N/M` fixed-denominator line — fill them in rather than re-deriving. The escalation then fires on its own at the moment you promised it would, without the owner asking or the coordinator being awake in-session.

**Every tick and every on-demand status answer carries a per-card percentage** — the owner explicitly requests a progress percentage and 15-minute updates during active work. But a % is an ESTIMATE: derive it from evidence (diff of the worker's workspace vs baseline, milestone acceptance criteria, completed/total milestones), never from a worker's self-report or elapsed runtime. State the evidence basis and what remains; distinguish card completion from end-to-end delivery (QA, packaging, upload). Never invent precise percentages such as 90% from a RUNNING status alone. Changed-file count, byte growth, or a new hash proves only ACTIVITY, never completion: a source file growing from 45KB to 51KB means edits happened, not that any acceptance criterion passes — never translate file-level activity into a completion % or a "component finished" claim; map the actual diff to acceptance criteria first, and report activity as activity when the mapping cannot be made. A screenshot likewise proves only what its framing shows: an overview/top-down shot cannot establish desk-level detail (whether a pose is actually sitting, whether a screen is emissive), so it does NOT count as visual-acceptance evidence — require a close-up at the relevant angle before crediting that milestone, and describe a wide shot only as "scene renders" evidence. If evidence cannot support a meaningful percentage, say "belum bisa diukur" and give the verified milestone counts.

**Fix the denominator at dispatch, never over "visible" cards.** Board UIs and naive queries count only non-terminal cards, but children AUTO-ARCHIVE the moment the parent/root closes — so a percentage computed over active cards collapses from 50% to 0% *while all the work is actually done*, and the owner reads it as a regression ("kenapa 0% lagi"). Capture the milestone card-id list once at dispatch and compute every later percentage as `done_or_archived / that fixed list`; when the list is fully terminal, report "selesai" outright instead of a percentage, and say which cards were archived.

The opposite-direction lane-count artifact: a `no_agent` snapshot printing `done/total` over its watched cards reports `0% (0/1 done)` forever while a single `running` card is demonstrably producing (fresh events, `ws_30m` rising) — one non-terminal card yields 0 by construction, and the owner reads it as "no progress" and demands the report be fixed or deleted. In monitor scripts, compute the printed percentage from fixed acceptance MILESTONES (`progress_estimate: 60% (3/5 milestones evidenced) | pending: <items>`) with the pending work named on the same line, never from card statuses; then prove the corrected text by running the script directly AND firing the job manually (`hermes cron run <id>` → `Ran now: succeeded`) — editing the script alone does not change the report the user last received. A % that drops without any card reverting to a non-done status is a counting artifact — check archival before reporting anything alarming. A % identical across two consecutive ticks is a suspicion signal, not a plateau: the worker may be in analysis or visual verification. **Never invent fine-grained percentages from a binary checklist.** If the evidence is only 2/5 criteria passing, report 40% verified criteria (or 'belum terukur' for implementation completion); do not inflate it to 85% because code was written or a page rendered. Label separate denominators explicitly: verified acceptance coverage, implementation estimate, and card lifecycle are different measures. If all code checks pass but an independent review or Kanban completion gate remains open, report the verified gates and state that completion is pending—do not assign a near-done number without weighted criteria fixed in advance. The per-tick evidence is `ws_30m`; confirm on demand with `diff -rq baseline workspace` or inspect recent changed files and the latest substantive worker comment. Explain the active phase and its concrete blocker in the same report, then steer the worker with a bounded, deliverable-shaped next step. Do not repeat a fixed milestone percentage as if it answers “sudah sampai mana”; pair it with what changed since the last report, what remains, and a reliable ETA only when the remaining work has a measured basis. If a prior ETA has slipped, acknowledge it plainly, retract it as unreliable, and give the next checkpoint instead of inventing another duration. When the user sets a hard stop time, explicitly distinguish it from the completion target: the work should finish earlier, with named interim checkpoints and a one-shot guard that performs the stop/report action at the cutoff—not merely remind the coordinator. If a worker is `running` with fresh messages but ZERO
workspace changes for >30 min, it is a request-burning loop — the owner's
called-out fear ("looping tanpa akhir yang hanya buang-buang request") —
steer on the card first, reclaim+dispatch on recurrence, and name the
incident in the report.

- **Intervensi berbasis BUKTI, bukan polling rutin — inilah makna "efisien, tanpa pemborosan request".** Owner melarang "bekerja pemborosan request/token tanpa hasil". Artinya: JANGAN balas tiap laporan dengan ping manual berikutnya. Jadikan jadwal cron (15m) + watchdog no-agent (5m) sebagai SATU-SATUNYA sumber pembaruan; koordinator baru bertindak saat menerima sinyal perubahan/STALE/BUDGET-WARN, atau saat owner bertanya. Tiap panggilan tool manual yang tidak menghasilkan keputusan baru = 1 request terbuang. Kalau tidak ada perubahan nyata sejak laporan terakhir, balas 1 baris "tidak ada perubahan sejak <jam>, X% budget tersisa" dan berhenti — jangan isi ulang laporan panjang hanya untuk terlihat sibuk.
- **Turn menghasilkan NOL tool call yang berhasil = kegagalan, bukan rencana.** Saat argumen tool terpotong (`dibatalkan: argumen tidak valid`), jangan narasi ulang niat — turunkan ukuran payload sampai call benar-benar jalan. Disiplin yang terbukti: (1) uji kanal dengan call trivial (`echo ok`), (2) tulis isi panjang ke file, (3) panggil file itu dengan satu baris pendek. Tiga call sukses mengalahkan 5 call identik yang gagal. The user
repeats fleet checks ("periksa semua profile … berikan hasil seperti diatas
tadi") and expects the next audit to MATCH the last one: one table (row =
subject, column = each thing checked, ✅/❌ marks), then short "Detail temuan"
bullets, then a closing "Yang perlu kamu tahu" with an honest `n/N` headline
(e.g. 11/11 OK) + the single most actionable weak point. Every cell must
reflect a live check from that session, never carried-over status.

**Interpret every board lane for the owner.** The owner reads the Kanban UI
alongside the report and asks "kenapa masih ada yang blocked — sampah?" A
status line that names `blocked` without its reason reads as a stuck project.
For each non-running card state WHY it waits (dependency-wait = antre otomatis
buka sendiri saat induk done; needs_input = menunggu keputusan) and mention
superseded cards you archived, so the visible board and the report agree. A
blocked lane the reports never explain becomes a trust question, not a status
question. Extend the same reading to silence: a `done` card whose worker sends
nothing is **tuntas, not macet** — never write a finished card's idle worker
stall/loop language is reserved for a `running` card that stops producing.

**Never label a wave/stage by its worst card.** Writing "W0 masih blocked" when 4 of 5 cards
are `done` reads to the owner as the whole stage being stuck, and the only reply it earns is
"kenapa masih blocked?". Always print the pair (`W0 5/5 done`) and name the single blocked
card with its reason and what releases it; if the block sits on an external service, say so in
the same line plus the substitute you plan to build, so the status never looks like an
unfinished stage. When the owner then orders the substitute ("buat lokal dulu"), go build it in
that turn rather than re-explaining the blocker.
producing.

**Resolve a new block from live evidence, not a previous snapshot or a guess.**
When the owner shows a blocked badge, read the current task row, newest run,
block event/reason, and latest worker comment first; the screenshot may already
be stale, and an earlier `running` report is not current state. Classify the
block kind before acting. For `capability`, test the exact claimed capability
in the worker's execution environment (import/module and real browser launch,
not merely `which` or package metadata), then compare with an existing passing
repo recipe. If the claim is disproven and the coordinator has authority to
resolve the decision, post the measured counter-evidence and a bounded,
file-scoped next step to the card, then unblock. Verify what `unblock` actually
did by rereading DB status/run/events: some versions auto-spawn on unblock, so
an empty subsequent dispatch is not proof of failure and a second dispatch may
race. Confirm the new run id and message growth (or active child process for a
long quiet test) before telling the owner it is running; distinguish a proven
recovery from a configured intention. If the capability really is absent, do
not call the worker wrong or unblock blindly—provide a proven alternate setup
or raise the real blocker. Never turn a worker's honest refusal to claim an
untested acceptance gate into a completion claim.

**Separate elapsed deadline clock from active worker budget.** `MIN(started_at)`
across runs measures wall-clock since the first run, including blocked and
queued intervals; it does not measure active runtime consumed. Label it
"elapsed since first run" and derive an ETA/deadline only from a verified
runtime cap and a stated clock basis. If the task is requeued, report both
cumulative active run time (sum of run intervals where available) and wall-clock
elapsed, or say active budget usage cannot be measured. A past ETA must be
explicitly retracted, not replaced by a new precise estimate from heartbeat or
file mtimes.

**When the owner asks you not to forget a named cron report, verify the exact job rather than making a vague promise.** Match its job ID/name in `cronjob_manage action='list'`, confirm it is enabled and scheduled, then inspect the newest execution's completion and delivery outcome (or the latest report artifact). Explain that the cron itself delivers reports automatically; do not imply you can independently remember or manually relay future outputs unless the system confirms delivery to this conversation. If the latest execution is still running, state that precisely and cite the newest completed/delivered report time; never present a prior report as the current tick. Continue with the existing end-to-end reporting-chain verification below.

**Between delegated checkpoints, self-verify the reporting chain — do not take
"cron active" at face value.** The owner measures the delegation itself ("pastikan
laporan tetap jalan"), so silence is failure even when the workers are healthy.
When schedule + delivery are in doubt, check BOTH ends: the job record
(`enabled`, name) and delivery proof (executions/deliveries store: `status='delivered'`,
timestamps; or the newest output file's mtime). The ticker keeps ticking even
if agent runs or deliveries break, so a heartbeat alone proves nothing — the
delivery row does. One evidence-backed line (", laporan terakhir 05:52:39
delivered") answers faster than a promise, and read the execution durations
before diagnosing gaps: long runs queue the next fires serially, which reads as
a missed cycle but is only backlog draining. Read `Last run`'s error line too:
a `(N failures in a row)` streak means every fire has been erroring while
`Next run` keeps looking healthy — an enabled schedule plus a future `Next run`
proves firing intent, never a successful run; prove a fix with `hermes cron run
<id>` → `Ran now: succeeded` AND the delivered text.

**On-time delivery of the wrong text is still a missed report.** The owner
judges a report by its CONTENT, not its arrival: a cron that fires on schedule,
lands `status='delivered'`, and pushes a few raw status lines cannot fulfill a
promise like "laporan berikutnya berisi keputusan dan persentase" — a monitor
script can only print what its snapshot knows, and it never saw your decision.
Keep two separate checks on every promise: (1) did it fire and reach the chat;
(2) does the text contain what was promised (decision, evidence, percentage,
next step). If the promised content exceeds the monitor's knowledge, send it
yourself as a labeled message at the deadline and let the routine ticker
continue underneath; give generic snapshots a label ("status mentah — laporan
keputusan menyusul") so a thin tick is never read as the promised update.

## Owner notification: kanban notify-subscribe (so the owner never has to ask)

Standing complaint when this is missing: *"harus saya dahulu yang menanyakan."\*
The gateway runs a notifier watcher that DMs the owner on terminal card events
(blocked/completed/crashed) — but ONLY for subscribed cards. The subscription
table (`kanban_notify_subs` in the board DB) ships EMPTY: zero rows = total
silence no matter how healthy the monitors are.

Procedure:

1. Subscribe at card creation/dispatch time, not at incident time:
   `hermes kanban notify-subscribe <id> --platform telegram --chat-id <owner>
   --user-id <owner> --chat-type dm --notifier-profile <profile>
   --delivery-mode notify+wake`. Use the SAME chat/user id as the owner's
   origin DM — a stamped row with the wrong route or notifier profile gets
   dropped by the gateway with only a log warning.
2. `notify+wake` = DM AND wakes the gateway agent to reply with full board
   context; plain `notify` = passive message. Prefer `notify+wake` for blocked
   cards so the owner gets an answer, not just a status line.
3. **Auto-subscribe every `blocked` card from the no-agent watchdog**: loop
   `SELECT id FROM tasks WHERE status='blocked'`, skip ids already in
   `kanban_notify_subs`, `notify-subscribe` the rest. This is the safety net
   for the worst failure mode — a coordinator blocks a card for a takeover,
   switches context, and the card dies silently for hours.
4. **Prove delivery once (E2E), don't trust the row**: fire a terminal event,
   wait ~1–2 watcher ticks, then require `last_ping_event_id` on the
   subscription to equal the newest `task_events.id` for that task.
   `last_ping_event_id=0` after an event = delivery unproven.

Mechanism notes: the notifier watcher is spawned by the gateway itself
(`_PRE_RECONNECT_WATCHERS` in `gateway/run_startup.py`) — there is no daemon
to start. Notifier activity logs at DEBUG, so absence of "kanban notifier"
lines in `gateway.log` proves nothing either way; the ping cursor is the proof.

5. **Prune subscriptions with the cards, or the owner gets replay spam.**
   `notify-subscribe` rows outlive their cards: a finished or archived card
   keeps a row, and its late `gave_up`/`crashed` events — or a replayed
   notification batch — keep pinging the chat long after the work ended, which
   the owner experiences as "bersihkan notifikasi lama yang tidak perlu".
   When a card reaches `done`/`archived`, run `hermes kanban notify-unsubscribe
   <id> --platform telegram --chat-id <owner>` in the same pass. NOTE: the
   unsubscribe command REQUIRES `--platform` and `--chat-id` — without them it
   errors out, so a bare `notify-unsubscribe <id>` silently leaves the row
   behind. Prove the cleanup with `hermes kanban notify-list`: only the
   currently-active card ids may remain.

6. **Treat every Kanban notification as data, not as a state to act on.**
   Notifications arrive late, out of order, and replayed in batches, so the
   same `gave_up`/`blocked`/`crashed` can be announced several times after the
   event already resolved. Before any unblock/dispatch/archive decision, read
   the CURRENT truth from the board DB (`SELECT status, consecutive_failures
   FROM tasks WHERE id=…`, newest row in `task_runs`, latest `task_comments`)
   and confirm it against the notification's text. If the DB already shows the
   card `archived`/`done`, or the failing run id is an OLDER run than the
   current one, reply with one line that it is a replay and take no action —
   acting on a replayed crash kills a healthy in-flight run. Repeated
   identical notifications with no DB change also mean you are answering
   history, not live state: batch-verify once, state that nothing changed, and
   stop replying per replay.

## Procedure

### Pre-development design delegation

For a design-only project, split content architecture/positioning from visual direction/assets when the scopes are distinct, and link the visual card as dependent on the content brief. Put the same project context and acceptance criteria in each card (workers do not share sibling context), specify explicitly that the deliverable is a design specification rather than code, and preserve the real reference assets in a path accessible to the assigned profiles. Before dispatch, verify each assignee can read the referenced files; if not, attach/embed the essential reference content in the card brief rather than reporting it as supplied. Give each card an evidence-shaped output path or final comment requirement, a bounded runtime estimate, and owner notification subscription; after dispatch, verify actual card status/run rather than treating dispatch exit 0 as proof of execution. Report progress only from live evidence, distinguish “running” from substantive deliverable progress, and state when inputs remain unverified. Ask for confirmation before specifying consequential flows whose requirements are ambiguous (e.g. RSVP versus paid registration/QRIS).

0. **Plan the report lifecycle at dispatch, before giving the owner an ETA.** Create or update the persistent monitor script + self-contained cron prompt right when cards are created — never a bare "update coming in 15 minutes" promise backed by nothing. Set a bounded lifetime or completion cleanup, and immediately verify `enabled`, `next_run_at`, `deliver`, and the watched card IDs. A future `next_run_at` is not a delivered report: inspect the first run's output text and delivery evidence, then fix schedule/script/prompt if it failed. The user asking for the promised update is a failure signal — answer with a measured on-demand report in the same turn.

1. **Use the existing monitor template** `templates/kanban_progress_monitor.py`; copy it into the active profile's persistent `scripts/` directory, then set the board and current card IDs. Never store a cron dependency in `cache/scratch/`: age-based pruning can silently remove it while the schedule remains enabled. When a follow-up card joins, update the watched IDs before dispatch — and when the active card set churns (archived + new cards), prefer rewriting the probe as a dynamic discovery (SELECT every non-archived card, evidence-based progress) over chasing IDs: a hard-coded-ID script silently reports the archived card's frozen numbers forever, and the re-pointed cron prompt must be re-verified with one manual fire. Run the script directly and inspect its output before scheduling; verify its SQL against the real DB schema (`.tables`, `PRAGMA table_info`) rather than guessing. Use `ws_30m` plus `state.db` message-count growth over 60–90s to distinguish productive work from a live-but-stalled API call; heartbeat proves process liveness only, not progress.
2. **Create the change-gated job** with the cron tool:
   `action='create', schedule='every 15m', deliver='origin',
   monitor='<name>_monitor.py'`, plus a self-contained prompt:
   - write in Indonesian (the user's language);
   - state the card ids/roles as context (jobs run in a fresh session with no
     chat history);
   - **quote only numbers present in the snapshot/result** — never invent
     progress; distinguish done / running / blocked plainly;
   - for evaluation/comparison tasks, carry the worker's verdicts verbatim in
     an explicit vocabulary (**LULUS / GAGAL / TIDAK TERUKUR** with numbers
     and sample counts) and flag non-paired inputs ("not apple-to-apple") —
     never soften a failed criterion into "belum terbukti";
   - announce when the monitor will be removed once the work completes — BUT
     only if this job is the final gate. When a coordinator session performs
     the final QA/packaging AFTER the worker cards finish, the prompt must
     FORBID self-deletion and completion claims: "never delete this cron;
     when all cards done report 'rantai worker selesai — menunggu QA &
     packaging oleh sesi utama' and keep reporting status as-is." A
     self-retiring monitor goes silent exactly when the owner is still
     waiting for the final deliverable, and a report job cannot know the
     coordinator's audit passed.
   The `monitor` gate makes idle time free: identical bytes skip the agent
   run. With the template's `tick` heartbeat (see Pitfalls), any running card
   changes the bytes each check, so reports arrive at the promised cadence
   while work is active. Do not substitute an ad-hoc event timestamp or comment
   count for this heartbeat: Kanban events may be heartbeats too, so a fresh
   event timestamp alone does not establish worker progress.
3. **While work runs:** one short report per tick (the heartbeat guarantees a
   diff whenever a card is `running`); between workstreams the job is paused
   or removed, so no idle spam. Do not create a second job for the same cards.
   As the FIRST action of a new work round — BEFORE dispatching any card —
   check the standing report job's `enabled` state: a job paused at the end of
   the previous project looks configured while every report silently never
   arrives, and the user then asks why updates stopped. When a round starts
   under such a paused monitor, UPDATE the job (monitor path + prompt context
   to the new card ids) and **`action='resume'` it** — an update alone leaves
   it disabled and the reports silently never arrive. Verify `enabled: true`
   after resuming.
   - **After one missed or late fire, add a one-shot verification guard** at
     the next cycle (T+~20 min past the scheduled time, `--repeat 1`): check
     the artifact exists and is valid (`pdfinfo` Pages > 0, not file size),
     diagnose + re-run the job and prove delivery if it is missing, and
     report only the outcome. The recurring job keeps running; the guard
     retires itself. User-facing schedule promises ("masuk sebelum 07:45")
     deserve this backstop after a single slip. For a deadline YOU state in chat
  mid-session, set the guard when you make the promise, not after it slips:
  the session has no timer of its own and will not wake you at the stated
  time, so a one-shot cron is the only thing that fires it — when only the
  owner can notice the miss, the failure has already reached them.
4. **Completion is event-driven, not timer-driven.** When the Kanban completion
   notification arrives, inspect the final card/report/artifact and send the
   user the completion summary immediately — do NOT wait for the next 15-minute
   cron tick. Note that the dispatcher often PRUNES the card's workspace right
   after `done`: evidence files (screenshots, measurements) are gone even
   though comment summaries survive. Copy any evidence you intend to quote
   into scratch BEFORE the card finishes, or re-render/re-measure it yourself
   during the coordinator audit — never plan a final report on card-workspace
   files you have not re-checked. The periodic monitor is only for interim changes and may be
   paused/removed afterward. Cron's change gate can remain unchanged between
   ticks even when a worker just finished, so it cannot guarantee an immediate
   final report.
5. **On completion or abandonment: remove the job AND its script**
   (`cronjob_manage action='remove'`). The user considers leftover paused
   monitors garbage — pause is only an interim state inside one session, never
   the end state. Then confirm `cronjob_manage list` no longer shows it.

## Delivering files back

- **Delivery gate (user's contract): hold the FINAL deliverable until every
  milestone card is `done` and your own audit passes** — the user evaluates
  only the finished package (they test on their own machine and give the human
  verdict on the final build). Interim ZIPs ship only when the user explicitly
  asks for one. Audit before sending: `unzip -t`, required launch entry present,
  forbidden-content scan, `md5sum` from disk, runtime tests and release gates.
  For a requested *full package*, compare the ZIP manifest against all promised
  deliverables, including final independent-review reports and reproducibility
  builders; do not assume the latest developer ZIP is complete just because its
  checksum and runtime files pass. If any promised artifact is missing, build a
  new version without overwriting prior releases, rerun the archive checks, and
  verify the new entries byte-for-byte against their source files. A reviewer
  report written AFTER the archive was built is by definition not inside it —
  re-check the manifest against final-verdict timestamps, not file counts alone.
  State which milestones are and are NOT inside the package if it is partial.
  See `multi-profile-project-orchestration` for the full gated-delivery workflow.
- Telegram rejects user file uploads over ~20 MB before they reach us (no
  cache entry appears). For inbound large files ask for a public link instead
  and pull it on the server:
  `curl -sSL -o <dest> 'https://drive.google.com/uc?export=download&id=<id>'`,
  then `file -b` to confirm real type (rename `.bin` to the true extension),
  `ffprobe` for media properties.
- **Document/analysis deliverables get the same audit as ZIPs.** Prove
  existence on disk with a `find` scoped to the worker's run window (profile
  homes, project dir, kanban `attachments/`, card workspaces) before
  reporting completion. A completion comment claiming "written to the
  deliverable" with no file at the claimed path is a FAILED deliverable:
  open a follow-up card whose acceptance criteria name the absolute output
  path + a minimum size, and never report success on the comment alone.
- **Check `status:` before injecting mid-task user updates.** A comment
  posted to a `done` card is never read by the finished run, so late input
  (price change, rewritten title) silently goes unprocessed; put the new
  input into a follow-up card's body and acceptance criteria instead. The
  monitor's `latest_comment` will otherwise showcase your own unprocessed
  update as if it were handled.
- **For delegated marketing/design packages, inspect the actual rendered outputs yourself before reporting delivery.** Check image dimensions and file sizes from disk, open every final PNG/mockup with vision, and verify text is legible, uncut, consistent with the real product facts, and free of overlap. Worker vision-pass summaries are claims, not independent QA. Cross-check quantities across assets: distinguish interior count from total pages (e.g. "20 halaman isi + 1 cover" / "21 halaman total"), and fix ambiguous badges before delivery. If editing an asset after the worker's QA, rerender and inspect the changed output again; update the worker/card summary if its old verdict no longer describes the final artifact.
- Send deliverables with `MEDIA:<absolute path>` in the reply. **Standing user
  rule: NEVER send a `file:///` or bare path link for any requested document
  (PDF/doc/etc.) — the link does not download in Telegram and the user calls
  it an error. Always attach the actual file via MEDIA:.** If MEDIA is
  rejected (>20 MB), fall back to Google Drive link + tell the user why.
  This applies to MEDIA deliverables too — a rendered video is not exempt
  because it is "media" rather than a document. Plan for the ceiling: a
  60 s 1280x720 30 fps H.264 clip encodes to roughly 25 MB at crf 23, which
  sits just over the ~20 MB attachment limit, so expect to upload to Drive
  and send the link (plus the MEDIA attempt and the reason it was refused).
  If the owner wants a chat-attachment-sized video, re-encode tighter
  (crf 26-28, or `preset veryfast`) instead of shipping a file that cannot
  cross the wire.
- **Recurring/office files are archived to Google Drive AS WELL as sent to
  chat.** For scheduled reports, build the Drive folder tree first to mirror
  the schedule (e.g. root → `Harian/<hari> <jam>` / `Mingguan/Minggu-N`),
  upload there with `gws drive upload --parent <id>`, verify the file landed
  via a parent-id search, THEN reply with the local MEDIA attachment + the
  folder link. Match the user's file naming to their stated convention
  (`Harian_<tanggal>_<jam>.pdf`, week number = calendar weeks containing the
  first Monday).
- **Never `rsync --delete` into a live worker/test workspace.** A test server
  running there (e.g. `php -S`) serves that directory with its own install
  config, DB, and router; a broad sync deletes unexcluded files and breaks the
  server mid-QA behind a misleading HTTP 500. Compare read-only first
  (`diff -rq` with explicit exclusions), then copy ONLY files intentionally
  changed. Exclude `config.php`, `uploads/`, DB files, and server router files
  by default; verify server health after any controlled overlay.
- **An artifact edited AFTER it was uploaded is out of sync — resync before
  reporting done.** Adding a file to an already-uploaded ZIP (or regenerating a
  PDF) changes size/content but NOT the Drive copy, leaving the owner with a
  stale download. Re-upload the changed artifact, trash the superseded copy
  (default trash = reversible; only files uploaded in THIS task — never touch
  older versions outside scope), then re-list the parent folder so exactly one
  current version of each deliverable remains. Report the new file id, not the
  original one.
- **A recurring job that exports through a web form needs a proven recipe, not a memory of one session.** Before trusting a scheduled browser job (site login → form → download), drive the whole path ONCE interactively and write the recipe to a file the prompt references (`Baca: <path>`): exact form field values, the submit selector, and the output-verification command. Form quirks are invisible until the job runs unattended — a styled radio ignores `.click()` on the input itself and stays on the default (silently exporting the wrong format), so click its `<label>`, force `checked` + dispatch `change`, and VERIFY the state string (`csv:false, pdf:true`) BEFORE submitting. Verify downloads with `pdfinfo` (`Pages: N`), never by file size or `file` output. Also re-login if the session expired; a redirect back to `/login` is the tell. Job prompts run fresh with no chat history — every selector and pitfall must live in the recipe file, not in the conversation.
- **Keep every unattended-job dependency outside auto-pruned scratch/cache.** Store recipes, folder mappings, and delivery rules in a persistent profile skill or scripts directory; have the cron prompt point to that canonical file and verify the path/readability before enabling or editing the schedule. Scratch is for disposable artifacts only: age-based pruning can remove a recipe while leaving the cron active, causing a valid-looking run to produce no deliverable.
- **Separate production failure from delivery-procedure failure.** When an export fails, verify the exact run output and artifact first; then probe the source endpoint independently (bounded HTTP requests plus a control endpoint). Report measured HTTP/connectivity results and whether the blocker is origin service or credentials/UI. Do not label a site/network outage from one failed browser attempt, and do not claim delivery until the artifact is validated and found in the target Drive folder.
- **Do not schedule a retry guard until its recovery path is real and bounded.** A guard must check for the required artifact and Drive presence, invoke a supported retry command without killing its own run, limit attempts, and escalate with the exact error if still blocked. Test one guard execution and confirm it can actually perform the recovery; a cron prompt that merely promises to retry, lacks the necessary tool, or repeats a long job on every tick is not automatic recovery.
- **A new project gets a NEW Drive folder; never reuse or reorder the previous
  project's folder.** The user keeps the old app's folder (e.g. the OSIS
  election archive, its backups, data CSVs) untouched as history — create the
  sibling folder for the new deliverable and upload there. Moving/renaming
  files in the old folder requires explicit approval.

- **Full-mandate overnight pipeline (one job, gate + execute).** When the user
  delegates final results entirely ("serahkan ke kamu... tanpa konfirmasi"),
  answer in one line that no further approval is needed, then create ONE cron
  job whose monitor snapshots the work state and whose prompt branches: gate
  `NO` → brief evaluation only (never act prematurely); gate `YES` → run the
  whole verify pipeline (audit → backup → execute → read-back verify → final
  report), with rollback-on-suspicion and an honest failure report if the
  target is unreachable. Mandate removes the approval loop, NOT the safety
  gates — backups and verification still run in full. Prove the job fires once
  manually (`action='run'`) before going quiet; a blanket "dijalankan otomatis"
  claim with zero fire history is unverified.
- **Rate-limited card ≠ failed work.** A run exiting 75 returns the card to
  `ready`; confirm guard cooldown with `hermes kanban dispatch --dry-run`
  (`Guarded (rate_limit_cooldown)`) instead of recreating the card or
  reporting the work as failed.

- **Separate the reporting job from the recovery job — and prove recovery
  runs.** A report cron that only PRINTS `ALERT ... -> reclaim+dispatch` never
  executes the fix, so cards sit stalled for hours while reports keep arriving
  (the owner then reads "stuck" despite a healthy-looking monitor). Keep reports
  as change-gated agent jobs; put the ladder itself in a second `no_agent`
  cron whose script actually runs reclaim→`dispatch --json` every few minutes,
  stdout silent when healthy. Verify the recovery path fires (`hermes cron run
  <id>` once, expect `Ran now: succeeded`) rather than trusting it exists.
- **Test every dependency transition explicitly — `todo` is not claimable.**
  The dispatcher only claims `ready`; a card auto-released from `needs_input`
  back to `todo` (or left `todo` after an initial-block) idles until someone
  calls `hermes kanban promote <id>`. After any parent flips `done`, check each
  child's `status`/`block_kind` in the board DB: promote only when ALL parents
  are `done` (promoting a child with a pending parent defeats the ordering and
  races siblings), and only after answering the input that caused the block.
  An unverified "auto-promote" claim in a report is wrong until you have read
  the child's status yourself.
- **Deadline + context handoff beats waiting for the worker to finish
  exploring.** Give a running audit card a hard deadline and a
  deliverable-shaped ask (final summary with file:line + numbers, then
  `complete`), and when it passes, push its findings into the NEXT card's
  thread as a scoped execution brief: exact file:line, the chosen fix, the
  verification command, an explicit out-of-scope list (no re-audit, no build,
  no restart), and a deadline. Workers do not read sibling threads, and a card
  without its predecessor's numbers re-derives them from scratch — that is
  where requests get burned.
- **Stop an analysis-looping worker with measured evidence, not a status
  complaint.** Count the worker's tool calls over a window (reads vs
  writes/commands from `state.db`) and steer with that number: "N reads, M
  commands in 15 min — stop widening the search, use the evidence already
  gathered, deliver by <time>." One such steer ended a stalled audit within
  minutes; generic "hurry up" comments did not.
- **Take a missed-deadline worker's files over only after taking the worker
  off them.** When a deadline you gave the owner passes with zero measurable
  output — no source/test file changed in the window (`find src -newermt
  '<deadline>'`, empty `git status --short`) — another steer is wasted:
  reclaim the run (`hermes kanban reclaim <id>`), then `hermes kanban block
  <id> --kind <transient> '<takeover notice: who is editing now, why, and do
  not dispatch>'`, and implement in that same pass. The block is the point:
  it stops the dispatcher respawning a run onto files you are editing, and a
  silent two-writer diff loses work with no error anywhere. Hold the block
  Hold the block until your own verification passes, then release it as the record of that outcome. Two hardening steps, because the block is not self-proving: (a) re-read the target file immediately BEFORE each patch — a concurrent run may have rewritten it since your last read, and a patch against stale content duplicates functions and breaks comment openers; (b) after any concurrent-edit window run a syntax check plus a duplicate-symbol grep (`node --check`, count of `function <name>` occurrences) — a two-writer merge corrupts silently with no error surfaced anywhere. Confirm the worker is gone with `ps` AFTER one dispatcher tick: a respawn appearing minutes later means the hold did not stick — kill it again before touching the files.
  outcome. (`reclaim+dispatch` is the rung BELOW this — right only before the
  deadline, when one more cycle can still deliver.)
- **Don't claim efficiency as a guarantee.** "No blockage / fully automatic"
  is unverified until a transition has actually fired in front of you; report
  measured history ("audit done at 10:24, child auto-promoted, now running")
  and keep unproven mechanisms labelled as configured-but-not-yet-observed.
- **An all-empty `dispatch --json` does not prove the card failed to spawn.**
  The spawn can land between the JSON snapshot and your read (or on the next
  60s tick), so `spawned: []` + `promoted: 0` while a card shows `ready` must
  be verified against the board DB before concluding "dispatch didn't work":
  `sqlite3 <board.db> "SELECT status FROM tasks WHERE id='<id>'"` plus the
  newest `spawned`/`claimed`/`heartbeat` rows in `task_events`. Re-dispatching
  on the empty JSON alone races the worker already starting and burns a
  request — status check first; dispatch again only if status is still `ready`
  with no `spawned` event after one full tick.

## Pitfalls

- **A card flipping to `blocked`/`needs_input` is an IMMEDIATE incident, not an item for the next report tick.** The owner's complaint when this fails is "kenapa kamu tidak melaporkan error ini ke saya? apa saya harus selalu cek sendiri?" — so on detection: report the block NOW (status, `block_kind`, last error verbatim), then resolve in the same pass: comment the decision within mandate → `unblock` → dispatch → confirm the spawn (run id + first heartbeat). Four failure modes kept one block invisible for 39+ minutes: (1) the report script still watched the PREVIOUS project's card-id list, so the new card never entered its query — re-bind watched IDs in the SAME edit that creates the card; (2) the report cron was stale/paused from the last round — check `enabled` + `Last run` at round start and fire it once manually; (3) the watchdog alerted only stale-running, never blocked — it must print `BLOCKED ALERT <id> kind=... detail=...` while still REFUSING to auto-unblock `needs_input`/auth blocks (the decision stays with the coordinator); (4) cron said `succeeded` while its output covered the old scope — never claim delivery from an exit status: read the generated text AND confirm it reached the owner's chat. Worker-side prevention: never block for a decision inside your own mandate; if input is genuinely required, make the blocking comment self-serve (exact question + options + the command/screenshot path the coordinator can run) so resolution takes minutes instead of a discovery cycle. Coordinator-side belt:
subscribe the owner to the card (notify-subscribe section above) BEFORE
switching context, so a takeover block that outlives its session still pings
the owner instead of rotting silently.

- **Before fixing code behind a FAIL, classify the assertion: stale test vs
  real regression.** Design intentionally changed since the test was written
  (new palette, renamed/moved class) makes the test fail forever while the
  product is correct — re-run against the changed intent and update the
  assertion; don't "fix" working code to satisfy a legacy expectation.
  Classify four ways with evidence: (a) assertion encodes the OLD design →
  update the test; (b) product code deviates from current spec → fix the
  code; (c) test targets the wrong artifact (staging workspace, wrong path,
  dead server) → retarget the test; (d) suite shares a harness/DB with
  another suite in the same run → RE-RUN IT ALONE first; a failure that
  vanishes when isolated is cross-suite interference, not a regression, and
  must be reported as exactly that class. Name the class in the report so a FAIL
 is never silently swallowed — and never call the suite green by editing
 an assertion until it passes.
 - **A suite that fails at SETUP (missing helper/harness file, missing fixture)
 is not a product FAIL — classify it before dispatching a fix.** When the
 failure names a path outside the repo (e.g. a `require`d setup script living
 in a profile's pruned `cache/scratch/`), the defect is infrastructure: rebuild
 the helper INSIDE the repo (`tests/`, `scripts/`) so it survives pruning, then
 re-run. Filing it as a product bug burns a worker dispatch and misleads the
 owner. Rule of thumb: grep the suite for every external path it loads and
 verify each exists from a fresh shell before trusting any red/green result.
- **Never go silent after a failed or hanging tool call — the silence is what the user notices.** A cell timeout, blocked command, or interrupted turn must still produce a short reply: what failed, that you are checking it, then continue in the next turn. The user cannot distinguish "agent crashed" from "tool hung" when nothing arrives, and asks "kenapa kamu diam saja" within minutes — one honest blocker line beats total silence every time. Report first, retry second. Same for the provider-recovery boilerplate ("Your request was not processed. Send it again…"): it must never stand as the final answer to a direct user question — retry the answer once, and if the rejection repeats, send the honest status line anyway.  The user pinging your name after a run of these reads as "you are ignoring me", which is worse than admitting the provider is recovering.
- **Chat messages get truncated when they exceed the platform cap — chunk long
  reports, and announce before a long silent verification chain.** Telegram
  caps one message at ~4096 chars, so a full milestone report sent as a single
  block cuts off mid-sentence and the user reports "chat terpotong" (with no
  typing indicator, so it also reads as a hang). Split a long report into
  coherent parts — headline/measured outcome FIRST, then the detail — rather
  than one giant dump. Before running a long chain of checks, send one short
  visible line naming what you are verifying, so the wait is never mistaken
  for silence or a crash. A user who asks "kenapa chat terpotong" is giving a
  delivery-format correction, not a content one: the facts were fine, the
  packaging failed.
- **Prove a recovery before reporting it — heartbeat is the weakest proof.** A card can show `running` + heartbeat while the worker is hung on an API call. Check: (1) `count(messages)` in profile `state.db` over 60–90s; (2) worker child processes (`ps --ppid`); (3) project-workspace mtimes; (4) latest substantive card comment. Normalize time values before age comparisons (`v/1000 if v > 1e12 else v`). Full ordered recipe — which board-DB columns lie, how to read run history as a recovery story, and why a fresh artifact in the current run's window is the ONLY proof of advancement — in `references/card-health-probe.md`. Two rules from it that belong here: a worker profile's `state.db` may hold no reachable message table (only stale `request_dump_*.json`), so "no message growth" is NOT a stall signal when no source was measurable — drop to process + heartbeat-gap + workspace-mtime checks and name the missing metric; and map the newest artifacts to a defect named in the prior gate before calling activity "progress" (unmapped churn is activity, never a percentage). No message growth, no executing child, and no workspace change across repeated checks is a stall signal; do not kill a quiet worker if a child is actively running a long test. Before any kill/reclaim, check the card's current run, failure reason, and whether a new run was already spawned; after recovery, verify fresh message/API-call growth beyond the previous failure window before claiming it is healthy. Report the model that actually served from logs, not only config.

- **Separate provider response health from worker protocol health.** A provider `HTTP 200` is not enough: inspect `stop_reason`, content blocks, and non-empty text using a probe with adequate `max_tokens`; a tiny output budget can produce an empty text block with `stop_reason=max_tokens`, which is not evidence of a provider outage. A malformed or wrong-route probe is likewise not a diagnosis. Conversely, repeated worker exits without `kanban_complete`/`block`/`request_review` may be protocol failures even when API calls succeed. Use the card's `task_runs.error` and worker logs to distinguish provider errors, empty/truncated responses, and missing terminal Kanban calls; do not label quota exhaustion from a generic 'No reply' without current per-key evidence.

- **A background-process exit notification identifies ONE attempt — resolve it to a session id before reporting anything.** The gateway notifies on exit for every backgrounded job, including an early attempt that was already superseded. When such a notification arrives mid-task, read the session id in the notification and check THAT session's status via `process_manage action='log'`; do not report its exit code as the state of the work. A failure notification for an earlier launch (e.g. `Cannot find module` because the script file was written by a rejected command) is history, while the re-launched job runs fine — calling that a failure sends the owner a false alarm mid-render. Conversely, a `completed normally` notification for one attempt does not mean the DELIVERABLE is ready: a job that exits 0 can have produced a truncated artifact (a muxer that consumed only the frames present on disk yields a valid-looking 1-second file). Gate every "done" claim on the artifact itself — frame count on disk, then the container's own metadata (duration/frame count/resolution) — not on the exit code.
- **Answer "is it running in the background?" with the session id and the measured progress line.** The owner asks this to know whether to wait or intervene, so quote the live log (`rendered N/1800 … eta=…s`), name the background session id, and state plainly what is still outstanding (e.g. the encode has not started). "Ya, berjalan di background" without the count and the session id is not actionable.
- **A watchdog is not safe merely because it exits 0.** For a custom recovery guard, verify the DB URI/schema, run it directly once while healthy (expect exit 0 and no output), and trigger/verify its anomaly path in a controlled test before relying on it. Use a minimum cooldown and require repeated independent stall signals (message growth + workspace activity/children) before reclaiming, so one quiet tick does not kill an in-flight test. Keep watchdog and narrative-report jobs separate: no-agent guard prints only on a measured action/anomaly; the report job owns cadence and explanatory context. Verify registration, schedule, destination, and an actual fire; configured intentions are not delivery proof.
- **Run any reused/custom monitor script twice before trusting it.** First run must produce the expected snapshot; the second run must be silent when unchanged (or change only its deliberate tick while work is running). A typo'd table/column can crash every fire while the job record still looks active, and an untested custom script can report nonsense; inspect schema, fix, then trigger and verify an actual delivery—not just an enabled schedule.
- **A healthy worker still generating no output for one tick is not yet
incident-worthy.** Reviewer/long-test phases are legitimately quiet; a single
non-delivery for a `running` card is "fase wajar, belum ada output" — verify
then keep watching. Escalate only on repeat (e.g. 2+ consecutive non-deliveries
or no output over ~30 min), because premature reclaim+dispatch restarts the
the run and throws away hours of in-flight work.
- **Never trust `hermes kanban list` output as a complete board, and never
guess a board DB schema.** The list CLI shows only the first ~20 cards — a
card "missing" from it is pagination, not deletion — and `show --json` nests
its payload under a `task` key, so a flat read of `status` yields nothing.
For status that matters, query the board DB directly (`SELECT status FROM
tasks WHERE id=?`) or parse `d['task']`; board DBs live at
`~/.hermes/kanban/boards/<board>/kanban.db` (glob `~/.hermes/kanban/**/*.db`
when unsure which board); before any hand-written query, list
real names first (`sqlite3 <db> ".tables"`, `PRAGMA table_info(...)`) —
table/column names differ between boards and a guessed name silently returns
empty data, which then flows into a confidently wrong report. For a busy
board, use Python `sqlite3.connect('<uri>?mode=ro', uri=True, timeout=5)`;
the sqlite3 CLI has no `-timeout` flag (its busy timeout is the `.timeout`
dot-command), and a raw read against a live board can throw `database is
locked` mid-script.
- **Match the gate to the user's reporting contract
  change-gated monitor to a user who asked for a fixed cadence.** Standing
  rule for this user: a report every 15 minutes DURING active work, plus an
  immediate handoff at each stage completion. Output with only status/comment
  bytes goes silent whenever a worker runs a long stretch without posting
  comments (verification runs especially), and the user then asks why reports
  stopped. Append a heartbeat line (`tick: %H:%M | running: <ids>`) so the
  bytes change every tick while any card is `running`. When a stage completes,
  inspect its artifact/verdict and dispatch the next already-approved gated
  stage immediately; never wait for the user to ask for status or re-authorize
  routine next steps. Each report: Indonesian, concise-but-complete, with
  labeled status, measured evidence, any blocker + root cause, and next action;
  separate verified facts from estimates. The heartbeat is harmless at rest
  because the job is paused/removed at completion anyway — silence costs
  nothing between workstreams. Keep output otherwise deterministic (no other
  wall-clock fields, fixed field order) so the snapshot stays diffable.
- **Never nest a `python3 -c` with parentheses inside a shell loop built
  from a heredoc.** A bash `for` loop that shells out to an inline `python3 -c
  "..."` quote poorly: the `(` of the call is eaten by the outer quoting, the
  checker raises `SyntaxError: '(' was never closed`, and the loop spins
  printing errors instead of monitoring — while the agent reads the healthy
  lines it DID print as success. Prefer one pure-Python loop (heredoc `<<'PY'`
  with `time.sleep`), or write the checker to a script file first; if a
  monitor loop must run longer than the tool's cell timeout, run it via
  `terminal(background=True)` and read it with `process_manage`, not a
  foreground cell — a 300s cell timeout kills the kernel and loses the state.
- **After creating or editing a monitor, prove delivery once:** fire
  `cronjob_manage action='run'` and inspect the async completion. Confirm it
  is a real agent run, not `no_change (agent run suppressed)`. A fire may
  execute after the monitor source changes but before its hash refreshes; if
  suppressed, run once more and confirm delivery. Do not tell the user a
  manual report was sent until its completion contains actual report text.
- **Cron output must survive a shell that eats `$` in f-strings.** Building a
  monitor/prompt with Python f-strings containing `\u`/LaTeX/`$` sequences
  corrupts the command before it reaches the shell — build such strings as
  raw literals or concatenation, never f-strings. Same class of bug: a `curl
  -w` template written as `{{http_code}}` inside an f-string prints the
  literal braces instead of the status code, which silently "proves" a 200
  You never received. Print the status code from a non-f-string call.
  - **Never hand-type a long prompt into a tool_call payload.** A multi-paragraph
    cron prompt written inline into `cronjob_manage` `arguments` repeatedly fails
    JSON parsing at a few hundred chars; write the prompt to a file first
    (`write_file`), then create/update from the shell — `hermes cron create
    '<cron>' "$(cat <file>)" --name ... --deliver origin --repeat N` and `hermes
    cron edit <id> --prompt "$(cat <file>)"`. Keep tool payloads to
    name/schedule/flags. The file stays the single source of the prompt text, so
    later edits cannot drift from what the job actually runs, and re-editing
    needs no re-quoting.
- **Distinguish the change-gated progress monitor from a no_agent watchdog.**
  A progress monitor (`monitor=` gate, agent prompt) reports PERIODIC UPDATES
  and must heartbeat while work runs. A healing watchdog (`no_agent=true`,
  `script=` only) runs the ladder unattended and must stay SILENT when healthy
  — any stdout is delivered to the user, so `print` only on real action or
  anomaly. A single ALL-DONE sentinel line (board has zero non-done cards) is
  compatible with that silence: print it only in that state, so the watchdog
  doubles as the "workstream finished" trigger without a second job. Do not add
  in watchdog output.
  - **Percentages must have one explicit denominator across every report.** Before answering “tadi X%?”, grep the archived reports for the milestone (`grep -rn '<milestone>' ~/.hermes/profiles/<profile>/cron/output/<job_id>/*.md`), then re-measure current workspace + acceptance evidence in the SAME turn. Keep separate fields for (a) per-card estimate and (b) whole-project milestone completion; never reuse the same percentage for different denominators. Derive per-card progress from weighted acceptance criteria with a fixed denominator (e.g. 1 of 4 AC verified = 25% AC coverage, not an unsupported 35% code-completion claim); code volume/diff size proves activity, not proportional completion. Count a criterion only with its test/result evidence, not a worker's self-report. If past reports conflict, acknowledge which number had the wrong scope or stale snapshot, explain the basis, and correct it without defending it. Re-run the worktree diff and latest GREEN comments immediately before quoting any percentage; a snapshot from minutes earlier may predate new edits. **Scope-qualify a milestone percentage at the moment you write it**: when code is complete but the review gate is not, write the full phrase ("M4: 100% kode, review belum final") rather than a bare "M4 100%" — the owner later cross-checks earlier reports ("bukankah tadi M4 sudah 100%?"), and a bare number whose scope was stated only in your head reads as a contradiction or a walk-back even when both reports were accurate.
- **A card status in an owner-supplied screenshot is HISTORY — reconcile it with
  the DB in the SAME turn and name the discrepancy.** The owner posts their own
  Kanban UI capture as the question's premise; if you answer from the DB without
  addressing the image, your answer contradicts what they are looking at and
  reads as you ignoring their evidence. Read the live row first, then open with
  the reconciliation ("screenshot shows `ready`, DB sekarang `running` —
  screenshot sudah tidak mutakhir"), then report the measured state. Also check
  whether the disagreement is a rendering lag vs a real revert before calling
  the image stale.
- **`tasks.last_failure_error` persists AFTER a successful recovery — never
  report it as a current failure.** The field keeps the last requeue note (e.g.
  a rate-limit exit) while the card is healthy and mid-run; a status report
  built from the row's error column alone announces a failure that already
  resolved. Read the CURRENT run's `status` in `task_runs` (newest id) and the
  latest comment before quoting any error field; a stale error plus `running`
  current run = recovered, report the recovery, not the old error.
- **A `done` card's self-reported gates are a claim, not proof the gates ran at THAT commit.** Workers may run gates mid-session and commit afterward, or quote numbers from an earlier state, so a "5/5 gerbang lulus" comment can describe code that never got built. Before merging or calling a milestone green: (1) grep the worker log for the gate commands (`typecheck|vitest|build`) and compare their timestamps against the final commit time; (2) re-run the cheap gates yourself at HEAD — forbidden-dep grep + typecheck + targeted tests take seconds; full build only after those pass. Run each gate as its own command capturing each exit code: a `set -e` verification script dies at the first non-zero gate while its partial output still reads like a full pass, so the later gates silently never ran. Gates never run at the commit = reject the handoff, do not merge.
- **A REVISE verdict returns the SAME card to `ready`, and reclaim deadlines must honor `max_runtime_seconds`.** Remediation cycle: reset the card in place (`status='ready'`, clear `last_failure_error`/`consecutive_failures`/`completed_at`/`worker_pid`/`current_run_id`), comment the verdict as fix instructions, then `dispatch` — this preserves the worktree, branch, and prior commit and avoids a duplicate card for the fix round. A kick/watchdog script with a hard-coded fallback deadline silently reclaims long cards every cycle (measured: one card cut every ~47 min, losing in-flight context each time); budget reclaim at card `max_runtime − 300 s`, using the fallback only for cards that declare no runtime.
- **Never let a watchdog label a transient probe failure as `auth-error`.** The
    owner reads every watchdog line as a broken worker, so one timed-out probe
    must not escalate: retry the probe, and if it still fails on the network
    layer report it as a transient probe failure (or stay silent) — reserve
    `auth-error` for a 401/403 or credentials verified as suppressed. Prove the
    fix by running the script once (`0 masalah`, exit 0) before trusting its next
    scheduled fire.
- **Watchdog cadence comes from the schedule, not from sleep loops.** The user's
  "probe every hour" contract is one cron job (`schedule='every hour'`), never
  a background terminal loop or polling script that outlives the project.
  Remove both monitor and watchdog when the workstream ends. Ready-made hook:
  `templates/worker_hang_watchdog.py` — a silent-when-healthy no_agent guard
  that kills+respawns hung workers (liveness metric, not heartbeat) and scrubs
  dead credential-pool entries; copy it into the profile scripts dir, set
  CARD/PROFILE, register with `no_agent=true, deliver='local', every 5m`.
- **Heartbeat must be inside the monitor's normal output path.** Do not put
  it after an unconditional `return`/inside a skipped branch. Run the script
  twice with an interval and verify the final tick line differs while a card
  is running; stable snapshots otherwise let change-gating suppress the report.
- **Recurring report jobs use POSITIONAL schedule and prompt arguments in the `hermes cron` CLI.** `cron create ... --every 15m` fails with `unrecognized arguments: --every`, and there is no `--prompt` flag either (`--prompt` → `unrecognized arguments`); the working form is `hermes -p <profile> cron create '<cron expr or 15m>' '<prompt>' --name ... --deliver origin --repeat N`. `--monitor-script` / `--script` take a BARE FILENAME resolved inside the profile's `scripts/` dir — an absolute path is rejected (`Script path must be relative to .../scripts/. ... use just the filename`). A shell pipeline may hide create errors, so verify with `hermes cron list` that the name, `Next run`, and `Deliver` are correct. Then fire the job once manually: `Ran now: failed` whose error line is `Telegram send failed: Timed out` is a DELIVERY failure, not a script failure — the finished report text already sits under `cron/output/<id>/<ts>.md`; re-fire once, and only report delivery after a `succeeded` fire whose text you actually read.
- **A cron create can be refused by the lifecycle guard for an UNEXECUTED file the prompt/script merely NAMES.** A literal absolute path to a non-scannable file (the board `kanban.db`, >1 MiB) yields `Blocked: the lifecycle guard could not scan this cron job or referenced script: ... is larger than the scan cap` even though the scan found no gateway-lifecycle command — build such paths at runtime (`os.path.join(os.path.expanduser("~"), ".hermes/kanban/...")` in the monitor script, prose without a hard absolute literal in the prompt) and re-run the SAME create; no other change is needed.
- **Inspect job state with `cronjob_manage action='list'`** (`last_run_at`, `last_status`, `monitor_state.last_output_hash`, `enabled`). The `hermes cron` CLI is a different subsystem and reports "No cron execution attempts recorded" for plugin jobs — don't read that as "the job never ran".
- **Cron jobs cannot see this conversation**; a prompt that says "report on
  the work like before" fails. Everything needed must be in the prompt.
- After removing a job, also delete its monitor script if nothing else uses it
  — the user explicitly wants no dead artifacts.
- **A recurring job with `--repeat N` dies silently when the cap hits** (`state:
  completed`, `enabled: false`, `next_run_at: null`) and simply stops reporting —
  the user then asks "kenapa laporan berhenti". Create long-lived report jobs with
  a large cap (`--repeat 5000`) or no cap. A `completed` recurring job cannot be
  revived (`resume`/`update_job` both refuse terminal state) — the fix is
  `hermes cron remove <id>` then recreate from the saved prompt (prompt text lives
  in jobs.json / the prompt file, nothing is lost). Detect it via
  `cronjob_manage action='list'`: `enabled:false` + `state:'completed'` on a job
  the user still expects reports from. `hermes cron list` HIDES completed jobs
  while they still sit in `jobs.json` — when an expected job vanishes from the
  CLI listing, audit the file (or `cronjob_manage action='list'`) instead of
  concluding it was deleted.
- **`last_run_at: null` does not prove a job never ran.** A fire still executing
  records `last_dispatch`/`fire_claim` in `jobs.json` while `last_run_at` stays
  null — the job is IN FLIGHT (typical right after a busy gateway restart).
  Poll until `last_run_at` lands instead of re-firing; a duplicate fire sends
  the user a second copy of the report.
- **Never edit `jobs.json` directly to resume or rename a job.** The gateway holds `next_run_at` in memory, so a hand-edited job can sit `enabled: true` while its `next_run_at` is stuck in the past: overdue for hours, never firing, and CLI `pause`/`resume` do NOT recalculate the schedule. Proven repair: force a schedule rewrite through the CLI (`hermes cron edit <id> --schedule "every Nm"`, or remove + recreate), then verify `Next run` is in the FUTURE from `hermes -p <profile> cron list`, then fire once (`hermes cron run <id>`) and read the completion before claiming delivery. Always re-read `Next run` after any job mutation; `enabled: true` alone proves nothing about firing.

- **Cron jobs VANISH from the active store after a gateway restart — re-verify the list, don't trust yesterday's inventory.** Observed: monitor + watchdog scripts still on disk and working when run by hand, but their job records absent from `hermes cron list` AND from every `jobs.json` (profile store `~/.hermes/profiles/<p>/cron/jobs.json`, global/default `~/.hermes/cron/jobs.json`) — the schedule silently stops firing. After any restart, re-list and re-create missing jobs; a script that runs fine manually proves nothing about its schedule. `hermes cron show` does NOT exist (only init/boards/create/list/ls/edit/remove/pause/resume/run) — inspect state with `cronjob_manage action='list'` or read the stores directly. The `hermes cron list` CLI renders the PROFILE store, so a job you created from another profile is invisible there.
- **Wave-scoped card titles make percentage reporting survive the next round.** Prefix every card with its wave (`<PROYEK>-R3/FIX-A: ...`) and have the monitor derive the active wave with a regex (`<PROYEK>-R(\d+)` → `max(waves)`), then compute the percentage over THAT wave's cards only. Otherwise a finished wave's 20 done cards inflate the new wave to ~85% before any work starts. Two denominators, two lists: filter `done`/`archived` out of what the report PRINTS (the owner wants only live work) but compute the percentage from the UNFILTERED list (otherwise the % collapses to 0% exactly when the round finishes — the same artifact as the auto-archive rule above).
- **Extract the worker's own progress number from its comments, not from elapsed time.** Have each card's body require comments in the exact form `Progres NN% — <apa yang selesai>` (the worker posts them per phase), then the monitor regexes the newest comment for `Progres\s+(\d+)%`. This gives a real per-card % with a fixed denominator and zero extra requests; fall back to budget-consumed only when no progress comment exists yet. Label the two sources differently (`kerja=NN%` vs the budget line) so a budget-derived guess is never read as measured work.
- **`hermes kanban comment` takes the body as a POSITIONAL argument — `--body` does not exist and silently falls through to the top-level `hermes` usage text.** Correct form: `hermes kanban --board <b> comment <task_id> "<text>" --author <profile>`. Anything that prints the general `usage: hermes [...]` banner means your flag was wrong, not that the comment failed.
- **Skills are set at CREATE time (`--skill <name>`, repeatable); `hermes kanban edit` cannot change them.** For an already-created card that must run the design gate, post the skill list + gate invocation steps as a card COMMENT (workers read their thread before acting) instead of recreating the card and losing its parent chain.
