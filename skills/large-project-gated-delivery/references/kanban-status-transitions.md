# Transisi status kartu Kanban & jalur pemulihan

Dipanggil saat sebuah kartu tidak mau berjalan, tidak mau ditutup, atau saat "papan diam" harus
dipulihkan tanpa melanggar dependency. Cek status dulu, baru pilih perintahnya.

## Perintah → status yang diterima

| Perintah | Status asal yang sah | Efek | Kalau salah status |
|---|---|---|---|
| `promote <id>` | `todo`, `blocked` | → `ready` / dilepas ke dispatcher | diam / error |
| `unblock <id> --reason` | `blocked`, `scheduled` | hapus hold, `consecutive_failures` direset | **`triage`** bila terdeteksi loop |
| `specify <id>` | `triage` saja | tulis ulang spec (aux LLM) → `todo` | error pada status lain |
| `reclaim <id>` | `running` | lepas claim worker mati | — |
| `block <id> --kind <k> "alasan"` | `todo`/`ready`/`triage` | menahan; alasan posisional, bukan `--reason` | — |
| `complete <id> --result "…"` | `running`/`review` | → `done`; tanpa `--result` ditolak | — |
| `link <parent> <child>` | bebas | tambah edge dependency di `task_links` | anak sudah `running` = balapan kalah |

Tidak ada perintah reopen untuk kartu `done`. Satu-satunya jalan: kartu baru + `link`.

## Peta gejala → penyebab → tindakan

| Gejala | Periksa | Tindakan |
|---|---|---|
| `running=0`, semua kartu `done`/`todo`, tidak ada progress | baca berkas bukti gate kartu terakhir; apakah verdict-nya BLOCKED padahal kartu `done`? | rantai FIX → RE-AUDIT → `link` ke kartu hilir → `dispatch --max 1` |
| Kartu `blocked` tapi semua parent `done` | `block_kind`: kosong = auto-release; `dependency` = menunggu parent; `capability`/`needs_input` = tahanan MANUAL | kalau penyebabnya sudah diperbaiki → `unblock` eksplisit (tidak pernah auto-release); kalau belum → itu blokir basi, laporkan |
| Kartu `triage`, tidak pernah spawn | body kosong? parent terpasang? | pulihkan body → pastikan parent → `specify` atau transisi ke `todo` |
| Anak jalan sebelum parent selesai | `task_links` vs status parent | `reclaim` → `link` → verifikasi edge → dispatch |
| Dua worker di satu profil | kartu `running` per assignee | `reclaim` yang lebih baru; serialkan dengan `link` |
| Worker `running` tapi diam | `max(timestamp)` di tabel `messages` profil (`state.db`), bukan heartbeat | reclaim >12 menit, dispatch ulang, lalu buktikan pesan bertambah |

## `needs_input`: audit the cause chain, not just the label

A `blocked`/`needs_input` row says the card is held; it does not explain why the
latest run stopped. Recover the chain from the board's durable records:

1. Read the current task row and newest `task_runs` entry, including its full
   error/metadata/worker output where available.
2. Read the latest `task_events` payload for the block. Inspect table schema
   first if the event or payload column names are unknown.
3. Read the worker profile's latest messages/tool calls around that run's end.
4. Reconstruct: initiating question → any coordinator answer → worker's next
   action → immediate termination trigger. Distinguish the original blocker
   from the later trigger (e.g. answered dependency decision, then repeated
   search stopped by a guardrail).
5. Before release, resolve any dependency decision from evidence rather than
   assuming the artifact is absent: check the repository/worktree and known local
   caches, identify the exact version and source, and run a minimal isolated
   smoke test when safe. Do not download, vendor, or change project policy merely
   to clear a hold; if approval is genuinely required, ask the owner. Post a
   self-contained comment with the decision/approval, verified artifact path and
   provenance, bounded next action, and acceptance proof. Verify the comment
   landed; then unblock only after the root cause is addressed, and confirm a
   new run plus fresh activity.

Do not treat repeated identical tool calls as progress: if the worker's tail
shows the same query/call repeated, it is a loop. A guardrail message such as
"I stopped retrying" proves termination, not successful resolution. If exact
payloads are truncated in tool output, recover the earlier result from session
history or query only the needed columns/rows; never fill in the cause from a
stale `block_kind` or guess.

## Perintah yang TIDAK ada (jangan diarang)

| Yang dicoba | Hasil | Ganti dengan |
|---|---|---|
| `kanban add` | "not a `hermes kanban` command" | `kanban create` |
| `kanban cancel <id>` | usage/exit 0 tanpa efek | komentar `DITUTUP SEBAGAI DUPLIKAT` + sebut kartu pengganti; jangan hapus riwayat |
| `create --priority high` | tidak diterima (prioritas numerik) | `--priority 10` |
| reopen kartu `done` | tidak ada | kartu baru + `link` |

## Worker dibunuh keliru → `reclaim`, bukan dispatch ulang

Kalau proses worker sah mati di luar kendalinya (watcher/orphan-killer, kill manual salah sasaran), kartunya
tetap `running` dengan `worker_pid` menunjuk proses yang sudah tidak ada (defunct). `dispatch --max 1` akan
mencetak `Spawned: 0` karena kartu dianggap sudah dipegang.

1. `reclaim <id> --reason "worker mati di luar kendali; jalankan ulang"` → status `ready`, `worker_pid` kosong.
2. Tunggu satu siklus dispatcher gateway (beberapa detik), lalu baca `status`,`worker_pid`,`current_run_id`.
   Run baru bisa lahir TANPA perintah `dispatch` Anda — itu normal, bukan kegagalan.
3. Verifikasi `/proc/<pid>` ada dan `count(messages)` profil bertambah dalam 60–90 detik.
4. Jangan kill worker pengganti untuk "membersihkan", dan jangan dispatch lagi saat kartu sudah `running`.

Mulai sekarang, bunuh hanya PID yang diambil dari `tasks.worker_pid` dan hanya bila pesan terakhirnya lebih tua
dari ambang diam; worker berumur <5 menit tidak pernah layak dibunuh.

## Verifikasi setelah setiap transisi

1. `hermes kanban --board <board> list` — status yang diharapkan muncul.
2. `hermes kanban --board <board> show <id>` — body masih utuh, parent/edge benar, tidak ada komentar hilang.
3. `SQL: select status,assignee from tasks where id=?` di `~/.hermes/kanban/boards/<board>/kanban.db`.
4. Untuk dispatch: keluaran JSON memuat `spawned` tidak kosong, lalu `task_runs` punya baris `running` baru.

## Audit topologi rantai: serial vs bintang

Gejala: rantai yang dimaksudnya serial berjalan paralel begitu kartu pertama selesai —
beberapa anak `ready`/`running` bersamaan, sering di profil berbeda. Penyebab: semua anak
di-`link` dari akar yang sama (topologi bintang/fan-out), bukan dari kartu sebelumnya.

Tindakan:
1. `SELECT parent_id, child_id FROM task_links` — lihat bentuk edge set.
2. Bentuk yang benar untuk rantai serial: A→B→C→D (tiap anak punya satu parent = kartu
   sebelumnya). Bentuk yang salah: A→B, A→C, A→D.
3. Hapus edge yang tidak tergolong, lalu pasang rantai berurutan:
   `hermes kanban --board <slug> unlink <parent> <child>` lalu
   `hermes kanban --board <slug> link <parent> <child>`. WAJIB `--board <slug>`: tanpa flag
   itu CLI menulis ke board default, yang bisa berbeda dan kosong — perbaikan lalu hilang
   tanpa efek pada papan target.
4. `link` ditolak saat anak sudah `running` ("child is already running") — `reclaim` anak itu
   dulu, baru `link`, lalu `dispatch --max 1`.
5. Verifikasi ulang edge set, bukan hanya output `link`: anak dengan DUA parent tetap bisa
   jalan begitu salah satunya `done`, jadi paralelisme tersembunyi masih ada.
6. Setelah smoke/tes selesai, baca artefak gate yang disebut di body kartu beserta verdict
   eksplisitnya. Smoke parsial (mis. hanya homepage/health/404) membuktikan respons tersebut
   saja; jangan tutup gate sebelum sanitasi data demo, analisis statis/Graphify, dan seluruh
   bukti bernama pada acceptance tersedia. Catat PASS / FAIL / NOT MEASURED per bukti.

## `blocked` tidak pernah melepas sendiri

Bedakan dua hal yang mudah tertukar:

- **`block_kind=dependency`** — dispatcher melepas sendiri begitu semua parent `done`.
- **`blocked` tanpa `dependency`** (`capability`, `needs_input`, atau hold manual) — TIDAK ada yang
  melepasnya. Parent `done` tidak mengubah apa pun. Kartu tetap `blocked` selamanya sampai ada
  `unblock` eksplisit, walaupun penyebabnya sudah hilang berjam-jam lalu.

Karena itu, setelah kartu FIX yang menutup temuan gate berstatus `done`, langkah berikutnya BUKAN
menunggu: jalankan probe-nya sendiri untuk memastikan angkanya, lalu
`hermes kanban --board <board> unblock <gate-id> --reason "F<n> fixed: <angka sebelum> -> <angka sesudah>"`,
`dispatch --max 1`, dan buktikan run baru + pesan worker bertambah.

## `block_kind` basi membuat papan terlihat masih blocked

`unblock` mengubah `status` tetapi kolom `block_kind` bisa tetap menyimpan nilai lama (mis. `needs_input`)
pada kartu yang kini `running`. Siapa pun yang membaca papan dari kolom itu akan menyimpulkan masih
blocked, lalu mengira pemulihan gagal.

- **Selalu jawab status dari `status`, bukan dari `block_kind`.** `block_kind` bermakna hanya bila
  `status='blocked'`.
- Sebelum melapor "tidak ada blocked", query ganda:
  `select count(*) from tasks where status='blocked';` → harus 0, DAN
  `select substr(id,3,8),status,block_kind from tasks where block_kind is not null;` → harus kosong.
- Kalau nilai basi masih ada, kosongkan hanya untuk baris non-blocked:
  `update tasks set block_kind=null where status!='blocked' and block_kind is not null;`
  Sempit, idempoten, dan tidak menyentuh kartu yang memang tertahan.

## Supervisor: deteksi blokir basi (`BLOCKED-BASI`)

Blokir basi = kartu tertahan padahal semua prasyaratnya sudah `done` dan usianya lewat ambang. Ini
kegagalan senyap yang paling mahal karena semua sinyal kesehatan lain terbaca normal.

- Deteksi: `blocked` + `len(parent belum done) == 0` + usia hold >10 menit → alert `BLOCKED-BASI`
  dengan sisa dependency 0 dan kalimat "semua prasyarat DONE → perlu keputusan buka/re-audit".
- Dedupe per kartu (mis. 60 menit) supaya tick 2 menit tidak mengirim pesan yang sama terus; simpan
  `blocked_since` dan `blocked_alert_at` di state supervisor, hapus entri saat kartu lepas.
- Supervisor **melaporkan**, tidak membuka sendiri: `needs_input` bisa berarti keputusan nyata. Yang
  otomatis hanya dispatch kartu yang sudah `ready`.

## Jangan

- Memperbaiki status dengan `promote` massal dari skrip supervisor — itu menghapus dependency.
- Menutup kartu gate gagal dengan `complete` agar papan terlihat rapi.
- Menghapus baris `task_events`/`task_runs` untuk "membersihkan" riwayat; riwayat itu bukti audit.
- Mengubah body dengan substitusi yang bisa kosong tanpa memeriksa hasilnya.
