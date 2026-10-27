---
name: codi-team-dispatch
description: 'Use when assigning work to another Hermes profile/worker.'
version: 1.1.0
author: codi
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [kanban, delegation, orchestration, profiles, token-efficiency]
---

# Team dispatch protocol

## When to Use

Use this whenever the user asks to *assign, schedule, delegate, or command*
work to a profile other than the coordinator (developer, analyst) — or asks
what other workers exist.

User's convention: route ALL work assignments through the coordinator first. The user
speaks casual Indonesian; codi translates each request into a precise task
spec aimed at the target worker's own persona.

## Worker roster (verify with `hermes profile list` before assigning)

Display names are set via `set_profile_display_name` (profile.yaml) — presentation-only;
IDs/aliases stay canonical. The user refers to workers by display name.

| Profile ID | Display name | Persona (from `hermes profile describe <name>`) | Model / effort | Use for |
|---|---|---|---|---|
| `<developer-id>` | **Developer** | Senior SWE, owns the final result | top model / high | implementationation, builds, fixes |
| `<analyst-id>` | **Analyst** | Code analyst / AppSec reviewer, skeptical+constructive | top model / highest effort | review | review, security, audit |
| `<planner-id>` | **Planner** | Program planner, brainstorm→spec | mid model / high | specs, scoping, brainstorming (proxy-only) |
| `<marketing-id>` | **Marketer** | Marketing & advertising strategist | mid model / high | positioning, ads, campaigns, growth strategy |
| `<social-id>` | **Social** | Social media & content specialist | mid model / medium | content calendars, captions, hooks, scripts |
| `<sales-id>` | **Sales analyst** | Sales analyst & strategist | mid model / high | sales data analysis, honest strategy review |
| `skripsi-writer` | **Danu** | Senior Thesis Writer & Academic Editor, 18+ yrs | <top-model>|<mid-model> / high | drafting, struktur bab, bahasa, revisi skripsi |
| `skripsi-writer2` | **Raka** | Senior Thesis Writer & Academic Editor, 18+ yrs (clone Danu) | <top-model>|<mid-model> / high | lane sama dgn Danu — pemecah antrean/bagi bab |
| `skripsi-research` | **Nadia** | Senior Research Methodologist, 18+ yrs | <top-model>|<mid-model> / high | metodologi, sampling, analisis data, kajian pustaka |
| `netops` | **Rick** | Senior NOC/Network Engineer, 20+ yrs (MikroTik/Cisco/Aruba/Juniper/Linux) | <top-model>|<mid-model> / high | jaringan kantor: hardening router, firewall, monitoring, QoS |
| `graphic-designer` | **Reno** | Visual designer — layout, poster, brand assets | <top-model>|<mid-model> / medium | poster, design, visual assets |
| `amanda` | **Amanda** | Orchestrator profile — delegates work across the fleet | <top-model>|<mid-model> / medium | coordination, multi-profile dispatch (use her as orchestrator, not as a worker) |
| `default` | — | base profile; runs the gateway multiplexer | — | never assign work; do not delete |
| `codi` | **Codi** | primary assistant, Telegram-facing | <top-model>|<mid-model> / medium | orchestration only, not card execution |

Marketing team lane rules: marketer=strategi & iklan, social=konten & channel, sales=data penjualan & review jujur. Mereka menyerahkan lintas-lane lewat Codi (tidak ada chat langsung antar profile).

## Standing delegation behavior

When the user asks me to handle work suitable for another profile, I may delegate a clearly scoped task to the appropriate specialist, then review the returned result and report it to the user. Prefer delegation for parallelizable, specialist, or context-heavy work; do straightforward single-step tasks directly. The coordinator remains accountable: do not treat a worker's completion claim as verified, and independently check consequential deliverables or external side effects before reporting success. Respect the user's explicit choice of worker, scope, and approval boundaries.

## Channels

- **One-off work** → kanban card: `kanban_create(title, assignee=<profile>, body=<spec>)`.
  Use the project’s existing board when one is active; `<default-board>` is the
  default only when no project board applies. Durable; auto-requeues on rate
  limit. Route implementation to its specialist worker instead of silently
  doing it yourself when the user asks for delegation or worker-specific keys,
  skills, or persona.
- For a large project, delegate the concrete implementation to the proper
  worker; the coordinator owns acceptance criteria, sequencing, monitoring,
  independent verification, and final report—not competing edits in the same
  workspace.
- **Recurring work** → `hermes -p <profile> cron create '<schedule>' '<prompt>'`
  so the job runs under that profile's home, not codi's.
- **No direct chat between profiles** — coordination happens only via card
  body, comments, and completion summaries.

## Writing the task body

1. Restate the goal in one sentence, from the worker's point of view.
2. Context the worker cannot see (paths, API constraints, user's real intent).
3. Acceptance criteria — how completion will be verified.
4. Language: match the worker's persona register (technical, English or
   Indonesian both understood; be explicit either way).
5. Always instruct: post `kanban_comment` progress notes while working, so
   a rate-limit requeue never loses progress (user-approved requirement).
6. When the task is diagnostic: require the worker to PROVE root cause with
   a measurement (hash/number) in a comment BEFORE the first code edit.
   This found 4/4 real bugs in proyek; guess-first produced misses.
7. State the measurement window for any before/after number (extract vs
   full span) — mismatches there overstated benefit ~3× in review.

## Orchestration lessons (field-proven, Sep–Oct 2026)

- **Check the board before creating a card.** Two sibling cards with
  identical scope both released when the parent finished → two workers
  edited the same files (collision). Dependency gating orders parent→child,
  NOT siblings. Never create a card overlapping a running card's scope.
- **Prepare the environment BEFORE dispatch.** A broken venv burned one
  worker's whole 150-iteration run. Pre-build venv/test deps yourself, then
  hand the card a working command (this host: prefix
  `env -u PYTHONPATH .venv_run/bin/python` — system PYTHONPATH corrupts
  py3.10 venvs).
- **`agent.max_turns` ≠ provider quota.** Iteration-exhaustion timeouts
  (exit with 'Iteration budget exhausted (N/N)') come from the profile's
  `agent.max_turns` (raised 150→500 fleet-wide), not provider proxy limits.
- **Failure vocabulary:** exit 75 = rate limit → auto-requeue, no failure
  counted, no action needed; exit 78 (401/403/404) = sticky block → fix
  credential then `hermes kanban unblock <id>`.
- **Verify deliverables yourself before reporting to user:** confirm the
  worker's card is actually `done`, independently inspect the final artifact,
  recheck live URLs or tests where relevant, and verify archive contents with
  `unzip -t` plus an explicit file listing. A worker summary or a `running`
  card is not completion evidence; do not claim "done" until status and files
  agree.
- **GitHub repo refresh from live webroot:** clone existing repo into profile scratch; establish live source and runtime exclusions first (auth DB/session/invite, TLS cert/key, logs, caches, backups). Compare portable file hashes, sync only intended source/assets/docs (never blanket-copy runtime), update README and `.gitignore`, then run secret + staged-file scans before commit. If the app is mounted under a reverse-proxy prefix, document and template `OFFICE_PREFIX` without changing the live service. Push only after local commit, then verify remote branch SHA/tree with fresh `gh api` reads.
- **Periodic updates:** use a deterministic monitor for long work, but
  independently inspect the deliverable before each progress claim. Keep
  scheduled reports factual and bounded; remove *all* task-specific monitor
  jobs as soon as the card is done, then verify `hermes cron list` has no
  matching jobs. Do not promise a future proactive message unless the delivery
  mechanism is confirmed to reach this chat.
- **Cron CLI gotchas (hermes cron create, terbukti 20 Okt 2026):** (1) `--script` WAJIB path RELATIF ke `~/.hermes/profiles/<profil>/scripts/` — path absolut ditolak ("must be relative to..."), jadi file monitor harus disalin ke folder itu lalu dipanggil pake nama file saja. (2) `--repeat N` = total maksimum run; saat habis, job HILANG dari `hermes cron list` tanpa jejak → perpanjang `--repeat` SEBELUM habis (saya hampir kehilangan anti-macet karena repeat 12 habis). Verifikasi tiap sesi: `hermes cron list | grep <nama>`. (3) Deadline slip saat worker PRODUKTIF (activity <10 mnt) tapi lewat budget → JANGAN reclaim; perpanjang deadline lewat komentar kartu + update konstanta `DEADLINE_EPOCH` di monitor script, tulis alasannya. Reclaim hanya untuk worker tanpa output. (4) `hermes cron runs <name>` bisa kosong walau job jalan (atribut run tak selalu tercatat) — jangan pakai itu sebagai bukti hidup; pakai `hermes cron list` + `Last run`.
- **Format laporan progres (preferensi pemilik, 6 Okt 2026 — WAJIB):** semua
  laporan rutin ke pemilik memakai format berikut (pemilik suka; sudah
  disampaikan ke Codi 2026-10-06, dia simpan juga):
  1. Jam + judul laporan.
  2. Status per kartu/tugas: ID + nama + status (DONE/RUNNING/BLOCKED/TODO)
     + persentase perkiraan.
  3. Aktivitas konkret sejak laporan terakhir, berbukti (file:baris, jumlah
     komentar, angka hasil tes) — bukan klaim kosong.
  4. Masalah & tindakan (atau "tidak ada masalah"); deteksi macet worker
     (umur pesan terakhir di state.db > 600 dtk -> reclaim + dispatch, insiden
     disebutkan).
  5. "Tanpa perubahan" bila nihil.
  Kirim tiap ~15 menit selama pekerjaan aktif; stop + laporan final saat semua
  selesai.
- **Reasoning effort by role:** audit tertinggi untuk verifikator, eksekusi tinggi
  untuk produsen, planner tinggi, koordinator medium — sesuaikan dengan biaya salah.
- **Gerbang independen menangkap klaim optimis** (5 dari 6 milestone proyek
  REVISE di putaran 1) — jangan pangkas verifikasi demi kecepatan. Detail ada di
  skill `large-project-gated-delivery`.
- **Kartu `needs_input` = kebijakan, bukan error.** Putuskan di komentar dengan format:
  opsi + guardrail (angka mentah dilaporkan, konstanta beku, tanpa tuning threshold)
  + "keputusan final, jangan block lagi" → `unblock`.
- **Kirim final hanya setelah kartu `done` dan audit koordinator bersih.**
  Untuk riset web, cek URL secara independen, cocokkan screenshot dengan halaman
  yang dimaksud, lalu verifikasi isi/struktur laporan dan arsip bila ada.
  Untuk software, jalankan ulang suite/gate dan scan artefak (mis. rahasia atau
  environment yang tak boleh dibundel). Jangan klaim audit yang belum dilakukan.
- **File delivery di Telegram:** lampirkan artefak dengan `MEDIA:/absolute/path`
  (atau format native yang tersedia); jangan kirim `file:///...` karena itu
  tautan lokal yang tidak bisa diunduh penerima. Jika hasil riset punya banyak
  file pendukung, buat ZIP terverifikasi, kirim ZIP sebagai lampiran, dan
  sertakan ringkasan singkat serta isi ZIP.
- **Buat kartu berantai = RECLAIM dulu, baru link (proyek berantai 7 Okt 2026):**
  dispatcher melepas 5 kartu serentak begitu dibuat karena `link` belum sempat
  dipasang (semua start di detik yang sama). Urutan aman: `create` semua →
  `reclaim` anak-anak yang lari → `link` → verifikasi edge di `task_links` DB
  papan (`sqlite3 ~/.hermes/kanban/boards/<default-board>/kanban.db`) — jangan
  percaya output CLI link tanpa cek DB.
- **Seed papan dari manifest (terbukti 23 Okt 2026):** `kanban boards create <slug> --name … --default-workdir <repo> --switch`; body multi-baris lewat `create <title> --body-file <path> --json` (`comment` tak punya `--body-file`, tapi `create` punya) dan ambil `id` dari JSON itu; `--parent` boleh berulang saat create; `complete` menolak tanpa bukti → `complete <id> --force --result "…"`; `block` alasannya POSISIONAL (`block <id> --kind capability "…"`), dan `--kind dependency` auto-release begitu semua parent `done`. Seed wajib idempoten: baca `kanban list --json` dan lewati judul yang sudah ada, karena skrip seed yang diulang menggandakan kartu.
- **Anti-loop: `running` ≠ produktif.** Ukur output nyata, bukan status: worker
  `running` tapi TANPA AKTIVITAS APAPUN >10 menit (ambang wajib pemilik 12-Okt-2026:
  maks macet-tanpa-output 10 menit) = kerja tanpa hasil. Sinyal aktivitas = TIGA
  lapis gabungan, JANGAN file saja: (a) file workspace, (b) komentar kartu,
  (c) pesan runtime `<profil>/state.db`. File-saja = FALSE POSITIVE untuk worker
  yang bekerja via browser/API (pekerja via curl/screenshot pernah dikira macet 30 menit padahal jalan).
  Cron monitor juga wajib membawa sinyal macet ini di snapshot. Ladder: (1) steering
  comment minta eksekusi + milestone berbukti dalam 15m; (2) ulang → reclaim + dispatch.
  Kartu `done` yang senyap NORMAL—bedakan macet dari tuntas.
- **Ukur kerja di WORKSPACE kartu, bukan hanya repo utama:** worker dkk.
  mengedit di `workspaces/<id>/webroot` lalu sinkron ke `build/` di akhir
  milestone. `find build/ -newermt` = false negative (mengira tidak ada
  kerja). Sumber kebenaran: `diff -rq workspace vs build/` + komentar
  milestone. Selalu pastikan sinkronisasi workspace→repo sebelum QA final.
- **Cron monitor WAJIB dibatasi otoritasnya:** prompt cron laporan dilarang
  menghapus diri sendiri / mengklaim proyek selesai — batas akhir (QA → ZIP →
  laporan final) urusan koordinator di sesi utama. Salah baca kondisi
  "semua done" membuat laporan 15-menit berhenti padahal 1 kartu masih jalan.
  Cron juga wajib memuat deteksi anti-loop (buta data di workspace) seperti
  ladder di atas, bukan cuma snapshot status.
- **Proses yatim bekas run:** sisa `php -S` / server uji dari run kartu lama
  (mis. verifikator, port terbuka tapi kartu sudah todo) → kill, port dicek bersih;
  jangan biarkan menumpuk antar run.

- **Cron laporan yang hanya MELAPOR tidak memperbaiki (terbukti 8 Okt):**
  `h3d_status_report.py` mencetak `ALERT ... -> Amanda: reclaim+dispatch`
  tapi tidak pernah mengeksekusi → kartu macet selama berjam-jam sementara
  laporan tetap keluar tiap 15 menit (owner melihat "stuck" padahal monitor
  aktif). Pasang cron `--no-agent` TERPISAH yang mengeksekusi ladder
  (`h3d_dispatch_kick.py`: reclaim running stale >600s → `dispatch --json`,
  stdout kosong saat tenang) tiap 5m; laporan tetap perintah terpisah.
  Sekunder: kartu auto-release dari `needs_input` berstatus `todo`, dan
  dispatcher hanya claim `ready` → kartu menganggur tanpa `promote`;
  promote gagal bila induknya belum done (itu normal, dependency_wait).
- **Kartu `--initial-status blocked` + `hermes kanban link` TIDAK auto-unblock** saat parent `done` — blokirnya berlabel `reason: initial_status` (manual), bukan `dependency_wait`. Tercoba 2× (review verifikator): parent selesai tapi child tetap `blocked` sampai koordinator unblock manual → jeda 30-90 menit sunyi yang terlihat seperti "proyek berhenti". Rantai benar: (a) tanpa initial-block / pakai `dependency_wait`, (b) buat child begitu parent `done`, atau (c) monitor auto-unblock. **Selalu cek `hermes kanban show <child>` tepat setelah parent `done` — jangan berasumsi gerbang terbuka.**
- **Kanban command gotchas (terbukti 13 Okt, VO2D R5):** `hermes kanban done <id>` TIDAK ADA → pakai `hermes kanban complete <id>`; `comment --body-file` TIDAK didukung → `comment <id> "$(cat file)"`; `tasks.worker_started_at` = UUID BUKAN timestamp (pembacaan kolom itu sebagai waktu menghasilkan elapsed nonsense — kartu segar terbaca 30 jam over budget); `task_runs.started_at` bisa ISO-8601 sementara `task_comments.created_at` epoch detik dan `state.db messages.timestamp` bisa detik ATAU milidetik di tabel yang sama. Route SEMUA komputasi umur lewat satu `to_epoch()` yang menangani ketiga bentuk + deteksi satuan (`t/1000 if t > 1e12`).
- **Cron laporan 15-menit: scope HARUS dinamis, berhenti hanya bila 0 kartu aktif (VO2D, 13 Okt):** prompt lama "self-delete saat R1–R4 done" menghapus cron saat kartu lanjutan R5 masih ada → monitoring mati beberapa jam, blokir `needs_input` duduk 106 menit tanpa terdeteksi. Benar: derive tracked set dari query dinamis (`SELECT ... WHERE title LIKE 'VO2D-R%'`) supaya kartu baru otomatis ke-track; berhenti hanya bila query dinamis itu menghasilkan NOL baris non-done. Script status juga harus DINAMIS mengikuti board, bukan hardcode daftar kartu — kartu R5+ tidak akan terpantau oleh script hardcode R1–R4.
- **Laporan cron no-agent harus berdasarkan status aktual dan tidak menggantikan final QA:** pastikan parser menangani status kanban yang nyata (termasuk `done`), jangan infer DONE dari kata di output bebas; setelah kartu selesai, verifikasi file dan URL secara langsung, hapus seluruh job terkait, lalu cek ulang daftar cron. `--repeat` terbatas bisa habis atau job bisa sudah tidak tercantum, jadi audit nama semua job proyek, bukan hanya menghapus ID yang diingat.
- **Budget per-step harus selamat dari requeue rate-limit (VO2D R5, 13 Okt):** timer budget yang reset tiap requeue 429 menyembunyikan bahwa wall-clock sudah 5× over budget (90 menit asli → 435+ menit run efektif, kartu tetap kelihatan "aman"). Benar: `active_elapsed = union(interval task_runs) − union(span blocked via task_events kind='blocked'/'unblocked')`; jangan `now − started_at` (menghitung ganda requeue yang tumpang tindih) dan jangan mulai dari run aktif (reset tiap requeue). 5 outcome `rate_limited` (exit 75) bisa menghabiskan budget 90 menit tanpa terlihat — status script WAJIB menjumlahkannya. Kalau wall-clock over tapi worker masih produktif (yang membunuh bukan kemalasan tapi 429), perpanjang budget secara eksplisit (+30/+45m) dengan alasannya di thread kartu — lebih baik daripada reclaim run yang sehat.
- **Cron laporan 15-menit: scope HARUS dinamis, berhenti hanya bila 0 kartu aktif (VO2D, 13 Okt):** prompt lama "self-delete saat R1–R4 done" menghapus cron saat kartu lanjutan R5 masih ada → monitoring mati beberapa jam, blokir `needs_input` duduk 106 menit tanpa terdeteksi. Benar: derive tracked set dari query dinamis (`SELECT ... WHERE title LIKE 'VO2D-R%'`) supaya kartu baru otomatis ke-track; berhenti hanya bila query dinamis itu menghasilkan NOL baris non-done. Script status juga harus DINAMIS mengikuti board, bukan hardcode daftar kartu — kartu R5+ tidak akan terpantau oleh script hardcode R1–R4.

## Token-efficiency discipline (always-on doctrine)

Every request burns the shared provider budget (550 req/5h across the fleet),
and cost is billed per request, not per task. So the coordinator optimises for
*requests avoided*, not just tokens.

- **The `request-token-efficiency` skill is always-on in every profile**
  (`skills.auto_load: ["request-token-efficiency"]`). It injects ~1.1K tokens
  per request: the 12 waste patterns, a binary done-when, locked boundaries,
  and stop conditions. Do not re-explain these rules in a card body — the
  worker already has them. Repeating them in the card wastes tokens twice.
- **`prompt-master` is on-demand, never always-on.** Its SKILL.md is ~8.1K
  tokens; auto-loading it on every request would cost more than it saves.
  Invoke it only when a task genuinely needs prompt engineering:
  `hermes -p <profil> chat -q "/prompt-master <instruksi>"` — or let the
  worker auto-load it when the trigger matches (writing/fixing/improving a
  prompt for a specific AI tool).
- **Write card bodies as specs, not essays.** The 12 waste patterns from the
  doctrine apply directly to delegation: state the outcome, scope, done-when,
  allowed surfaces, output format, and the evidence bar. Cut adjectives, never
  constraints. One task per card.
- **Do not stack deliverables.** A card asking for a PDF *and* a web page
  *and* a spreadsheet usually returns one vague deliverable. Split it.
- **Batch independent work.** Independent reads, searches, and fetches belong
  in one turn, not three. Fewer round-trips = fewer requests = cheaper.
- **Verify, don't re-ask.** A clarifying question costs a full request round.
  Prefer deciding low-stakes details yourself and stating the assumption.
- **Evidence beats re-prompting.** Specify the proof bar once ("test count",
  "file:line refs", "real command output") so the worker returns a finished
  result instead of a partial one you must chase.

## Force-loading skills into a card (owner mandates: workers MUST use named skills)

Owner may require that every worker on a project *have and use* specific
skills. "Have" and "use" are two different verifications:

1. **Have** — list `<profile>/skills/` for each worker profile. Profiles drift:
   a newer copy of the same skill can live only on the coordinator. Compare
   SKILL.md hashes; when they differ, sync the newest over the stale ones
   (`rm -rf <dst> && cp -a <src> <dst>`) so every worker runs identical
   content. Installed ≠ installed everywhere.
2. **Use** — `hermes kanban create --skill <name>` (repeatable) force-loads a
   skill at worker spawn. `kanban edit` has NO `--skill` flag: for cards that
   already exist, write `tasks.skills` directly with a one-shot Python script
   — the column is TEXT holding a JSON list (`json.dumps([...])`) that
   `Task.from_row` parses into a list. Update ALL cards of the chain,
   including done ones (rework/requeue then inherits the mandate).
3. **Verify both layers:** (a) re-read `skills` from the DB and compare with
   the payload; (b) count skill-name occurrences in the worker's `state.db`
   messages — a populated column proves the wiring, not that the worker ever
   opened the skill. Only (b) proves "uses".
4. Comment the mandate once per card so the worker (and every requeue) sees
   why. Schema of `task_comments` is only `id, task_id, author, body,
   created_at` (no `updated_at`) — read `pragma_table_info` before INSERTing
   into tables you did not author.

Pitfalls: python `sqlite3` needs an explicit `con.commit()` — an exception
before it silently rolls the whole loop back (re-run is then safe), but a
half-finished script can also leave partial state, so RE-READ and assert
before reporting success. Make per-card inserts idempotent (skip if the
mandate comment already exists) or dedupe after — re-running a fixed script
blindly duplicates comments. A card already `running` picks up `skills` only
on its next spawn (requeue); for the current run, prove usage via state.db.

## Escalation

- **429 with "usage limit resets in ~Nd" (long reset)** → dispatcher calls it
  terminal (exit 1, `gave_up`, sticky `blocked`). Cause is usually NOT the
  server anymore: after a crash, the **local credential pool benches the key
  for that model** and keeps refusing even after the provider resets.
  Diagnosis ladder (do this BEFORE asking the user):
  1. Probe: `hermes -p <profile> chat -q 'OK' -m <model> --provider anthropic` **and
     read the OUTPUT BODY, never the pipe exit code — a shell pipeline ending
     in another command returns that command's exit code (often 0). A response
     body containing "credentials are rate-limited for <model>" = LOCAL bench
     (even if exit code says 0); a real model answer (e.g. bare "OK") = green.
     Probing wrongly here caused a wasted unblock cycle (2 cards re-crashed at
     60s, 2026-10-02).
  2. Fix: `hermes -p <profile> auth reset anthropic` (clears exhaustion status).
  3. Probe again — success → `hermes kanban unblock <task>` with the evidence
     in `--reason`. Sonnet succeeding while Opus fails confirms a per-model bench.
  4. **Konfirmasi pemulihan = heartbeat bertahan melewati titik crash sebelumnya**
     (±60s) — jangan mengumumkan pulih dari probe saja (crash-terulang 2 Okt).
- **Pool 2-key per profile (ganda kapasitas, otomatis):** `hermes -p <p> auth add
  anthropic --type api-key --api-key <KEY> --label <label>` — credential manual
  otomatis di atas env-seeded; rotasi antar-key terbukti di log `credential_pool`.
  Metadata `base_url` bisa default `api.anthropic.com` tapi endpoint aktual ikut
  `ANTHROPIC_BASE_URL`; dua key di host sama = rotasi mulus, BUKAN jendela kuota
  terpisah.
- **Pool probe per entry (bukti 4-Oct):** uji tiap entry pool (`access_token` atau env-seeded `.env`) dengan `urllib` lokal (token dalam variabel shell, tidak dicetak) → lapor per-ID fingerprint (tanpa mencetak rahasia). Kunci `provider-fallback` 200 tapi `.env` baru 429 → pool sehat tapi rotasi belum terbukti; catat di komentar kartu. Jangan klaim "fallback sudah jalan normal" hanya dari satu entry sehat.
- **Key yang dipaste di chat = kompromi (4-Oct, semua profile):** cabut per profile (`hermes auth remove anthropic <id>` per profile — `program-developer`, `code-analyst`, `harry`, `codi`), regenerasi di provider proxy, `auth add` kembali. Kunci tidak boleh tercetak di chat/file; hanya fingerprint lokal atau label.
- **`needs_input` otorisasi (UI/UX, 4-Oct):** format izin eksplisit menyebutkan path edit (`~/projects/<project>`), batasan (`frontend/`, M6 token, axe 0, reduced-motion), dan penegasan final. Terbukti berhasil: unblock + izin → run 119 heartbeat berlanjut. Ini kebijakan, bukan error.
- **Watchdog cron per jam (`no_agent`, script):** stdout KOSONG saat sehat
  (anti-spam), ladder otomatis untuk blocked-429, JANGAN sentuh `needs_input`,
  umumkan sinyal RAMPUNG saat semua kartu done, **pause job saat workstream
  selesai** (tanpa monitor basi).
- Terminal provider errors (401/403/404) → task blocks for human unblock;
  report to user. For 429 follow the ladder above first — don't report a
  server limit that a local reset clears.
- A Kanban rate-limit requeue (exit 75) does not prove the worker is currently
  unable to work. Follow the 429 ladder: probe the assigned profile’s own
  credentials with its configured provider/model and inspect the response body.
  If a real answer succeeds, do not change its model/key; let the configured
  cooldown expire, then run `hermes kanban dispatch --max 1 --json` and verify
  that a worker was spawned. If it reports `respawn_guarded` with
  `rate_limit_cooldown`, the task is still waiting—do not tell the owner it was
  redispatched. Recheck status/events after the cooldown and dispatch again.
  Report separately: task status, probe result, guard result, and whether a run
  actually started.
- Respect user corrections about delegation immediately. If they say to use
  the worker whose credentials/skills are appropriate, stop coordinator-side
  implementation, assign/update the Kanban card for that specialist, and avoid
  overlapping edits. If the coordinator already created local changes, disclose
  them and leave them isolated rather than silently merging into the worker’s
  workspace.
- **Koordinator boleh eksekusi langsung bila jalur specialist buntu, asalkan
  mandat owner eksplisit.** Kartu yatim (run-nya mati) + mandat jelas (urutan
  langkah eksplisit, credential via vault) = koordinator menuntaskan sendiri,
  lebih cepat daripada requeue ke worker yang kekurangan akses. Wajib: komentar
  kartu menyebut siapa mengeksekusi + bukti terukur; setelah selesai, beri tahu
  owner apa yang tersisa untuk worker. Jangan asumsikan vault kosong cuma karena
  worker tidak melihat shell koordinator — konfirmasi via jalur resmi, tanpa
  minta/mencetak secret di chat. Owner yang menyatakan pengalokasian credential
  (mis. vault sudah diberikan ke worker) sedang mengoreksi alokasi: catat
  segera, lalu laporkan bahwa pekerjaan sudah tuntas agar worker tidak mengulang.
- Never assign to `default`; never modify another profile's skills/cron/memory
  directly unless the user explicitly asks.