# Audit board hidup: single-flight, budget, deadline, crash

Resep terukur untuk menjawab "apakah board ini jalan nyata, progresnya berapa,
deadline-nya kapan, budget-nya berapa, urutannya tumpang tindih atau tidak".
Semua angka dihitung dari DB board + proses nyata; status CLI bukan bukti.

## 0. Temukan DB board yang benar

```bash
find ~/.hermes -name 'kanban.db' -path '*boards*' -printf '%p %s\n'
```

Satu board = satu direktori: `~/.hermes/kanban/boards/<slug>/kanban.db`.
`~/.hermes/kanban.db` adalah board default dan bisa berisi 0 baris.
Buka read-only dengan timeout:
`sqlite3.connect('file:<db>?mode=ro', uri=True, timeout=5)` — CLI `sqlite3`
tidak punya flag `-timeout` (busy timeout = dot-command `.timeout 5000`).

## 1. Rantai + hard gate dependency

```sql
SELECT t.short_id, t.status, t.assignee, t.max_runtime_seconds, t.max_retries,
       (SELECT group_concat(p.short_id) FROM task_links l
          JOIN tasks p ON p.id = l.parent_id WHERE l.child_id = t.id) AS parents
  FROM tasks t WHERE t.archived_at IS NULL ORDER BY t.created_at;
```

- Kartu anak tetap `todo` / `dependency_wait` sampai SEMUA parent `done`
  (`recompute_ready` di `kanban_db.py` = hard gate). Anak yang parent-nya belum
  `done` tidak mungkin paralel secara struktur.
- `block_kind` tiap kartu `blocked` dibedakan: `dependency_wait` (normal, tunggu
  induk) vs `initial_status` (perlu unblock manual) vs `needs_input` (menunggu
  keputusan coordinator).

## 2. Bukti single-flight (4 lapis, semua harus lolos)

1. Edge dependency (di atas).
2. Satu run aktif per kartu:
   `SELECT task_id, count(*) FROM task_runs WHERE status='running' GROUP BY task_id;`
   >1 baris untuk satu task = duplikasi, jangan dispatch lagi.
3. Claim hidup:
   `SELECT id, current_run_id, worker_pid, claim_expires, last_heartbeat_at FROM tasks WHERE status='running';`
   `claim_expires` di masa depan + `worker_pid` hidup = worker memegang kartu.
4. Dispatcher tunggal di seluruh host:
   ```bash
   grep -rl 'kanban dispatch\|kanban daemon' ~/.hermes/cron ~/.hermes/profiles/*/cron 2>/dev/null
   ps -eo pid,ppid,etime,cmd | grep -E 'kanban (dispatch|daemon)' | grep -v grep
   ```
   Satu dispatcher watchdog sudah cukup. Dispatcher kedua = work ganda.

## 3. Worker hidup vs mati (sebelum intervensi apa pun)

```bash
ls -d /proc/<worker_pid>    # masih hidup?
sqlite3 <profile>/state.db "SELECT count(*) FROM messages WHERE timestamp > <epoch-now-90>;"
```

Worker hidup = `/proc/<pid>` ADA **dan** ada pertumbuhan pesan dalam 60–90 detik.
Hanya satu sinyal → worker mungkin macet; dua-duanya hilang → boleh reclaim +
dispatch. Kartu yang sudah `running` dengan worker hidup **tidak boleh**
di-dispatch manual: itu pekerjaan duplikat yang membakar kuota.

## 4. Budget & deadline (board tidak punya kolom due-date)

- Budget per kartu = `max_runtime_seconds` (cap keras, bukan durasi terjadwal).
- Deadline operasional = jumlah cap kartu pada rantai yang jalan SERIAL
  (mis. 120+240+360+360+240 = 1320 mnt ≈ 22 jam wall-clock).
- Posisi kartu sekarang = (lama run aktif) ÷ cap kartu; ≥80% → NEAR_DEADLINE,
  >100% → DEADLINE.
- Elapsed WAJIB dari union interval `task_runs` (sort + merge, bisa overlap)
  dikurangi span `task_events` kind=blocked→unblocked. `now - started_at` run
  saat ini reset tiap requeue → hijau palsu.
- Normalisasi satuan waktu: `t = v/1000 if v > 1e12 else v` (detik vs milidetik),
  dan `task_runs.started_at` bisa ISO-8601 sementara tabel lain epoch.

## 5. Progres nyata (bukan klaim)

- File: `find <workspace> -newermt '-30 minutes' -type f` + `git status --short`.
- Commit: `git log --oneline -N` di repo workspace.
- Komentar: `SELECT count(*), max(created_at) FROM task_comments WHERE task_id=?;`
- Target milestone: kartu biasanya menyebut target eksplisit (mis. "11 view
  publik") — hitung artefak nyata terhadap target itu, jangan mengarang persen.

## 6. Jendela request (berbagi antar profil)

Hitung API call sukses per profil dalam 5 jam dari `logs/agent.log` tiap profile
home + home default. Dua angka wajib dilaporkan:
- `terpakai/limit` per jendela (mis. 418/550).
- WASTE = (panggilan gagal/retry) ÷ total. Waste turun = efisiensi membaik,
  bukan kartu lebih cepat.

Ambang 75% jendela terpakai: kartu baru pada rantai serial berisiko mentok.
Requeue exit-75 TIDAK dihitung kegagalan, jadi rantai boleh menyeberang jendela
— nyatakan berapa jendela dibutuhkan.

## 7. Pisahkan kegagalan worker vs infrastruktur

- Worker: `task_runs.error` + `json_extract(metadata,'$.worker_output')` +
  log kartu `logs/<task_id>.log` (teks keluar lengkap yang dipotong `error`).
- Infrastruktur: drain/startup gateway, tool-argument truncation, 429/5xx proxy.
  Gejala ini tidak membuktikan worker rusak; re-dispatch manual atas worker
  hidup hanya menambah pemborosan.
- Bug parser SDK (mis. `IndexError` saat accumulate event SSE) BUKAN rate
  limit. Cek apakah exception itu masuk kategori transient/streaming di
  `error_classifier.py` — kalau tidak, fallback otomatis tidak pernah menyala.

## 8. Bentuk laporan (pola yang dipakai owner)

Satu baris terukur per dimensi yang ditanyakan (jalan nyata, progres, deadline,
budget, urutan/overlap, crash), lalu tutup dengan dua baris TERPISAH:
1. **sudah dikerjakan** — perubahan konkret + cara verifikasi.
2. **hanya diperiksa** — temuan tanpa perubahan.
Jangan menggabungkan keduanya; audit yang hanya menginspeksi akan terbaca
sebagai "sudah diperbaiki" kalau dua jenis itu tidak dipisah.
