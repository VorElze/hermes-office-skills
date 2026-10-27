# Verifikasi SSL & ACME pada hosting (jangan percaya badge panel)

Panel billing/reseller dan panel DirectAdmin punya badge SSL-nya sendiri;
badge itu **state UI**, bukan keadaan sertifikat di server. Terbukti: badge
"Unlocked" merah di portal sementara sertifikat di ujung koneksi sehat
penuh. Selalu ukur dulu dari sisi klien sebelum menyentuh pengaturan apa pun.

## Urutan verifikasi (read-only, tidak mengubah state)

1. **DNS publik via DoH** — resolver lokal bisa gagal (`Temporary failure in name resolution`); DoH independen:
```bash
curl -s -H 'accept: application/dns-json' \
  'https://cloudflare-dns.com/dns-query?name=<domain>&type=A'
```
   Cek apex + `www`; pastikan IP konsisten dan DNS juga dicocokkan dengan parent delegation/dua resolver publik sesuai prosedur DNS di SKILL.md.
2. **Port** — pastikan 80 dan 443 terbuka di IP hasil DNS; terbukanya port bukan berarti vhost benar.
3. **TLS + HTTP terarah, tanpa `-k`:**
```bash
curl -sv --max-time 25 --resolve <domain>:443:<ip> --resolve <domain>:80:<ip> \
  https://<domain>/ -o /tmp/out.html -w 'http=%{http_code} size=%{size_download}\n'
```
   Baca `subject`, `issuer`, `expire date`, dan `SSL certificate verify ok` dari stderr; HTTP 200 + verify ok membuktikan TLS sah untuk hostname yang diuji. Ulangi untuk `www` dan pastikan SAN-nya tercakup.
4. **Cek konten yang tersaji** — halaman default/placeholder hosting (judul "Hosting Ready - ...") berarti DNS+TLS sehat tetapi konten belum tersaji; bukan bukti deploy selesai.

## Membaca status ACME di panel DirectAdmin (setelah login)

Setelah login vault terbukti (misalnya nama akun tampil di sidebar), halaman terkait:

- `/evo/ssl` — **Manage certificates**: tabel Certificate / DNS Names / Validity / Expires / Renewal mode. Kolom Validity="Valid" + Renewal mode="Automatic" + kalimat "All DNS names have valid TLS certificates" = ACME sehat.
- `/evo/ssl/acme` — **ACME settings**: status Enable ACME, key type, provider, skip list, external DNS provider. Memeriksa halaman ini read-only; jangan menekan SAVE CHANGES hanya untuk menyamakan badge portal.
- `/evo/ssl/history` — **Provisioning history**: Status, Started, Duration, Challenge type. Baris Success terbaru = provisioning berjalan; cocokkan dengan pengukuran sisi klien.

Tombol "View" pada tabel sertifikat dapat berupa `<button>`, bukan `<a href>`; jika tidak ada link, inspeksi kontrol UI dahulu dan jangan menebak URL detail.

## Kapan boleh mengubah pengaturan SSL

Membaca `/evo/ssl*` = read-only. Mengubah ACME/menerbitkan ulang sertifikat/menyentuh DNS = perubahan eksternal → **butuh persetujuan owner eksplisit** (lihat always-on rules di SKILL.md). Badge yang tidak sinkron di portal billing bukan alasan menerbitkan ulang sertifikat yang terbukti valid.
