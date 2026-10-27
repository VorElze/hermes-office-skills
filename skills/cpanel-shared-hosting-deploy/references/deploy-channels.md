# Kanal deploy ke cPanel — pilih yang mana?

Peringkat untuk kasus update berkala site kantor:

| Kanal | Cocok untuk | Kelebihan | Kekurangan |
|---|---|---|---|
| **Git** (menu Git panel) | update berkala, tim >1 orang | `git pull` satu perintah; riwayat versi; rollback mudah; jalan via SSH (menu SSH Keys) | perlu repo perantara (GitHub); setup sekali di awal |
| **SFTP/SSH** | hotfix 2-3 file | drag-drop dari Explorer/VS Code, langsung live | tanpa riwayat; rawan overwrite parsial/keliru |
| **ZIP (File Manager)** | deploy awal / restore backup | cepat untuk paket tunggal, tanpa setup | tiap update: zip→upload→extract; file lama tidak ikut terhapus → sisa asset/cache basi |

**Default**: Git sebagai jalur utama, SFTP untuk hotfix, ZIP hanya saat
pertama kali atau restore.

## Catatan panel Evolution (akses ke `https://panel.example.com:2222`)

Fitur yang tersedia dan relevan untuk deploy:

- **Git** — pull dari remote (butuh URL repo + credential/token).
- **SSH Keys** — akses shell/sync langsung (rsync) ke docroot.
- **File Manager** — upload ZIP + extract (jalur ZIP).
- **SSL/TLS** — pasang sertifikat setelah domain hidup.
- **Cron Jobs** — scheduler (backup harian, script periodik site).
- **Select PHP version / Setup Node.js App / Setup Python App** — runtime
  app; cek dulu stack site sebelum pilih.
- **Domains** — docroot per domain; pastikan path deploy = docroot domain
  tujuan (site utama umumnya `public_html`, domain tambahan punya folder
  sendiri).
- **Backup and Restore / JetBackup** — snapshot sebelum deploy besar.

## Catatan Git via cPanel

Menu Git cPanel melakukan clone dari remote (GitHub dkk.) lalu pull —
kode harus sudah di-push ke remote sebelum bisa ditarik. Artinya alur
lengkapnya: build lokal → push ke repo → pull di panel. Kalau owner tidak
ingin memakai GitHub, alternatifnya rsync/SCP lewat SSH key (sekali jalan,
tanpa riwayat — catat bahwa riwayat versi hilang di jalur ini).
