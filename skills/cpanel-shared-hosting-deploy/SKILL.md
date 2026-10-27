---
name: cpanel-shared-hosting-deploy
description: "Use when deploying a website to shared-hosting cPanel."
version: 1.0.0
author: amanda
license: MIT
metadata:
  hermes:
    tags: [deploy, cpanel, hosting, web, git, sftp]
    related_skills: [service-credential-onboarding, self-hosted-web-service-ops, portable-app-handoff]
---

# Deploy website ke shared-hosting cPanel

## Pitfall terukur — wajib dicek sebelum deploy

**`Options -FollowSymLinks` mematikan situs.** Di Apache 2.4 cPanel, direktif itu di `.htaccess`
yang sama dengan blok `mod_rewrite` membalas **403 untuk SEMUA request**, termasuk berkas statis.
Diukur berpasangan di example.com: dua direktori uji identik, `uji11` (dengan baris) = 403,
`uji12` (tanpa) = 200. Pakai `Options -Indexes` saja; docroot cukup berisi `public/`.
Uji di satu direktori kecil dulu, jangan langsung timpa produksi.

**Subfolder staging.** Docroot induk sering menyetel `DirectoryIndex index.html`, jadi `/staging/`
= 403 walau `index.php` ada → tambahkan `DirectoryIndex index.php index.html`. Symlink
`public_html/staging -> ~/app/public` **gagal (403)**; pakai direktori nyata berisi `assets/`,
`uploads/`, `.htaccess`, dan `index.php` 3 baris:

```php
<?php
require __DIR__ . "/../../<app>/public/index.php";
```

Karena `require` menunjuk berkas asli, `__DIR__` tetap benar sehingga kode yang diuji identik
dengan kode rilis (tanpa patch khusus staging).

**Database tidak bisa diprovision lewat SSH.** `uapi` biasanya tidak ada, dan sandi cPanel ≠ sandi
user MySQL (`MYSQL_PWD=<sandi panel> mysql -u <user>` = **ERROR 1045**). Cek lebih awal: tanpa DB,
semua halaman konten = 500 (hanya halaman login yang 200) dan provisioning harus lewat UI cPanel
oleh pemilik. Unggah berkas tetap bisa: `scripts/ssh_upload.py` (tar.gz via stdin + `SSH_ASKPASS`
dari vault) menaruh sandi di env, bukan argv.

**Tanda tangan diagnosa 500 di staging: aset statis 200 + halaman PHP 500.** Kalau
`/staging/assets/css/*.css` membalas 200 tetapi `/staging/` 500, deploy-nya SUKSES — yang hilang
adalah `.env`/koneksi DB. Jangan ulang deploy; cek keberadaan `.env`, lalu uji koneksi PDO dari
hosting sebelum menyimpulkan apa pun. Sebaliknya, aset juga 500 = masalah rewrite/`.htaccess`.

**Staging di dalam docroot produksi adalah utang rilis.** `public_html/staging/` berarti setiap
deploy staging menyentuh direktori produksi, dan `.env` staging yang salah tempat bisa terunduh
publik. Sebelum `launch`, pisahkan jadi subdomain/`addon domain`, dan pastikan `.env` berada di
luar `public/` dengan mode 600 (uji: `curl /staging/.env` harus 403/404).

Prosedur verifikasi backup/restore (3 lapis, termasuk unduh off-site binary-safe dan perbandingan
sha256 per berkas) ada di `references/backup-restore-verification.md` — pakai itu saat acceptance
berbunyi "backup restore teruji".

Alur deploy site kantor ke hosting cPanel (panel Evolution). Kredensial login
sudah tersimpan di vault dan terverifikasi — aksesnya lewat
`service-credential-onboarding` (jangan pernah ketik password di chat).
Keputusan kanal update ada di `references/deploy-channels.md`. Untuk
akses shell/key dan wiring Git ke GitHub, lihat
`references/hosting-access-and-git-link.md`. Untuk verifikasi SSL/ACME
dari sisi klien dan pembacaan halaman ACME panel (badge portal ≠ kenyataan
sertifikat), lihat `references/ssl-acme-verification.md`; jangan menyalin
private key, repo test, atau external side effect tanpa target dan
persetujuan yang jelas.

Kasus aktif: site `example.com` di `panel.example.com:2222`.

## When to Use

- Owner minta deploy / update website di domain hosting kantor.
- Owner tanya soal cara update berkala website hosting.

## Always-on rules

- **Bangun lokal dulu, deploy belakangan.** Site dikembangkan di direktori
  lokal server (mis. `~/projects/<nama>/`) dan di-preview lokal tiap
  iterasi; domain publik baru tersentuh setelah owner approve hasilnya.
  Site setengah jadi tidak boleh ke-publish.
- **Tunggu bahan/koordinasi yang sedang berjalan sebelum mulai.** Jika owner
  atau profil lain (Codi/team) sedang menyiapkan referensi atau aset untuk
  proyek yang sama, jangan mulai scaffold sampai bahannya turun — dua pihak
  mengerjakan scope yang sama = tabrakan hasil.
- **Kanal update berkala: Git utama, SFTP hotfix kecil, ZIP hanya deploy
  awal.** Rasio dan alasannya di `references/deploy-channels.md`; jangan
  pakai ZIP untuk update berulang (sisa file lama menumpuk di docroot).
- **Pisahkan verifikasi jangkauan panel dari autentikasi dan deploy.** Untuk cek konektivitas ringan, jalankan `curl -s -o /dev/null -w "HTTP %{http_code} in %{time_total}s\\n" --max-time 20 https://<host>:2222/`; respons HTTP (mis. 302 ke `/evo/`) membuktikan endpoint dapat dijangkau dan memberi redirect, bukan bahwa login berhasil atau kredensial valid. Klaim autentikasi hanya setelah login benar-benar diuji; klaim deploy hanya setelah verifikasi situs live.
- **Pisahkan approval hasil kerja dari approval perubahan eksternal.** QA/release approval saja tidak membenarkan push ke remote, membuat/menautkan deploy key, atau overwrite hosting. Sebelum perubahan eksternal, pastikan mandat owner secara eksplisit mencakup target repo/jalur auth dan deploy/pemulihan docroot; jangan mengartikan izin umum sebagai izin tersendiri untuk mengubah DNS/nameserver, TLS, firewall atau layanan struktural. Jika mandat tidak jelas, kerjakan hanya pemeriksaan/solusi yang tidak mengubah state dan nyatakan gate yang memerlukan otorisasi khusus.
- **Jangan ubah konfigurasi hosting di luar scope deploy** (DNS, firewall,
  redirect server-wide, hapus akun) tanpa persetujuan owner — itu keputusan
  struktural.

## Procedure

1. **Amankan akses dan ukur sesuai pertanyaan.** Untuk pertanyaan apakah panel masih dapat dijangkau, cukup cek endpoint dengan curl dan laporkan status HTTP, waktu respons, serta redirect bila diketahui; jangan login hanya untuk membuktikan konektivitas. Untuk pekerjaan yang memerlukan sesi panel, pastikan kredensial tersedia via vault (`service-credential-onboarding`) dan lakukan login satu kali di awal proyek, bukan tiap tahap. Jangan pernah menampilkan rahasia.
2. **Tunggu spec lengkap** — jenis site, sumber kode, domain tujuan
   (default: domain utama, tanpa subdomain kecuali diminta). Untuk Git,
   pastikan owner menyebut repo sumber yang dimaksud; jangan menciptakan
   repo production atau menghubungkan repo tebakan.
3. **Scaffold lokal** — bangun di direktori project server, preview lokal,
   iterasi sampai owner approve.
4. **Buktikan kemampuan hosting dan DNS sebelum konfigurasi.** Cek SSH port 22 (2222 adalah panel, bukan SSH), `git --version`, akses hosting ke GitHub, docroot, dan Git UI cPanel. Untuk TLS ACME, kerjakan urutan DNS dahulu: (a) `dig +trace <domain> NS` untuk menemukan nameserver yang benar-benar didelegasikan oleh parent, (b) query A/AAAA/NS pada tiap nameserver delegasi, (c) bandingkan apex dan setiap hostname yang diminta dengan minimal dua resolver publik, lalu (d) uji HTTP pada port 80 untuk hostname tersebut. Rekaman yang terlihat di panel atau query ke nameserver hosting yang tidak didelegasikan bukan bukti DNS publik; resolver publik yang NXDOMAIN/tidak resolve, atau nameserver delegasi yang `REFUSED`/timeout, berarti perbaiki delegasi/zona di pihak registrar atau DNS authoritative terlebih dahulu. Bandingkan nameserver dari parent, bukan asumsi berdasarkan screenshot cPanel. Jangan ubah nameserver/DNS tanpa otorisasi khusus serta backup/preview zona. Setelah DNS publik sehat, pastikan setiap hostname mengarah ke server hosting dan HTTP port 80 dapat mencapai vhost yang tepat; baru minta provisioning ulang ACME dan periksa hasilnya. Untuk Git, pastikan public/private key arahnya benar: private key clone hanya di akun hosting; public key read-only pada repo yang tepat setelah target/auth disetujui. Jangan campur kredensial GitHub lokal dengan akses hosting.
5. **Pilih kanal deploy** — sesuai `references/deploy-channels.md`;
   default: Git (repo yang dikonfirmasi owner → cPanel Git → pull).
6. **Pastikan jalur autentikasi tersedia pada mesin yang melakukan operasi.**
   GitHub CLI HTTPS auth milik koordinator dapat push hanya bila owner telah
   mengotorisasi remote/target; itu tidak memberi hosting akses pull. Jika
   mandat untuk repo dan deploy key jelas, gunakan deploy key read-only khusus
   repo; GitHub menolak pemakaian key yang sama pada repo lain, jadi buat
   keypair baru untuk setiap repo. Simpan private key hanya di hosting dengan
   izin file ketat, dan tambahkan public key pada repo yang tepat. Jangan
   menyalin key test atau mencetak secret. Uji clone scratch dari hosting,
   cocokkan commit dan file, lalu hapus scratch dan verifikasi penghapusannya.
7. **Periksa kondisi live sebelum perubahan**: akses repo, status DNS, HTTP,
   dan TLS/SAN untuk hostname yang dimaksud. Jika resolver mesin gagal, cek
   hostname via resolver publik DoH (mis. Cloudflare DNS JSON) dan simpan
   hasil DNS sebagai bukti terpisah; `--resolve` hanya mengisolasi pengujian
   vhost/TLS dari DNS lokal, bukan memperbaiki DNS publik. Jalankan
   `curl --resolve <host>:443:<ip> https://<host>/` tanpa `-k` untuk menguji
   validasi sertifikat serta HTTP pada vhost yang tepat; catat status HTTP,
   judul/identitas halaman, dan masa berlaku sertifikat. Jika HTTPS gagal,
   uji HTTP dan TLS terpisah untuk melokalisasi masalah. Respons valid dengan
   `--resolve` tidak membuktikan resolver pengguna dapat menemukan domain.
   Sertifikat salah SAN, sertifikat gagal validasi, atau DNS publik tidak
   konsisten adalah gate sebelum menyebut HTTPS/live sehat.
8. **Sebelum menyentuh docroot**, ukur dan catat symlink, path asli, daftar
   file, ukuran, permission, dan filesystem free space. Buat backup bertanda
   waktu di luar docroot; verifikasi archive integrity, manifest/count, dan
   bahwa backup dapat dibaca sebelum perubahan. Siapkan langkah rollback yang
   dapat dieksekusi dan gate verifikasinya, lalu deploy hanya setelah repo,
   kanal, koneksi host, rollback, serta otorisasi owner eksplisit tersedia.
   QA lokal bukan live verification. Jangan overwrite file bawaan/website
   lama tanpa backup dan persetujuan.
9. **TLS dan DNS adalah gate terpisah dari deploy file.** Site harus memiliki
   DNS publik yang konsisten dan sertifikat valid untuk hostname sebelum
   dinyatakan live; jangan mengubah DNS/nameserver atau menerbitkan ulang TLS
   tanpa otorisasi dan pemeriksaan zone.
10. **Deploy file via staging + manifest checksum, jangan tulis docroot
   langsung.** Stream `tar czf - -C <dist> .` lewat SSH ke hosting
   (`cat > ~/incoming_dist/dist.tar.gz && gzip -t`), kirim juga manifest TSV
   (`sha256\\tsize\\trelpath` per baris), ekstrak ke direktori staging, lalu
   verifikasi SEMUA file terhadap manifest (`sha256sum` + `stat -c %s`) —
   hanya lanjut bila mismatch = 0 — baru `cp -a stage/. docroot/`. Verifikasi
   checksum di hosting WAJIB sebelum menulis docroot: transfer yang gzip-OK
   hanya membuktikan arsip utuh, bukan isi file yang cocok. Pertahankan file
   bawaan yang bukan milik rilis (mis. `cgi-bin/`, `index.php` lawas) — biarkan
   `DirectoryIndex` memutuskan mana yang menang, jangan hapus warisan tanpa
   instruksi owner. Bersihkan staging/scratch setelah selesai; backup tetap
   disimpan.
11. **Uji rollback dengan EKSEKUSI, bukan hanya menulis rencana.** Ekstrak
   backup ke staging dan cocokkan inventaris + ukuran file persis dengan isi
   backup (bukan sekadar `tar -t`); jalankan simulasi restore ke docroot
   tiruan (copy docroot saat ini → hapus file rilis → restore backup → file
   harus kembali persis ke inventaris backup); bersihkan dir simulasi;
   verifikasi docroot live tidak tersentuh tes. Laporkan angka sebelum/sesudah.
   Rollback yang belum pernah dieksekusi = NOT MEASURED.
12. **Verifikasi live** dengan hostname publik setelah deploy, lalu laporkan
   URL, status HTTP/HTTPS, validasi sertifikat, commit yang tayang, dan jumlah
   file. Bedakan uji via IP/host-header dari DNS publik yang benar-benar
   sehat; laporkan blocker tersisa dan tindakan lanjut. Sekaligus audit di
   browser sungguhan: overflow horizontal per route (1440 & mobile), toggle
   menu `aria-expanded`/Escape/fokus, dan simpan screenshot live ke `docs/`.
   Atribut aksesibilitas di-DOM-check; status screen-reader yang tak diuji
   harus disebut sebagai NOT MEASURED.
13. **Bukti deploy masuk ke dokumen + kartu sebelum dinyatakan selesai.**
   `docs/DEPLOYMENT.md` diisi hasil pengukuran nyata (status code, waktu,
   checksum, inventaris) dengan tiap gate berstatus VERIFIED/TESTED/
   NOT MEASURED; komentar kartu membawa ringkasan terukur yang sama. Jangan
   mengklaim kartu tertutup tanpa membaca ulang statusnya.

## Pitfalls

- Jangan menyamakan approval QA/release, hak approval tugas, dan otorisasi eksternal: push ke GitHub, pemasangan deploy key, perubahan DNS, serta overwrite docroot masing-masing punya target, dampak, dan risiko yang perlu diperiksa sebelum dilakukan.
- Jangan menyimpulkan DNS sehat hanya dari panel, satu resolver, atau query langsung ke IP hosting: authority dapat menjawab record sementara parent delegation/referral masih REFUSED atau tidak sinkron. Bandingkan parent delegation dan resolver publik untuk apex serta www; bila resolver lokal bermasalah, gunakan DoH sebagai pemeriksaan independen dan nyatakan batas cakupannya.
- Jangan menyebut domain bisa diakses publik hanya karena `curl --resolve` menghasilkan 200; opsi itu melewati resolver lokal. Laporkan terpisah DNS publik, status HTTP/TLS pada vhost terarah, dan apakah halaman yang tersaji memang konten situs yang diharapkan—halaman default hosting bukan bukti deploy selesai.
- Jangan menyamakan HTTP 200 di IP dengan rilis sehat. Uji HTTPS menggunakan hostname dan `--resolve`, baca SAN sertifikat serta status HTTP; `curl -k` hanya diagnosis response, bukan validasi TLS.
- Jangan anggap GitHub CLI yang berhasil push berarti hosting dapat pull. Verifikasi deploy key read-only pada repo target, private key di hosting, dan clone uji dari hosting sebelum menautkan cPanel Git.
- Mulai membangun sementara bahan dari pihak lain masih diproses — hasil
  dua builder berbeda harus digabung manual; tunggu dulu lebih murah.
- Menganggap repo ter-create / ZIP ter-upload = deploy selesai tanpa cek
  live — docroot panel bisa berbeda dari yang diasumsikan (subfolder
  `public_html` vs addon domain), buktikan dengan request ke domain.
- ZIP extract berulang meninggalkan file versi lama (asset/cache basi
  nyangkut) → gejalanya halaman campur lama/baru; karena itu ZIP hanya
  untuk sekali jalan.
- Jangan menganggap GitHub CLI yang login di mesin koordinator, port SSH
  hosting yang terbuka, atau keberhasilan `git clone` uji sebagai bukti repo
  website sudah terhubung; otorisasi host lokal dan hosting terpisah, dan
  clone hanya memverifikasi repo/key yang benar-benar diuji.
- Jangan membuat repo test/production, menambah deploy key, atau menyalin
  private key ke akun hosting untuk menjawab pertanyaan kemampuan; itu
  mengubah state eksternal dan dapat mengekspos akses. Minta target repo
  eksplisit dan persetujuan sebelum side effect; hapus artefak test bila
  dibuat, lalu verifikasi penghapusannya.
- Hindari memakai satu deploy key lintas repo: GitHub mengikat deploy key
  ke satu repo; gunakan key khusus per repo atau metode organisasi yang
  disetujui. Setelah memasang key, buktikan clone read-only dari akun hosting
  ke direktori scratch dan bersihkan scratch; konfigurasi lokal saja bukan
  bukti konektivitas deploy.
- **Badge SSL di portal billing bukan status sertifikat.** Badge "Unlocked"
  merah di panel reseller bisa berdiri sebelah sertifikat Let's Encrypt yang
  valid penuh; jangan menerbitkan ulang atau mengubah ACME karena badge.
  Ukur dari sisi klien (DNS publik + `curl --resolve` tanpa `-k` + baca
  issuer/expiry/verify) dan konfirmasi halaman ACME panel — langkahnya di
  `references/ssl-acme-verification.md`. Perubahan pengaturan SSL tetap
  butuh persetujuan owner.
- Otomasi login cPanel Evolution: form login memakai id duplikat
  (`input#username`, bukan `#username` polos) dan SPA re-render tiap aksi —
  detail pitfall browser ada di skill `service-credential-onboarding`,
  jangan duplikasi di sini.
