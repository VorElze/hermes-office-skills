---
name: office-skill-distribution
description: "Use when distributing shared skills across Hermes profiles."
version: 1.0.0
author: Koordinator
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

Pustaka kantor: `~/.hermes/skills-office` (53 skill, satu salinan fisik).
Dua tuas, keduanya per profil di `<root>/config.yaml`:

1. `skills.external_dirs: [~/.hermes/skills-office]` → skill terdeteksi.
2. `skills.disabled: [...]` → hanya profil yang berhak yang dapat skill itu
   (dipakai `agent/prompt_builder.py` untuk iklan skill di prompt DAN
   `tools/skills_tool.py` untuk skill_view). Jadi relevansi diatur tanpa
   menyalin file, dan skill tak relevan tidak membakar token tiap request.

Peta sebaran (peran → jumlah aktif): default 53, koordinator 49, code-analyst 47,
program-developer 46, koordinator 45, planner 27, netops 16, marketing 13,
social-media 12, graphic-designer 10, sales-analyst 10. Daftar mesin-baca +
alasan per peran: `.office-skill-map.json` (kunci `assign` = daftar skill
**AKTIF**, bukan dimatikan) dan `README.md` di folder itu.

Provenance batch 28 Okt 2026 (10 skill, 5 repo): `pbakaus/impeccable`
(Apache-2.0, jalur `.hermes/` resmi upstream), `miqdadbadjuber/anti-slop`
(MIT, core `antislop` + 5 sub; profil dengan sub WAJIB punya core),
`conorbronsdon/avoid-ai-writing` (MIT, self-contained), `hardikpandya/stop-slop`
(MIT), `petergyang/no-ai-slop` (MIT). Sudah diaudit: lisensi permisif semua,
tanpa injeksi prompt/eksfiltrasi. Dependensi teruji: `impeccable` (engine Go
ter-cache di `~/.impeccable`, **telemetry sudah dimatikan**), `node` v26
untuk `avoid-ai-writing/detector`, `python3` untuk `antislop-human`.
Sumber upstream lengkap: `~/.hermes/upstream-sources/office-2026-10-28`.

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
- `auto_load` boleh diubah **hanya** kalau skill itu relevan peran dan badannya
  kecil. Aturan: badan < 6.000 char, dan skill harus AKTIF di profil itu
  (auto_load + disabled berlawanan = skill di-skip, bukan error, tapi diam-diam).
  Status per profil 28 Okt: `.autoload-status-2026-10-28.md` di folder pustaka.

## Mekanisme "tanpa disuruh" — lapis SOUL.md (28 Okt 2026)

Untuk memaksa satu profil memakai kumpulan skill tertentu tanpa owner perlu
menyebutnya, urutan mekanisme dari yang paling murah:

1. **SOUL.md protocol block** — pilihan terbaik. SOUL.md di-render ke
   `stable_parts`, jadi biayanya sekali per sesi, bukan tiap turn, dan selalu
   ada di prompt. Tulis blok `## MANDATORY SKILL PROTOCOL` berisi urutan kerja
   + skill yang wajib dipanggil `skill_view` + stop condition. Sudah dipakai di
   program-developer, code-analyst, graphic-designer (backup `.bak-protocol-<ts>`).
2. **auto_load** — untuk badan < 6.000 char yang memang selalu relevan.
3. **Deskripsi** — untuk skill besar (badan 10-45K char); deskripsi masuk tiap
   turn, badan menyusul saat model memanggil `skill_view`.

Skill besar jangan pernah di-auto_load: `task-observer` 44447,
`design-taste-frontend` 40724, `avoid-ai-writing` 32953, `graphify` 38465.

Contoh SOUL.md block yang sudah terpasang: 3 profil eksekusi
(program-developer / code-analyst / graphic-designer, `## MANDATORY SKILL
PROTOCOL` versi engineer) dan planner (`## MANDATORY SKILL PROTOCOL — peran
program planner`, 12 langkah). Backup `.bak-protocol-<ts>`. Verifikasi: 6
layer — L1 bentuk YAML, L2 resolve==config, L3 missing=0, L4 no kolisi
disabled, L5 blok benar-benar masuk `load_soul_md()`, L6 SEMUA skill yang
disebut di blok harus `LOADS` (kalau `DISABLED` → perbaiki config, jangan
pangkas bloknya).

## Pitfall: backup dir — jangan iterate string (insiden 28 Okt 2026)

**Jangan pernah** menulis backup loop sebagai `for d in PATH + "/skills":` —
variabel itu string, jadi loop per KARAKTER. Satu karakter `"/"` lulus cek
`os.path.isdir("/")` → `shutil.copytree("/", "/.bak-...")` menyalin seluruh
filesystem root. Kasus nyata: artefak 64 GB di `/`, disk 45% → penuh, script
hang sampai timeout.

Aturan: simpan path ke variabel dulu (`SKILLS = f"{HOME}/skills"`), lalu for
di list literal nama skill. Selalu curigai `copytree` yang mungkin menyentuh
`/`, `/root`, atau `/home`. Backup yang benar untuk restore-additive (graphify)
bahkan tidak perlu copytree — cukup `if not os.path.isdir(dst)`.

## Verifikasi: hati-hati bug di VERIFIER-nya sendiri

Tiga kali sesi ini layer `False` ternyata salah di skrip verifikasi, bukan di
konfigurasi. Pola yang terbukti:
- **Cross-process mismatch** — membandingkan list milik subprocess profil
dengan `resolve_auto_load_skills()` yang dipanggil di proses induk (config
berbeda) → selalu `False`. Jalankan assertion di SATU proses.
- **Urutan itu bermakna** — `resolved == sorted(resolved)` salah; urutan
auto_load harus persis seperti di config (`request-token-efficiency` dulu).
- **`all()` melahap list kosong** — `all([True, [], True]) == False` padahal
`[]` berarti "tidak ada pelanggaran" = lulus. Pisahkan pengecekan list.

Kalau hasil verifikasi aneh, perbaiki dulu verifier-nya, jangan langsung
mengubah config. Simpan `print` isi list mentah tiap layer supaya bisa bedakan
"config salah" vs "assertion salah".

## graphify (dipulihkan 28 Okt 2026)

Skill `graphify`, `graphify-query-first`, `graphify-request-hemat` sempat dipindah
ke `~/.hermes/_disabled-graphify/<role>/skills/` pada 22 Okt tanpa catatan
alasan. Kini dipulihkan ke program-developer, code-analyst, graphic-designer.
Plugin `graphify-bridge` sejak awal aktif (tools `graphify_query`/`graphify_update`
+ hook `pre_tool_call` yang mengalihkan grep buta ke graph lokal).
Graph lokal offline = 0 request API. Verifikasi nyata 28 Okt: `graphify_query`
balas 91 node dari graph 308.556 node.

## Memasang skill baru ke beberapa profil sekaligus

Skill yang ditulis lewat `skill_manage` mendarat **hanya** di profil sendiri
(`~/.hermes/profiles/<id>/skills/<kategori>/<nama>/SKILL.md`). Untuk kelas kerja
yang harus dipakai beberapa peran (mis. playbook delivery web), salin berkasnya ke
tiap profil sasaran, jangan mengandalkan `external_dirs` kalau skill itu belum masuk
`~/.hermes/skills-office`:

```python
for pr in ['program-developer', 'code-analyst', 'graphic-designer', 'planner']:
    dst = f'~/.hermes/profiles/{pr}/skills/web/<nama-skill>'
    os.makedirs(dst, exist_ok=True)
    shutil.copy2(SRC_SKILL_MD, dst + '/SKILL.md')
```

Verifikasi per profil — **grep nama pendek, bukan nama penuh**: kolom nama di
`hermes skills list` terpotong ±15 huruf, jadi `grep -c '<nama-penuh>'` selalu 0
padahal skill-nya `enabled`.

```bash
HERMES_PROFILE=<id> hermes skills list | grep -i '<12-huruf-pertama-nama>'
```

Aturan tambahan: `description` di frontmatter dibatasi 60 char dan **itulah** yang
masuk prompt tiap turn — taruh frasa pemicu bahasa Indonesia owner di situ, karena
badan skill baru terbaca saat model memanggil `skill_view`. Setelah menyalin,
selaraskan kembali: sumber diubah → salin ulang ke semua profil (salinan tidak
otomatis ikut).

Mau tahu skill/tool apa yang **benar-benar** dipakai tiap profil sebelum memutuskan
apa yang dipasang/di-auto_load? Resep audit dari `state.db`: `references/skill-usage-audit.md`.

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

- **`~/.hermes/profiles/default` itu ORPHAN, bukan profil.** Roster asli
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
