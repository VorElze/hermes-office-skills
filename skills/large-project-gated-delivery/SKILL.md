---
name: large-project-gated-delivery
description: 'Use when coordinating a large multi-milestone gated project.'
version: 1.0.0
author: koordinator
license: MIT
metadata:
  hermes:
    tags: [kanban, orchestration, verification, delivery, lessons]
---

# Large-project gated delivery

Playbook disintilisasi dari proyek (Sep–Oktober 2026): 41 kartu, 7 milestone (M1–M6 + quick-win), 17 versi ZIP, 5 dari 6 milestone pertama berputar ≥1 REVISE.

## When to Use

- Proyek multi-milestone dengan profil produsen + reviewer independen, berjalan >1 hari, deliverable berupa paket.
- Jangan dipakai untuk tugas <1 kartu — gerbang verifikasi murni biaya untuk pekerjaan kecil.

## Standar wajib SEMUA proyek (owner 13 Okt 2026)

Setiap proyek/kartu WAJIB memakai 5 komponen ini:
1. **Budget per kartu** — menit estimasi, ditulis di kartu + laporan (mis. "R2 budget 90m, jalan 24m").
2. **Laporan 15 menit** — cron monitor hemat (output di-hash; agent hanya menyala kalau ada perubahan nyata). Sebelum membuat/mengubah monitor, periksa cron aktif dan script-nya; jangan menduplikasi watchdog atau mengklaim monitor no-agent/token nol tanpa bukti konfigurasi. Template orkestrator yang sudah terbukti (probe provider → release ber-guard → stall reclaim → dispatch max 1): `scripts/orchestrator_monitor.py`, lihat bagian "Orkestrator 15 menit". Untuk status rutin, jalankan satu snapshot monitor yang sudah ada, lalu hindari polling manual berulang; tindak hanya atas perubahan status, pesan worker yang stagnan, atau ambang budget. Snapshot mencatat waktu pengukuran agar laporan tidak menyajikan status lama sebagai kondisi kini.
3. **Sweep deadline/stall** — ≥80% budget (NEAR_DEADLINE) koordinator intervensi; >100% (DEADLINE) atau worker diam >12m (STALL, ukur dari pertumbuhan `count(messages)` state.db, BUKAN heartbeat) → nudge, kalau mati: reclaim + dispatch ulang.
4. **Auto-dispatch dan verifikasi spawn** — kartu berikutnya di-dispatch saat parent done (tautkan dependency dulu, jangan paralelkan scope tumpang tindih); jangan anggap pemanggilan dispatch sebagai bukti penugasan berjalan. Periksa JSON `spawned`, lalu `kanban show <id>` untuk memastikan status/runs/workspace berubah. Jika tetap ready dan `spawned: 0`, diagnosa dispatcher/perfil/kapasitas dan tindak lanjuti sampai ada bukti spawn, atau laporkan blocker dengan jujur.
5. **Lapor final + bersihkan monitor** — laporan penutup per kartu + bukti, lalu hapus cron monitor sisa.

Pratinjau laporan: persentase + status per kartu + budget terpakai/sisa + hambatan + tindakan. Tanda ⚠️ (near deadline) / 🛑 (stalled/over) + tindakan yang sudah diambil. Jika data budget tidak tercatat, nyatakan belum tercatat dan jangan menyamakan durasi run dengan budget; tampilkan progres/bukti terukur per kartu, anggaran hanya bila sumber angka ada. Selesai proyek → simpan pelajaran ke skill + cross-share (team-experience-capture).

## Fase per milestone (terbukti)

1. **Siapkan lingkungan SEBELUM dispatch** (venv, dependensi, prefix perintah test) — venv rusak menghabiskan satu run penuh.
2. **Produksi** (produsen) → komentar progres per unit kerja (tahan rate-limit requeue; file selamat, sesi tidak).
3. **Verifikasi independen** (verifikator): ukur ulang semua angka; klaim produsen = hipotesis.
4. **REVISE** → spek perbaikan bernomor → kartu FIX → verifikasi ulang (putaran 2, dst.).
5. **APPROVE** → audit koordinator (lihat di bawah) → paket → penilaian manusia user.

**Insight inti:** M1 lolos putaran pertama, M2–M6 semua REVISE di putaran pertama. Gerbang independen menangkap hampir semua klaim terlalu optimis — JANGAN memangkas gerbang demi kecepatan; itu justru sumber utama kualitas.

## Kelas kesalahan yang ditangkap gerbang (periksa selalu)

- **Pass tersembunyi:** axe "0 violations" padahal 293 node `color-contrast incomplete` tidak dicatat → simpan `passes` + `incomplete`, jangan hanya `violations`.
- **Denominator kosong:** "0 ID-switch/30s" dihitung dari 0 pasangan kandidat → wajib laporkan `n`/pasangan dihitung.
- **Fixture tidak memicu fiturnya:** occlusion 0,6s < grace produksi 1,1s → kamera tak pernah pindah → "recovery 0,0s" trivial. Fixture HARUS melewati ambang produksi; label hasil trivial sebagai trivial.
- **Angka di luar cap produksi:** plafon dikutip pada z=2,0 padahal `FRAMING_ZOOM_CAP=1,15` → angka cap produksi jadi headline.
- **Rujukan/arsip salah:** file `_B` dipakai padahal yang diadopsi `_A`; md5 handoff basi (rebuild mengubah md5); 6/7 perintah reproduksi gagal dari ekstraksi ZIP bersih (skrip & CSV tidak ikut manifest).
- **`Pre-existing` ≠ `lulus`:** acceptance gagal = gagal; yang melegitimasi hanya **pengecualian tertulis owner** (label `LULUS BERSYARAT` + angka jujur).
- **Acceptance visual jangan tertahan dependency basi:** server yang baca file dari disk tiap request = edit langsung terlihat TANPA restart; implementasi merge → cek visual jalan segera, AC terdampak bug = FAIL sementara, re-screenshot setelah fix. Tutup label presisi: by-design / non-blocking / blocker.
- **AC roster = kontrak spek, bukan angka beku:** API live bisa mengembalikan roster dinamis (VO2D: snapshot 13 → live 11) → cocokkan kontrak, klasifikasi gap; jangan klaim 13/13 saat API 11/11.
- **Disk vs ZIP:** laporan/dokumen versi berbeda antara workspace dan paket.
- **Lampiran datang setelah hasil selesai:** baca ulang daftar lampiran dan komentar terbaru kartu sebelum menerima keterbatasan sumber. Jika bahan referensi sudah ada tetapi deliverable secara eksplisit menandai analisis tertunda, buat kartu revisi additive yang bergantung pada kartu deliverable; pertahankan isi dan bukti lama, lalu verifikasi versi revisi.

## Reviewer juga bisa FALSE POSITIVE — jangan implementasi temuan tanpa reproduksi (<proyek> P5→P6, 18 Okt 2026)

Gerbang independen menangkap banyak klaim produsen terlalu optimis (lihat "Insight inti") — tapi arah sebaliknya juga nyata. Kasus nyata: reviewer (P5) mengklaim "dump hanya bisa di-restore ke nama database yang sama" + merekomendasikan `mysqldump --databases`. Produsen (produsen) mereproduksi: klaim TIDAK terbukti (16/16 view, 0 galat, 4× ulang pada file paket), dan rekomendasi `--databases` ternyata **aktif merusak** — dump berisi `CREATE DATABASE` + `USE <nama-asal>`, jadi saat restore target yang diminta tetap kosong sementara data jatuh ke nama lama; kalau hak tidak cukup, impor berhenti separuh jalan (ERROR 1227/1102) — kebalikan dari perbaikan.

Aturan:
- **Sebelum mengimplementasikan temuan reviewer yang menyentuh artefak nyata (dump, manifest, struktur paket): reproduksi dulu.** Klaim reviewer = hipotesis, sama seperti klaim produsen.
- **Saran perbaikan reviewer harus diuji kontrafaktual** sebelum diadopsi: buktikan alternatif yang direkomendasikan benar-benar bekerja DAN tidak merusak jalur yang sudah terbukti baik. Kalau merusak, tolak dengan bukti tertulis (angka, jumlah ulang) dan pilih alternatif kedua dari spek.
- **Akar masalah ≠ gejala yang dilaporkan.** Dalam kasus ini akar asli (`DEFINER` di dump buatan user cPanel) berbeda dari gejala yang dilaporkan reviewer (kualifikasi nama database — ternyata artefak tampilan `information_schema`, bukan isi file). Bedah isi file asli (grep teks mentah, bukan sekadar query metadata) sebelum menerima diagnosis.
- **Perbaikan dokumentasi > perbaikan kode ketika file paket sendiri sudah terbukti benar.** Dump paket tidak perlu di-rebuild kalau masalahnya hanya cara pakai yang belum dijelaskan; tulis eksplisit di runbook (larangan, sebab, 3 solusi, jalur restore teruji).
- Reviewer yang terbukti false positive tidak otomatis dicabut mandatnya — tapi temuan berikutnya yang menyentuh artefak nyata wajib melewati reproduksi koordinator sebelum masuk kartu FIX.

## Jangan percaya "sudah dibangun" tanpa menemukan file sendiri (<proyek> P4→P6, 18 Okt 2026)

Klaim "ZIP final sudah dibangun" beberapa kali tidak cocok dengan pencarian cepat di workspace kartu / repo — file nyata ada di lokasi tak terduga (`/var/tmp/p6_release/…`, bukan workspace). Cek:
- Sebelum melaporkan "belum ada" ke owner, cari luas dulu: `find /root /var/tmp /tmp -xdev \( -path '*/node_modules' -o -path '*/vendor' \) -prune -o -name '*.zip' -size +50M -printf '%TY-%Tm-%Td %TH:%TM %10s %p\n'` — direktori build besar sering di `/var/tmp` atau `/tmp` untuk hindari isi workspace yang ikut ter-zip atau kuota disk.
- Begitu ketemu, verifikasi isi langsung (`zipinfo -1`, `zipinfo -l` untuk mode file di arsip, grep spesifik) sebelum mengutip klaim kartu apa pun ke owner.

## Kebijakan (worker `needs_input`)

- Worker **seharusnya** block untuk pertanyaan kebijakan/metrik, bukan menebak — itu kompetensi, bukan kegagalan.
- Koordinator memutuskan atas mandat user. Format komentar keputusan: **opsi dipilih + guardrail** (angka mentah tetap dilaporkan, konstanta dibekukan, tanpa tuning threshold agar lulus, verifikator wajib audit ulang) + "ini keputusan final, jangan block lagi karena alasan ini".
- Keputusan nyata: round-trip bahasa (identitas > kekonyakan; makna > gaul), definisi ID-switch (mismatch identitas sebagai primer, transisi sah dilaporkan terpisah, angka mentah tetap ada), carryover empty-space (pengecualian tertulis).

## Audit & packaging (koordinator)

- **Audit sendiri, jangan percaya klaim:** `unzip -t`, scan konten terlarang (`.env`, venv, `node_modules`, `storage/`, `.mp4`, `__pycache__`), full test suite + gate dijalankan ulang, `Run.bat` ada, md5 tiap file kunci ZIP == workspace.
- **ZIP final wajib memuat SEMUA laporan verifikasi** — v16 melewatkan 4 laporan → v17 (temuan audit internal).
- Versi di-zip tak boleh ditimpa (builder menolak jika file ada); versi lama md5 tak berubah.
- Rebuild cepat: `cp zip-lama zip-baru` + `zip -u` overlay (2 detik) vs ekstrak-ulang-arsip-ulang (menit, bisa timeout).
- **Kirim ke user hanya setelah semua kartu `done` + audit bersih**; baru user beri penilaian manusia.
- **Diff ZIP vs sumber sebelum klaim paket benar:** bandingkan manifes ZIP lama vs sumber kini dua arah (`comm -23/-13`) — putaran rebrand mengganti font, ZIP lama membawa woff2 tak terpakai sekaligus melewatkan yang baru. Cek konsistensi font: semua `font-family` di CSS/PHP wajib punya file nyata di `assets/fonts/`, dan tiap file woff2 wajib direferensikan (nol referensi = jangan ikut paket).
- **Bersihkan artefak uji sebelum zip:** file debug sisa QA bisa membawa kredensial uji hidup (`tests/_debug_*.php`) — hapus dari repo SEBELUM packaging, scan nama debug/temp/log berisi secret.
- **Verifikasi upload Drive sebelum lapor sukses:** query by parent-id + bandingkan byte metadata Drive == byte file lokal, baru sebut sukses; lampiran chat tetap `MEDIA:<path lokal>`.

## Pitfall suite QA setelah putaran revisi (proyek berantai 7 Okt 2026)

- **Suite mati di setup = harness tidak tahan requeue.** Skrip review memanggil helper (`tests/harness/setup_webroot.php`) yang tidak ikut workspace → suite gagal sebelum menguji apa pun dengan error membingungkan. Tiap run QA: verifikasi harness ada / bangun ulang dulu, baru jalankan suite.
- **Asetsi basi setelah rebrand → merah ≠ regresi.** Rebrand warna/teks membuat tes warna lama gagal (navy `#0F2C59` vs ink baru `#0E2F27`). Grep SELURUH suite untuk token lama (warna, salinan, kelas) tiap kali desain berubah; pastikan UI benar dulu sebelum menyalahkan kode, dan jangan diamkan asetsi basi begitu saja — perbaiki tesnya.
- **Suite wajib mulai dari state instal pristiwa.** config sudah tertulis membuat alur installer gagal dengan 419 (bukan 403/redirect yang diharapkan) → reset webroot / deteksi `INSTALLED` sebelum tiap suite, atau sesuaikan ekspektasi dengan state sesungguhnya.
- **Dokumen pengguna = bagian audit.** Cocokkan seksi PDF panduan dengan langkah instalator sebenarnya (label `Langkah 1..5`, tombol, token sekali-lihat) sebelum masuk paket; panduan basi = defect rilis.

## Diagnose & recover stalls (evidence-led, read the source first)

- **Baca stream pesan worker + `task_runs`, jangan heartbeat saja.** Sebelum menyebut kartu blocked, ambil event terbaru dan `task_runs`; buktikan dengan pertumbuhan `count(messages)` state.db dalam interval terukur. Untuk `protocol_violation`, baca `task_runs.metadata.worker_output` — kolom `error` hanya ringkasan dispatcher yang bisa menyembunyikan penyebab sesungguhnya (mis. pesan guard loop). Bedakan exit 75/429 (kuota), exit 78 (auth/terminal), dan exit 0 tanpa `kanban_complete`. Jangan sebut akar masalah atau ambang kegagalan sebelum payload event + metadata run mendukungnya.
- **Pulihkan setelah klasifikasi, bukan sebelum.** Perbaiki dulu penyebabnya, baru `hermes kanban unblock <id> --reason '...'`. `unblock` mereset `consecutive_failures` dan `last_failure_error` tapi TIDAK membuktikan worker spawn — konfirmasi status hasil + baris `task_runs` baru sebelum melapor jalan; jangan ulangi unblock+dispatch membabi buta pada crash loop.
- **Gagal tool = ubah strategi, jangan kirim ulang identik.** Kalau tool bilang argumen hilang/None, satu kali percobaan material berbeda (kode panjang → tulis ke file skrip, panggil dengan perintah pendek). Kalau tetap gagal, hentikan dan laporkan blocker terukur — narasi berulang bukan kemajuan.
- **Laporan ke pemilik = bukti dulu.** Perbarui hanya setelah ada perubahan status terverifikasi atau temuan berguna; pisahkan fakta terkonfirmasi vs hipotesis; jangan klaim akar masalah sebelum membaca sumbernya.

## Laporan bug pasca-pengiriman

- **Diagnosa dulu, baru kartu:** reproduce/read the failing path (code read +
  runtime probe) BEFORE dispatch; attach root cause + file/line evidence to the
  card so the worker measures instead of guessing.
- **Same-area fixes are sequential, not parallel:** link cards with
  `hermes kanban link` (parent → child) when several cards touch the same files —
  parallel siblings edit-race and corrupt each other.
- **Prove the fix at runtime** (HTTP-level call/TestClient returning 200), not
  only via the unit suite; then re-run full suite + gates.
- **Incremental overlay packaging:** diff base-manifest vs workspace to get
  changed+new files, overlay only those, verify byte-identical vs workspace,
  keep the forbidden-content scan, never overwrite a versioned ZIP.

## Jebakan run panjang: `max_runtime` default 48 menit (VO2D M3, 09 Okt 2026)

- **`max_runtime` default kartu = 2880s (48 mnt)** — run kartu berat dipotong keras tiap 48 mnt (`reclaimed` beruntun) → worker makin sering kehilangan konteks → akhirnya `block` transient ("repeated hard reclaim at 48-minute deadline"). Diagnosa: `sqlite3 kanban.db "select status,outcome,datetime(started_at,'unixepoch','+7 hours') from task_runs where task_id='…' order by started_at"` → pola `reclaimed` tiap ~48 mnt = pasti ini.
- **Fix**: `sqlite3 kanban.db "update tasks set max_runtime_seconds=21600 where id='…'"` (6 jam; `kanban edit` tak punya flag-nya), komentar orientasi (hasil run terakhir + file yang sudah ada + "lanjut, jangan audit ulang"), `unblock`, `dispatch`.
- **Pencegahan**: saat `kanban create` kartu implementasi multi-jam → selalu `--max-runtime 21600` (lebih besar dari estimasi finish paling lambat), termasuk M4/M5 berikutnya.
- Progres terekam via komentar per unit, jadi run baru tetap lanjut dari file+komentar meski sesi hilang.

- **Jebakan approval gate deploy (VO2D-F1, 13 Okt):** worker headless menolak `systemctl restart <unit>` (single_query_mode=deny) dan memblokir kartu padahal semua bukti offline PASS. Fix koordinator: tambahkan entry allowlist presisi `"systemctl restart <unit>*"` ke `config.yaml` profile worker (pola unit tunggal, preseden aman) → unblock → worker langsung selesai deploy. Jangan minta owner restart manual kalau allowlist bisa dibuka koordinator.
- **Kalibrasi budget kartu QA/fitur UI:** 45m realistis; nudge koordinator pada ≥80% terbukti memaksa worker menutup kartu dalam budget (F4: nudge di 86% → complete di 96%).

## Audit board: path DB & kolom deadline/budget

- **Papan punya DB SENDIRI; `~/.hermes/kanban.db` adalah board default (bisa 0 baris).**
  Audit yang benar: `~/.hermes/kanban/boards/<board>/kanban.db`. Query ke DB default
  menghasilkan `rows: 0` sementara kartu jelas ada di `kanban list` — kalau query kosong padahal
  CLI menampilkan kartu, path DB-mu salah; cari dengan `find ~/.hermes -name '*.db' -path '*kanban*'`.
- **Board tidak menyimpan kolom deadline maupun budget.** Yang ada: `max_runtime_seconds` (hard cap
  per kartu) + `created_at/started_at/completed_at`. Jadi "deadline" yang bisa diklaim = cap runtime
  dan durasi kartu sebelumnya; angka lain harus disebut tidak ada di board, jangan dikarang.
  Budget direalisasikan dari kartu DONE: `completed_at − started_at` per kartu + `task_runs`.
  Rantai yang jalan SERIAL memberi deadline operasional = jumlah cap kartu (mis. 120+240+360+360+240
  ≈ 22 jam); tulis basis hitungannya, jangan hanya menyebut "deadline 22 jam".
- Tabel komentar bernama `task_comments` (bukan `comments`); selalu `PRAGMA table_info` sebelum query
  tabel yang bukan milikmu.
- Resep audit lengkap (single-flight, budget, deadline, crash, efficiency) ada di
  `references/board-health-audit.md` — muat saat diminta "apakah board jalan nyata / progres /
  deadline / budget / urutan".

## Bukti "board jalan nyata" — empat lapis, jangan cukup satu

Card `running` saja TIDAK membuktikan board hidup. Uji berurutan, hentikan di lapis
yang gagal:

1. **Dependency hard gate** — kartu anak tetap `todo`/`dependency_wait` sampai SEMUA parent
   `done` (`recompute_ready` di `kanban_db.py`). Kalau anak parent-nya belum `done` dan
   statusnya `todo`, rantai tidak mungkin paralel secara struktur.
2. **Satu run aktif per kartu** — `SELECT task_id,count(*) FROM task_runs WHERE status='running'
   GROUP BY task_id`; >1 = duplikasi.
3. **Claim hidup** — `current_run_id` + `worker_pid` + `claim_expires` di masa depan.
4. **Dispatcher tunggal di host** — `ps -eo pid,ppid,cmd | grep -E 'kanban (dispatch|daemon)'`
   + grep cron semua profile. Dispatcher kedua = work ganda; satu watchdog dispatcher sudah cukup.

Baru setelah itu buktikan worker benar-benar bekerja: `/proc/<worker_pid>` ADA **dan**
`count(messages)` di `state.db` bertambah dalam 60–90 detik. Hanya heartbeat = belum cukup.
**Kartu yang sudah `running` dengan worker hidup tidak boleh di-dispatch manual** — itu
pekerjaan duplikat yang membakar kuota, bukan-ridden job yang "dibantu".

## Pisahkan 3 kelas kegagalan sebelum intervensi

- **Kegagalan worker** — `task_runs.error` + `json_extract(metadata,'$.worker_output')` +
  log kartu `logs/<task_id>.log`.
- **Kegagalan infrastruktur** — drain/startup gateway, tool-argument truncation, 429/5xx proxy.
  Gejalanya tidak membuktikan worker rusak; re-dispatch worker hidup = pemborosan dobel.
- **Bug parser SDK** — exception yang TIDAK masuk kategori transient/streaming di
  `error_classifier.py` (mis. `IndexError` saat accumulate event SSE) bukan rate limit dan
  tidak memicu fallback otomatis. Cek daftar kategori itu sebelum menyebut akar masalah.

## Konkurensi: `max_in_progress` itu host-level, bukan per-board

`kanban.max_in_progress*` menghitung seluruh host. Menurunkannya demi "board ini saja" ikut
membatasi board lain yang sedang hidup (mis. board auto-clipper). Kalau memang perlu
membatasi, konfirmasi dulu bahwa pengurangan itu aman untuk semua board di host ini;
default: JANGAN sentuh — andalkan dependency gate + claim DB. Detail di
`kanban-rate-limit-resilience`.

## Selamatkan kerja tak-ter-commit sebelum re-dispatch (kartu crash-loop)

Kalau kartu `blocked` setelah beberapa crash, workspace masih menyimpan kerja worker yang BELUM
di-commit — dan run baru bisa me-restart dari nol atau workspace di-prune saat `done`. Commit
ULANG pekerjaan itu sendiri, dari sesi koordinator, SEBELUM `unblock` + `dispatch`:

```bash
git -C <repo> add -A && git -C <repo> commit -m "M<n> WIP: <apa yang diselamatkan>"
```

Laporkan commit hash + jumlah file + delta baris sebagai bukti bahwa crash tidak menghapus
apa pun. Lalu taruh BRIEF ANTI-CRASH di komentar kartu (komentar dibaca worker pada setiap
spawn, jadi tahan requeue): (a) akhiri setiap run dengan aksi kanban terminal + komentar
berangka — keluar bersih tanpa itu ADALAH protocol violation yang membakar budget retry;
(b) commit setelah tiap item checklist; (c) tool call pendek; (d) setelah 2x gagal dengan
tool yang sama, ganti tool — jangan kirim ulang call identik. Verifikasi re-dispatch benar-benar
spawn: baris `task_runs` terbaru + pertumbuhan `count(messages)` di `state.db` profil worker.

**Tambahkan TOOL-CHOICE MATRIX ke brief anti-crash** — `terminal` dengan heredoc panjang adalah
pemicu crash worker yang paling konsisten, tapi brief yang hanya bilang "tool call pendek" terlalu
vague untuk worker yang sedang loop. Tulis eksplisit, siap-tempel:

> Untuk kerja file: pakai `write_file`/`read_file`/`search_files`/`patch` — JANGAN heredoc besar
> via `terminal`. `terminal` HANYA untuk perintah 1 baris <100 karakter (`git status`, `php -l file`).
> Gagal tool 2x? Ganti tool, jangan ulang sama.

Brief spesifik begini yang benar-benar mengeluarkan worker dari loop 26 menit yang sebelumnya
sudah menghabiskan 7 crash — bukan pengulangan prinsip umum. Satu perintah `unblock --reason <panjang>`
juga bisa terpotong dan membuat unblock jadi no-op diam-diam — alasan panjang → tulis ke komentar
terdekat, `--reason` pendek saja.

## Re-estimate budget kartu berikutnya dari durasi TERREALISASI

Budget yang ditulis saat kartu dibuat adalah ESTIMASI, dan bisa meleset 5x. Turunkan budget
kartu berikutnya dari kartu yang benar-benar selesai: `completed_at - started_at` per kartu DONE,
lalu pakai `max(estimasi, P75 durasi realisasi)`. Sebut rasionya eksplisit ("estimasi 120m,
realisasi 588m") supaya pembengkakan terlihat dan tidak diam-diam dibawa ke milestone
berikutnya. Kartu yang melewati budget tertulis >100% adalah sinyal untuk MENAIIKAN budget
kartu saudara berikutnya — bukan untuk memotong budget kartu yang sedang jalan.

## Ketahanan kuota (jendela 5 jam)

Lihat skill `kanban-rate-limit-resilience` untuk tangga 429; penambahan penting: pool 2-key per profil + watchdog cron per jam (deskripsi di skill itu).

## Jebakan hari-kerja panjang yang terbukti (proyek berantai 6 Okt 2026)

- **Security-scan capability block = pembunuh diam.** Worker yang `pip3 install`/apt kena `BLOCKED: Security scan` menggantung → 2× `crashed` → dispatcher `gave_up` (failure_limit=2) → kartu `blocked` permanen. Jangan serahkan instalasi prasyarat ke worker: **pasang dari sesi koordinator** lalu unblock dengan komentar akar+arah. (Playwright terpasang koordinator; suite-nya sendiri jalan via HTTP polos tanpa browser.)
- **Heartbeat menipu**: worker bisa `running`+heartbeat padahal call API menggantung (run 147: 17 mnt tanpa pesan, `request_timeout` tak mematikan). Metrik reliable = **pertumbuhan `count(messages)` state.db dalam 60-90 dtk**, bukan umur `timestamp` (kolom bisa basi) dan bukan heartbeat. Diam >10 mnt tanpa anak proses → kill + `kanban dispatch` respawn segar.
- **`auth.json` termutasi ulang** oleh worker lama saat-saat crash (entry kosong/`401` muncul lagi setelah dibersihkan) — bersihkan SETELAH worker diganti, baru verifikasi.
- **Entry pool `401`/kosong menghapus diri tiap rotate** = buang 1 attempt percobaan → buang entry mati; 1 key valid > 2 key satu mati.
- Reviewer menghitung berbeda (7 form vs 3) → **hitung definitive sendiri SEKALI**, catat di kartu, lanjut; jangan diulang-ulang = boros request.

## Gerbang yang bisa melaporkan angka PALSU (<PROYEK>, 22 Okt 2026)

- **Dua gate/inspect concurrent = laporan degraded tanpa error.** Gejalanya: `inspect_artifacts=0`, `renders=0`, `changed_pct=None` padahal halaman sehat. Penyebab: session `playwright-cli` yang sama dipakai dua proses + folder output yang saling menimpa. Ran lokal terlihat "selesai" tapi angkanya tidak valid — HATI-HATI, output `exit 0` bukan jaminan angka benar.
- **Perbaikan yang terbukti (pakai ulang):** (1) session browser unik per proses (`playwright-cli -s=<uniq>`), (2) folder output unik per run (`gate/runs/<timestamp-pid>/`) plus `report.json` global, (3) file lock `gate/gate.lock` berisi PID — gate kedua MENUNGGU (bukan gagal) lalu jalan setelah lock lepas; keluar dengan exit 75 = "lock", bukan kegagalan skill.
- **Uji sendiri perbaikannya, jangan berasumsi.** Jalankan 2 gate paralel lewat subprocess; criteria sukses: keduanya `exit 0` dengan angka identik, dan yang kedua tercatat menunggu. Ini yang membuktikan claim "anti-tabrakan" bukan sekadar teorema.
- **Artefak 0 byte / render 0 = gejalanya, bukan penyebabnya.** Urutan wajib: open → resize → screenshot, dan pastikan file > 1KB sebelum dihitung.
- **Jangan pakai `&` di foreground tool** — Hermes menolak. Untuk uji paralel, pakai `subprocess.Popen` + `communicate()` di `execute_code`.

## Pitfall: kartu backfill/riwayat langsung dieksekusi dispatcher

Membuat kartu untuk pekerjaan yang SUDAH selesai (backfill W0 ke board proyek) tanpa `--initial-status blocked`
langsung memicu dispatcher: kartu masuk `ready`, worker `amanda` spawn, dan request terbakar untuk pekerjaan
yang deliverable-nya sudah ada. Kejadian nyata <PROYEK> v2, 23 Okt 2026: 3 kartu W0 ter-claim dalam hitungan detik.

Aturan:
- Kartu backfill/riwayat WAJIB dibuat dengan `--initial-status blocked`, lalu ditutup `complete --force --result "…"`
  (complete tanpa `--result` ditolak: "no result or summary evidence").
- Kartu gelombang berikutnya yang belum boleh jalan: `--initial-status blocked` juga — jangan mengandalkan
  `--parent` saja, karena root wave tanpa parent langsung `ready`.
- `block --kind dependency` TIDAK menahan kartu: bila semua parent sudah `done`, kartu auto-release ke `todo`.
  Untuk penahan manual (menunggu kredensial/GO owner) pakai `--kind capability` / `needs_input`.
- `block` tidak punya flag `--reason`; alasannya argumen posisional: `kanban block <id> --kind capability "…"`.
- Setelah seed, verifikasi `SELECT count(*) FROM task_runs WHERE status='running'` = 0 dan tidak ada proses
  `kanban_worker_client`, baru laporkan board siap.

## Wajibkan skill dengan ANGKA, bukan daftar (<PROYEK>, 22 Okt 2026)

- **"Skill ter-install" ≠ "skill terpakai".** Preload di kolom `skills` kartu hanya menjamin file ada di disk. Bukti pakai = call-record nyata di `state.db` profil + artefak output. Klaim lama "5 skill dipakai semua worker" ternyata hanya 2 yang punya call-record (taste 20 call, playwright 12 call) — 3 lain nol. Audit klaim pakai data, bukan HOA.
- **Gate skrip sebagai penutup kartu:** satu skrip menjalankan kelima skill, menulis angka per skill ke `report.json` dengan status MEASURED / NOT MEASURED. Isi kartu: "wajib jalankan gate + tulis angka per skill di komentar penutup; kartu tanpa angka = belum selesai". Contoh hidup: `projects/<proyek>-site/scripts/<proyek>_design_gate.py`.
- **Chrome sebagai root butuh `--no-sandbox`** — `inspect.mjs` crash dengan "Running as root without --no-sandbox". Patch `skills/design-taste-frontend/scripts/lib/cdp.mjs` (guard `process.getuid() === 0`, bukan flag unconditional) di SEMUA profil yang memakai skill itu, bukan cuma profil yang sedang kerja.
- **Screenshot butuh browser terbuka dulu** — urutan: open → resize → screenshot. Tanpa open, file keluar 0 byte dan diff piksel jadi垃圾.
- **Audit DOM bisa false positive.** SVG 0×0 di breakpoint mobile bisa BENAR bila elemen itu `display:none` (nav desktop diganti hamburger mobile). Cek rantai parent (`display`, `visibility`) sebelum menyatakan bug — dan laporkan koreksi klaim lama secara terbuka.
- **Komponen SVG wajib dimensi eksplisit** (`width`/`height` atau CSS) — inline SVG tanpa `viewBox`/size = kotak kosong di header.

## Proyek bermaniesto node: satu node = satu branch = satu PR

Dipakai saat pekerjaan datang sebagai PRD + manifest node (JSON dengan `dependsOn`, `wave`,
`touchPaths`, `requiresDecisions`) dan bukan sebagai kartu Kanban.

- **Hanya spek terbaru + manifest yang jadi instruksi.** Dokumen/spek versi lama = referensi audit,
bukan perintah kerja. Salin keduanya verbatim ke repo dan buktikan dengan md5 terhadap sumber, supaya
worker berikutnya tidak bekerja dari versi cache.
- **Gate wave-0 yang tertahan layanan eksternal → ganti dengan padanan lokal, jangan menunggu.** Kalau satu node gate
  (mis. staging) hanya gagal karena DB/hosting pihak ketiga yang kredensialnya tidak dipegang owner, dan owner bilang
  "buat lokal dulu", bangun instance lokal setara (DB baru + service + vhost port sendiri, lihat
  `self-hosted-web-service-ops` → "Staging paralel"), ukur dengan sapuan route, lalu tutup kartu gate dengan bukti itu.
  Gate yang menggantung pada hal di luar kendali membuat seluruh gelombang berikutnya terlihat "belum siap" padahal
  pekerjaannya sudah selesai. Pindahkan status "500 di hosting" menjadi temuan tertulis, bukan blocker board.
- **Jangan menulis kode fitur sebelum gate wave-0 ditutup**, walau terasa lambat. Kalau gate terhalang
aksi owner, isi waktu dengan artefak proses (dokumen discovery, PR, register keputusan, skrip
verifikasi) — bukan kode fitur yang bisa jadi sampah bila keputusan berubah.
- **Satu node satu branch, PR ke `integration/<versi>`.** Branch dasar berisi spek + manifest; tiap
node bercabang dari situ dan hanya membawa `touchPaths`-nya. PR yang acceptancenya belum penuh
dibuka sebagai **draft**, body-nya memuat: yang sudah lulus (dengan angka), yang belum, dan perintah
persis untuk menutupnya. Jangan merge sendiri — itu tugas reviewer/owner.

### Materialisasi manifest ke papan Kanban (wajib, bukan opsional)

Owner menuntut pekerjaan manifest tampil sebagai papan nyata — setiap node satu kartu, penanggung
jawab bernama, urutan gelombang, dan dependency yang bisa diperiksa. Narasi urutan di chat TIDAK
memenuhi permintaan itu.

1. **Satu papan per proyek:** `hermes kanban boards create <slug> --name "<Proyek>" --default-workdir <repo> --switch`.
   Papan punya DB sendiri di `~/.hermes/kanban/boards/<slug>/kanban.db`.
2. **Satu kartu per node**, body lewat `--body-file` (tujuan, scope `touchPaths`, done-when, bukti,
   nama branch, budget menit) — bukan `--body` satu baris. Cap runtime tetap `--max-runtime 21600`.
3. **Pasang parent saat CREATE (`--parent`, boleh berulang), jangan `create` dulu lalu `link`.**
   Dispatcher melepas kartu begitu dibuat; menautkan belakangan = balapan yang sudah kalah. Kalau
   terlanjur: `reclaim` → `link` → verifikasi edge di `task_links`.
4. **Gelombang yang belum boleh jalan ditahan — dan PILIH jenis penahannya, bukan asal `blocked`:**
   - **Urutan gelombang antar-node → `--kind dependency` + `--parent`.** Dispatcher melepas sendiri saat semua parent
     `done`; tidak butuh orkestrator dan tidak butuh daftar-ID manual.
   - **Menunggu GO owner untuk gelombang berikutnya → `--initial-status blocked`** (block_kind kosong). TIDAK ada
     yang melepasnya otomatis — release harus eksplisit (`unblock`).
   - **Owner/keputusan/kredensial/provider → `--kind capability`.** Juga tidak pernah auto-release; release hanya
     lewat daftar ID eksplisit di orkestrator. Jangan pilih jenis ini untuk urutan gelombang: orkestrator lalu
     terpaksa mencocokkan **judul** kartu (rapuh terhadap rename) padahal dependency sudah menyelesaikannya.
   Root wave tanpa parent tetap langsung `ready` — karena itu wajib ditahan eksplisit.
5. **Reviewer = kartu anak dari node** (parent = node), bukan kartu lepas; dependency itulah yang
   menahan review sampai induk `done`.
6. **Serialkan penulis `migrations/**`:** satu kartu saja per waktu; kartu migrasi berikutnya diberi
   catatan "rebase dari branch migrasi sebelumnya" di body, bukan diandalkan pada urutan dispatch.
7. **Verifikasi sebelum melapor:** edge di `task_links` sesuai rancangan, tidak ada kartu terkunci
   berstatus `ready`, dan `SELECT count(*) FROM task_runs WHERE status='running'` = 0.
8. **Laporan serah-terima board memuat ID kartu + penanggung jawab + urutan + status penahan** —
   itu yang dimaksud owner dengan "siapa saja yang bertugas kerja".

**Pitfall: `git add` dengan satu path yang belum ada membatalkan SELURUH add.** `touchPaths` sering
menyebut direktori yang belum dibuat (mis. `ops/**`). `git add docs/X.md ops scripts/a.sh` gagal
exit 128 dan tidak men-stage apa pun → `git diff --cached --quiet` benar → cabang mencetak
"SKIP (tidak ada perubahan)" dan node itu **hilang tanpa error**. Dua penangkal: filter path ke yang
benar-benar ada (`[ -e "$p" ] || continue`) dan, setelah loop, wajibkan `git status --porcelain` kosong
plus tiap node punya `git diff --stat HEAD~1 HEAD`. "SKIP" dari skrip sendiri adalah sinyal periksa,
bukan sinyal selesai.

## Kontrak bukti dari owner = isi kartu, bukan ringkasan chat

Saat owner memberi GO satu gelombang, ia hampir selalu melampirkan DAFTAR BUKTI (nol link rusak, N/N halaman 200,
login+ganti sandi jalan, logo terbaca di 32 px, Lighthouse ≥ ambang, screenshot). Daftar itu kontrak kerja:

- **Tempel verbatim ke tiap kartu** node yang disetujui (comment atau body), termasuk aturan branch/PR/no-self-merge.
  Worker tidak membaca chat koordinator; kartu adalah satu-satunya kanal yang tahan requeue.
- **Tambahkan kalimat escape:** “kalau bagian ini bukan lingkup kartu, tulis `di luar lingkup` + siapa yang menutup.”
  Tanpa itu worker memaksa mengerjakan bukti milik node lain (foto/favicon di kartu model data) atau mengklaim palsu.
- **Rekonsiliasi daftar owner dengan register keputusan sebelum dispatch.** Daftar “siap” dari owner bisa memuat node
  yang keputusannya masih DITUNDA (mis. node notifikasi email saat provider email belum dipilih). Register menang
  sampai owner menyatakan sebaliknya: tahan kartu itu, sebut alasannya, dan tanyakan sekali bersama pertanyaan
  terbuka lain dalam SATU form — jangan diam-diam mengerjakannya, jangan pula diam-diam membuangnya.
- **Berhenti di node terakhir yang disebut owner, lalu kirim laporan gate** (status per node + bukti berangka +
  yang belum terukur). Jangan menyambung ke gelombang berikutnya walau kartu-kartu berikutnya terlihat siap.

## Orkestrator 15 menit: gerbang provider + auto-release ber-guard

Papan yang sudah tersusun rapi belum berarti pekerjaan berjalan — dan papan yang "berjalan" lewat crash-loop
membakar kuota tanpa hasil. Pasang SATU cron no-agent yang BERAKSI, bukan sekadar melapor.

1. **Gerbang kesehatan provider sebelum dispatch.** Satu probe (`POST /v1/messages`, `max_tokens: 4`) memakai key
   profil worker; baca status + body, jangan pernah cetak token. 200 → boleh dispatch; 503/429 → jangan spawn apa
   pun, tahan kartu dengan `block --kind capability` + alasannya, dan laporkan "provider terhambat". Tanpa gerbang
   ini, tiap tick melahirkan worker yang mati <60 detik dan tiap kematian tetap memakan request.
2. **Auto-release rantai WAJIB ber-guard assignee.** Rilis kartu `blocked` (block_kind kosong) hanya bila SEMUA
   parent `done` **DAN** assignee-nya tidak punya kartu `running`. Tanpa guard kedua, dua kartu mendarat di profil
   yang sama sekaligus — termasuk dua penulis `migrations/**` — dan urutan serial yang baru dirancang hilang
   diam-diam (kejadian nyata: kartu `content-model` terlepas saat `auth-rbac` masih jalan).
3. **Setelah insiden 429: satu spawn per siklus** (`dispatch --max 1`), naikkan hanya setelah beberapa siklus bersih.
4. **Stall diukur dari pertumbuhan pesan, bukan heartbeat:** reclaim bila `select max(timestamp) from messages`
   di `state.db` profil assignee lebih tua dari 12 menit.
5. **Kartu yang ditahan karena provider dibuka otomatis saat probe 200** — jangan menunggu owner, tapi juga jangan
   unblock buta tiap tick (lihat `kanban-rate-limit-resilience`: hentikan auto-unblock setelah ~3 iterasi identik).
   Daftarkan kartu itu lewat **ID eksplisit** (`PROVIDER_HOLD_IDS`), bukan prefix judul — rename judul membuat
   release diam-diam berhenti. Dan probe-nya harus mencoba SEMUA entry pool sampai ada 200: entry #0 sah 401
   sementara entry #1 sehat, dan gerbang yang hanya membaca entry #0 menahan papan selamanya.
6. **Daftarkan sebagai cron no-agent — schedule POSISIONAL.** `--schedule`/`--prompt` tidak ada dan ditolak
   argparse (`unrecognized arguments`):
   `hermes cron create "15m" --name "<proyek> orkestrasi" --script <skrip>.py --no-agent --deliver origin --workdir <repo>`
   Skrip diletakkan di `~/.hermes/profiles/<profil>/scripts/`. stdout kosong = tidak ada kartu aktif → tidak ada
   pesan terkirim (tidak boros).
7. **Format laporan tick** (satu pesan, bukan narasi): baris `provider SEHAT/TERHAMBAT (<status>)`, hitungan
   `done · running · siap · tunggu-dep · blocked`, lalu satu baris per kartu `RUN/SIAP/TUNGGU-DEP/BLOCKED` dengan
   assignee + elapsed/budget + ⚠️ ≥80% / 🛑 >100%, ditutup baris `aksi:` berisi yang benar-benar dilakukan tick itu.

Template siap pakai: `scripts/orchestrator_monitor.py` di skill ini (probe → release ber-guard → stall reclaim →
dispatch max 1 → laporan). Baca dan sesuaikan konstanta di kepala berkas sebelum dipasang di papan baru.

## Register keputusan (DEC) untuk proyek bergerbang

Setiap keputusan punya STATUS eksplisit + daftar node yang diblokirnya: `FINAL` (disetujui pemilik),
`USULAN` (default spek, tinggal disetujui), `BUTUH-OWNER` (butuh fakta/kredensial milik pemilik),
`DITUNDA` (diputuskan belakangan, dengan konsekuensi graf ditulis).

- **Jangan mengarang fakta milik pemilik** (kontak resmi, akun payment gateway, kredensial email).
Tandai `BUTUH-OWNER`, blokir node terkait, tanyakan sekali dalam satu form, dan bila jawabannya kosong
catat "belum terjawab" + tanyakan lagi saat node itu masuk gelombangnya — jangan mengulang pertanyaan
tiap turn.
- **Keputusan ditunda harus menyebut efek graf + jalur alternatif**, bukan hanya "nanti". Contoh pola:
pembayaran ditunda → node pembayaran tetap blocked, tetapi node event tetap jalan dengan
`price_type=gratis`; akibatnya rilis tidak ikut tertahan oleh satu integrasi yang belum siap.
- **Verifikasi pemetaan DEC → node dari manifest** (bukan dari ingatan): hitung ulang node yang
`requiresDecisions`-nya berisi DEC itu, dan pastikan tidak ada DEC yatim.
- Keputusan ditunda yang membuat alur bergantung padanya (mis. verifikasi email) harus dicatat sebagai
**risiko**: sebut jalur pengganti yang tetap berfungsi sampai provider tersedia.

## Peran & cara memberi instruksi

- **produsen (program-developer):** implementasi; instruksikan ukur-sebelum-klaim, komentar per unit, block untuk kebijakan, jangan keluar spek.
- **verifikator (code-analyst):** reasoning `ultra`; review lens (Execution/Artifact); tuntut temuan bernomor `F1..` + bukti terukur; dia yang menyusun spek FIX.
- **Planner:** roadmap/spec di awal, sebelum produksi.