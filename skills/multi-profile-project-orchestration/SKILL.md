---
name: multi-profile-project-orchestration
description: Use when coordinating multi-profile project work.
version: 1.0.0
author: koordinator
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [kanban, orchestration, multi-agent, project-planning]
---

# Multi-Profile Project Orchestration

Coordinate planners, implementers, and reviewers through durable Kanban cards. Card bodies, comments, artifacts, and dependencies are the handoff protocol for WORK. For one-off policy/format directives that must reach a persona (e.g. instructing a worker's standing report format), a one-shot CLI chat works: `hermes -p <profile> chat -q '<msg>'` runs under that profile's own home and returns its reply — use it when the card channel would distort the message, but keep actual task execution on cards.

## When to Use

- A user asks for a planning meeting, multi-worker project, implementation followed by review, or recurring progress updates.
- Several profiles need to work on one shared deliverable.

Don't use for a single self-contained task that one worker can finish without a handoff.

## Procedure

1. **Inspect before acting.** Read the current board, task bodies, statuses, dependencies, latest comments, and existing artifacts. Reuse or update an existing card when its scope already matches; never create a duplicate before checking.
2. **Resolve the brief and preflight tools.** Capture the user's goal, constraints, inputs, output language, and acceptance criteria. Ask for missing user-only facts (such as test observations, credentials, their personal experience) rather than inventing them — and only for those: for every other open decision, adopt the documented recommendation (planner's proposed order, default tooling) and act without pausing for approval; **exception — decisions that change what "pass" means** (a metric definition, an acceptance threshold, a scope cut) belong to the user: present the options with ONE recommended choice and let them pick, because silently redefining acceptance criteria is the orchestrator grading its own homework. When the user picks a redefinition, bind the fix card with guards: report the RAW pre-redefinition number alongside the new definition (never bury it), never tune thresholds to force a pass, and require the reviewer to audit the redefinition itself before any APPROVE. Record adopted decisions as a comment on the workstream's anchor card so the rationale survives requeues. If a hard acceptance criterion remains unmet but is pre-existing, do not silently reinterpret it as passing: get an explicit owner decision (or act only within a clearly delegated decision mandate), record a written exception and the measured miss, label the result CONDITIONAL PASS rather than full pass, and retain reviewer sign-off on that exception. Keep behavioral regressions and inherited baseline failures distinct. Copy user-provided assets to the shared workspace when workers need access; preserve originals and do not upload assets externally. Identify install/build/test prerequisites before dispatch; where safe, install them from the orchestrator session and run a smoke test so the worker starts from a usable environment. **The owner has standing-authorized this**: "aplikasi yang diperlukan untuk install di server silakan lakukan" — install missing server-side prerequisites yourself and never make a worker install them (a worker's `pip install` hitting the security-scan capability block crashed two runs and trip the dispatcher's failure limit); state what you installed in the card comment. Match new dev-tool major versions to the project's existing toolchain before installing. If a worker gets a `capability` block because its-session security scan times out, don't tell it to bypass the guard: install/verify the prerequisite from the orchestrator session, comment exact state and resume point, then unblock.
3. **Choose the smallest safe graph.** For a planning/review meeting, create a planner/lead card and one reviewer child gated on the lead. For a website project that is still in planning, first report whether the planner's brief already exists and is done (verify the board, not conversation recollection); distinguish completed pra-desain from owner approval and from implementation. State explicitly what has not been checked or authorized. Recommended website sequence: content/requirements and approval → visual design and asset validation → implementation → independent QA → integration/deployment preflight → controlled launch. Include SSH access, Git repository/source-of-truth, and server-to-GitHub reachability as explicit deployment acceptance gates; do not imply they were tested by a planner or by local DNS alone.
   **Design-first fan-out, BEFORE any card:** when the user asks for a rancangan first ("bentuk rancangannya dulu … lalu beritahu saya siapa yang ditugaskan"), run ONE `delegate_task` unit per design lens in parallel, all read-only (no file edits): planner → spec + acceptance criteria, implementer → technical design against the source, reviewer → UX/quality review of the proposed flow. Consolidate their outputs YOURSELF into one design doc in the project dir before creating any execution card — subagents do not talk to each other, and a design that exists only as three scattered summaries will be re-derived by the workers. Then report the roster by display name BEFORE dispatching: the user tracks the team by name and has asked "apakah tidak melibatkan planner?" when the planner was absent from a design phase — whenever a phase produces a spec, the planner is part of it even if the user only names builders. **During consolidation, the user's written brief outranks every subagent recommendation** (a reviewer proposing the opposite voting model than the brief specifies): adopt the brief, and record the conflict + your resolution in the design doc rather than silently picking a side. For implementation, create an implementer card and a reviewer child gated on implementation. Make each card's deliverable, scope boundary, evidence required, and completion test explicit.
   **Review loop:** the reviewer may return `REVISE` with findings numbered and located (file:line). When that happens, create a revision card gated on the reviewer, whose body lists each finding and what evidence the fix must show; then a round-2 reviewer card gated on the revision. **Cap the loop at one blocking revision round** — the round-2 verdict must be APPROVE or a bounded set of genuinely-blocking findings, so a review cannot expand scope indefinitely. Verify claims baris-per-baris (`fixed per T-N`), never on the implementer's word alone. For an existing milestone card explicitly designed to own the implementation+remediation lifecycle, reopen/requeue THAT card for bounded fixes instead of creating an overlapping duplicate; retain the review card as audit history and gate re-review after the fix commit.
   **A `done` card may still have uncommitted work.** Immediately inspect its actual worktree (`git status --short`, `git log -1`) before trusting completion or allowing auto-prune; commit any intended dirty files, verify the commit contains the expected artifacts, then synchronize the reviewer worktree to that commit. Otherwise review may run against a stale branch and dispatcher pruning may destroy the only copy.
   **For a BLOCK on an existing implementation milestone, reuse that same card.** Read the current board row, latest `task_runs` outcome/metadata, review comments, and worktree before acting; notifications may describe an earlier review attempt. If it is already `running` after `changes_requested`, leave it alone and do not redispatch. If it is still `review`, use `hermes kanban request-changes <id> '<bounded, evidence-based findings>'`, then dispatch only when the task is `ready`; verify a fresh running run in the canonical worktree. Keep the review failure as history, preserve the branch/worktree and acceptance thresholds, and require measured closure of each finding before the next review. Never interpret handoff or status transition as approval, create a duplicate fix task, or deploy until an explicit final APPROVE and all acceptance evidence are present. **Do not requeue a ceremonial investigation when a mandatory runtime gate cannot be measured under the current safety constraints.** If the owner prohibits the only known test environment, preserve the latest measured FAIL/NOT MEASURED evidence and leave the card blocked/needs_input with the exact authorization or environment decision required; don't relabel offline code inspection as runtime validation or spend another worker run searching for an unproven route. Requeue only when the card has a concrete permitted action capable of closing a named acceptance gap.
   **The orchestrator owns the loop's integrity, not the reviewer.** A reviewer sometimes closes its card with REVISE and creates neither the fix card nor the round-2 review — the milestone then hangs forever. Scan for that gap after every REVISE verdict (verify card `done` + no FIX/round-2 child) and create the missing card yourself; in specs that depend on a policy decision the REVISE raised, write the decision into the fix card's thread first.
   **Trace the whole verdict chain when reporting a milestone's status.** The verification card's LAST comment is usually the initial REVISE — the APPROVE lives on the fix/round-N card (or a later review comment). Report a milestone as approved only after finding an explicit APPROVE at the END of the chain (verify → fix → review round-N), and when asked "is X still REVISE?" walk every card carrying that milestone's tag rather than reading one card. **A gate card's `done` status is not a verdict:** an auditor can call `kanban_complete` while its own report says REVISE, and any orchestrator whose loop exits on `status='done'` then announces a false finish (log line "SEMUA KARTU DONE", release claimed, gate actually failed). Read the gate report's verdict line — APPROVE vs REVISE/BLOCKED — before declaring the chain complete, and encode the vortex in the driver: exit only when every gate card carries APPROVE, otherwise create the FIX card (producer profile) plus a gated RE-AUDIT card (`code-analyst`) and continue the loop. Recipes for that chain and for measuring worker liveness live in `references/card-progress-diagnostics.md`.
4. **Prevent workspace collisions.** Before creating a card, compare its files and deliverables with every active card. Dependency gating orders parent→child; it does NOT serialize siblings. If scope overlaps, add the new requirement to the existing card thread or make it a gated child—never run two writers on the same files.
   **When the owner mandates a PARALLEL flow, enforce it with a scope guard, not just gates.** Unlinking siblings from a parent removes the dependency wait but also removes all ordering — so grant write access to ONE implementer card and set every parallel QA/acceptance card read-only (they may write only their own report files). State the guard in each card body at creation time, and keep a final coordinator QA gate against the live endpoint, because any reviewer running before the code lands will report stale findings.
   **Triage `block_reason` before treating a block as an incident.** Read the block's payload first and classify: a WORKFLOW block (parent waiting for children, `initial_status`, waiting on a parallel card's implementation) is the design working — leave it until its trigger completes, since force-unblocking makes workers claim or verify before evidence exists; a STALE block (waiting for a file that already exists, waiting for a restart a disk-reading server does not need) is unblocked manually with a corrective factual comment; a FALSE CAPABILITY block — the worker's own verdict that a tool or dependency "cannot run" — is a hypothesis, not a measurement: the refusal may belong to ONE tool route in that session while another route on the same host works, so re-probe the capability from the orchestrator session with the smallest helper that performs the task, then comment the exact working command and its measured output on the SAME card, verify the comment landed, and unblock that card rather than opening a duplicate. Report the triage with the payload and the live work status as audit evidence, rather than a bare "blocked = problem" claim.
   **Building a sequential chain: prefer `--parent` at create time; fall back to create→reclaim→link.** When the parent id is known before creation, pass `--parent t_<id>` directly on `kanban create` for every child: the child lands in `dependency_wait` immediately, the dispatcher never claims it early, and no reclaim/link step is needed (verify the edge anyway in the board DB, per the check below). Only when the parent id is not yet known does the old sequence apply: a freshly created card is claimed by the dispatcher within seconds, and `hermes kanban link parent child` REFUSES while the child runs (`child is already running`), so: write each body to a scratch file and `kanban create` the whole chain up front → `hermes kanban reclaim <child>` every waiter → `link` parent→child in order. The reclaim step is only needed when a dispatcher is live; with NO dispatcher running (manual-dispatch mode), create→link directly succeeds without reclaim. The dispatcher can re-claim a reclaimed card before the link lands, so a link may fail twice — do reclaim+link back-to-back and retry once rather than assuming the first refusal is final. Verify the finished chain in the board DB (`sqlite3 ~/.hermes/kanban/boards/<slug>/kanban.db 'SELECT parent_id, child_id FROM task_links'` plus per-card `status`): only the head should be `running`, the rest `todo`/`blocked` with `dependency_wait` reasons. **Do not trust `hermes kanban list --json` as the snapshot for this check** — it can return a truncated set that omits the cards you just created and reads as "empty"; the board DB is authoritative.
   **Integrate before seeding the next work card.** When a milestone card finishes on its own branch, `git merge --ff-only <branch>` into the integration branch and re-run the whole gate suite THERE (grep/typecheck/unit/build) before creating the next card's worktree from the merged HEAD: the next card otherwise starts on pre-merge state, and a regression introduced by the merge itself surfaces at the final milestone instead of at the seam where it was born. Capture each command's exit status while continuing through all gates; a known baseline test failure must not let `set -e` skip build, grep, or dirty-tree checks. Summarize each measured result, including baseline failures, after the complete gate set runs.
   **Archive superseded cards instead of leaving them visible.** A stale card from an earlier phase (`hermes kanban archive <id>` — archive mode, `--rm` only to purge already-archived) stays on the board as apparent garbage: the owner reads the UI directly and asks whether blocked cards are "sisa sampah". Archive pre-phase leftovers the moment their scope is absorbed by a new card, and when reporting status label every non-running card's reason (dependency-wait = antre otomatis, needs_input = menunggu keputusan, archived = digantikan) so a blocked lane never becomes a trust question.
5. **Make progress durable.** Require comments after meaningful units of work: completed / in progress / not started, file or artifact path, and concrete result. Tell workers to reread their card thread after a rate-limit respawn; new runs have fresh conversation context.
   **`running` ≠ progressing.** A card can show `running` for hours with the
   heartbeat ticking while progress comments stay at zero and workspace mtimes
   never move — usually the worker is stuck in a read/re-verify loop. A card
   comment cannot reach the in-flight run: `hermes kanban comment` on a
   `running` card is read on the next dispatcher spawn — durable handoff, not
   live correction; `steer` applies only to a true `delegate_task` child, never
   a Kanban-dispatcher run. Detect
   with `hermes kanban show <id>` (comment timestamps) plus workspace file
   mtimes, never status alone. The proven nudge, sent BEFORE the owner's
   periodic report notices the silence: one comment demanding (1) which item
   is in progress right now, (2) the latest test result, (3) blockers — plus
   work discipline if the quota keeps requeueing: start editing instead of
   re-reading, one finding per turn with a GREEN comment between them, and run
   the full suite only once at the end. Real progress comments arrive within
   minutes. **A card comment cannot reach an in-flight run.** `hermes kanban comment` on a `running` card is read only when the dispatcher SPAWNS a run — it remains unread by the live worker until the next requeue, so it is durable handoff, not a live channel. **To make a steer actually land on a live worker, pair it with `reclaim` + `dispatch`** — posting the comment alone leaves the correction sitting in the thread while the current run keeps burning budget on the behavior you meant to correct. To correct a `delegate_task` child mid-turn, steer its live subagent: `delegate_task action='list'` for the id, then `steer` (injected into the current turn immediately) — but steer does NOT reach a Kanban-dispatcher worker (see the dedicated rule below in §6); for those the fastest live levers are comment+reclaim/kill. Use a card comment for what must survive a requeue, a steer for the immediate correction of a delegate_task child, and both when the correction must persist — a mid-recon nudge posted only as a card comment can burn the worker's budget before anyone reads it. **Account for `dispatch`'s default `--failure-limit 2`:** the dispatcher auto-blocks a card after 2 consecutive `spawn_failed`/`timed_out`/`crashed` outcomes, so a run of provider-driven `crashed` exits parks the card even with `consecutive_failures=0` at task level — a guard that re-dispatches without watching for that block will dispatch into nothing. Read the newest `task_runs.outcome` before each requeue and check for an auto-block, rather than assuming every crash was simply requeued. Give the nudge a hard reply deadline together with the exact
   deliverable shape it owes (findings as file:baris + numbers, posted as a
   comment by HH:MM); on a miss, `reclaim` + dispatch and read the dispatch
   JSON `spawned` array before reporting the card alive — a reclaim that
   prints nothing means no worker restarted, so the silence continues.
   **A stalled analysis loop needs a written gate, not a fifth nudge.** When
   comment-count stays zero across hours while workspace files never change,
   censuses the worker's `state.db` messages for the current run: reads/searches
   vs writes. Many actions with zero writes = the worker re-reads because each
   read spawns a new "need to verify" — time-boxed nudges do not break it (three
   failed in a row). Remedies in order: (a) comment with a hard gate AND hand
   over a finished minimal artifact plus the exact `file:line` locations for
   every change ("open X, edit Y, no more reconnaissance") with work discipline
   — read at most once per file, edit immediately, GREEN comment per item — from
   that point the worker only runs it and fixes; (b) if it stalls again,
   `reclaim` + `block` BEFORE editing any file yourself (same-files writers race
   and corrupt each other), comment the takeover transparently onto the card,
   finish the measurable items with RED→GREEN evidence, then hand the next round
   back to the worker/reviewer. Never let a deadline burn while two parties read
   the same files. **Reassign the card before giving the same profile a fourth run.**
   A profile that closes two or three runs with zero write calls is not going to
   write on the next spawn: `hermes kanban reassign <id> <other-profile>
   --reclaim --reason '<reads, 0 writes, N runs>'`, then comment a brief that
   (1) names the branch/commit to continue from so the new worker does not
   restart from zero, (2) bans `skill_view`/`skills_list`/`tool_search`, (3)
   caps files read at 3–5, (4) requires a `write_file`/`patch` inside the first
   10 minutes, (5) requires commit + `kanban_complete` after ~12 tool calls.
   Verify the switch with write-call counts in the new profile's `state.db`
   within 4–5 minutes — a reassigned card that still only reads means the brief
   was not read, not that the profile changed.
   **Under a deadline the owner stated, act and report in the same turn.**
   Diagnose, remediate, and re-trigger in one tool batch, then answer with
   root cause + fix evidence + a time-to-deliverable estimate carrying its
   uncertainty (best case / worst case) — a findings-only reply that waits for
   another prompt is what reads as "berhenti di tengah jalan". Before giving
   any ETA, inspect the newest worker comment, artifact timestamps, active
   process, and remaining acceptance/deploy gates; estimate each remaining gate
   from current evidence, not from the original plan or a prior estimate.
   Separate elapsed time from remaining effort, state the clock time used, and
   label an estimate low-confidence or unavailable if an unresolved blocker
   dominates it. Never present a speculative range as a commitment or repeat a
   missed ETA without revising the cause and evidence; if meaningful progress
   has not changed, say so plainly and offer a bounded decision point (continue,
   take over, or pause). For percentages, define explicit acceptance
   milestones and count only independently evidenced passes; activity, heartbeat, and
   repeated probes are not completed milestones. The owner's standing report
   contract is one unit: PERCENTAGE + per-milestone progress lines + an explicit
   ⚠️ blocker flag on every stall (with the aksi taken) — never ship a percentage
   without the blocker scan, even when nothing is wrong say "no blockers" so the
   absence is itself an answer.
   **When the owner sets a hard stop deadline, treat it as the latest cutoff,
   not the target completion time.** Aim to finish earlier, surface blockers
   before they consume the remaining window, and schedule a one-shot deadline
   guard at the exact cutoff with a self-contained prompt and verified delivery.
   That guard must inspect measurable acceptance evidence and actually stop or
   pause the worker/monitoring plus report if incomplete; a reminder that merely
   says "check later" does not enforce the owner's instruction. Verify its
   schedule, enabled state, and delivery target at creation (test-fire it once
   only when an early execution would be harmless — a guard whose action is
   "stop the worker" must never be fired manually). State the
   deadline as a stop condition, never as an ETA or promise of completion.
6. **Monitor only when requested, and match the gate to the reporting contract.** **STANDING PREFERENCES (owner): no manual polling and no wasted requests.** The owner explicitly rejects manual check-ins ("tidak perlu, pastikan saja progress tetap berjalan...") and unproductive request burn ("hanya pemborosan request") — so: do NOT reply "saya akan cek lagi nanti" then wait for a prompt; every reply must carry a verified status, and question-answering about progress is delegated to an automated monitor the owner did not have to ask for. Guarantee forward motion with a mechanism (watcher cron, supervisor, dispatch-on-done), not with a promise to look later. Same economy applies to tools: batch independent reads, hash-gate agent runs so unchanged state costs zero LLM calls, and prefer one owned measurement over a queued verification card. A blocked/needs_input card is an immediate reportable incident: report it to the owner without waiting for the next 15-minute tick, resolve if authority permits, comment the decision, unblock, dispatch, then confirm the spawn. Every monitor must track the current active card IDs (not an old project chain); run it once after edits and verify its actual output/delivery target. **Derive the tracked set from the board, never hardcode it** — workers auto-decompose follow-up cards mid-project (QC finding → fix card), and a script hardcoded to the original chain goes blind to a card that later sits blocked for hours while its percentage still reads 100%; query the project's parent chain/tag from the board DB each run instead. The RETIREMENT condition must be equally dynamic: a monitor whose self-delete instruction names the original card ids or a fixed count retires itself the moment those finish — even while a follow-up card the project spawned later (QC finding → fix card) keeps running, leaving the owner with hours of silence and a 'mana laporan progressnya?' accusation. Phrase self-deletion as a board query evaluated at fire time (e.g. `COUNT(*) WHERE title LIKE '<project-tag>-%' AND status<>'done'` = 0), never as a literal id list, and give every follow-up card the same tag so it enters both the tracked set and the retirement check. When restoring a monitor after any gap, re-apply the full per-step budget table to the CURRENT card set — follow-up cards included (a fix card inherits its predecessor's budget class) — not just the original chain. Stale paused cron jobs do not count as monitoring. Do not report success merely because a no-agent cron says `succeeded`; inspect its generated content and verify it went to the requested channel. For periodic updates, create one change-detecting monitor (fixed field order, no wall-clock noise) and deliver on actual changes — but if the user asked for a fixed cadence (e.g. "lapor setiap 15 menit" while work runs), append a `tick: HH:MM` heartbeat line so the bytes change every tick during active runs; change-only output goes silent whenever a worker posts no comments for a stretch and the user asks why reports stopped.
   **Event-triggered watcher ("saat X commit / laporkan saat selesai").** When the
   owner asks for a report at the MOMENT of one event rather than a cadence, use
   a monitor-mode cron job, not a polling agent cron: `hermes cron create '2m'
   --monitor-script <name>.sh --deliver origin`. The script prints a constant
   sentinel line (e.g. `WAITING`) while the event hasn't happened — monitor mode
   hashes stdout, so the agent run is suppressed and idle cost is exactly zero —
   and prints an `EVENT:` line the instant the trigger fires. Rules: (a) the
   script lives in the profile scripts dir and is passed as a BARE FILENAME —
   `--monitor-script /abs/path` is rejected; (b) trigger on an observable
   ARTIFACT (target file's content constant, board-DB status/column), never on
   worker liveness or heartbeat — those lie about progress; (c) embed stall
   detection in the same script: worker `state.db` MAX(messages.timestamp) age
   over threshold (≈12 min) while the artifact is unchanged → emit `STALL_EVENT`
   instead of the sentinel, and the prompt must chain the response: one hard
   nudge with deadline, then reclaim+dispatch, then report chronology + new ETA
   to the owner; (d) the prompt carries the exact baseline constant, the expected
   new constant, and the self-pause instruction WITH the watcher's own job id,
   so the chain retires its own monitor when the milestone lands — never leave
   an event watcher running past its event. Always verify the report's denominator and scope: a legacy status script may summarize an old or archived workstream and show a misleading percentage (for example, 3/8 done); add the newly active card to its tracked set and label per-card progress estimates separately from measured test/build gates. The heartbeat costs nothing at rest because the job is paused/removed at completion. Verify it is enabled and delivers to the requested channel; then inspect the first real report's content, not merely cron registration. periodic report stops arriving, inspect recent execution failures and delivery outcomes (not just the job's enabled flag), correct scheduling/auth/config state without changing model or acceptance settings, then verify a fresh report is generated AND delivered before telling the owner reporting has resumed.
   **Measure workload, not instrumentation.** For runtime performance or animation gates, report sample duration, population, and active/moving count alongside the metric; a counter may report FPS while zero agents move. Seed deterministic workload, fail closed below the stated minimum, and retain raw output. For browser zoom/boundary gates require an actual viewport assertion or screenshot proving the expected region is visible and centered; helper unit tests alone cannot establish rendered behavior.
   **The benchmark environment must match the acceptance question.** Before quoting a performance number against a threshold, record ALL of: build mode (dev vs production bundle), where rendering runs (server-side software rasterizer vs visitor GPU), viewport/resolution, and workload size (agent count + moving count). A high FPS from 1 agent cannot satisfy a 13-agent gate, and a GPU-less server result does not predict visitor-device FPS — label numbers by build mode, renderer/hardware, viewport, population, active count, duration, and sampling method. First identify whether the acceptance question is visitor-device experience or server capacity; use the matching environment and have the owner explicitly approve any change in pass definition. If the owner's machine is needed, use a preview in a bounded, access-controlled path: verify the exact public IP/port externally, give the owner the exact tested URL (never guess between similarly numbered hosts), and tear down the exposure immediately after collecting evidence. Do not expose an unauthenticated preview to the public merely because a high port is reachable; prefer an authenticated tunnel or temporary access control, and if unavailable ask before opening it. Never rebind a port deliberately bound to 127.0.0.1 — proxy it instead. Preserve the raw server result as an environment note when owner explicitly accepts visitor-machine evidence; record owner decision and limitations on the canonical card. Do not silently change threshold, population, duration, or interpretation.
   **Owner-delegated "do it all yourself" mode with per-step budgets.** When the owner says "serahkan ke kamu, lapor otomatis, jangan buang-buang request", build a self-serve loop: (1) a per-step wall-clock budget table (e.g. R1=90m, R2=90m, R3=60m, R4=60m — derived from observed runtimes of earlier comparable cards, not guessed); (2) a status script that emits `NEAR_DEADLINE` at >=80% budget and `DEADLINE_BREACH` at >100% — the script is the contract enforcement, not a nag; (3) stall detection by comparing elapsed time vs. budget AND worker state.db message age (>12m = stalled while card is `running`); (4) cron prompt that EKSEKUSI on DEADLINE/STALL (comment nudge with hard reply-by deadline; reclaim + dispatch if no response after 2 consecutive nudge failures) instead of merely reporting the problem. The budget table also feeds the ETA the owner receives: each step's ETA = current clock + (budget - elapsed), labeled best/worst case. Update the budget when a real cause (rate-limit 429 gap) invalidates the raw elapsed — report the working-time vs. wall-clock-time split so the owner sees real progress, not just the timer. **Measure wall-clock vs. active time separately:** a card that burned 53 of its 97 minutes rate-limited (429) did ~44 minutes of actual work — conflate the two and you both misreport progress AND waste a premature takeover. The status script can extract this from `task_runs` (failed runs' start→end spans) as "dead time", subtracting it before comparing against the budget. **Budget timers must SPAN requeues — a per-run timer is a false green.** Elapsed computed from the CURRENT run's start (`MAX(task_runs.started_at) WHERE ended_at IS NULL`) silently resets to zero on every rate-limit requeue: after N requeues a card that burned hours of real effort still reads "within budget", so the monitor's DEADLINE gate never fires exactly when it matters. Compute effective elapsed as the UNION of ALL `task_runs` intervals for the card (sort + merge overlaps — successive/respawned runs can overlap) MINUS blocked time (pair `task_events` kind=blocked→unblocked and subtract each span). Then, when requeue churn makes the original budget unachievable, make ONE explicit extension decision — state the new cap with its reasoning (original budget + allowance per observed interruption) as the card's budget entry in the status script — and re-arm NEAR_DEADLINE at 80% of the new cap; never let the timer reset silently, and never keep the stale cap silently either.
   **Kanban workers are NOT `delegate_task` subagents.** `delegate_task(action='steer', subagent_id=<kanban-run-id>)` fails with `requires subagent_id (from the spawn dispatch response or action='list')` — a Kanban card run is spawned by the dispatcher, not by the delegation runtime, so `list` never returns it. The live-correction tool documented above (`steer`) only works for `delegate_task` children; for a Kanban worker the correct lever is: (a) `hermes kanban comment` (durable, read on next run spawn) + card `reclaim`/`block` when immediate termination is needed; (b) `kill <worker-pid>` where the PID comes from `task_runs.worker_pid` in the board DB. Do not retry `steer` variants hoping a hidden id exists.
   **Verify a takeover actually stopped the old writer.** After `reclaim` + `block` + `kill <worker-pid>`, the DISPATCHER may respawn a fresh run seconds later (its own loop re-claims the card before your kill settles). Before touching any shared file: re-run `ps aux | grep 'kanban task <card-id>'` after a 5-second settle, and if a new PID exists, trace its PPID — the dispatcher's own process (`hermes kanban daemon` / cron) may need `kill` too, or the respawn loop continues. Only proceed to your own edits after a zero-PID check passes, and comment the takeover on the card so the next worker knows why its run was interrupted.
   **SQLite `timestamp` units vary per DB — normalize per source.** Hermes Kanban `task_comments.created_at` and `tasks.started_at` are EPOCH SECONDS; `program-developer state.db messages.timestamp` in this deployment was observed BOTH as seconds (1.79e9) and as milliseconds (1.79e12) at different times in the same table. Normalize the FORMAT too: one board can hold epoch seconds, milliseconds, AND ISO-8601 text (`task_runs.started_at` observed as ISO string while sibling tables hold seconds) — route every age computation through one `to_epoch()` that handles all three shapes. And check WHICH column carries time before using it: `tasks.worker_started_at` is a WORKER UUID, not a timestamp — the active run's start time is `MAX(task_runs.started_at) WHERE ended_at IS NULL`; reading the UUID column as time yields either a crash or a nonsense elapsed that misreports the step's budget position (a fresh run read as 30h over budget). Any age computation must branch: `t = v/1000 if v > 1e12 else v`, then `age = time.time() - t`. Hardcoding one unit silently produces `age=none` ("tak pernah") or negative ages, which the monitor script reports as a permanent false STALL — normalize the unit in the status script. Same script, same class of bug: a `SELECT status, assignee, started_at` run through a helper that returns only `r[0]` drops the other columns, so every downstream unpack crashes — fetch the full `fetchone()` row and index it explicitly, or use a dedicated multi-column helper.
   **Verify reporting delivery, not registration.** If a requested periodic report stops arriving, inspect recent execution failures and delivery outcomes, fix the underlying scheduling/auth/config issue without changing the configured model, then verify a fresh report was generated and delivered before claiming recovery.
 **Define the measurement, not just the target (numeric handoff precision).** A worker verdict that says "anchor A: 368 -> 356" can be wrong by exactly the delta between two named quantities: `anchor` (input to `y - h + 4`) vs `draw-top` (output, already produced by the current anchor). In VO2D, the coordinator's verdict gave draw-top values as if they were new anchor values; the worker refused the -12px patch, proved the unit confusion by reading `stage1_grids.py` source (label `y=%d` prints `dy_fix+off`, not the anchor), and shipped `SHIFT=0` + sprite bottom-pad trim instead - the correct fix. **Rule: any numeric handoff must give ONE worked example mapping every named quantity to its formula AND its current value** (anchor -> draw-top -> dy), or the worker will plug numbers into the wrong slot. A worker that pushes back with source-line evidence is an asset, not a blocker - verify its claim (2 minutes of `sed -n` on the cited script) before overruling, and if it was right, say so explicitly in the verdict comment and close the card with `hermes kanban complete <id>` (NOT `done` - that subcommand does not exist).

**Report-cron self-delete must match the dynamic scope, and budgets must survive requeue.** Two coupled lessons from one night: (1) a 15-min report cron whose prompt says "self-delete when R1-R4 are done" deletes itself while a follow-up card (R5) still exists - monitoring silently died for hours and a `needs_input` block sat unattended for 106 min. Fix: derive the tracked set dynamically (`SELECT ... WHERE title LIKE 'VO2D-R%'`) so new cards are covered automatically, and self-delete only when that dynamic query returns zero non-done rows. (2) a per-step budget timer reset on every 429 requeue, hiding that wall-clock had already blown past the budget 5x. Fix: `active_elapsed = union(task_runs intervals) - union(blocked spans)` using `task_events kind='blocked'/'unblocked'`; never `now - started_at` (double-counts overlapping requeues) and never the current run's start (resets on requeue). Five `rate_limited` (exit 75) outcomes can silently eat a 90-min budget - the status script must sum them. When wall-clock exceeds budget but the worker is still producing (429 kills, not slowness), extend the budget explicitly (+30/+45 min) with the reason in-thread instead of reclaiming a healthy run.

For visual bugs, treat a user screenshot as concrete acceptance context: preserve/reference it for the worker, and require a post-fix runtime screenshot that shows the actual state, not just a passing HTTP check or a behavioral counter. For asset-driven pixel-art redesigns, inspect the supplied manifest and README before choosing a rendering model; measure native dimensions, alpha mode, @2x consistency, and edge artifacts. If room art is opaque and its native dimensions conflict with collision-grid cells, choose explicitly between rescaled room backgrounds and a larger world with native-size rooms plus manually authored walk masks; keep pathfinding grid semantics stable and document seat/anchor mapping. **Coordinate edits with the claimed worker before coordinator takeover.** `reclaim` may only change Kanban state while an already-running process still edits the shared directory; before touching its files, terminate/confirm absence of that process, disable any dispatcher/watchdog capable of respawning it, then verify no matching worker PID remains. A card-level `blocked` flag alone is not an exclusive filesystem lock. After takeover, inspect the complete current file and diff before patching—workers may have written between earlier reads and reclamation, so compose edits against current state and run syntax checks immediately to catch duplicate declarations/brackets. For grid/collision changes, define acceptance probes from the exported map API (dimensions, boundary/partition cells, doors, furniture/seat cells, flood-fill reachability of every roaming target); count and report actual assertions/results. After code checks, restart/reload the actual service and verify the live browser canvas dimensions, console/resource failures, and a screenshot at the target view. A successfully rendered canvas proves runtime load only, not visual completion: do not claim a high overall percentage until the asset renderer and visual acceptance are independently verified. Do not dispatch overlapping writers: create a dependency chain and verify the actual parent edges and statuses in the board DB before dispatch. In the independent QA gate require fresh-navigation resource capture through forced animation states, exact avatar image handles (not DOM counts), healthy API payload fields (not HTTP status alone), and real runtime screenshots at specified viewport/zoom/DPR. Test chat routing through the UI for broadcast, direct mention, and division mention; inspect the sent payload and delivered result before concluding a hint/parser is broken. Treat reviewer findings as hypotheses to verify against the current source/runtime, not automatic truth; record disproven findings with reproducible evidence and preserve valid findings in the acceptance gate. Before probing, inspect the app's onboarding/auth/consent gates and seed the documented test-state in browser storage BEFORE navigating to the route; otherwise a wizard/modal can cover every screenshot while the probe keeps producing misleading artifacts. Set the camera/viewport to the exact acceptance view (e.g. front-desk close-up, not an overhead overview), and inspect the resulting image yourself before crediting the visual milestone. Distinguish application status from rendered pose/animation and verify both, plus the relevant visual affordance (e.g. lit/active display). Report PASS / FAIL / NOT MEASURED distinctly, with limitations. When
   acceptance is a runtime behavior (state counts, HTTP status, rendered
   page), run the bounded probe YOURSELF the moment the deploy lands instead
   of waiting on a verification card that may be stalled — a short
   measurement you own beats a queued verdict, and the card still completes
   its formal review afterwards. When an owner-approved exception is used, state both the original acceptance failure and the bounded conditional disposition; never summarize it as an unqualified APPROVE or full pass.
   **Reviewer failure taxonomy — instruct the reviewer to hunt these specifically:** hidden passes (tool reports `violations` but drops `incomplete`/untested nodes — require all three), empty denominators (a 0/0 result quoted as a pass — require `n` on every rate), fixtures that never trigger the production branch (test inputs must cross the real timeout/grace threshold, else label the result trivial), numbers measured outside production caps quoted as shipped performance, stale reference or checksum mismatch (report newer than the archive; disk vs packaged copies diverge), and `pre-existing` used as an excuse for an unmet criterion (attribution is not acceptance — only a written owner exception with the failing number makes it a conditional pass). The high first-round REVISE rate this taxonomy produces is the gate working; do not weaken the gate to shorten the loop.
**Resuming work from a dead/interrupted session.** When the owner hands over a session that died mid-task (provider stale-abort, explicit `/new`), the FIRST deliverable is durable materialization, not in-session continuation: recover the dead session's context from its `request_dump_<sid>_<ts>.json` in `<profile>/sessions/` — parse with `json.load(..., strict=False)` (dumps contain raw newlines) and read `messages[]` (role/tool_use/tool_result) to reconstruct verified facts and decided scope — then VERIFY live state against those facts (hashes, greps, HTTP probes: research often outran implementation before the death). Write a Kanban card whose body carries every verified fact (paths, ports, measured state, constraints, backup locations) and dispatch it before further in-session investigation; a session can die again mid-turn and un-materialized research dies with it. The owner's recovery request bundles three asks in one — durable card, progress report, explicit deadline budget — deliver all three in the same reply. Prove the budget exists on the record, not just in chat: after create, read back `max-runtime` on the card and the worker lease `expires_at` (must match dispatch-time + max-runtime); a deadline only stated in a report is unenforced. Recover a dead session's context from `request_dump_<sid>_<ts>.json` in `<profile>/sessions/`, not from memory.

8. **Close the loop.** Summarize decisions, remaining risks, and exact deliverable paths to the user. When asked for a plan, give the named roster and ordered assignment flow with dependencies and measurable acceptance evidence; separate verified facts from recommendations and blockers. Do not claim server SSH, Git operations, or GitHub reachability are supported until each has a successful measured probe on the actual hosting target. Ask for approval before converting a planning roadmap into implementation work when the user requested planning first.

## Mode delegasi penuh: owner tidur, koordinator yang jaga

Owner yang menaruh seluruh pekerjaan ke koordinator dan menganggapnya ("saya delegasikan
penuh tugasnya kepada kamu", "saya mau beristirahat") MEMBUTUHKAN dua kontrol yang BERBEDA,
bukan satu:

1. **Supervisor internal cepat (2–5 menit)** — menangkap kemacetan SEBELUM anggaran kartu
   hangus. Wajib tanpa LLM (`no_agent` script): loop 2 menit versi agent = ratusan run per
   hari untuk pemeriksaan yang tidak mengubah apa pun, persis pemborosan request yang owner
   tolak. Aturan diam: **skrip supervisor tidak mencetak apa pun saat normal** — stdout
   kosong berarti tidak ada pesan terkirim, jadi loop cepat hanya bicara saat ada reclaim,
   kegagalan beruntun, stall, kartu `blocked`/`triage` yang tak terjawab, atau dispatch fallback.
   Sebuah kartu yang mem-blokir dirinya sendiri menghentikan seluruh rantai serial sementara
   SEMUA sinyal kesehatan (0 worker, nol kartu running, heartbeat) terbaca NORMAL — karena itu
   `blocked` adalah kondisi alert, bukan keadaan idle.
2. **Laporan ke owner (15 menit)** — kontrak pelaporan. Skrip terpisah, READ-ONLY: TIDAK
   boleh mengubah status kartu dan TIDAK boleh dispatch. Supervisor boleh reclaim + memancing dispatch; laporan tidak boleh. Memisahkan kedua fungsi mencegah dua sumber kendali (dispatch ganda) dan memastikan kemacetan tidak baru diketahui pada laporan 15 menit berikutnya.

Aturan tambahan mode ini:
- **Laporan harus berisi waktu, worker aktif, kartu berjalan, gate, blocker, dan langkah
  berikutnya yang konkret** — "belum ada blocker" itu sendiri jawaban, dan langkah
  berikutnya harus bisa dieksekusi, bukan "akan saya lanjutkan".
- **Test-fire satu kali** tiap cron setelah dibuat dan periksa ISI keluaran, bukan status
  "succeeded". Supervisor yang diam karena salah jalannya script = ketiadaan laporan yang
  terbaca sebagai macet.
- **Jangan menjanjikan "nanti saya cek".** Di mode delegasi penuh, mekanisme yang menjamin
  gerak (cron, dispatcher, auto-release) adalah deliverable; janji untuk mengecek manual
  adalah kegagalan.
- **Posisi kartu harus PAS dengan bahasa owner**: "2 menit" = supervisor, "15 menit" =
  laporan owner. Menyebut supervisor sebagai "laporan 15 menit" (atau sebaliknya) membuat
  owner menghitung sumber informasi yang salah.
- **Supervisor wajib mendeteksi blokir BASI, bukan hanya blokir baru.** Kartu `blocked`
  yang SEMUA parent-nya sudah `done` dan sudah >10 menit = blokir yatim: prasyaratnya
  selesai tetapi tidak ada yang membukanya, dan karena 0 worker + 0 kartu running semuanya
  terbaca sehat, rantai serial diam tanpa alert (pernah 3 jam 47 menit). Query parent dari
  `task_links` (`parent_id`/`child_id`), tag `BLOCKED-BASI` + hint "perlu keputusan buka/
  re-audit", dan throttle alert per kartu (≥1 jam; 10 menit khusus blokir basi) supaya
  loop 2 menit tidak jadi spam.
- **Laporan harus memuat APA yang sedang dikerjakan, bukan hanya status.** Status + menit
  dibaca owner sebagai "tidak ada laporan pekerjaan" walaupun cron mencatat `succeeded`.
  Tiap kartu `running` diberi satu baris `↳ diam <N>m · <tool/aksi terakhir>`, dibaca dari
  `state.db` profil worker (umur `max(messages.timestamp)` + 12 pesan terakhir).

## Auto-advance: jangan biarkan rantai berhenti

Owner: *"atur semua alur sampai selesai dan saya dapatkan ZIP-nya, picu semua
perbaikan tanpa harus saya tanyakan."* Jeda antar-gerbang yang di-klik manual
(kartu done → koordinator baru bangun → buka kartu berikutnya) terlihat sebagai
**"proyek berhenti"** (panel menampilkan 0 pekerja) dan memicu kritik tajam.
Aturan keras:

1. **Setelah setiap kartu `done`, jangan berasumsi kartu berikutnya jalan** —
   cek statusnya dalam hitungan menit. Dua jebakan nyata: (a) reviewer menutup
   kartu REVISE TANPA membuat kartu fix/round-2 (loop menggantung selamanya),
   (b) kartu dibuat `--initial-status blocked` + `link` TIDAK auto-unblock saat
   parent done (blokirnya berlabel `initial_status`, bukan `dependency_wait`) →
   harus `hermes kanban unblock` manual. Detail pola ini di skill
   `koordinator-team-dispatch`.
2. **Untuk proyek yang harus sampai deliverable: pasang SUPERVISOR cron**
   (`every 15m`, deliver `local`, `failure-deliver telegram`, self-pause saat
   tugas tuntas). **Cadence = cadence kartu, bukan "secepat mungkin":** tiap
   run supervisor = satu putaran LLM penuh dgn prompt state-machine; pada
   `every 2m` dengan kartu yang butuh 30–60 menit per step, itu ~50 request/hari
   untuk cek yang tidak mengubah apa pun (terukur; owner menyebutnya
   "hanya pemborosan request"). Pilih interval terlambat yang tetap menangkap
   transisi (15m), atau ubah cek-nya jadi `no_agent` script; lebih cepat dari
   cadence kartu hanya bila transisi sendiri bisa macet <1 menit.
   Prompt supervisor = state machine eksplisit: ada `running`?
   diam; FIX done → buat+dispatch kartu REVIEW; REVIEW done → baca verdict
   (REVISE → buat kartu fix baru / APPROVE → koordinator audit+packaging+KIRIM
   deliverable sendiri, lalu pause cron laporan + self-pause); tangani macet
   (rate-limit → auth reset, needs_input → putuskan dengan guardrail);
   anti-duplikat (cek board sebelum create); senyap kecuali deliverable final.
   Contoh prompt: cron `eVoting SUPERVISOR` (job cdd1a9e5bd6c).
   Quota config (dead backup key, stale spawn credentials, empty-token
   re-seeding) is a common "kuning" cause — the per-key probe ladder lives in
   `references/provider-quota-recovery.md`.
3. Gerbang review TETAP jangan dipangkas demi cepat — yang dipasang supervisor
   adalah **transisi otomatis antar-gerbang**, bukan penghapusan gerbangnya.
4. **Kick ≠ supervision.** A bounded dispatch kick — one explicit
   `hermes kanban --board <board> dispatch --max 1`, since the standalone
   `hermes kanban daemon` is deprecated and refuses to start while the
   gateway runs its own dispatcher — flushes queued cards for that tick
   only; use it to unstick a queue, never count it as coverage, and never
   tell the owner the chain will advance "otomatis" on its strength.
   Confirm the durable mechanism by config, not by a pidfile:
   `kanban.dispatch_in_gateway: true` plus a live gateway process — a stale
   board `dispatcher.pid` left by an older standalone daemon proves nothing,
   and starting a second dispatcher races the gateway's for claims. Before
   reporting uninterrupted progress, confirm a durable mechanism exists
   (persistent dispatcher, or a supervisor cron that re-kicks) AND re-verify
   the reporting monitor's registration under the profile that owns it
   (`hermes -p <profile> cron list`: name, schedule, enabled, deliver target)
   — a monitor created under the wrong profile or left paused emits nothing
   while the owner is being promised updates.

## Recovering and answering blocked cards

A card blocked with `kind: needs_input` is a worker's question, not a
failure — it obeyed its guard and stopped rather than guessing. Resolve any
block through the card, then confirm recovery:

- **The cause lives in the block EVENT, not in `block_kind` — and the final
  trigger can differ from the question that opened the block.** A card may get
  its original question answered, then end blocked because the worker repeats
  a lookup until a guardrail stops it. Read the newest `task_events` payload
  and the worker's last messages; reconstruct asked → answered → next action
  → termination. Report the initiating question and immediate trigger
  separately; the status label alone does not explain the current hold.
- **A guardrail stop is a termination, not a resolution.** Repeated identical
  tool calls in the worker's tail indicate a loop. Before unblocking, comment
  the exact actionable path/command and bounded next step; otherwise the next
  run can repeat the same search and hit the same guardrail.
- **Comment first, then unblock — and VERIFY the comment landed before
  unblocking.** The comment is the only thing the respawned run reads:
  decision, safeguards, and the next concrete step, self-contained (no
  references to chat). Batched `comment && unblock && dispatch` hides a
  comment failure behind two successes: the dispatcher spawns within seconds,
  and the worker re-blocks on an empty thread. Check the comment's own output
  ("Comment added") first; if it failed, fix it BEFORE the unblock — a failed
  comment in the same batch is never a reason to skip the decision.
- **A "missing dependency" question is usually the coordinator's to answer —
  search the host before escalating it.** Before treating a missing
  library/asset as a decision for the user, look where it already lives: the
  project's `vendor/`, a package cache, a `/tmp` staging dir, a sibling
  checkout, a system install path. A release tarball already on disk turns an
  owner decision into a coordinator action (vendor it, pin the version, record
  it) — the same reason server prerequisites get installed from the
  orchestrator session rather than by a worker. Escalate to the owner only
  when the artifact is genuinely absent AND fetching it is forbidden AND the
  acceptance criterion names that library. When you vendor it, the repo gains
  untracked files: audit them (licence, version pin, audit output), commit them
  with the milestone, and state in the report that the dependency was supplied
  locally.
- **Answer only with means the worker actually has.** A requirement pointing
  at a resource that does not exist (e.g. "human annotation" with no human
  annotator) guarantees a re-block; two identical blocks trip
  `block_loop_detected` (limit 2) and auto-release the card to `todo`.
  Prefer an achievable method plus honest provenance labelling — state WHAT
  produced the evidence (AI visual review vs human) and who audits it
  downstream — over an unmeetable purity bar. Never let a worker claim a
  stronger provenance than it can deliver.
- **If `unblock` reports "not blocked/scheduled?",** the block already
  auto-released to `todo`, and the dispatcher only claims `ready` — the
  `todo` card then sits unclaimed indefinitely. Promote it with
  `hermes kanban promote <id> '<audit reason>'`. Promote re-checks parents
  and refuses if unsatisfied: `hermes kanban show <id>` the named parent ids
  first — a worker may have auto-decomposed the card while blocked. Inspect each child’s scope, status, workspace, and spawn diagnostics before deciding. Let valid, non-overlapping children run; if children duplicate acceptance work already owned by the parent or cannot spawn due to invalid workspace, record the evidence on the canonical card, then remove only the redundant dependency links and resume that existing card. For needed but invalid children, repair their workspace before dispatch. If the canonical parent is in `triage`, do not unlink dependencies or promote on guesswork: inspect `hermes kanban show` and the DB-backed parent statuses first. Remove only links to proven redundant or unspawnable children, preserve required predecessors, then promote once all required dependencies are satisfied. Auto-created triage children may themselves have linked the parent as their child; inspect both directions and clean up that reverse edge only after confirming the child's scope is already owned by the parent. **When a card lands in `triage` with `needs_input` after repeated blocks, `unblock`/`promote` may both refuse it** — diagnose with `hermes kanban diagnostics --task <id>` + latest `task_events`/comments first (never a duplicate follow-up card). If the decision is now concrete and the existing card is still the valid owner of the scope, `hermes kanban specify <id>` converts the triage item into a concrete `todo`; then `dispatch --max 1 --json` once and verify the fresh run past its historical failure window (age + heartbeat + state.db message growth). `specify` packages an already-made decision into a spec — it must not be used to invent unresolved policy or acceptance criteria. Finally verify the parent list and dispatch JSON `spawned` result; never report recovery from a status transition alone.
- **A block saying the task workspace is empty and the project lives outside it** is an authorization request, not a failure or an API problem: the worker refused to edit files it was never granted. Resolve it by verifying the canonical project path and the card's scope, then posting a durable comment that authorizes edits ONLY in that path (name the allowed subdirs/files, the tests it may touch, and the prohibited areas — Hermes profile/config/kanban state), then unblock once and confirm a sustained heartbeat. Do not copy the whole project into the scratch workspace when authorizing the real path is safe, and never grant blanket filesystem access.
- **Resolving the blocker does NOT release the card.** `blocked` is a manual hold, not a dependency queue: a card whose fix card is already `done` stays `blocked` indefinitely until `hermes kanban unblock <id> --reason "<measured evidence>"`. After every fix/gate card completes, read the GATED card's own row — never infer release from the child finishing — then unblock, dispatch once, and confirm a fresh run. **Clear the stale block metadata too:** `tasks.block_kind` keeps its previous value (e.g. `needs_input`) after the unblock, so a card that is genuinely `running` still renders as blocked in any view that reads that column; `update tasks set block_kind=null where status!='blocked' and block_kind is not null` and re-query `select count(*) from tasks where status='blocked'` before telling the owner "no blocked cards".
- **A block caused by a skill's mandatory configuration choice is the coordinator's decision, not an owner escalation.** When a worker halts because a skill demands an explicit mode (antislop `1 — DURING` vs `2 — AFTER`) and the config file does not exist yet, that is a question inside your authority: pick the mode that matches the remaining scope, write it ONCE globally so later cards never re-block (`~/.config/antislop/settings.json` → `{"mode":"during"}`), verify it parses as JSON, comment the exact mode name the skill expects, then unblock + dispatch. Treating such a block as an owner decision stalls the whole serial chain for the cost of one small file.
- **Verify recovery before reporting it.** Watch the respawned run past its
  historical failure window — sustained heartbeats, not a single spawn. A
  successful probe proves the key works, NOT that the worker survives spawn;
  announcing "sudah pulih" on probe alone wastes a whole unblock cycle.

## Pitfalls

- **Triage every status notification against the board before acting on it** — deliveries are out of order, so a BLOCK review or a `gave_up` can arrive AFTER the state it describes changed (fix already committed, card already respawned with `consecutive_failures=0`). Compare the event's timestamp against current `status`, `consecutive_failures`, and the newest run outcome first; when the demand is already satisfied, post the numbered evidence (file:line + measured gates) onto the SAME card thread so the next review round cannot relitigate it, and answer the owner with the staleness proof (event time vs heartbeat/process) instead of re-doing work. Never create duplicate cards from a notification alone, because overlapping workers race on a shared workspace.
- **Guard a downstream card against re-doing work that already shipped.**
  When an earlier card has applied AND deployed a fix, comment the downstream
  card the exact applied state (build id, restart time, measured test counts)
  and bind its scope: edit ONLY a gap proven with numbers; if no gap, comment
  "no gap" + evidence and complete. An unguarded worker re-derives the same
  fix from its own analysis and edits deployed code twice — duplicate edits
  are pure regression risk.
- **Never have a worker build in-place under a live service.** A build
  rewrites the served bundle while the running process still points at it, so
  open sessions get HTTP 500s mid-swap even though the service looks healthy.
  Instruct instead: with no code change, verify the deployed build id matches
  `.next/BUILD_ID` plus a typecheck, then complete; after a real code change,
  stop and comment `PERLU RESTART` — the coordinator performs the restart
  (worker `sudo` restarts trip the permission guard).
- **Verify the gate actually landed when creating a gated card.** If `--parent` is built from an unverified variable, a fallback/placeholder id silently yields an UNGATED card that the dispatcher claims immediately — catching it later means reclaim → link (link refuses while the child runs) → unblock, a wasted run each time. Read the created card's `parents` field from the create result or `show` before moving on.
- **Before dispatching auto-decomposed children, validate each child's workspace against the actual Git repository and the canonical parent's worktree.** Auto-decomposition may set `workspace_kind=worktree` while leaving `workspace_path` unset, causing dispatch to fall back to a board default directory outside any Git repository; repeated retries then produce `spawn_failed`/`gave_up` without starting a worker. Inspect `hermes kanban show <child>` and run `git -C <candidate-path> rev-parse --show-toplevel`; if the child has no valid workspace but its scope is already owned by the canonical parent, record the exact spawn evidence in the parent, remove only the redundant dependency links, and continue on the parent's valid worktree. Do not unblock/retry the invalid child or mistake watchdog-written “unblocked” comments for proof that workspace dispatch is fixed. For required distinct work, create a real Git worktree first and set the child workspace explicitly before dispatch.
- **A `kanban create` with a wrong flag creates NOTHING while its output still looks like success.** The CLI prints usage/description text and exits 0 when it doesn't recognize a flag (e.g. `--description`, which does not exist — use `--body`/`--body-file`), so the card never exists and no error surfaces; long bodies also must go through `--body-file <scratch>` because inline text mangles newlines. `--body-file` exists ONLY on `kanban create`; for a long comment use `hermes kanban comment <id> "$(cat <scratch>)"`. Flag quirks are per-subcommand — check the failing subcommand's own help, not the create command's. After every create, confirm the card id in the board DB (`SELECT id,status,assignee FROM tasks WHERE title LIKE ...`) and its parent link — not from the CLI's exit code — before reporting the card created.
- Never describe a stale paused cron as still monitoring; inspect its current state and remove it after the project ends. **Retire with `hermes cron delete <id>`, not `pause`**: a paused monitor can still appear in listings and (observed) keep scheduling runs; only `delete` guarantees silence. Verify by re-running `hermes cron list` after the delete.
- **`hermes cron create` flag quirks (verified):** the agent prompt is a POSITIONAL argument placed AFTER all flags (`--prompt` is not a flag and a wrong flag makes the CLI print usage while exiting 0 — same silent-failure shape as `kanban create`); `--monitor-script` accepts a BARE FILENAME resolved against the profile's scripts dir, not an absolute path; **`--json` does NOT exist on `cron create`** — argparse rejects it, the CLI prints usage and still exits 0, so the job IS created but stdout is not JSON and any parse of it fails. Read the job id from `hermes cron list` instead. The same bare-filename + profile-scripts-dir rule applies to `--script`. After every create, confirm the job in `hermes cron list` (name, schedule, enabled, deliver target) — never trust the exit code alone.
- **Cron report ke owner butuh target chat EKSPLISIT, dan bukti kirimnya diambil dari log gateway.** `--deliver origin` pada job yang dibuat dari CLI tidak membawa binding chat tersimpan, sehingga pengiriman jatuh ke `send_path_degraded` walau job tetap tercatat `succeeded` — owner lalu bilang "tidak ada laporan". Perbaiki dengan target eksplisit (`hermes cron edit <id> --deliver telegram:<chat_id>`, format `platform:chat_id`) lalu buktikan lewat baris `delivered ... message_id=<n>` untuk chat tersebut di log gateway profil. **Jangan menilai delivery dari `cron/deliveries.db` kolom `content`:** ledger itu bisa menyimpan seluruh riwayat dengan `length(content)=0` dan `job_json={}` walau pesan benar-benar terkirim — membacanya sebagai bukti akan menghasilkan laporan "semua gagal" yang keliru, dan sebaliknya `succeeded` saja bukan bukti pesan sampai.
**Classify provider recovery by observed HTTP result.** HTTP 429 establishes rate/quota limiting for that key/model/endpoint; 502/503/504 or timeout indicates gateway/upstream availability and does not establish whether quota reset. After a transient gateway error, reprobe once; do not repeatedly dispatch while probes fail. A later HTTP 200 proves only that the tested key/model/endpoint can make a request now: update the existing card's recovery condition, promote/unblock and dispatch it, then verify fresh worker API calls and advancing state beyond its historical failure interval before claiming sustained recovery. If unblock reports the card is no longer blocked, inspect current state and use the documented promote/requeue path rather than assuming a transition occurred. Never borrow another profile's key or change model/effort. **Verifying ANOTHER profile from inside a session needs `-p <profile>` or `HERMES_HOME=<profile home>` — the bare env var `HERMES_PROFILE` does not switch it.** A live session pins `HERMES_HOME` to the current profile, so `HERMES_PROFILE=koordinator hermes auth list` silently prints the CURRENT profile's pool and the run looks fine; identical credential IDs across two "different" profiles is the tell, not proof of a shared pool. Use `hermes -p <profile> ...` (or `env -u HERMES_RPC_SOCKET -u HERMES_RPC_TOKEN HERMES_HOME=~/.hermes/profiles/<profile> hermes ...`) and confirm DIFFERENT entry IDs before reporting any cross-profile result — a mis-switched probe becomes false evidence in a status report.
- **A 429 that says "usage limit resets in ~Nd" is usually a LOCAL credential-pool bench, not a server wall** — never report it as a multi-day provider outage. The full diagnosis ladder (probe the response BODY not the exit code, probe a second model to scope the bench, `auth reset`, verify every crashed profile, unblock with evidence) plus structural mitigation (2-key pool, hourly healing watchdog, never edit a running worker's `auth.json`, wait-out mode) lives in `references/provider-quota-recovery.md` — load it before touching credentials.
A `kanban create --workspace worktree:<path>` that is NOT inside a real git repo fails at dispatch: `spawn_failed ... is not inside a git repo`, then `gave_up` (failures 2/2) → `blocked`. For a non-git project the WORKING alternative is `--workspace dir:<real project path>` (tested: worker edits the live files in place) — pair it with a pre-dispatch backup tarball of the project, since no VCS exists to roll back to, and with strict sequential gating, because in-place writers on the same files cannot be isolated by branch. Create the git worktree FIRST (`git worktree add -b <branch> <path> <base>` from the project repo), set the card's `workspace_path`/`branch_name` to match, then clear `last_failure_error`+`consecutive_failures` (a stale failure message trips the dispatcher's respawn guard) and `unblock`+`dispatch`. Verify with `git log -1` inside the path before dispatching. Auto-decomposition can silently assign `workspace_kind=worktree` without a valid repo-rooted workspace; inspect each child’s diagnostics and repair/retire it before dispatch, rather than retrying the default path.
- **After a task workspace auto-prunes on task done, its `git worktree` entry goes stale** and the branch still reads as checked out (`fatal: 'X' is already checked out at <deleted path>`) → `git worktree prune` first, then create the next worktree; one worktree cannot hold the same branch twice.
- **Reclaim helpers must honor the card's runtime budget.** Before reclaiming a live run by age, read that task's `max_runtime_seconds`; a global hard-coded timeout (e.g. 2700s) can repeatedly kill legitimate long runs despite a 6-hour card limit. Use the per-card limit with a small safety margin, retain a fallback only for cards lacking a limit, then compile and test the helper against real card values before relying on it.
- **Measure a card's progress in the card's OWN workspace, never the project repo.** A card created with `--workspace worktree:<path>` writes into `<board>/workspaces/<task_id>/repo` on its own branch, so `git status`/`git log` in the main checkout can read perfectly clean while the worker has 26 modified files — and that clean read becomes a false "worker changed nothing" report. Read `SELECT workspace_kind, workspace_path, branch_name FROM tasks WHERE id='<id>'` first, then run git inside that path.
- **Read the head card's own status BEFORE diagnosing `dispatch` printing `Spawned: 0`.** On a board whose gateway dispatcher is live, a freshly created card is usually claimed within seconds and is already `running`, so `Spawned: 0` is the CORRECT answer for that tick — reporting "V1 belum berjalan" from the dispatch line alone is a false alarm. Check `SELECT status, assignee FROM tasks WHERE id='<head>'` plus the worker's `state.db` message count first; only when the head is still `ready`/`todo` does a stale worker holding the concurrency slot explain it: `Spawned: 0` with `--dry-run` saying it would spawn 1 means an orphan `kanban_worker_client` from a finished card still occupies `--max 1`. List them (`ps -eo pid,etimes,args | awk '/kanban_worker_client/ && !/awk/'`), `kill -TERM` the ones whose card is already done, then dispatch again and confirm `Spawned: 1` plus a new `current_run_id`. Never use `pkill -f 'kanban_worker_client'`: the pattern matches the invoking shell's own command line and the call dies with exit -15.
- **A gate card that returns REVISE keeps weight 0 in the progress percentage** until the re-audit APPROVES. Reporting 100% for a chain whose final gate rejected the release destroys trust faster than a low number; show the gate as `done (REVISE)` and the FIX/RE-AUDIT cards as their own weighted rows.
- If a deliverable is a ZIP, verify archive integrity, required launch files, forbidden secrets/sample data, and final on-disk size/hash before sending it.

## State koordinator yang hanya hidup di output terminal AKAN HILANG

Status papan, daftar edge, dan hasil verifikasi yang hanya dicetak ke stdout hilang saat
konteks sesi dipadatkan atau gateway terputus — lalu koordinator tampak "belum pernah
memverifikasi" padahal sudah. Simpan state yang perlu bertahan sebagai BERKAS di repo, bukan hanya output:

- **Body tiap kartu** ditulis ke berkas (mis. `docs/coordination/cards/<Kartu>.md`) lalu
  dipasang dengan `--body-file` → berkas itu jadi sumber kebenaran yang bisa dipulihkan
  kalau kartu rusak/terhapus. Tanpanya, satu kartu yang body-nya hilang tidak bisa dibangun
  ulang tanpa menulis ulang spec dari nol.
- **Berkas status/verifikasi** (mis. `docs/coordination/state.md`: id kartu, edge set,
  bukti yang sudah lolos, gate berikutnya) ditulis ulang tiap beberapa ticket.
- **Bukti** di `docs/evidence/**` — bukan di deskripsi tugas.

Aturan pemulihan setelah gateway/turn terputus: **verifikasi state SEBELUM bertindak, lalu
lanjutkan dari state aktual** — jangan mengulang proyek dari awal, jangan mengulang
pembuatan kartu yang sudah ada, dan jangan melaporkan ulang pekerjaan yang sudah terbukti
selesai. Ambil yang benar-benar belum terverifikasi. **Output tool yang terpotong atau
demote saat kompaksi bukan bukti, dan mengirim ulang call yang sama persis tidak
memulihkannya** — perkecilnya (SELECT kolom spesifik langsung ke board DB) atau pulihkan
keluaran detail sebelumnya dari riwayat sesi, lalu simpan hasilnya ke berkas sebelum
dipakai dalam laporan; klaim "sudah diverifikasi" hanya boleh berdiri di atas hasil yang
benar-benar terbaca.

## Verification

Before reporting completion, verify: all intended cards are done; no unintended card is running; reviewer disposition is explicit; final artifact exists and passes its stated checks; and no project-specific monitor remains enabled.