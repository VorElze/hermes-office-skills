# Verifikasi backup & restore (shared hosting)

Backup yang belum pernah di-restore dan dibandingkan per berkas = **belum teruji**, bukan "sudah dibackup".
Tiga lapis di bawah ini yang dipakai untuk membuktikan acceptance "backup restore teruji".

## Lapis 0 — uji kewajaran arsip yang SUDAH ADA sebelum dipakai

Sebelum mengandalkan backup lama di hosting, bandingkan jumlah entri arsip dengan jumlah berkas nyata
di docroot. Arsip yang jauh lebih kecil dari isi docroot adalah arsip rusak/terpotong, bukan restore point.

```bash
tar -tzf ~/backups/<arsip>.tar.gz | wc -l          # entri arsip
find ~/domains/<domain>/public_html -type f | wc -l # berkas nyata
```

Kalau angkanya berjarak lebar (contoh nyata: 4 entri vs 14 berkas), jangan dipakai untuk rollback —
buat arsip baru dan verifikasi (Lapis 3). Laporkan temuan ini ke owner; backup yang dipercaya tapi
tidak lengkap lebih berbahaya daripada tidak ada backup.

## Lapis 1 — database: dump → restore ke DB scratch → bandingkan checksum

- Dump dengan user aplikasi (`MYSQL_PWD=… mysqldump`), DDL/restore dengan `mysql -u root` via unix socket.
- Restore ke nama DB BERBEDA (`<db>_restoretest`), jangan ke DB asli.
- Bandingkan jumlah tabel + checksum per tabel; laporkan `n/n tabel identik`.
- **Jangan pernah** jalankan skrip backup dengan `bash -x`: trace menulis isi `.env` ke log.
- Kalau memakai dump untuk dipindah antar hosting, jangan tambahkan `--databases` — hasilnya membawa
  `CREATE DATABASE`/`USE <nama-asal>` sehingga restore ke nama target tetap kosong (lihat skill
  `large-project-gated-delivery`, kasus reviewer false-positive).

## Lapis 2 — berkas build lokal: tar → ekstrak → sha256 per berkas

```bash
tar -czf dist_$TS.tar.gz -C dist .
mkdir -p $(mktemp -d)/x && tar -xzf dist_$TS.tar.gz -C $_
# bandingkan sha256 relatif per berkas, hitung mismatch
```

Lolos bila `mismatch = 0` DAN smoke test HTTP hasil restore 200. Jumlah berkas saja tidak cukup.

## Lapis 3 — docroot produksi: unduh off-site, sha256 server vs restore

1. Buat arsip **dari sisi hosting** (read-only terhadap produksi):
   `cd ~/domains/<domain> && tar -czf ~/backups/prod_$TS.tar.gz --exclude=public_html/staging public_html`
2. Hitung `sha256sum` arsip di sisi server.
3. Unduh **binary-safe** ke mesin lokal. Mode teks merusak gzip; pakai subprocess mode bytes:

   ```python
   proc = subprocess.run(cmd + [f"cat {remote_path}"], env=env, capture_output=True)  # TANPA text=True
   open(local_path, "wb").write(proc.stdout)
   ```

   Sandi SSH masuk lewat `SSH_ASKPASS` + handle vault, tidak pernah argv/env global.
4. Bandingkan sha256 lokal vs server — harus identik sebelum ekstrak.
5. Ekstrak ke `tempfile.mkdtemp()`, lalu bandingkan sha256 **per berkas** antara hasil ekstrak dan
   arsip server. Laporkan `n berkas server vs n berkas restore, 0 mismatch, 0 hilang`.

Hasil yang boleh diklaim "teruji": angka per berkas + sha256 arsip. Bukan `tar -t` sukses, bukan `gzip -t`.

## Rollback yang bisa dieksekusi

```bash
cd ~/domains/<domain> && tar -xzf ~/backups/prod_$TS.tar.gz   # timpa public_html
curl -o /dev/null -w '%{http_code}' https://<domain>/          # bukti 200
```

Tulis perintah ini di dokumen staging/ops sebelum menyentuh produksi, beserta arsip yang dipakai.
Simpan salinan arsip off-site (di luar hosting) — backup yang hanya ada di mesin yang sama tidak
menolong saat akun/quota bermasalah.

## Cakupan yang wajib dilaporkan

Tabel singkat per objek: DB dev, build `dist/`, docroot produksi, kode aplikasi staging — masing-masing
`tercover / belum` + lokasi. Objek "belum" harus disebut eksplisit, jangan disembunyikan di balik
kalimat "backup sudah selesai".
