---
name: server-hygiene-cleanup
description: Use when cleaning job residue and config from a server.
version: 1.0.0
author: amanda
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [cleanup, ops, hygiene, server, maintenance]
    related_skills: [kanban-rate-limit-resilience, codi-team-dispatch]
---

# Server hygiene cleanup

Bersihkan server kantor dari sampah pekerjaan, sumber perlambat, dan config
lawas — tanpa menghapus aset yang masih bernilai.

## When to Use

- Owner meminta "bersihkan server / sampah pekerjaan / config lawas".
- Menjelang milestone besar (rapat, handover, delivery) sebagai gate kebersihan.
- Setelah proyek besar selesai: sisa cron, monitor, backup, dan scratch proyek
  menumpuk di banyak lokasi.

## Standing rule: TWO LAYERS, inventory dulu

Jangan hapus apa pun sebelum inventarisasi. Pisahkan temuan menjadi:

- **Lapis 1 (aman)** — cache paket, jurnal yang dibatasi ukurannya, dan debug/probe
  yang terbukti yatim: eksekusi langsung, lalu ukur sebelum→sesudah.
- **Lapis 2 (bernilai/berisiko)** — backup, config aktif/proses jalan, deliverable,
  dokumen bukti, serta log login/autentikasi (`btmp`, `wtmp`, `auth.log`) atau log
  sistem yang mungkin memuat bukti keamanan: DAFTARKAN ke owner dengan ukuran +
  alasan, minta keputusan, baru eksekusi. Jangan truncate log audit hanya karena
  besar. Owner boleh memilih subset — ikuti persis pilihannya.

## Procedure

### 0. Audit perintah tersimpan yang rusak (stored-command integrity)

Owner's standing ask: *"cari tahu apakah ada perintah error atau rusak yang
masih tersimpan"* — broken references hide in three places and fail only when
the job runs unattended, so scan them BEFORE touching disk:

1. **Skill folders without SKILL.md** (folder exists, index skips it →
   `skill_view` fails and any prompt saying "WAJIB BACA <path>" loops):
   ```bash
   python3 - <<'PY'
   import glob,os
   for root in glob.glob('~/.hermes/profiles/*/skills')+glob.glob('~/.hermes/skills'):
       for d in sorted(os.listdir(root)):
           p=os.path.join(root,d)
           if os.path.isdir(p) and not d.startswith('.') \
              and not os.path.isfile(os.path.join(p,'SKILL.md')) \
              and not glob.glob(os.path.join(p,'*','SKILL.md')):
               print('BROKEN:',p,os.listdir(p)[:6])
   PY
   ```
   Fix = rebuild SKILL.md from the folder's surviving files (guide/resep/README),
   frontmatter description ≤57 chars, then verify with
   `hermes -p <p> skills list` (row must show `enabled`).
2. **Cron prompts referencing missing scripts / invalid flags** — parse
   `<profile>/cron/jobs.json` directly (the `jobs.json.bak-*` sibling is a
   history copy, ignore it): check each job's `script` resolves under the
   profile's `scripts/` (NOT `cron/` — a naive existence check there reports
   FALSE "missing" for healthy jobs) and grep prompts for flags the target
   tool never had (`get_service` imports, `--parent` on a CLI that lacks it).
3. **Skill referenced by prompt but absent from `skills list`** — cron prompt
   pointing at a broken skill is the same defect as (1); verify the index
   after the rebuild, not just the file on disk.
4. **Classify cron by schedule, not just recency** — parse enabled state,
   `last_run_at`, `next_run_at`, and script existence. An enabled weekly job whose
   last run was over 24 hours ago is not stale when its next run is in the future.
   Preserve all healthy jobs; do not infer "unused" from age alone.
5. **Remove fire locks only when proven orphaned** — inventory allowed profiles
   only; never enter Danu/Raka/Nadia. Remove a lock only if it is a regular,
   zero-byte file with no process file descriptor open; report removed/remaining
   counts and verify cron jobs remain intact. Never glob-delete locks blindly.

### 1. Inventarisasi (read-only)

```bash
df -h /; uptime; free -h                    # baseline kesehatan
du -sh ~/.hermes/profiles/*/cache       # cache per profil
du -sh ~/.hermes/profiles/*/cache/scratch | sort -rh
find /tmp -maxdepth 1 -printf '%TY-%Tm-%Td\t%s\t%f\n' | sort
journalctl --disk-usage; du -sh /var/log /var/cache/apt
find /root -maxdepth 5 -type f \( -name '*.tgz' -o -name '*.zip' \) -printf '%s\t%p\n' | sort -rn
ps aux --sort=-%mem | head -12              # proses makan RAM
ss -ltnp                                    # proses listen port
```

Cek juga sumber perlambat non-disk: cron yatim (`hermes cron list` per profil),
kartu kanban basi, proses manual yang jalan berhari-hari tapi bukan service
(`systemctl list-units` untuk membedakan), LSP/test-server yatim. Untuk service
residu, pastikan unit gagal/nonaktif, tidak memiliki listener, dan tidak menjadi
pemilik route sebelum menonaktifkan; hapus hanya symlink/config yatim yang tepat.
Setelahnya uji konfigurasi serta endpoint pengganti dan endpoint produksi lain.

### 2. Klasifikasi dengan bukti kepemilikan

Sebelum menandai "bernilai", buktikan: apakah file itu direferensikan (grep nama
file di config/skill/proyek), apakah sudah ada gantinya (backup vs versi final),
apakah prosesnya direferensikan config atau service resmi. File bukti audit
(`review-evidence/`, `.rsc`, config backup) SELALU lapis 2 walau kecil.

### 3. Eksekusi lapis 1

```bash
apt-get clean
journalctl --disk-usage              # ukur sebelum
journalctl --vacuum-size=100M
journalctl --disk-usage              # ukur sesudah
```

Jangan truncate `btmp`, `auth.log`, atau log autentikasi/sistem lain secara
otomatis; klasifikasikan sebagai bukti audit Lapis 2 dan minta keputusan owner.
Untuk `.fire-*.lock`, ikuti pemeriksaan orphan pada langkah 0; hapus hanya lock
kosong tanpa file descriptor aktif, profil non-terlindungi, lalu verifikasi jumlah.

Untuk `/tmp`: umur file saja bukan bukti basi. Pertahankan file bukti, report,
config/service/install script, log, fixture yang dirujuk test, serta artefak milik
workspace aktif. Hapus hanya kandidat debug/QA yang jelas, tidak sedang dibuka,
tidak dirujuk job/service/proyek aktif, dan berada dalam scope yang disetujui.
Ukur daftar dan byte sebelum→sesudah.

### 4. Eksekusi lapis 2 sesuai persetujuan, lalu VERIFIKASI

Tiap penghapusan wajib dibuktikan: daftar ulang (cron/job/kartu), `unzip -t` atau
checksum aset yang dipertahankan, `df -h` / `free -h` sebelum→sesudah. Laporan
akhir: tabel angka sebelum/sesudah + daftar yang TIDAK disentuh beserta alasannya.

## Pitfalls

- **Installer sandbox is not filesystem-isolated.** `HERMES_HOME` confines Hermes state only; third-party installers may also write into `~/.claude/plugins/`, `~/.claude-mem/`, `~/.local/bin/`, or mutate `~/.claude/settings.json`. Inventory those paths and any worker/listener before calling a sandbox test clean; see `third-party-tool-adoption-review` for the review workflow.
- **Jangan nilai "besar" dari angka `du` parent** — `du -sh dir` bisa tertukar
  dengan entri saudara saat output dipotong; konfirmasi dengan `du` per-kandidat
  sebelum menyebut ukurannya ke owner (angka salah merusak laporan terukur).
- **Proses manual ≠ sampah.** Dashboard/worker yang jalan berjam-jam tapi tidak
  direferensikan config adalah kandidat, TETAP lapis 2 — matikan hanya setelah
  owner bilang tidak dipakai. LSP (tsserver) aktif dipakai worker: jangan disentuh.
- **Jangan sentuh profil tim skripsi** (Danu/Raka/Nadia) — API terpisah, diatur
  manual owner.
- **Jangan anggap cron lama sebagai cron yatim**: job mingguan normalnya punya
  `last_run_at` lebih dari sehari; cek cadence dan `next_run_at` sebelum menyimpulkan
  usang, karena penghapusan berdasarkan umur saja mematikan pekerjaan terjadwal.
- **Lock cleanup harus membuktikan tidak aktif**: file lock kosong tetap bisa
  menjadi mutex bila proses menahannya terbuka; periksa file descriptor sebelum
  unlink agar tidak mengizinkan dua worker berjalan serentak.
- **Pencarian referensi jangan membanjiri output**: scan hanya direktori config,
  job, dan workspace yang relevan; kecualikan `.git`, `node_modules`, vendor, dan
  cache; keluarkan path yang cocok saja, bukan isi baris yang bisa memuat secret
  atau satu file graph/minified berukuran sangat besar.
- **Cron deletion gagal diam-diam**: flag yang ditolak mencetak usage dump
  berarti perintah tidak jalan — buktikan dengan `hermes cron list` (grep nama job)
  sebelum menyatakan terhapus.
- **Archive final adalah aset, bukan duplikat**: ZIP/PDF deliverable yang sudah
  terupload tetap dipertahankan; yang dihapus hanya backup pre-fix yang sudah
  tidak relevan (punya penggantinya).
- Setelah cleanup besar, matikan/pause monitor proyek yang sudah selesai —
  kebersihan mencakup job cron juga, bukan hanya file (lihat juga
  `kanban-rate-limit-resilience`, bagian automation hygiene).
- **Map orphan processes to ownership BEFORE killing, then re-verify the
  production services.** For `php -S`-class test servers: print
  `ps -eo pid,etimes,args`, keep only entries older than the session (hours,
  not minutes), and grep each cmdline for the task/workspace path to confirm
  the owning card is `archived`/unmapped — a live test server under an
  ACTIVE workspace is lapis 2. Kill SIGTERM→3s→SIGKILL, then prove production
  untouched in the same command block (`systemctl --user is-active <svc>`,
  `curl -o /dev/null -w '%{http_code}'` the health endpoint, `ss -ltn` for
  released ports). One compound command = one evidence trail: before-count,
  killed pids, after-count, service status.
- **Prove branch/worktree is merged BEFORE deleting, never trust the card
  status.** A card marked `done` does not mean its branch reached the main
  branch — the reviewer may have merged only part of it. Run
  `git merge-base --is-ancestor <branch> main` per branch; delete with
  `git worktree remove --force` + `git worktree prune` + `git branch -d`
  only for branches that answer YES. For a project archive, tag the final
  commit (`git tag archive/<name>-<sha>`) and push it to the owner's remote
  BEFORE removing worktrees, so the result is recoverable even if a branch
  tip was ahead of main.
- **When the owner orders a full project stop, the kill sweep has four
  layers, all verifiable in one pass**: (1) app units — mind user-vs-system
  scope (bare `systemctl stop` may "succeed" while user units keep serving;
  check `ss -ltnp` for each port after killing); (2) leftover manual
  processes (dev servers, adapters started by old workers — grep `ps aux`
  for the workspace name pattern, SIGKILL stragglers, re-verify zero);
  (3) project cron jobs — pause/delete every monitor+report+watchdog job of
  that project (`hermes cron list` by name); (4) git artifacts — tag, then
  worktree/branch removal per the ancestor-proof rule above. Report the
  end state as a per-port + per-process zero-check, not "done".
- **A resume of an interrupted takeover must close the abandoned block first.**
  When a session that wrote `block --reason 'X akan mengerjakan'` is interrupted,
  the card sits `blocked` forever with nobody doing X. On resume: comment the
  decision (who continues, with the handoff evidence), `unblock`, dispatch,
  confirm spawn+first heartbeat — in ONE pass. The block reason always names
  its owner; if that owner never acted, the block itself is the bug.
- **`uv cache clean` BISA MENGANTUNG berjam-jam** (bukti 27 Okt: hang sampai
  timeout 300 dtk), dan `<PATH_ANDA>` bisa berisi **lingkungan MCP yang
  sedang jalan** (chroma-mcp claude-mem memegang `archive-v0/`) — membersihkannya
  = mematikan tool. Jangan pakai perintah `uv cache clean`; kalau tetap mau,
  cek dulu `fuser -v <dir>` lalu `rm -rf <isi>` langsung (cepat, terkontrol).
  Cache uv milik hermes (`~/.hermes/cache/uv`) aman dihapus langsung bila
  tidak dipegang proses.
- **`~/.hermes/tools` bisa berisi dua versi toolchain** (python/node lama
  + baru). Versi lama ≠ otomatis sampah: ada risiko env pinned — lapis 2,
  tanya owner.
- **Job cron tipe `no_agent: true` + `script`** memang punya `prompt: ""`
  (skrip shell, bukan LLM) — itu NORMAL, jangan dianggap rusak. Nilai
  kesehatan dari `last_status` + `failure_streak`, bukan kekosongan prompt.
- **/tmp bisa berisi hasil kerja task TERBARU** (bukan sampah): file <7 hari
  tanpa referensi config pun belum boleh disimpulkan sampah. Batas aman
  pindah/hapus: >7 hari + tidak direferensikan + tidak dipegang proses
  (`lsof`). Pindah ke folder bukti selalu lebih aman daripada hapus.
- **Bukti insiden & sisa kerja lama di /tmp**: pindahkan (jangan hapus) ke
  `~/.hermes/skills-office/.provenance/<kategori>/` — tetap dapat diambil
  kalau dibutuhkan, tapi /tmp bersih. Filter per tanggal mtime, bukan umur
  perintah.
- **Timeout 300 dtk pada shell dengan banyak sub-perintah = kehilangan semua
  hasil parsial** (bukti 27 Okt: `npm cache clean` + `uv` bikin satu blok hang,
  seluruh bukti hilang). Pecah jadi blok kecil, atau jalankan tiap pembersihan
  mandiri agar pengukuran sebelum/sesudah tidak ikut hilang.
