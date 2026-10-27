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

Coordinate planners, implementers, and reviewers through durable Kanban cards. Profiles do not chat directly; card bodies, comments, artifacts, and dependencies are the handoff protocol.

## When to Use

- A user asks for a planning meeting, multi-worker project, implementation followed by review, or recurring progress updates.
- Several profiles need to work on one shared deliverable.

Don't use for a single self-contained task that one worker can finish without a handoff.

## Procedure

1. **Inspect before acting.** Read the current board, task bodies, statuses, dependencies, latest comments, and existing artifacts. Reuse or update an existing card when its scope already matches; never create a duplicate before checking.
2. **Resolve the brief and preflight tools.** Capture the user's goal, constraints, inputs, output language, and acceptance criteria. Ask for missing user-only facts (such as test observations, credentials, their personal experience) rather than inventing them — and only for those: for every other open decision, adopt the documented recommendation (planner's proposed order, default tooling) and act without pausing for approval; **exception — decisions that change what "pass" means** (a metric definition, an acceptance threshold, a scope cut) belong to the user: present the options with ONE recommended choice and let them pick, because silently redefining acceptance criteria is the orchestrator grading its own homework. When the user picks a redefinition, bind the fix card with guards: report the RAW pre-redefinition number alongside the new definition (never bury it), never tune thresholds to force a pass, and require the reviewer to audit the redefinition itself before any APPROVE. Record adopted decisions as a comment on the workstream's anchor card so the rationale survives requeues. If a hard acceptance criterion remains unmet but is pre-existing, do not silently reinterpret it as passing: get an explicit owner decision (or act only within a clearly delegated decision mandate), record a written exception and the measured miss, label the result CONDITIONAL PASS rather than full pass, and retain reviewer sign-off on that exception. Keep behavioral regressions and inherited baseline failures distinct. Copy user-provided assets to the shared workspace when workers need access; preserve originals and do not upload assets externally. Identify install/build/test prerequisites before dispatch; where safe, install them from the orchestrator session and run a smoke test so the worker starts from a usable environment. Match new dev-tool major versions to the project's existing toolchain before installing. If a worker gets a `capability` block because its-session security scan times out, don't tell it to bypass the guard: install/verify the prerequisite from the orchestrator session, comment exact state and resume point, then unblock.
3. **Choose the smallest safe graph.** For a planning/review meeting, create a planner/lead card and one reviewer child gated on the lead.
   **Design-first fan-out, BEFORE any card:** when the user asks for a rancangan first ("bentuk rancangannya dulu … lalu beritahu saya siapa yang ditugaskan"), run ONE `delegate_task` unit per design lens in parallel, all read-only (no file edits): planner → spec + acceptance criteria, implementer → technical design against the source, reviewer → UX/quality review of the proposed flow. Consolidate their outputs YOURSELF into one design doc in the project dir before creating any execution card — subagents do not talk to each other, and a design that exists only as three scattered summaries will be re-derived by the workers. Then report the roster by display name BEFORE dispatching: the user tracks the team by name and has asked "apakah tidak melibatkan planner?" when the planner was absent from a design phase — whenever a phase produces a spec, the planner is part of it even if the user only names builders. **During consolidation, the user's written brief outranks every subagent recommendation** (a reviewer proposing the opposite voting model than the brief specifies): adopt the brief, and record the conflict + your resolution in the design doc rather than silently picking a side. For implementation, create an implementer card and a reviewer child gated on implementation. Make each card's deliverable, scope boundary, evidence required, and completion test explicit.
   **Review loop:** the reviewer may return `REVISE` with findings numbered and located (file:line). When that happens, create a revision card gated on the reviewer, whose body lists each finding and what evidence the fix must show; then a round-2 reviewer card gated on the revision. **Cap the loop at one blocking revision round** — the round-2 verdict must be APPROVE or a bounded set of genuinely-blocking findings, so a review cannot expand scope indefinitely. Verify claims baris-per-baris (`fixed per T-N`), never on the implementer's word alone.
   **The orchestrator owns the loop's integrity, not the reviewer.** A reviewer sometimes closes its card with REVISE and creates neither the fix card nor the round-2 review — the milestone then hangs forever. Scan for that gap after every REVISE verdict (verify card `done` + no FIX/round-2 child) and create the missing card yourself; in specs that depend on a policy decision the REVISE raised, write the decision into the fix card's thread first.
   **Trace the whole verdict chain when reporting a milestone's status.** The verification card's LAST comment is usually the initial REVISE — the APPROVE lives on the fix/round-N card (or a later review comment). Report a milestone as approved only after finding an explicit APPROVE at the END of the chain (verify → fix → review round-N), and when asked "is X still REVISE?" walk every card carrying that milestone's tag rather than reading one card.
4. **Prevent workspace collisions.** Before creating a card, compare its files and deliverables with every active card. Dependency gating orders parent→child; it does NOT serialize siblings. If scope overlaps, add the new requirement to the existing card thread or make it a gated child—never run two writers on the same files concurrently.
5. **Make progress durable.** Require comments after meaningful units of work: completed / in progress / not started, file or artifact path, and concrete result. Tell workers to reread their card thread after a rate-limit respawn; new runs have fresh conversation context.
6. **Monitor only when requested, and match the gate to the reporting contract.** For periodic updates, create one change-detecting monitor (fixed field order, no wall-clock noise) and deliver on actual changes — but if the user asked for a fixed cadence (e.g. "lapor setiap 15 menit" while work runs), append a `tick: HH:MM` heartbeat line so the bytes change every tick during active runs; change-only output goes silent whenever a worker posts no comments for a stretch and the user asks why reports stopped. The heartbeat costs nothing at rest because the job is paused/removed at completion. Verify it is enabled, and prove delivery once (`cronjob_manage action='run'` must not come back `no_change (agent run suppressed)`). When the workstream is complete, pause or remove the cron and delete its one-off monitor script if no longer useful.
7. **Review evidence independently.** Do not equate a worker's completion claim with acceptance. Verify artifact path and integrity yourself; have the reviewer independently reproduce critical measurements, tests, and packaging checks. Report PASS / FAIL / NOT MEASURED distinctly, with limitations. When an owner-approved exception is used, state both the original acceptance failure and the bounded conditional disposition; never summarize it as an unqualified APPROVE or full pass.
   **Reviewer failure taxonomy — instruct the reviewer to hunt these specifically:** hidden passes (tool reports `violations` but drops `incomplete`/untested nodes — require all three), empty denominators (a 0/0 result quoted as a pass — require `n` on every rate), fixtures that never trigger the production branch (test inputs must cross the real timeout/grace threshold, else label the result trivial), numbers measured outside production caps quoted as shipped performance, stale references/hashes (report newer than the archive; disk vs packaged copies diverge), and `pre-existing` used as an excuse for an unmet criterion (attribution is not acceptance — only a written owner exception with the failing number makes it a conditional pass). The high first-round REVISE rate this taxonomy produces is the gate working; do not weaken the gate to shorten the loop.
8. **Close the loop.** Summarize decisions, remaining risks, and exact deliverable paths to the user. Ask for approval before converting a planning roadmap into implementation work when the user requested planning first.

## Auto-advance: jangan biarkan rantai berhenti (lesson proyek berantai 2026-10-05/06)

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
   (`every 2m`, deliver `local`, `failure-deliver telegram`, self-pause saat
   tugas tuntas). Prompt supervisor = state machine eksplisit: ada `running`?
   diam; FIX done → buat+dispatch kartu REVIEW; REVIEW done → baca verdict
   (REVISE → buat kartu fix baru / APPROVE → koordinator audit+packaging+KIRIM
   deliverable sendiri, lalu pause cron laporan + self-pause); tangani macet
   (rate-limit → auth reset, needs_input → putuskan dengan guardrail);
   anti-duplikat (cek board sebelum create); senyap kecuali deliverable final.
   Contoh prompt: cron `proyek berantai SUPERVISOR` (job <job-id>).
3. Gerbang review TETAP jangan dipangkas demi cepat — yang dipasang supervisor
   adalah **transisi otomatis antar-gerbang**, bukan penghapusan gerbangnya.

## Recovering and answering blocked cards

A card blocked with `kind: needs_input` is a worker's question, not a
failure — it obeyed its guard and stopped rather than guessing. Resolve any
block through the card, then confirm recovery:

- **Comment first, then unblock.** The comment is the only thing the
  respawned run reads: decision, safeguards, and the next concrete step,
  self-contained (no references to chat).
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
  first — a worker may have auto-decomposed the card into linked sub-cards
  while blocked; let those sub-cards run rather than unlinking dependencies.
- **A block saying the task workspace is empty and the project lives outside it** is an authorization request, not a failure or an API problem: the worker refused to edit files it was never granted. Resolve it by verifying the canonical project path and the card's scope, then posting a durable comment that authorizes edits ONLY in that path (name the allowed subdirs/files, the tests it may touch, and the prohibited areas — Hermes profile/config/kanban state), then unblock once and confirm a sustained heartbeat. Do not copy the whole project into the scratch workspace when authorizing the real path is safe, and never grant blanket filesystem access.
- **Verify recovery before reporting it.** Watch the respawned run past its
  historical failure window — sustained heartbeats, not a single spawn. A
  successful probe proves the key works, NOT that the worker survives spawn;
  announcing "sudah pulih" on probe alone wastes a whole unblock cycle.

## Pitfalls

- Never create duplicate cards based only on a notification; inspect the board first, because overlapping workers may race on a shared workspace.
- **Verify the gate actually landed when creating a gated card.** If `--parent` is built from an unverified variable, a fallback/placeholder id silently yields an UNGATED card that the dispatcher claims immediately — catching it later means reclaim → link (link refuses while the child runs) → unblock, a wasted run each time. Read the created card's `parents` field from the create result or `show` before moving on.
- Never describe a stale paused cron as still monitoring; inspect its current state and remove it after the project ends.
- A rate-limit exit (75) is recoverable and requeued; a terminal auth/provider error (78) needs intervention. Keep project progress in task comments so requeues can resume.
- **A 429 that says "usage limit resets in ~Nd" is usually a LOCAL credential-pool bench, not a server wall.** After a worker crash, the pool benches the key *per model* and keeps refusing even after the provider window renews (other models on the same key succeed — that asymmetry is the tell). Diagnosis ladder before telling the user quota is out for days: (1) probe the model `hermes -p <profile> chat -q 'OK' -m <model> --provider anthropic` — "credentials are rate-limited for <model>; other Claude models remain available" = local bench; (2) probe a different model on the same key to confirm per-model scope; (3) `hermes -p <profile> auth reset <provider>`; (4) probe again, then `hermes kanban unblock <id>` citing the evidence. Never report a multi-day wall off the error text alone. **Read a probe's response BODY, not the shell exit code** — a pipeline ending in another command returns that command's exit code, which says nothing about whether the key is benched; only the message text distinguishes a local bench from a green call. **Reset EVERY affected profile, not just the one you're acting under** — `auth reset` clears `model_cooldowns` in that profile's own `auth.json`, so running it for one profile leaves the others benched; verify afterward that `model_cooldowns` is empty in each crashed profile's `auth.json` before unblocking.
- If a deliverable is a ZIP, verify archive integrity, required launch files, forbidden secrets/sample data, and final on-disk size/hash before sending it.
- **Mitigate quota structurally, not just reactively.** The 429 ladder above recovers one crash; two more measures cut crash frequency: (a) a **2-key credential pool** per heavy profile — `hermes -p <profile> auth add anthropic --type api-key --api-key <KEY> --label <label>` (manually added credentials outrank env-seeded ones; two keys on the SAME host rotate smoothly but share one quota window — they buy continuity, not a second window; point `ANTHROPIC_BASE_URL` per profile so both keys hit the intended endpoint); (b) an **hourly healing watchdog** (`cronjob_manage` `schedule='every hour'`, `no_agent=true`, deterministic script) that runs the auth-reset/probe/unblock ladder on blocked-429 cards, skips `needs_input` cards (those are decision requests), prints nothing while healthy, and announces a single RAMPUNG line when the board empties. Pause/remove it when the workstream ends.

## Verification

Before reporting completion, verify: all intended cards are done; no unintended card is running; reviewer disposition is explicit; final artifact exists and passes its stated checks; and no project-specific monitor remains enabled.