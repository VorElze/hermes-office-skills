---
name: office-skill-distribution
description: "Use when distributing shared skills across Hermes profiles."
version: 1.0.0
author: office
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [skills, profiles, distribution, kanban-ops]
    related_skills: [hermes-profile-provisioning, skill-library-merge-dedupe]
---

## When to Use

Pakai saat owner minta "pasang/bagikan skill ke profil tertentu", saat menambah
skill baru ke kantor, atau saat sebuah profil melaporkan skill hilang/kebanyakan.
Mekanisme, perintah, verifikasi 4 lapis, dan jebakan ada di bagian bawah.

# Distribusi skill bersama per profil (tanpa duplikasi)

Pustaka kantor: `~/.hermes/skills-office` (43 skill, satu salinan fisik).
Dua tuas, keduanya per profil di `<root>/config.yaml`:

1. `skills.external_dirs: [~/.hermes/skills-office]` → skill terdeteksi.
2. `skills.disabled: [...]` → hanya profil yang berhak yang dapat skill itu
   (dipakai `agent/prompt_builder.py` untuk iklan skill di prompt DAN
   `tools/skills_tool.py` untuk skill_view). Jadi relevansi diatur tanpa
   menyalin file, dan skill tak relevan tidak membakar token tiap request.

Peta sebaran (peran → jumlah aktif): hitung ulang tiap setup — contoh
tata letak: coordinator, developer, analyst, planner, network, marketing,
social-media 7, graphic-designer 4, sales-analyst 5. Daftar mesin-baca +
alasan per peran: `.office-skill-map.json` (kunci `assign` = daftar skill
**AKTIF**, bukan dimatikan) dan `README.md` di folder itu.

Provenance: 16 skill dari `github.com/addyosmani/agent-skills` (14 sudah ada
sejak awal + 4 baru 27 Okt: git-workflow-and-versioning, idea-refine,
interview-me, spec-driven-development — patch `AskUserQuestion`/`Glob` ke
cara Hermes sebelum dipasang). 7 kandidat addyosmani ditolak karena duplikasi
fungsi; daftar lengkap + alasannya di README folder.

## Cara mengubah sebaran

```bash
hermes -p <profile-id> config set skills.disabled '<json array of nama yang dimatikan>'
```

- Selalu `-p <profile-id>` eksplisit (defaultnya profil sendiri).
- Peringatan `"not a recognized config key ... saved anyway"` itu benign:
  key tetap tersimpan dan terbaca `_skills_cfg`. Verifikasi tetap wajib.
- `auto_load` jangan disentuh: hanya `request-token-efficiency` yang auto-load.

## Verifikasi wajib (4 lapis, semua harus lolos)

```bash
# 1) bentuk YAML: skills.disabled == ALL - peta
# 2) loader API
HERMES_HOME=~/.hermes/profiles/<id> python3 -c \
 "import sys; sys.path.insert(0,'~/.hermes/hermes-agent'); \
  import agent.skill_utils as su; print(sorted(su.get_disabled_skill_names()))"
# 3) hitungan CLI (baris kolom source = external)
hermes -p <id> skills list --enabled-only --source local
# 4) probe prompt: jumlah nama skill yang benar-benar muncul di banner
HERMES_HOME=... python3 -c \
 "import sys; sys.path.insert(0,'~/.hermes/hermes-agent'); \
  from agent.prompt_builder import build_skills_system_prompt; \
  t=build_skills_system_prompt(); print(sum(1 for n in NAMES if n in t))"
```

Lapis 4 adalah satu-satunya yang mengukur apa yang dilihat model; jalankan
setelah setiap perubahan config.

## Jebakan yang sudah ketemu

- **`~/.hermes/profiles/default` bisa jadi ORPHAN, bukan profil aktif.** Roster
  ditentukan `hermes profile list`; profil root = `~/.hermes`. Bug klasik:
  loop `homes[d] = ...` di atas direktori profiles menimpa kunci `default`
  dengan path orphan → hasil 0 skill terlihat seperti kegagalan padahal
  pengukurannya salah arah. Kunci path per profil harus dijaga manual.
- **`hermes skills inspect <nama>` menelusuri registry remote**, bukan katalog
  lokal; menemukan beberapa kandidat ≠ ada duplikat di lokal.
- **`.office-skill-map.json` bisa hilang sesaat** saat dibaca (dua kali ketemu
  FileNotFoundError lalu bisa lagi — dugaan penulisan ulang proses kurator).
  Baca peta dengan retry (6× jeda 0,7 dtk) sebelum menganggapnya rusak.
- **Snapshot prompt** (`.skills_prompt_snapshot.json` di tiap root) hanya
  menyimpan tier lokal; tier external selalu dipindai live, jadi snapshot tidak
  perlu dihapus saat menambah external dir.
- **Nama terpotong** di tabel `hermes skills list` (kolom nama max 15 huruf) →
  jangan hitung/cocokkan nama dari tabel; pakai baris `--enabled-only` atau
  API loader.
- Rollback: hapus blok `disabled:` di config profil, atau pakai
  `config.yaml.bak-before-office-skills` di direktori profil.
