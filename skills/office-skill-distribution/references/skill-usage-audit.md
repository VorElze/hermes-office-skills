# Audit pemakaian skill & tool per profil

Tujuan: memutuskan skill mana yang layak dipasang / di-`auto_load` / dihapus dari
sebuah profil berdasarkan **apa yang benar-benar dipanggil**, bukan asumsi.
Sumber: `~/.hermes/profiles/<id>/state.db`, tabel `messages` (`tool_name`, `content`,
`timestamp`).

## Resep

```python
import sqlite3, re, collections, datetime
since = datetime.datetime(2026, 1, 1).timestamp()   # batasi ke periode proyek
db = f'~/.hermes/profiles/{profil}/state.db'
c = sqlite3.connect(f'file:{db}?mode=ro', uri=True, timeout=5)
tools, skills = collections.Counter(), collections.Counter()
for name, content in c.execute(
        "select tool_name, coalesce(content,'') from messages "
        "where timestamp >= ? and tool_name is not null", (since,)):
    tools[name] += 1
    if name == 'skill_view':
        m = re.search(r'name["\']?\s*[:=]\s*["\']?([a-z0-9\-_:]+)', content)
        if m:
            skills[m.group(1)] += 1
```

Buka DB **read-only** (`?mode=ro`): worker bisa sedang menulis. Filter `timestamp`
sesuai rentang proyek supaya angka historis lama tidak menggeser kesimpulan.

## Membaca hasilnya

- **Tool dominan** = bentuk kerja profil itu. Contoh nyata: developer 12.035
  `terminal` + 6.264 `read_file` (menulis & memeriksa kode), gate 4.858 `terminal` +
  958 `write_file` (mengukur & menulis bukti), koordinator 2.113 `execute_code` +
  1.825 `terminal` (agregasi & orkestrasi). Kalau distribusi ini bergeser jauh, ada
  yang salah peran.
- **`skill_view` berulang pada skill yang sama** = tanda loop/macet, bukan
  ketekunan. Pernah tercatat 571 `skill_view` dan 164 panggilan skill yang sama
  dalam 30 menit tanpa satu tulisan. Nudge/reassign, jangan tunggu.
- **Skill yang tidak pernah muncul** tapi terpasang = kandidat `disabled`, atau
  bukti bahwa blok protokol di SOUL.md tidak menyebutnya (skill yang tidak pernah
  dipanggil praktis tidak ada).
- **`skills_list` besar** tidak perlu dipakai untuk audit ini; ia justru memicu
  loop. Query `state.db` memberi angka yang sama tanpa request API.

## Gunakan hasilnya untuk

1. Menyusun inventaris per peran (peran → skill wajib, skill pendukung, plugin,
   MCP, tool dominan) sebagai resep proyek berikutnya.
2. Memilih kandidat `auto_load` — hanya badan < 6.000 char dan memang dipanggil
   tiap task.
3. Membuktikan ke owner bahwa pembagian peran jalan (angka panggilan, bukan klaim).

Selalu sebutkan periode pengukuran saat melaporkan angka; `state.db` menyimpan
seluruh histori profil, jadi angka tanpa jendela waktu menyesatkan.
