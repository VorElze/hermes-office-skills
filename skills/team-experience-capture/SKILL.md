---
name: team-experience-capture
description: 'Use when a delegated task may yield reusable team learning.'
version: 1.0.0
author: codi
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [kanban, skills, delegation, learning]
---

# Team Experience Capture

## When to Use

Use when a delegated worker completes a substantive task, or when writing a Kanban brief whose work is likely to produce a reusable method. Trivial one-off requests do not need skill capture.

## Procedure

1. **Before dispatch:** For substantial work, add a concise acceptance item asking the worker to inspect their existing skills and, if the work produced a generalizable procedure, strengthen an existing class-level skill or create a reusable one. Do not ask for a skill just to satisfy a quota.
2. **At completion:** Inspect the worker's final summary for a claimed skill path/update. If absent and the result contains a reusable workflow, ask the worker in its Kanban thread to capture it; do not write to another profile's skills or memory yourself unless explicitly authorized.
3. **Keep the learning reusable:** Save procedures, decision points, user-specific workflow preferences, and proven pitfalls; attach each pitfall to its procedural step. Prefer updating one umbrella skill over creating a narrow task-specific skill.
4. **Keep task data out:** Never place credentials, private user data, raw logs, whole reports, transient status, dates, task IDs, or one-off results in skills. Keep project-specific artifacts in the project workspace.
5. **Verify:** Report a skill as saved only when the worker provides a path and the change is verifiable by the authorized owner. Otherwise say it was requested, not confirmed.
6. **At every project completion (standing user directive):** capture the round's
   reusable lessons into the coordinator's skills first, then cross-share — copy a
   skill to another profile only when it matches that profile's persona/expertise
   (planner / implementer / reviewer) and genuinely improves its reasoning. The user
   has explicitly authorized writing skills into other profiles' skill dirs for this
   purpose. Copies do not auto-sync: re-share after later rounds.
7. **Diff source and destination BEFORE overwriting a cross-share.** A destination
   copy may contain lessons the coordinator's own copy lacks (each profile's skill
   evolves independently). Run `diff` first, merge any destination-only blocks into
   the source, then copy — otherwise the share silently DELETES the destination's
   newer content. Verify with matching `md5sum` on both files afterward, not just
   an `exists` check.
8. **Verify each cross-share on disk before reporting it.** A copy can "succeed"
   yet leave the destination wrong — building the destination path as a FILE
   instead of a directory (`team-experience-capture` instead of
   `team-experience-capture/SKILL.md`) yields a file where the loader expects a
   folder, so the skill silently never loads. Per target, assert the exact
   `…/<skill>/SKILL.md` exists, its size matches the source, and it contains the
   NEW lesson just added; repair by deleting the stray file and re-copying into a
   real directory. A filesystem `exists` check on the wrong path reports success
   for a broken share.

## Aturan pembaruan (anti-tumpang-untih — wajib)

**Selalu PATCH/meng-update in place, jangan membuat duplikat:**

1. **Sebelum menulis apa pun, cek dulu** apakah skill/entry yang sudah ada
   membahas topik sama (baca skill terkait, atau old_text memori).
2. **Ada yang sama → `patch` entry lama itu.** Jangan `create`/`add` baru —
   dua entri sama = membuang memori + membingungkan pencarian.
3. **Hasil baru LEBIH BAIK dari yang lama → timpa (replace/patch) dengan versi
   lebih baik itu**, bukan menyimpan keduanya. Versi lama yang sudah ter-gantikan
   dihapus/hilang dalam patch yang sama.
4. **Satu umbrella skill per kelas kerja** (sudah di aturan di atas); kalau
   menemukan dua skill saling tumpang tindih → gabungkan jadi satu, hapus yang
   redundant.
5. **Memori = cek-dulu-patch**, dan saat ≥90% konsolidasi dalam SATU batch
   (gabung overlap + buang stale + tambah baru).

## Hierarki penyimpanan (aturan keras — cegah "memori penuh" selamanya)

Memori profile hanya 2.200 karakter dan EKSPLISIT bukan tempat pengalaman.
Sebelum menyimpan apa pun, pilih layer yang benar:

1. **Prosedur/pelajaran kerja → SKILL** (batas tidak bermakna; ter-load otomatis
   saat relevan). Ini TUJUAN UTAMA semua pengalaman: cara, pitfall, keputusan,
   format laporan. Satu umbrella skill > banyak skill sempit.
2. **Konteks tugas tahan-requeue → komentar kartu kanban / workspace proyek.**
3. **Riwayat & detail mentah → session history (search), BUKAN memori.**
4. **Memori hanya untuk standing facts profil-agnostik** (siapa user, konvensi
   berlaku di SEMUA sesi tanpa task home). JANGAN pernah: log mentah, dump data,
   status progres, laporan, angka hasil proyek.
   - **Standing rule yang berubah → update di sesi yang sama.** Saat user
     mengcabut/mengubah aturan lama (mis. "jangan sentuh profil X" menjadi
     "kosongkan semuanya"), patch memori SEBELUM sesi berakhir — aturan basi
     membuat penolakan salah di sesi berikutnya.
   - **Backup/arsip → satu berkas terkompresi.** Folder ekstrak hasil backup
     adalah scratch: setelah verifikasi, hapus; sisakan hanya `.tgz`.

### Saat memori ≥90%

Satu batch `replace`/`remove` — gabungkan entry yang tumpang tindih, buang yang
stale, BARU tambahkan yang baru (operasi batch dihitung terhadap akhir batch).
Jangan menambah tanpa mengosongkan lebih dulu.

## Pitfalls

- Ask for a reusable skill only when a stable method emerged; forcing every trivial task into a skill creates a noisy library that is harder to search.
- Never edit another profile's private skills as a shortcut; profiles are isolated and workers own their own skill libraries.
- Do not duplicate instructions already embedded in a worker's standing persona; put task-class procedures in skills and stable identity/boundaries in SOUL.md.