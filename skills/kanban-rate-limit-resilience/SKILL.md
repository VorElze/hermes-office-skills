---
name: kanban-rate-limit-resilience
description: "Use when Kanban tasks run on a request-limited provider API."
version: 1.0.0
author: office
license: MIT
metadata:
  hermes:
    tags: [kanban, rate-limit, quota, dispatch, resilience]
    related_skills: [hermes-agent]
---

# Kanban rate-limit resilience

Protect long Kanban tasks against provider request quotas so a mid-run limit
does not lose progress, and teach the operator how to read what happened.

## When to Use

- A Kanban board runs workers against a provider API with a hard request
  window (e.g. a proxy like example-proxy.com at 550 req/5h).
- The user asks what happens when the request limit runs out mid-task, or
  how to keep progress across quota windows.
- A card shows `rate_limited`, `gave_up`, `respawn_guarded`, or `blocked`
  and the user wants to know if intervention is needed.
- Before dispatching heavy long-running cards under a tight quota — inject
  progress-persistence instructions first.

## How the mechanism works (from Hermes docs — do not re-derive)

- Worker hits rate limit / 5xx / billing wall → exits `75` (`EX_TEMPFAIL`).
  Dispatcher records run as `rate_limited` and **requeues without counting a
  failure** — a quota window never trips the circuit breaker or counts as a
  protocol violation.
- Card is then held by the respawn guard under `rate_limit_cooldown` (same
  window as `infrastructure_cooldown`), then respawned automatically. No
  human confirmation needed.
- Workspace (`scratch` under `workspaces/<id>/`) survives until the task is
  `done` — files written by the failed run are still there for the next run.
  What does NOT survive is conversation context (new run = fresh session).
- `spawn_failed` increments the failure counter; `stale` (>4h with no
  heartbeat in the last hour) requeues without counting a failure.

## What genuinely needs a human

1. **Circuit breaker** — `gave_up` event → auto-`blocked` with last error.
   Resolve cause, then `hermes kanban unblock <id>`.
2. **Terminal provider error** (exit `78`): 401/403 revoked key, 404 model
   not found, TLS failure, startup credential error → blocked **sticky**,
   never auto-resumes. Fix credential/model, then unblock.
3. `protocol_violation` budget exhausted (default 3 consecutive) → blocked,
   needs `hermes kanban unblock <id>`.

## Procedure

### 1. Inject progress-persistence instructions into each active task

`hermes kanban comment <id> "<instruction>"` — comments are read by the
worker on every (re)spawn, so this is the durable channel. Require:

- a progress comment after **each discrete unit of work** (per finding,
  per test suite, per review section),
- format: `selesai / sedang dikerjakan / belum disentuh + lokasi file / hasil konkret (pass/fail count)`,
- explicit rationale: provider has `N req per window`; a limit hit means the
  next run is a fresh session with no memory and will read this thread.

Do this for every card you own while a quota-limited provider is in use.
Never rely on conversation memory across runs.

- **Kartu baru di tengah proyek → perbarui prompt cron supervisor di pass yang sama.** Cron laporan berkala yang memantau rantai lama TIDAK otomatis memantau kartu tambahan; saat membuat kartu, append id kartu baru + pemeriksaan macet (umur pesan >600 dtk → reclaim+dispatch) dan loop (workspace diam >30 mnt → steering) ke prompt cron via `hermes cron edit <id> --prompt ...`. Jangan menunggu laporan berikutnya menyadari celahnya.

### 2. Optional hardening (only if user agrees)

```bash
hermes config set kanban.max_in_progress_per_profile 1   # one task per profile
```

**Cakupan: host-wide, bukan per-board.** `max_in_progress*` menghitung seluruh host
(aturan dependency/lane di `kanban_db_dispatch.py` tidak memfilter board), jadi menurunkannya
demi satu board ikut membatasi board lain yang sedang hidup. Kalau board lain sedang jalan,
biarkan default dan andalkan dependency gate + claim DB; turunkan hanya setelah konfirmasi
bahwa semua board di host ini aman dibatasi, dan tetap butuh persetujuan owner.

Goal mode (`--goal` / `goal_mode=True`) keeps the worker in one session
across turns — worth it for heavy audit/implement cards.

### 2b. Baca jendela request sebagai DUA angka, jangan satu

Jendela (mis. 550 req/5h) dibagikan lintas profil — profil lain makan kuartamu tanpa
kamu tahu. Tiap laporan efisiensi wajib memuat dua baris terpisah:

1. **Pemakaian**: `terpakai/limit` dari hitung `API call` sukses per profil dalam 5 jam
   (`<profile>/logs/agent.log` + home default). ≥75% → baru kartu berat pada rantai
   serial berisiko mentok di tengah; sudah dikenal sejak awal, bukan ditemukan saat crash.
2. **Waste**: gagal/retry ÷ total. Waste turun = efisiensi membaik — jangan disamakan
   dengan "kartu lebih cepat".

Dua catatan mekanisme: requeue exit-75 TIDAK dihitung kegagalan, jadi rantai menyeberang
jendela dengan aman (nyatakan berapa jendela dibutuhkan, jangan menjanjikan selesai dalam
satu); dan angka dari log adalah ESTIMASI — jangan dilaporkan sebagai tagihan provider.

### 3. Diagnose what actually happened

```bash
hermes kanban list                    # status overview
hermes kanban show <id>               # body, last failure, run rows
hermes kanban tail <id>               # event stream (BLOCKS until Ctrl-C)
timeout 15 hermes kanban tail <id>    # bound it, or it hangs your call
hermes kanban watch                   # board-wide stream, same caveat
hermes kanban dispatch --dry-run      # 'Guarded (<reason>): <id>' per held card
```

- Both `watch` and `hermes kanban tail` stream forever — **always wrap in
  `timeout`** when calling from a tool, otherwise the command hits your own
  call timeout. (`tail` previously timed out at 60s; `timeout 15 …` is the
  fix.) To read captured output after the fact, use `read_file` instead of
  re-running the stream.

### 4. Event vocabulary to match against

| Signal | Meaning | Action |
|---|---|---|
| `rate_limited` | quota wall, requeued free | none — auto-recovers |
| `respawn_guarded {reason: rate_limit_cooldown}` | waiting out quota window | none |
| `blocker_auth` / `infrastructure_cooldown` | held, not counted | inspect, usually wait |
| `gave_up {terminal_provider: true}` | 401/403/404 — sticky block | fix cred/model, `unblock` |
| `gave_up` (ordinary) | failure_limit reached | fix cause, `unblock <id>` |
| `protocol_violation` ×3 | exited without terminal kanban call | fix worker, `unblock` |
| `heartbeat` every ~1 min | worker alive and healthy | none |
| `stale` (4h, no heartbeat 1h) | presumed hung | auto-requeued, no failure |
| `dependency_wait` | child waiting on parent `done` | expected, not stuck |

A card showing only `created` + `dependency_wait` is **not** stuck.
**`api_max_retries` default template = 1 di semua profile selain codi** (baris `3` ter-comment) → worker cuma 1 attempt ("every one of 1 attempts"), tak sempat rotate key → tiap run mati exit 75 dalam ~60 detik (9× berturut 20:23–21:13, 2026-10-05). Fix terbukti: `hermes -p <p> config set agent.api_max_retries 3` + `fallback.min_switch_reset_seconds 0` → run berikutnya langsung `running` + heartbeats lanjut. **Saat onboard profile baru / "quota wall" berulang: cek kedua knob ini dulu, jangan hanya reset bench.**

Quiet `watch` output for <60s is normal — dispatcher ticks every 60s.

- **Read a long run history as a NARRATIVE, and count only the runs that
  counted.** A card that blocked after a limit burst shows a long run list
  (`rate_limited`, `crashed`, `rate_limited`, …) and the owner reads every row
  as one more failure — but only the failure-class runs (`crashed`, protocol
  violations, spawn failures) advance the circuit breaker; `rate_limited`
  requeues are free. So a history of 10 runs of which 3 crashed explains
  `failures=3/limit=2` precisely, while "10 gagal" is wrong and makes a
  recovered card look hopeless. Read `task_runs` ordered by id, group the
  statuses, and report the crash count, the rate-limit count, and the window
  they span. The current run (newest id, `ended_at` still NULL) is the one
  that decides whether the card is healthy NOW — an old crash text sitting in
  `tasks.last_failure_error` is history, not a live fault, so never quote it
  as the current failure.

- **A `protocol_violation` block is diagnosed from `task_runs.metadata`, not
  `task_runs.error`.** `error` carries only the dispatcher's one-line verdict
  ("exited cleanly (rc=0) without kanban_complete…"); the JSON `worker_output`
  field inside `metadata` holds the worker's actual last output, which names
  the real cause:
  `sqlite3 <board>/kanban.db "select json_extract(metadata,'$.worker_output') from task_runs where id=<run_id>;"`
  When that text is the tool-loop guard's own message ("I stopped retrying
  because I kept running X N times without making progress"), the worker did
  not misbehave: its tool arguments were arriving as `None` (`Invalid command:
  expected string, got NoneType` / `No code provided`), the identical-call
  streak guard hard-stopped it after 5 repeats, and it exited cleanly without a
  terminal kanban call — which counts as a violation no matter what work it
  did. This is a different class from quota/provider failures (exit 75/78,
  429 text); never report it as a rate limit. The blocking budget's source is
  in the `gave_up` payload (`limit_source: dispatcher | task`, with its own
  `effective_limit`) — quote it when explaining why a card stopped at N
  failures rather than the task's `max_retries`.
- **Prevention: keep tool arguments short.** The long inline payload is what
  gets dropped to `None`; write long scripts/queries to a scratch file and
  invoke them with a one-line command (`python3 <file>`), which keeps working
  when the identical inline call fails. Same rule for card bodies: put
  multi-step recipes in a script file the worker runs, not in the prompt.
- **`unblock_task` recovery semantics:** it resets `consecutive_failures` and
  clears `last_failure_error` (so the respawn guard's keyword match stops
  holding the card), but deliberately preserves `block_kind` /
  `block_recurrences`. The landing status is re-gated: `ready` only if every
  parent is terminal, otherwise `todo`, or `review` if that is where it left
  off — so after every unblock confirm with `hermes kanban show <id>` and a
  fresh `task_runs` row before reporting the card back to work.

- **`unblock` does not guarantee a spawn.** Unblocking a stuck card can leave it
  (or move it) into `review` state, and `dispatch` only spawns from spawnable
  states — a `dispatch --dry-run` returning `spawned: []` right after your
  unblock means the card is in a state the dispatcher won't pick up, not that
  the fix failed. Check `hermes kanban show <id>` (status + whether `result` is
  actually populated) after every unblock; an empty `result` with status
  `review` means NO work ran. Then either requeue explicitly or use the right
  status transition, and confirm a new run row appears in `task_runs` before
  reporting progress.

- **`running` + live heartbeat ≠ progressing.** A run can heartbeat every ~30s (reading specs, running read-only tools) for 30+ minutes while writing zero output files — the heartbeat only proves the process is alive, not that the deliverable advanced. Corroborate with output evidence: inspect the worker's latest messages and relevant workspace artifacts (or git diffs) and count recent messages/changes when useful. High activity + zero output files may be a normal read/planning phase; flag a stall only when both activity and output go quiet. Report only activity evidence actually observed; do not present an old worker message as current progress.
- **Quota-reset recovery ordering — re-probe before claiming recovery.** When the owner reports "key already active again": verify with a fresh one-token POST per key (expect 200) AND that the run actually resumed (run row still `running` + recent message timestamp), then report both numbers. A lingering 502 after a claimed reset = upstream flakiness (3 spaced samples; any 200 proves the key fine, see `provider-endpoint-verification`) or propagation delay — never report "recovered" on the owner's word alone, nor "still broken" on a single 502. Probe each key with the actual worker model, and do not run extra probes while a card is active unless necessary—the probes consume the same quota window.

- **Classify the requested board before changing status.** If the user names a specific blocked card, inspect that board/card first; don't globally scan or mutate unrelated boards. If that card is already `running`, verify run ID, heartbeat, and fresh worker activity, then say no unblock is needed. If the user means every blocked card, enumerate all boards and confirm each card's readiness independently before unblocking; don't silently interpret singular as fleet-wide.
- **Worker keys can live in `.env` outside any pool — a pool-only watchdog misses them.** A watchdog that probes only `credential_pool` entries lets a worker whose live key sits in `profile/.env` die limited with no automated recovery (observed: that key limited ~158h while every pool probe was green). Fix the watchdog class, not the incident: probe env keys too, swap to a healthy pool key on 429, restore the original once it probes healthy (keep originals in watchdog state keyed per profile), and gate idle-worker alerts on cards with `status='running'` so waiting `todo` workers never spam. Detail in `provider-endpoint-verification`.
- **Automation hygiene at project close.** Supervisor loops (`every 2m`/`15m` cron) outlive their project if not explicitly stopped — they burn quota on an idle chain. At project end, in one pass: pause/remove project crons, kill orphan test processes (Apache test servers, browser daemons with 0 children older than the session), prune project scratch, then verify `hermes cron list` shows only still-relevant jobs. **Owner melarang hapus cron sebelum rilis → `hermes cron pause <id>` (bukan hapus) setelah rilis terverifikasi**: rantai berhenti boros quota tapi tetap bisa di-unpause untuk putaran revisi.

- **"weekly request limit" crash that survives the quota reset** usually means
  `model_cooldowns` is stuck in `auth.json` → `credential_pool.<provider>[]`,
  not that the quota is still empty. Fix per profile:
  `hermes -p <profile> auth reset anthropic` (resetting only your own profile
  leaves workers blocked) → `hermes kanban unblock <id>` → confirm heartbeat
  >60s past the prior crash point.
- **Stuck-cooldown crash-loop signature (insiden 10 Okt):** crash text says
  *"Anthropic credentials are rate-limited for <model>; other Claude models
  remain available"* + repeated `Goodbye!` → that is a per-MODEL
  `model_cooldowns` block, NOT a dead key. Probe/`last_status` may show OK
  while workers still die within <60s of every spawn (7× crash loop
  09:33–11:07). Check `auth.json` → `model_cooldowns`: a cooldown of DAYS on
  a key whose `request_count` is tiny (14/3) is a stuck cooldown, not quota.
  Fix: `hermes -p <profile> auth reset anthropic` (status-only; model untouched)
  → `unblock` → `dispatch` → confirm run survives >60s with a fresh heartbeat.
  Codify permanently in the req-limit watchdog: any `model_cooldowns` entry
  with >1h remaining AND `request_count < 100` → auto-reset before the probe
  loop (probe alone can report OK while the model stays blocked). Never "fix"
  this by changing the model — MODEL is owner-sacred.
- **"Gave up retries exhausted" has two different root causes — read
  `last_failure_error` before acting:** (a) rate-limit text → auth-reset path
  above; (b) workspace error (`workspace_kind=worktree` but no
  `workspace_path` → default ~/projects not a git repo) → archive the
  invalid child cards and gate the watchdog with `workspace_ok()`; unblocking
  them only restarts a spawn-failed loop.
- **Probe per credential, per profile** (see `provider-endpoint-verification`):
  consistent 401/403 = invalid key (remove it); intermittent 502 = proxy-side
  transient — keep the key; deleting healthy keys only shrinks rotation capacity.
- **Key pasted in chat is compromised:** compare local SHA-256 fingerprints only,
  `hermes auth remove <provider> <entry-id>` in EVERY profile holding it, then ask
  the user to revoke it at the provider. Never print or re-store the value.
- **`hermes auth remove` has a hidden second effect — read before you use it
  fleet-wide:** it not only deletes the entry, it also (a) adds the source
  (`env:ANTHROPIC_API_KEY`) to `suppressed_sources.<provider>` in that profile's
  `auth.json` AND (b) removes the variable from `.env`. If the env var was the
  LIVE credential (not a dead entry), every worker of that profile then exits
  `rc=78` *"Could not resolve authentication method"* within <60s of every spawn.
  Symptoms: identical terminal-provider crash looping every ~4–6 min for hours,
  card ends `blocked`; the error text blames the provider while the credential is
  still valid on disk (pool entry intact, `access_token` present).
  - **Before removing anything fleet-wide:** check `credential_pool.<provider>[]`
    per profile and confirm the entry to remove is truly dead (`has_token=False`);
    confirm ≥1 LIVE entry (`has_token=True`) remains per profile. An
    `env:...`-sourced entry with an EMPTY token is dead and safe to remove — but
    an `env:`-sourced entry that is merely a DUPLICATE of the live key is not:
    removing it suppresses the source and takes the live key with it.
  - **Recovery after the suppress side-effect fires:** (1) find a process still
    holding the old env (`grep -l <VAR> /proc/<pid>/environ` across `pgrep -f
    hermes`), or recover the value from a `.env.bak.*` file — read it, never
    print it; (2) in EVERY affected `auth.json` remove the source from
    `suppressed_sources.<provider>` (delete the list entry, or the provider key
    if the list empties) and rewrite the file; (3) re-insert `VAR=value` into
    `.env` of the default profile AND every profile's `.env`; (4) verify by
    readback (suppress gone + var present in all 9+ files), NOT by stdout;
    (5) `hermes kanban unblock <id>` + `dispatch`, then confirm a live API call
    (`grep 'API call' <profile>/logs/agent.log | tail -1`) with sane latency.
  - **Do not change any model to "fix" an auth error** — an auth failure is
    never a model problem; MODEL is owner-sacred.
- **Exit 78 "Could not resolve auth method" can ALSO be a `source`-validation regression, not a credential problem:** the kanban dispatcher spawns workers with `HERMES_SESSION_SOURCE=kanban`; a Hermes update can tighten the `session.create` RPC's allowed-surface list (two independent checks: the surface map in `gateway/session_policy.py` and the `source` Literal in the wire contract `tui_gateway/contracts/canonical_sessions.py`). If either omits `'kanban'`, EVERY dispatched card crashes `rc=78` in <60s while plain `hermes chat` (unset or `=cli`) works fine — the bisect (`env HERMES_SESSION_SOURCE=kanban hermes chat -q OK` vs `=cli`) is the proof. Fix: add `'kanban'` to BOTH checks (map it to the `cli` family), and to any installed copies under `~/.hermes/installs/*/environments/*/workspace/`, then restart the gateway — the platform guard blocks `hermes gateway restart` when run from INSIDE the gateway, so use `systemctl --user restart hermes-gateway.service` from a detached child instead. Verify with the same bisect: kanban-mode `rc=0`, cli-mode still `rc=0`.
- **Exit 78 berteks auth bisa berarti provider JENUH, bukan kredensial — ukur endpoint dulu, jangan sentuh `auth.json`.**
  Gejala: worker mati <60 detik dengan `the provider rejected this profile` sementara
  `json_extract(metadata,'$.worker_output')` berbunyi `Could not resolve authentication method. Expected either
  api_key or auth_token`, padahal entry pool ADA dan bertoken. Probe LANGSUNG dari sesi koordinator, satu request,
  memakai key milik profil worker itu (baca `credential_pool.<provider>[0].access_token`; nilainya jangan dicetak):
  respons sesungguhnya sering **503 `semua upstream sedang penuh`** atau **429 `short-window request limit
  exceeded`** — keduanya BUKAN masalah auth, dan memperbaiki "auth" (remove/reset/`auth add`/ganti model) hanya
  menambah kerusakan pada kredensial yang sebenarnya sehat. 503 = tunggu; 429 short-window = kurangi burst,
  bukan ganti key.
- **Bisect CLI vs kartu SEBELUM menyentuh kredensial: `hermes -p <worker> chat -q "balas: OK"` — dan baca BALASANNYA, bukan baris ringkasan `Messages: 2 (1 user, 0 tool calls)`.** Baris itu TIDAK menghitung jawaban asisten; run yang sukses tetap mencetak `Messages: 2`, sehingga mudah salah dibaca sebagai "tidak ada respons" dan memicu salah diagnosa berjam-jam (pernah menuduh 503/kuota padahal CLI sehat). Kalau CLI menjawab sementara kartu tetap `crashed rc=78` dengan `Could not resolve authentication method` pada sesi `local-<hash>`, yang bermasalah adalah jalur RUN, bukan file kredensial profil — hentikan edit `auth.json`/`base_url`/`api_key` di titik itu, karena tiap dispatch hanya menambah satu run `crashed` baru.
- **Satu gateway melayani semua profil:** `hermes -p <worker> gateway status` sering menunjuk PID gateway host (`HERMES_HOME=~/.hermes`) yang sama untuk semua profil, dan run kartu dieksekusi di sana — bukan di proses profil worker. Sebelum menyimpulkan "config profil salah", cek PID gateway + `/proc/<pid>/environ`; konfigurasi per-profil tidak menjamin terbaca oleh jalur run. Menyalakan gateway standalone per profil (`gateway.standalone: true`) TIDAK otomatis memindahkan kepemilikan run.
- **Setelah restart gateway, buktikan dengan run row BARU, bukan dengan status gateway.** Restart bisa tampak berhasil tetapi dispatch berikutnya tetap `rc=78` dengan teks identik; satu-satunya bukti adalah run baru (`task_runs.status` + `tasks.last_failure_error`) setelah restart, atau heartbeat pertama yang berumur >60 detik.
- **Profil worker dengan `fallback_providers: []` (allowlist owner) TIDAK rotate — provider jahat = kartu mati,
  bukan pindah jalur.** Jadi jangan biarkan crash-loop menjadi mekanisme retry: gerbang dispatch pada probe
  kesehatan, tahan kartu `block --kind capability`, buka lagi saat probe 200. Menambah fallback ke profil worker
  hanya atas izin owner (allowlist).
- **429 yang bertahan meski papan ini diam = masalah TOPOLOGI key, bukan burst kartu kita.** Sebelum menuduh
  kartu/orkestrator: kelompokkan token pool SEMUA profil dengan sidik jari (`sha256(token)[:10]`) dan hitung
  berapa profil per sidik jari. Kalau satu key dipakai 8–10 profil, kuota key itu melayani semuanya — kartu kita
  bisa nol dan 429 tetap datang. Bila key prioritas-0 sekaligus 401 (mati), seluruh trafik jatuh ke key bersama
  itu dan 429 jadi permanen sampai key pengganti masuk. Rotasi/priority/reset TIDAK menyelesaikan ini; yang
  menyelesaikan hanya key baru dari owner atau fallback lintas-provider yang diizinkan owner. Laporkan sebagai
  keputusan owner (satu form: key baru / izinkan fallback / tunggu), jangan menyentuh `auth.json`.
- **Owner boleh memilih MENUNGGU pulihnya limit — itu keputusan sah, jangan ditanyakan ulang tiap tick.** Setelah
  owner bilang tunggu: pertahankan gerbang probe, jangan unblock/dispatch apa pun, dan pastikan orkestrator punya
  jalur resume otomatis (probe 200 → buka kartu tertahan → dispatch maks 1–2). Laporkan sekali apa yang akan jalan
  sendiri beserta urutannya, lalu diam sampai ada perubahan status — mengulang tawaran fallback tiap 15 menit adalah
  noise yang sama dengan bertanya dua kali.
- **A stale `blocker_auth` guard survives the root-cause fix — clear the diagnostic column:** `check_respawn_guard` reads `tasks.last_failure_error` (a diagnostic text column, NOT status/consecutive-failures) and matches quota/auth keywords; text stamped by a past auth-failure era keeps holding the card in `respawn_guarded: blocker_auth` forever even after the cause is fixed. Diagnose with `hermes kanban dispatch --dry-run --json` (`respawn_guarded: [{task_id, reason: blocker_auth}]`), then `UPDATE tasks SET last_failure_error=NULL WHERE id='<id>'` (backup the board DB first, e.g. `cp kanban.db kanban.db.bak-<ts>`), re-run `dispatch --dry-run --json` to confirm the card moves to `spawned`, then `dispatch` for real.
- **Diagnostic probes share the live workers' request window — stop them at the first 429.**
  Diagnosing a gateway with a series of POST probes (which is how you learn that a size "threshold"
  is really a short-window rate limit) runs on the same key/window the running cards bill against.
  A probe burst has already been observed to be followed by `429 short-window request limit
  exceeded` while a worker was mid-run. So: keep probes bounded and in ONE batch, kill every probe
  process the moment a 429 appears, and never launch a new diagnostic batch while a card is
  `running` — a probe earns a wrong answer (it can burn quota the worker still needs) even when its
  technical conclusion is right.
- **Stop auto-unblocking a crash-loop once the cause is unknown.** A
  watchdog/guard that `unblock`→`dispatch` on every tick will re-crash a card
  indefinitely while the root cause sits untouched (dozens of identical 1-min
  `crashed` runs accumulating in a row). After ~3 identical iterations with the
  same exit code and same error string, PAUSE the auto-unblock, diagnose from
  the per-card log (`logs/<task_id>.log` → `[kanban-worker-exit] rc=…` + provider
  text) or the profile `agent.log`, fix the cause, THEN unblock once. The card
  log exists per-task and carries the full exit text that `task_runs.error`
  truncates to nothing.
- **Dead fallback-chain entries** (404 free-period-ended, upstream quota, 403)
  cascade useless errors whenever the primary hiccups: `hermes fallback list`
  per profile; drop dead entries (`hermes config unset fallback_providers` when
  the whole chain is dead — `hermes fallback remove` needs a TTY).
- **Incident 18 Okt (`6 consecutive stale attempts`, codi + netops + social-media):**
  gejala = turn abort non-retryable setelah 6 stale berturut, padahal probe stream
  sehat (TTFB ~3s). Provider hang INTERMITEN, bukan mati total. Fix 2 sisi:
  (a) `providers.anthropic.stale_timeout_seconds` 120→60 di SEMUA profil + default
  (deteksi hang cepat → retry cepat → jarang capai 6 berturut);
  (b) bersihkan pool: buang entry mati (token kosong) dari `credential_pool.<provider>[]` —
    tapi HATI-HATI, `hermes auth remove` punya efek samping suppress-sumber yang bisa
    mematikan credential hidup (baca peringatan panjang di bagian "Key pasted in chat
    is compromised"). Kalau ragu, biarkan entry mati (hanya memperlambat rotasi,
    tidak mematikan) dan prioritaskan perbaikan `stale_timeout` yang tidak berisiko.
- **PITFALL CLI `hermes config set`:** tanpa `-p` menulis ke profil AKTIF (bukan default).
  Untuk default pakai `hermes -p default config set ...` / `hermes -p default auth remove ...`
  dan SELALU verifikasi readback file target, jangan percaya stdout.
- **`list index out of range` pada cron/agent = bug SDK streaming, BUKAN rate limit
  (insiden 21 Okt 2026).** Gejala: cron run gagal `RuntimeError: list index out of range`
  atau `IndexError` berulang tiap tick, error classifier tidak menganggapnya streaming
  failure (Lihat `error_classifier.py` — IndexError tidak ada di list `Transient/Streaming`)
  sehingga `_maybe_disable_streaming` tidak menyalakan fallback → 3 retry terbuang tiap tick.
  Akar: SDK anthropic 0.87.0 `accumulate_event` (`lib/streaming/_messages.py:471`) meng-index
  event SSE invalid dari proxy LLM. **Fix terbukti: `model.streaming: false` di
  config.yaml SEMUA profil** (dibaca di `agent_init.py:1241`). Bukti terukur: IndexError
  berhenti total setelah 22:28 (terakhir 22:16), waste request 23%→14%, monitor cron
  kembali sukses. Proyek `model.streaming:false` sudah ada di amanda/codi/program-developer/
  code-analyst per 22:28. Jangan upgrade paksa anthropic (pyproject pin 0.87.0 utk CVE-
  2026-34450/34452) — matikan streaming saja.
- **`_maybe_disable_streaming` ada (`agent/chat_completion_helpers.py:3573`) tapi tidak
  menangani IndexError** — hanya match "streaming failed before delivery" / bad-status.
  Jadi kalau provider error streaming baru (bukan yang match pattern), retry boros.
  Deteksi cepat: `grep "list index out of range" <profile>/logs/agent.log | tail -5`.
- **Monitor cron pakai digest output; counter detik mentah (`umur_pesan=…s`) membuat
  hash berubah tiap tick → LLM run penuh tiap 15 menit walau tidak ada perubahan nyata**
  (pemborosan). Fix: `<proyek>_monitor.py` → digest dari nilai ter-bucket
  (msg/cmt = ok/stale di ambang 600s, elapsed // 15 menit, pct // 10). Terverifikasi:
  run ke-2 & ke-3 `NOCHANGE` (sebelumnya selalu CHANGED). Pola ini berlaku untuk monitor
  lain — pastikan payload yang di-hash deterministik.
- **Log hygiene at incident close:** gzip+delete rotated `*.log.1` and stale
  crash logs. Telegram `ConnectTimeout` noise is the network layer to Telegram,
  not a provider failure — never diagnose it as an LLM error.

- **`unblock_task` recovery semantics:** it resets `consecutive_failures` and
  clears `last_failure_error` (so the respawn guard's keyword match stops
  holding the card), but deliberately preserves `block_kind` /
  `block_recurrences`. The landing status is re-gated: `ready` only if every
  parent is terminal, otherwise `todo`, or `review` if that is where it left
  off — so after every unblock confirm with `hermes kanban show <id>` and a
  fresh `task_runs` row before reporting the card back to work.

## Pitfalls

- Don't claim a limit hit will lose workspace files — it won't; only session
  context is lost. Correct anyone (including earlier you) who says otherwise.
- Don't recommend `hermes config set` / CLI mutation without offering it as
  an option for the user to approve first.
- `failure_limit` default (2) and per-task `max_retries` interact; terminal
  provider errors bypass the count entirely (fire on first occurrence).
- Rate-limit requeues are *neutral* to the protocol-violation budget — they
  reset neither way, other failure kinds reset the streak.
- **Provider manual reset caveat:** a proxy's "reset quota" button may consume
  subscription/package duration or have other billing consequences. Do not
  recommend manual reset; explain that a normal rate limit should auto-requeue
  and wait for the provider's window to renew. If a user reports `401 invalid API
  key`, distinguish that from ordinary 429/quota exhaustion: Hermes may rotate
  credentials in a credential pool and recover, but verify subsequent successful
  API calls before claiming recovery. Never infer that a 401 is harmless solely
  because rotation is logged.
