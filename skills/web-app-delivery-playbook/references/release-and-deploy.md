# Rilis & Deploy — resep yang sudah terbukti

Dipakai pada langkah 7 (Rilis). Urutannya: periksa → merge → tag → ZIP → backup →
unggah → verifikasi ber-sesi → catatan rilis → bersihkan cron.

## 1. Pra-merge: pastikan yang di-merge memang kepala worktree kartu terakhir

Worktree membuat branch sendiri dengan nama `wt/<task-id>`, **bukan** nama yang
Anda berikan di `--branch`. Merge branch yang salah = rilis tanpa commit fix
terakhir dan tanpa kenaikan versi.

```bash
cd <worktree> && git rev-parse --abbrev-ref HEAD   # wt/t_xxxx, bukan wt/v12-fix3
git log --oneline -1
git merge-base --is-ancestor <tag-lama> <commit-kartu> && echo OK
```

Sebelum menyentuh checkout utama, cek `git status --porcelain | wc -l`. `git reset
--hard` di checkout utama **membuang berkas termodifikasi yang belum di-commit**
(untracked selamat). Kalau angkanya bukan 0, `git stash -u` dulu, jangan reset.

## 2. Merge & tag

```bash
git checkout main                       # checkout utama, bukan worktree
git merge --no-ff --no-edit wt/<task-id>
grep -n "APP_VERSION =" app/Installer.php    # WAJIB 'x.y.z' baru, bukan versi lama
git tag -a v<x.y.z> -m "<ringkas>"
git describe --tags --exact-match        # harus mencetak tag yang baru
git show v<x.y.z>:app/Installer.php | sed -n 15p
```

Kalau tag terlanjur menunjuk commit yang salah: `git tag -d v<x.y.z>` lalu tag ulang
setelah commit rilis benar-benar masuk. Jangan `tag -f` ke commit acak.

## 3. ZIP rilis dari tag (bukan dari worktree)

`git archive` ikut membawa berkas bukti yang sudah di-commit (screenshot, JSON) —
ZIP bisa membengkak 6–7×. Kecualikan dan ukur hasilnya:

```bash
git archive --format=zip --prefix=<app>/ -o docs/release/<app>-v<x.y.z>.zip v<x.y.z> -- . \
  ':(exclude)docs/evidence' ':(exclude)docs/release' ':(exclude)docs/reference' ':(exclude).worktrees'
unzip -tq <zip> | tail -1        # No errors detected
unzip -l <zip> | tail -1         # jumlah entri wajar (ratusan, bukan ribuan)
sha256sum <zip> | tee <zip>.sha256
unzip -l <zip> | grep -E 'config/config\.php|\.env'   # tidak boleh ada rahasia
```

## 4. Backup docroot + DB sebelum menyalin berkas

Docroot: `tar czf ~/backups/<app>-<ts>/docroot.tgz public_html`, lalu `gzip -t`.

Dump DB saat `shell_exec`/`passthru` dimatikan oleh kebijakan aplikasi: PHP hanya
**menulis** berkas kredensial, dump dijalankan shell.

```php
<?php
$c = require '<docroot>/config/config.php'; $d = $c['db'];
file_put_contents('/tmp/.app.cnf', "[client]\nuser={$d['user']}\npassword=\"{$d['pass']}\"\nhost={$d['host']}\nport={$d['port']}\n");
chmod('/tmp/.app.cnf', 0600);
```

```bash
mysqldump --defaults-extra-file=/tmp/.app.cnf --single-transaction --quick \
  --no-tablespaces <db> 2>/tmp/dumperr | gzip -9 > ~/backups/<app>-<ts>/db.sql.gz
rm -f /tmp/.app.cnf          # wajib, jangan tinggalkan kredensial
zcat ~/backups/<app>-<ts>/db.sql.gz | grep -c 'CREATE TABLE'
```

Password tidak pernah lewat argumen `mysqldump` (tidak muncul di `ps`) dan tidak
pernah dicetak. Baca nilai sensitif dari berkas env `0600`, jangan dari chat.

## 5. Unggah dengan pemetaan docroot yang benar

Hosting sering memakai docroot yang **isi `public/` di-flatten ke root** (root berisi
`index.php`, `assets/`, `app/`). Salin dua lapis, jangan seluruh repo ke root:

```bash
unzip -q zip -d /tmp/new
S=/tmp/new/<app>; D=<docroot>
tar -C $S/public -cf - . | tar -xf - -C $D
tar -C $S -cf - --exclude=public --exclude=docs --exclude=scripts \
  --exclude=config/config.php --exclude=storage --exclude=install.lock . | tar -xf - -C $D
find $D/app $D/config -name '*.php' -print0 | xargs -0 -n1 php -l | grep -v 'No syntax errors'
chmod -R u+rwX,go+rX $D/app $D/assets $D/vendor
```

`config/config.php`, `storage/`, dan `install.lock` milik server — dikecualikan agar
kunci instalasi dan data unggahan tidak tertimpa. Cek `git diff --diff-filter=D --name-only
<tag-lama> <tag-baru>`: kalau ada berkas dihapus, hapus manual di docroot (sync tidak
menghapus).

## 6. Verifikasi produksi ber-sesi tanpa browser login

Jangan ketik kata sandi ke halaman lewat tool browser. Login sisi server + parse DOM
sudah cukup sebagai bukti dan tidak membocorkan apa pun ke transkrip.

```bash
J=/tmp/jar.$$
tok=$(curl -s -c $J $B/masuk | grep -o 'name="_csrf" value="[^"]*"' | head -1 | sed -E 's/name="([^"]*)" value="([^"]*)"/\1=\2/')
curl -s -b $J -c $J -D /tmp/h.txt -o /dev/null \
  --data-urlencode "username=$U" --data-urlencode "password=$P" -d "$tok" $B/masuk
grep -iE '^(HTTP/|location:)' /tmp/h.txt        # 302 -> /  artinya sesi jadi
for r in / /pegawai /laporan /pengaturan /laporan/pdf; do
  curl -s -b $J -c $J -o /tmp/pg.html -w "%{http_code}:%{size_download} $r\n" "$B$r"
done
```

- Ambil nama field CSRF dari HTML nyata (`_csrf`, bukan tebakan `*token*`); token
  yang gagal diekstrak membuat POST tetap 302 dan semua rute ikut 302 — terlihat
  seperti sesi rusak padahal harness-nya salah.
- Parse angka KPI dengan `DOMDocument` + `DOMXPath` di skrip PHP, bukan grep regex.
- `/health` adalah bukti versi tercepat: `version`, `php`, `database.ok`, `tables`.
- `curl -H 'Host: ...' http://127.0.0.1/` bisa 404 walau situs publik 200; jangan
  simpulkan deploy gagal dari loopback.
- Data utuh dibuktikan dengan hitung baris tabel inti sebelum vs sesudah (users,
  employees, exams, referrals, settings).

## 7. Catatan rilis + bersihkan

Tulis `docs/release/RELEASE-v<x.y.z>.md`: tag, commit, ukuran entri ZIP, sha256,
waktu deploy, path backup, daftar verifikasi berangka, perubahan, dan catatan
perilaku yang sengaja tidak diubah. Lalu hapus cron driver + laporan proyek; cron
`ok` yang tertinggal = job basi.

## 8. Beda angka agregat vs panel: baca query sebelum menyebut bug

KPI yang menghitung **semua pemeriksaan** dan panel yang memakai **pemeriksaan
terakhir** per periode akan berbeda saat ada baris tidak lengkap. Sebelum melapor
"bug", buka service-nya (`Dashboard::perluPerhatian`) dan sebut perbedaan aturannya.
