---
name: portable-app-handoff
description: 'Use when publishing an app for reuse on other devices.'
version: 1.0.0
author: amanda
license: MIT
metadata:
  hermes:
    tags: [github, packaging, security, portability, handoff]
---

# Portable app handoff (GitHub / ZIP)

Merilis aplikasi kantor internal agar owner bisa pakai ulang di device/server
Hermes lain. Berlaku untuk rilis GitHub dan paket ZIP (prosedur sama; media
akhir berbeda).

## When to Use

- Owner meminta "upload hasil X ke GitHub / buat portabel" atau paket
  berpindah-server.
- Tugas sekali jalan (<1 file, tanpa deploy) tidak perlu alur ini.

## Procedure (dalam urutan ini)

1. **Cek auth & tujuan** — `gh auth status` (pastikan akun + scope `repo`);
   `gh repo list` untuk lihat konvensi nama; pilih visibility private untuk
   internal tool, kecuali owner minta public.
2. **Audit workspace SEBELUM salin** — kelompokkan:
   - Ikut: sumber runnable + aset + docs + template deploy.
   - JANGAN ikut: chat/db log, cache, backup, `__pycache__`, venv,
     `node_modules`, TLS private key, `.env`, token, kredensial.
   - Cari rahasia dalam docs: laporan QA bisa mengutip cuplikan key/token.
3. **Stage ke folder scratch** (`cp` selektif, bukan seluruh workspace).
4. **Portabelkan path & konfig** — path absolut di service/config diganti
   placeholder (`__APP_DIR__`) + komentar cara mengganti. Tulis README untuk
   pengguna baru: run cepat (demo) + mode penuh, kebutuhan runtime, endpoint,
   struktur folder, lisensi, portabilitas. Buat `.gitignore` sejak awal untuk
   runtime + rahasia.
5. **Redaksi kutipan rahasia** dengan placeholder deskriptif (`[REDACTED: PEM
   private key material]`) agar temuan QA tetap terbaca.
6. **Scan isi TERSTAGE**, bukan hanya nama file: `git diff --cached
   --name-only | xargs grep` untuk `BEGIN ... PRIVATE KEY`, token `gho_`,
   `sk-...`. Scan nama file melewatkan rahasia dalam Markdown.
7. **Commit + push + verifikasi remote** — pesan commit multi-baris via file
   (`git commit -F`); buat repo `gh repo create <name> --private ...`, lalu
   `git push -u origin main`. Verifikasi `git ls-remote origin main` SHA sama
   dengan HEAD lokal, cek daftar contents API dan jumlah blob di recursive
   tree. Repo-created ≠ push-landed.
8. **Lapor** — URL, isi terverifikasi, clone+run singkat, visibility, dan
   temuan keamanan (key lama terekspos → sarankan rotasi/regenerasi).

## Pitfalls

- Copy seluruh workspace memasukkan runtime state/cache/key/log; stage folder
  scratch selektif.
- QA/Markdown dapat membocorkan cuplikan secret walau key file dikecualikan;
  scan contents semua staged files dan redaksi salinan.
- Service path absolut membuat repo hanya jalan di mesin asal; gunakan
  placeholder yang eksplisit.
- Inline commit message dengan kutip dapat pecah quoting shell; gunakan file
  pesan commit.
- Internal tool dibuat public tanpa diminta membocorkan detail; default private.
- Jangan sebut berhasil berdasarkan `gh repo create` saja; verifikasi SHA dan
  tree remote.
