---
name: web-app-delivery-playbook
description: "Use when building or deploying a web app or site."
version: 1.1.0
author: Amanda (koordinator kantor)
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [delivery, web, deploy, kanban, gate, evidence]
    related_skills: [large-project-gated-delivery, multi-profile-project-orchestration, codi-team-dispatch, cleo-hosting, verification-before-completion, web-design-guidelines]
---

# Web App Delivery Playbook

Jalur kerja baku untuk permintaan "buat aplikasi / bikin website / deploy aplikasi /
rilis web". Tujuannya: tanpa owner menyebut satu per satu, semua skill, plugin, dan
alat ukur yang sudah terbukti dipakai otomatis masuk ke rencana kerja.

Skill ini TIDAK menyalin isi skill lain. Ia menetapkan siapa membaca apa, urutan
kartu, dan bukti apa yang dianggap lulus.

## When to Use — frasa pemicu

"buat aplikasi", "bikin website", "bangun web app", "deploy aplikasi", "rilis
website", "sprint aplikasi", "aplikasi baru", "parity visual", "perbaiki tampilan
web" — begitu salah satunya muncul, pakai playbook ini, jangan mengarang alur baru.

## Aturan induk (tidak boleh dilanggar)

1. **Satu kartu `running` pada satu waktu.** Kartu berikutnya dibuat `blocked` dan
di-`link` sebagai anak. Driver cron 5 menit hanya membuka berikutnya setelah
pendahulu `done` DAN verdict-nya dibaca.
2. **`done` ≠ lulus.** Verdict harus tertulis (APPROVE/REVISE + angka). Worker yang
menutup kartu tanpa verdict dianggap belum selesai; koordinator menegakkan verdict
sendiri dari berkas bukti mentah, lalu mencatatnya.
3. **Gate independen di akhir tiap kelompok**, dikerjakan profil berbeda dari yang
menulis kode (`code-analyst`), tidak boleh satu menit pun menulis bersamaan.
4. **Jangan turunkan ambang** untuk mempercepat rilis. REVISE → kartu FIX → kartu
REGRESI → baru rilis.
5. **Deploy hanya setelah izin eksplisit owner.** Backup docroot + DB sebelum
menyalin berkas, bukan sesudah.
6. **Laporan tiap 15 menit** dengan format owner: header 📊, 🎯 target+sisa,
📈 %+bar, bullet per kartu (status/assignee/run-budget), ▶ aktif · ⛔ blocked,
satu baris `langkah:`.

## Peran per profil

| Peran | Profil | Kartu yang dipegang |
|---|---|---|
| Koordinator | `amanda` | memecah lingkup, membuat/melink kartu, memantau, menegakkan verdict, deploy, lapor |
| Perencana | `harry` | PRD, acceptance criteria terukur, pembagian milestone |
| Developer | `program-developer` | fondasi UI, layar, form, tabel, fix temuan gate |
| Desainer | `graphic-designer` | acuan visual, mockup, token desain, screenshot-to-code |
| Gate/audit | `code-analyst` | audit independen, regresi, verdict tertulis |

`graphic-designer` hanya dipakai kalau lingkupnya desain murni; kalau sprint
menyentuh kode aplikasi, developer yang menulis. Pernah macet 70 menit tanpa satu
tulisan karena disuruh menulis kode aplikasi.

## Inventaris yang dipakai (terbukti di SIRAGA)

### amanda (koordinator)
- Skill: `large-project-gated-delivery`, `multi-profile-project-orchestration`,
  `codi-team-dispatch`, `cleo-hosting`, `kanban-rate-limit-resilience`,
  `task-progress-reporting`, `verification-before-completion`, `team-experience-capture`.
- Plugin: `graphify-bridge` (query graph offline), `deskrpg`
  (artifact_save, propose_kanban_card), MCP `claude-mem`
  (work_state_write/save_memory) dan `chrome-devtools`.
- Alat (teramati 5.475 panggilan): `execute_code` (agregasi/ukur), `terminal` (hermes kanban/cron, ssh, git),
  `browser_exec` (bukti halaman nyata), `vision_analyze` (banding screenshot),
  `write_file`/`patch`/`read_file`, `cronjob_manage`.

### program-developer (developer)
- Skill: `design-taste-frontend`, `web-design-guidelines`, `antislop-ui`,
  `screenshot-to-code`, `graphify-query-first`, `surgical-patch`, `safe-refactor`,
  `systematic-debugging`, `test-driven-development`, `verification-before-completion`,
  `php-panel-verification-evidence`, `css-overflow-verification`, `php-upload-size-limits`.
- Plugin: `claude-mem`, `graphify-bridge`, `hades-coding-workflows`, `pstack`, `plan-mode`.
- MCP: `claude-mem`.
- Alat: `graphify_query` dulu sebelum grep, `graphify_update` setelah kode berubah,
  `terminal` (`php -l`, `php -S 127.0.0.1`, `git`), Playwright/`browser_exec`,
  `write_file`/`patch`/`read_file`, `kanban_comment`/`kanban_complete`.

### code-analyst (gate)
- Skill: `code-audit`, `webapp-testing`, `screenshot-to-code`, `web-design-guidelines`,
  `verification-before-completion`, `investigate-first`, `verify-and-stop`,
  `requesting-code-review`, `upload-limit-audit`.
- Plugin (terpasang di profilnya): `claude-mem`, `deskrpg`, `graphify-bridge`,
  `hades-coding-workflows`, `pstack`. MCP: `claude-mem`.
- Alat (teramati 7.559 panggilan): `terminal` 4.858 · `write_file` 958 ·
  `read_file` 707 · `patch` 422 · `kanban_comment` 38 · CDP/Playwright (matriks lebar × rute), `urllib` untuk probe status/byte,
  dekoder PNG untuk bukti piksel, `php -l`, `git`, `kanban_comment` + verdict tertulis.

### graphic-designer (desain)
- Skill: `design-taste-frontend`, `graphic-design-lane`, `awesome-design-md`,
  `web-design-guidelines`, `ui-ux-pro-max`/`popular-web-designs`,
  `quick-mockups`, `screenshot-to-code`, `playwright-cli`, `antislop-ui`.

### harry (perencana) & bersama
- Skill: `writing-plans`, `measurable-acceptance-criteria`, `domain-modeling`,
  `codebase-design`, `release-gate-scan`, `spec-driven-development`.

## Urutan fase baku

0. **Acuan & PRD** (harry/`graphic-designer`) — dokumen acuan visual + acceptance
   criteria terukur. Tanpa acuan, gate tidak punya pembanding.
1. **Fondasi visual** (developer) — token warna/tipe/spasi/radius/shadow, layout,
   komponen dasar (card, badge, avatar, toast, tabel, tab), dark mode, ikon SVG inline.
2. **Layar inti** (developer) — beranda analitik: KPI, grafik SVG lokal, panel
   perhatian, dan **paritas angka** dengan halaman laporan untuk periode yang sama.
3. **Layar sisa** (developer) — tabel ber-avatar, form berkartu, halaman rujukan,
   pengaturan bertab, cetak PDF sisi server.
4. **Gate** (code-analyst) — ukur ulang penuh, verdict tertulis.
5. **FIX** (developer) — hanya temuan gate. Kalau temuannya berpola (tautan <44 px,
   luapan, `sr-only`), perbaiki **semua** rute/berkas yang memakai pola itu dalam
   kartu yang sama, bukan hanya layar yang dilaporkan gate. Kartu FIX wajib
   meninggalkan angka **sebelum vs sesudah** dalam satu berkas JSON.
6. **Regresi** (code-analyst) — lingkup sempit: 5–6 baris, verdict wajib tertulis.
7. **Rilis** (koordinator) — periksa kepala worktree (`wt/<task-id>`, bukan nama
   `--branch`) → merge → cek konstanta versi → tag → ZIP `git archive` tanpa
   `docs/evidence` → backup docroot + DB → unggah dengan pemetaan docroot →
   verifikasi ber-sesi → catatan rilis → hapus cron. Resep lengkap dengan perintah:
   `references/release-and-deploy.md`.

## Alat ukur wajib (bukan opsional)

- Luapan: 11 rute × 5 lebar (360/390/768/1024/1440), `scrollWidth − clientWidth`
  dibaca **setelah** `window.scrollTo(9999,0)` + 2 `requestAnimationFrame`, plus
  `scrollX`. Snapshot tunggal tanpa scroll melaporkan 0 palsu.
- Target sentuh: hitung `kurang44` DAN `kurang44_tanpa_inline`, plus `lebar<44`.
  Tautan 20 px di baris tabel 64 px lolos aturan WCAG, tetapi kalau owner minta
  44 px mutlak, pengecualian tidak dipakai.
- Kontras: alpha-compositing latar, ambang 4,5:1, laporkan min + median + jumlah gagal.
- Rute: 27–43 rute × 2 identitas (admin, petugas) + kasus negatif; hitung 500 = 0.
- Aset eksternal: rekam `Network.requestWillBeSent`, host asing harus 0.
- PDF: ukuran byte + magic `%PDF-`; CSV: impor 2× untuk bukti idempoten.
- Angka: banding kartu beranda vs halaman laporan untuk 3 periode identik.

## Jebakan yang sudah memakan waktu

- **curl ke domain ber-WAF → 403 walau User-Agent browser.** Ukur dari dalam host
  (`php -S 127.0.0.1`) lalu `browser_exec`, bukan curl eksternal.
- **`span.sr-only` absolut lolos dari klip `overflow-x:auto`** → luapan hantu
  153–569 px. Beri `position: relative` pada pembungkus tabel.
- **Harness bisa berbohong.** Klaim "0 px" yang tidak bisa direproduksi adalah
  temuan terhadap harness, bukan bukti lulus.
- **Pegawai terarsip** membuat `$pegawai === null` lalu detail 500. Uji rute dengan
  ID terarsip, bukan hanya happy path.
- **`/health` membaca `APP_VERSION` di `Installer.php`**, bukan `config.php`.
- **`rsync` tidak ada** di hosting; pakai `tar` + `scp`.
- **Kartu ditutup tanpa `result`** berulang terjadi; verdict harus ditulis ke
  `docs/evidence/<sprint>/<kartu>-report.md` sebelum `kanban_complete`.
- **Sesi login beruntun bisa hilang** (redirect `/masuk`); login ulang sebelum
  tiap tangkapan layar, jangan simpulkan bug sesi dari satu kegagalan.
- **Temuan berpola jangan diperbaiki per layar.** Gate melaporkan layar yang ia ukur;
  pola yang sama biasanya ada di 4–5 layar lain. Grep penanda markup (kelas sel,
  `data-primary`, pembungkus tabel) di seluruh `app/views/` sebelum menutup kartu
  FIX. Fix per layar memunculkan temuan Major baru di regresi dan memaksa satu
  siklus kartu tambahan.
- **Nama branch worktree = `wt/<task-id>`**, bukan nilai `--branch`. Merge branch
  yang salah merilis kode tanpa fix terakhir; `git rev-parse --abbrev-ref HEAD` di
  worktree sebelum merge, dan cek `APP_VERSION` di commit hasil merge sebelum tag.
- **`git reset --hard` di checkout utama membuang berkas termodifikasi yang belum
  di-commit.** Hitung `git status --porcelain | wc -l` dulu; kalau bukan 0, `git
  stash -u` dan pulihkan setelah merge.
- **`git archive` ikut membawa `docs/evidence`** sehingga ZIP rilis membengkak
  berkali-kali lipat. Kecualikan `docs/evidence`, `docs/release`, `docs/reference`,
  `.worktrees`; lalu wajib `unzip -t`, hitung entri, dan `sha256sum`.
- **`shell_exec`/`passthru` bisa dimatikan di hosting.** Untuk dump DB, PHP hanya
  menulis `--defaults-extra-file` (0600); dump dijalankan lewat shell, lalu berkas
  kredensial dihapus. Jangan taruh kata sandi di argumen perintah atau di obrolan.
- **Docroot hosting sering mem-flatten `public/` ke root.** Salin isi `public/*` ke
  root docroot dan sisa repo tanpa `public/`, sambil mengecualikan `config/config.php`,
  `storage/`, dan `install.lock` milik server.
- **Ekstraksi token CSRF yang salah membuat login terlihat gagal.** Ambil nama field
  dari HTML nyata (`_csrf`); kalau POST 302 balik ke `/masuk` padahal kredensial benar,
  periksa token dulu sebelum menuduh sesi atau kode.
- **Loopback `curl -H 'Host: …' http://127.0.0.1/` bisa 404** walau domain publik 200.
  Bukti status rute diambil dari URL publik ber-sesi, bukan dari loopback.
- **`skills_list` besar dan memicu loop**; maksimal 3 `skill_view` relevan per kartu,
  sekali baca, dan hentikan tool yang mengembalikan hasil identik dua kali.

Resep probe pengukuran siap tempel (luapan, target sentuh, kontras, host asing,
matriks rute, bentuk bukti sebelum/sesudah): `references/evidence-probes.md`.
Resep rilis & deploy (merge/tag/ZIP, backup DB tanpa `exec`, pemetaan docroot,
verifikasi ber-sesi, catatan rilis): `references/release-and-deploy.md`.

## Kerangka perintah

```bash
hermes kanban --board <board> create "V1 - ..." --assignee program-developer \
  --body-file <body.md> --workspace worktree --branch wt/v1 --priority 10 --json
hermes kanban --board <board> create "V2 - Gate ..." --assignee code-analyst \
  --body-file <body.md> --workspace worktree --initial-status blocked --priority 9 --json
hermes kanban --board <board> link <v1> <v2>
hermes kanban --board <board> dispatch --max 1
```

Cron pendamping: driver 5 menit (`--no-agent`, buka kartu berikutnya hanya kalau
pendahulu done) + laporan 15 menit (`--no-agent --deliver origin`, berhenti sendiri
saat semua kartu done). Setelah proyek selesai, hapus cron-nya.

## Definition of done proyek

Gate terakhir APPROVE dengan verdict tertulis · produksi melaporkan versi baru di
`/health` · login nyata 200/302 · 9 halaman utama 200 · PDF valid `%PDF-` · data
lama utuh · backup rollback tersimpan · ZIP rilis lolos `unzip -t` + sha256 ·
laporan akhir terkirim · cron proyek dibersihkan.
