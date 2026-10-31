---
name: large-project-gated-delivery
description: 'Use when coordinating a large multi-milestone gated project.'
version: 1.0.0
author: koordinator
license: MIT
metadata:
  hermes:
    tags: [kanban, orchestration, verification, delivery, lessons]
---

# Large-project gated delivery

Playbook disintilisasi dari AutoClipper (Sep–Oktober 2026): 41 kartu, 7 milestone (M1–M6 + quick-win), 17 versi ZIP, 5 dari 6 milestone pertama berputar ≥1 REVISE.

## When to Use

- Proyek multi-milestone dengan profil produsen + reviewer independen, berjalan >1 hari, deliverable berupa paket.
- Jangan dipakai untuk tugas <1 kartu — gerbang verifikasi murni biaya untuk pekerjaan kecil.

## Standar wajib SEMUA proyek (owner 13 Okt 2026)

Setiap proyek/kartu WAJIB memakai 5 komponen ini:
1. **Budget per kartu** — menit estimasi, ditulis di kartu + laporan (mis. "R2 budget 90m, jalan 24m").
2. **Laporan 15 menit** — cron monitor hemat (output di-hash; agent hanya menyala kalau ada perubahan nyata). Sebelum membuat/mengubah monitor, periksa cron aktif dan script-nya; jangan menduplikasi watchdog atau mengklaim monitor no-agent/token nol tanpa bukti konfigurasi. Template orkestrator yang sudah terbukti (probe provider → release ber-guard → stall reclaim → dispatch max 1): `scripts/orchestrator_monitor.py`, lihat bagian "Orkestrator 15 menit". Untuk status rutin, jalankan satu snapshot monitor yang sudah ada, lalu hindari polling manual berulang; tindak hanya atas perubahan status, pesan worker yang stagnan, atau ambang budget. Snapshot mencatat waktu pengukuran agar laporan tidak menyajikan status lama sebagai kondisi kini.
3. **Sweep deadline/stall** — ≥80% budget (NEAR_DEADLINE) koordinator intervensi; >100% (DEADLINE) atau worker diam >12m (STALL, ukur dari pertumbuhan `count(messages)` state.db, BUKAN heartbeat) → nudge, kalau mati: reclaim + dispatch ulang.
4. **Auto-dispatch dan verifikasi spawn** — kartu berikutnya di-dispatch saat parent done (tautkan dependency dulu, jangan paralelkan scope tumpang tindih); jangan anggap pemanggilan dispatch sebagai bukti penugasan berjalan. Periksa JSON `spawned`, lalu `kanban show <id>` untuk memastikan status/runs/workspace berubah. **`Spawned: 0` bukan bukti gagal:** dispatcher tertanam di gateway bisa sudah mengklaim kartu sebelum perintah Anda selesai — baca `status`,`worker_pid`,`current_run_id` kartu dulu. Bila kartu sudah `running` dengan PID hidup, jangan dispatch ulang (itu worker kedua) dan jangan kill. Hanya bila kartu masih `ready` tanpa run aktif, diagnosa dispatcher/perfil/kapasitas dan tindak lanjuti sampai ada bukti spawn, atau laporkan blocker dengan jujur.
5. **Lapor final + bersihkan monitor** — laporan penutup per kartu + bukti, lalu hapus cron monitor sisa.

Pratinjau laporan: persentase + status per kartu + budget terpakai/sisa + hambatan + tindakan. **Format yang disukai owner (30 Okt 2026, dipakai untuk semua proyek):** header `📊 <proyek> <versi> — laporan <tgl> <jam> WIB (<status>)`, lalu `🎯 Target selesai: <tgl> WIB · sisa N jam (anggaran M jam)`, lalu `📈 Progres: NN% ██░░░░░░░░ · kartu D/T done (bobot …)`, kosong, bullet satu baris per kartu (`• R1 running [assignee] run 7m kartu 7/180m` + baris `↳ diam 0m · <aktivitas terakhir worker>`), kosong, penutup `▶ aktif: … · ⛔ blocked: …` dan satu baris `langkah: …`. Jangan ganti bentuk ini dengan tabel atau paragraf naratif. Tanda ⚠️ (near deadline) / 🛑 (stalled/over) + tindakan yang sudah diambil. **Bobot kartu mengikuti verdict gate, bukan kolom `status`:** kartu yang gate-nya berakhir REVISE/BLOCKED menyumbang 0 bobot sampai RE-AUDIT menulis APPROVE (dan kartu FIX + RE-AUDIT yang baru diberi bobot sendiri). Tanpa aturan ini laporan menampilkan 100% sementara rilis masih ditolak — angka tinggi yang menyesatkan pemilik lebih mahal daripada progres rendah yang jujur. Saat bobot digeser, sebutkan di laporan bahwa rilis masih 0%.

**Alarm status (LEWAT/over-budget, STALL) hanya dihitung untuk kartu berstatus `running`** — kartu `done` dilaporkan sebagai durasi realisasi (`completed_at − started_at`); memicu alarm pada kartu selesai membaca kerja historis sebagai kondisi hidup, dan alarm palsu berulang membuat pemilik berhenti percaya laporan. Jika data budget tidak tercatat, nyatakan belum tercatat dan jangan menyamakan durasi run dengan budget; tampilkan progres/bukti terukur per kartu, anggaran hanya bila sumber angka ada. Selesai proyek → simpan pelajaran ke skill + cross-share (team-experience-capture).

## Sprint perbaikan diawali kartu BASELINE read-only, bukan langsung kartu fix

Sprint perbaikan di atas rilis yang sudah terpasang mudah membakar budget untuk memperbaiki gejala
lama atau sesuatu yang bukan defect. Kartu pertama wajib **baseline read-only**:

- **Larangan tertulis di body kartu:** jangan ubah kode/CSS/skema/data, jangan deploy, jangan sentuh
  produksi; staging hanya instance lokal. Baseline yang "sekalian memperbaiki" kehilangan seluruh
  nilainya sebagai pembanding.
- **Deliverable = dokumen verdict, bukan ringkasan naratif.** Tiap butir acceptance dinilai `LULUS` /
  `GAGAL` / `TIDAK TERUKUR` dengan denominator ("23 rute, 0×500", "5/5 PDF"). Butir tanpa angka =
  `TIDAK TERUKUR`; jangan dibulatkan jadi lulus dan jangan dihitung ganda.
- **Paritas repo vs produksi dibuktikan dengan hash, bukan asumsi:** bandingkan manifest sha256 yang
  diekspor dari server dengan hash worktree ("75/75 identik", atau daftar selisih sebagai temuan).
  Tanpa langkah ini, kartu fix berikutnya bisa dibangun di atas kode yang berbeda dari yang berjalan.
- **Sumber definisi gate = berkas gate report proyek + rencana kerja, bukan lampiran PRD.** Bila
  keduanya berbeda, sebut berkas mana yang mengikat dan jangan menghitung butir lampiran sebagai
  acceptance tambahan.
- **Keluaran baseline adalah definisi "selesai" untuk kartu hilir:** verdict `GAGAL` harus bisa diubah
  menjadi acceptance berangka di kartu fix, dan butir `LULUS` tidak dikerjakan ulang.
- **Artefak bukti itu snapshot.** Bila sesudahnya Anda melakukan aksi terverifikasi yang menutup butir
  terbuka di dokumen itu (mis. menghapus DB/artefak sisa), kirim komentar koreksi ke kartu yang
  menyebut berkas + keadaan terukur sekarang. Jangan melaporkan butir itu sebagai masih terbuka, dan
  jangan menyunting bukti historis seolah sejak awal begitu.
- **Berhenti di kartu baseline bila owner memintanya:** laporkan verdict, temuan yang butuh keputusan,
  dan tahan kartu fix pertama sampai ACC. Jangan menyambung sendiri ke gelombang berikutnya.

## Fase per milestone (terbukti)

1. **Siapkan lingkungan SEBELUM dispatch** (venv, dependensi, prefix perintah test) — venv rusak menghabiskan satu run penuh.
2. **Produksi** (Developer) → komentar progres per unit kerja (tahan rate-limit requeue; file selamat, sesi tidak).
3. **Verifikasi independen** (Analyst): ukur ulang semua angka; klaim produsen = hipotesis.
4. **REVISE** → spek perbaikan bernomor → kartu FIX → verifikasi ulang (putaran 2, dst.).
5. **APPROVE** → audit koordinator (lihat di bawah) → paket → penilaian manusia user.

**Insight inti:** M1 lolos putaran pertama, M2–M6 semua REVISE di putaran pertama. Gerbang independen menangkap hampir semua klaim terlalu optimis — JANGAN memangkas gerbang demi kecepatan; itu justru sumber utama kualitas.

## Kelas kesalahan yang ditangkap gerbang (periksa selalu)

- **Audit token ≠ audit halaman.** Kontras yang diukur per pasangan token (mis. 70/70 PASS ≥4,5:1) tetap bisa
  gagal di halaman nyata karena komponen memakai warna LITERAL yang melewati token (`#fff` di atas surface
  gelap = 3,31:1). Ukur warna komputasi DOM pada halaman yang benar-benar terender, bukan tabel token, dan
  ikutkan yang tidak muncul sebagai text node: `::placeholder`, `::before`/`::after`, serta state
  `:focus`/`:disabled`/`:hover`. Sebutkan denominatornya ("84 nilai/placeholder, 3 gagal") — gate kontras yang
  lulus di level token tapi tidak pernah merender halaman adalah lulus palsu, dan placeholder adalah titik
  buta paling umum karena bukan elemen teks.
- **Pass tersembunyi:** axe "0 violations" padahal 293 node `color-contrast incomplete` tidak dicatat → simpan `passes` + `incomplete`, jangan hanya `violations`.
- **Render valid ≠ layar bebas overflow:** PNG >1KB dengan 0 console error tetap GAGAL bila halaman melebar melewati viewport — ukur `scrollWidth - innerWidth` di 390/768/1440 dan laporkan ketiga angkanya; kartu UI hanya `done` bila overflow 0 di ketiga lebar, dan temuan responsif dikembalikan ke worker sebagai angka sebelum/sesudah yang bisa diukur ulang ("overflow 154px di 390" adalah acceptance, bukan catatan kosmetik).
- **Snapshot `scrollWidth` tunggal bisa melaporkan 0 px padahal halaman bergeser 150–570 px.** Di bawah
  breakpoint, tabel berubah jadi daftar kartu sehingga pembungkus `overflow-x:auto` tidak ada pada saat ukur;
  geser halaman dulu baru baca: `window.scrollTo(9999,0)` → 2× `requestAnimationFrame` → baca `window.scrollX`
  **dan** `scrollWidth - clientWidth` **dan** elemen terlebar (`getBoundingClientRect().right` maksimum,
  beserta kelasnya). Wajibkan berkas matriks mentah (layar × lebar × ketiga angka) sebagai bukti, bukan
  ringkasan "0 px". Kalau klaim worker 0 px tidak bisa direproduksi, tulis DUA temuan: cacat tata letak dan
  harness yang mengukurnya.
- **Luapan hantu hampir selalu elemen absolut yang lolos dari klip.** `span.sr-only` ber-`position:absolute`
  memakai *initial containing block*; pembungkus `overflow-x:auto` tanpa `position` bukan containing block-nya,
  jadi teks tersembunyi itu menempel di kanan halaman dan menambah lebar gulir walau tak terlihat. Perbaikan
  satu baris: `.tablewrap { position: relative; }`. Periksa juga `position:fixed` dan elemen berlebar 100vw.
- **Target sentuh <44 px: klasifikasikan sebelum menyebut blocker.** Tautan teks inline di dalam baris tabel
  (tinggi 20 px di baris 64–66 px) dan tautan header 14 px masuk pengecualian inline WCAG 2.5.8 — jarak antar-target
  sudah dipenuhi oleh tinggi barisnya sendiri. Ukur `height`/`width` tiap elemen **plus** tinggi pembungkus barisnya,
  lalu laporkan hitungannya sebagai catatan Minor, bukan temuan blocking; yang blocking hanya kendali berdiri sendiri
  (tombol, checkbox, ikon-aksi) di bawah 24 px. Sebaliknya gate yang mengklaim "0 kendali <44 px" tanpa daftar
  elemen+ukuran tidak sah — minta matriksnya, karena angka agregat tanpa daftar tidak bisa direproduksi.
  **Pengecualian inline itu untuk MENYEBUT blocker, bukan izin rilis:** kalau standar angka datang dari owner
  (mis. "target sentuh 44 px") atau owner berkata "kalau masih ada revisi minor, revisi dulu baru deploy", maka
  temuan di bawah ambang owner WAJIB jadi kartu revisi. Menyebutnya "pengecualian WCAG, tidak menghalangi" saat
  owner punya standar numerik sendiri = memutuskan kebijakan miliknya; menolak pengecualian selalu lebih murah
  daripada eskalasi.
- **Defect pola = kartu fix harus menyapu SEMUA pemakaian pola, bukan satu layar pelapor.** Tautan telanjang di
  sel tabel muncul identik di banyak view; kartu fix yang menyebut satu berkas meluluskan gate untuk satu layar
  dan melahirkan temuan baru di layar lain pada gate berikutnya (putaran tambahan penuh). Sebelum `create`,
  `grep -rn '<pola>' app/views/` lalu tulis daftar `berkas:baris` di body kartu, sebut pola yang SUDAH benar
  di repo sebagai acuan tiruan ("tiru `views/pegawai/index.php:154` + `app.css:950`"), dan jadikan acceptance
  berlaku untuk SEMUA layar yang memuat pola (`kurang44 == 0` tanpa pengecualian inline di tiap layar × 5 lebar).
  Gate berikutnya juga wajib memeriksa seluruh daftar itu, bukan hanya layar yang baru diperbaiki.
- **Denominator kosong:** "0 ID-switch/30s" dihitung dari 0 pasangan kandidat → wajib laporkan `n`/pasangan dihitung.
- **Route detail pemilik soft-deleted = 500 yang lolos dari sapuan rute biasa.** Daftar yang difilter `deleted_at`
  tetap memuat pemeriksaan/transaksi milik pegawai terarsip; JOIN-nya mengembalikan NULL dan view mengakses
  `$pegawai['nama']` → fatal. Probe matriks rute harus memakai ID milik baris terarsip, dan view-nya wajib
  menangani NULL secara eksplisit (tampilkan "pemilik terarsip", data tetap terbaca), bukan menutupi dengan
  redirect. Aturan arsip/otorisasi tidak diubah oleh perbaikan ini.
- **Fixture tidak memicu fiturnya:** occlusion 0,6s < grace produksi 1,1s → kamera tak pernah pindah → "recovery 0,0s" trivial. Fixture HARUS melewati ambang produksi; label hasil trivial sebagai trivial.
- **Angka di luar cap produksi:** plafon dikutip pada z=2,0 padahal `FRAMING_ZOOM_CAP=1,15` → angka cap produksi jadi headline.
- **Rujukan/arsip salah:** file `_B` dipakai padahal yang diadopsi `_A`; md5 handoff basi (rebuild mengubah md5); 6/7 perintah reproduksi gagal dari ekstraksi ZIP bersih (skrip & CSV tidak ikut manifest).
- **`Pre-existing` ≠ `lulus`:** acceptance gagal = gagal; yang melegitimasi hanya **pengecualian tertulis owner** (label `LULUS BERSYARAT` + angka jujur).
- **404 pada route-matrix wajib diklasifikasi, bukan otomatis defect.** Probe route menghasilkan 404 untuk tiga kelas berbeda: route memang tidak terdaftar di router; route POST-only yang dipukul GET (mis. endpoint logout); route berparameter (mis. download backup dengan nama berkas) yang diprobe tanpa parameternya. Sebelum menyebut 404 sebagai temuan: cocokkan tiap 404 ke definisi router (grep tabel route di file router utama) dan ke metode/argumen probe — hanya route yang tidak ada di router yang jadi temuan, sisanya dilabel "artefak probe". Sebutkan kelasnya di laporan; melaporkan 404 POST-only sebagai bug mengirim worker memperbaiki kode yang benar.
- **Metrik yang rendah KARENA keputusan owner tertulis = klasifikasi `SESUAI-KEPUTUSAN`, bukan defect.** Contoh nyata: noindex/meta-tertutup yang lahir dari keputusan "tanpa data sampel/SEO nonprioritas" membuat skor Lighthouse SEO rendah dengan sendirinya; mengejar angka itu membuang budget dan berpotensi melanggar keputusan. Klaskan dengan rujukan id keputusan di laporan gate, jangan dihitung sebagai GAGAL murni, dan jangan "diperbaiki" diam-diam ke arah yang melanggar keputusan. Kebalikannya tetap berlaku tanpa pengecualian: temuan yang menyentuh keselamatan pengguna, teks medis, atau kredensial tidak pernah masuk kelas ini.
- **Acceptance visual jangan tertahan dependency basi:** server yang baca file dari disk tiap request = edit langsung terlihat TANPA restart; implementasi merge → cek visual jalan segera, AC terdampak bug = FAIL sementara, re-screenshot setelah fix. Tutup label presisi: by-design / non-blocking / blocker.
- **AC roster = kontrak spek, bukan angka beku:** API live bisa mengembalikan roster dinamis (VO2D: snapshot 13 → live 11) → cocokkan kontrak, klasifikasi gap; jangan klaim 13/13 saat API 11/11.
- **Disk vs ZIP:** laporan/dokumen versi berbeda antara workspace dan paket.
- **Lampiran datang setelah hasil selesai:** baca ulang daftar lampiran dan komentar terbaru kartu sebelum menerima keterbatasan sumber. Jika bahan referensi sudah ada tetapi deliverable secara eksplisit menandai analisis tertunda, buat kartu revisi additive yang bergantung pada kartu deliverable; pertahankan isi dan bukti lama, lalu verifikasi versi revisi.

## Reviewer juga bisa FALSE POSITIVE — jangan implementasi temuan tanpa reproduksi

Gerbang independen menangkap banyak klaim produsen terlalu optimis (lihat "Insight inti") — tapi arah sebaliknya juga nyata. Kasus nyata: reviewer (P5) mengklaim "dump hanya bisa di-restore ke nama database yang sama" + merekomendasikan `mysqldump --databases`. Produsen (Developer) mereproduksi: klaim TIDAK terbukti (16/16 view, 0 galat, 4× ulang pada file paket), dan rekomendasi `--databases` ternyata **aktif merusak** — dump berisi `CREATE DATABASE` + `USE <nama-asal>`, jadi saat restore target yang diminta tetap kosong sementara data jatuh ke nama lama; kalau hak tidak cukup, impor berhenti separuh jalan (ERROR 1227/1102) — kebalikan dari perbaikan.

Aturan:
- **Sebelum mengimplementasikan temuan reviewer yang menyentuh artefak nyata (dump, manifest, struktur paket): reproduksi dulu.** Klaim reviewer = hipotesis, sama seperti klaim produsen.
- **Saran perbaikan reviewer harus diuji kontrafaktual** sebelum diadopsi: buktikan alternatif yang direkomendasikan benar-benar bekerja DAN tidak merusak jalur yang sudah terbukti baik. Kalau merusak, tolak dengan bukti tertulis (angka, jumlah ulang) dan pilih alternatif kedua dari spek.
- **Akar masalah ≠ gejala yang dilaporkan.** Dalam kasus ini akar asli (`DEFINER` di dump buatan user cPanel) berbeda dari gejala yang dilaporkan reviewer (kualifikasi nama database — ternyata artefak tampilan `information_schema`, bukan isi file). Bedah isi file asli (grep teks mentah, bukan sekadar query metadata) sebelum menerima diagnosis.
- **Perbaikan dokumentasi > perbaikan kode ketika file paket sendiri sudah terbukti benar.** Dump paket tidak perlu di-rebuild kalau masalahnya hanya cara pakai yang belum dijelaskan; tulis eksplisit di runbook (larangan, sebab, 3 solusi, jalur restore teruji).
- Reviewer yang terbukti false positive tidak otomatis dicabut mandatnya — tapi temuan berikutnya yang menyentuh artefak nyata wajib melewati reproduksi koordinator sebelum masuk kartu FIX.

## Scanner pola rahasia: hit = KELAS, bukan kebocoran

Gate/scan rahasia yang melaporkan "1 pola sandi literal" hampir selalu mendarat di hal yang BUKAN
kredensial. Cocokkan tiap hit ke sumbernya sebelum menyebutnya kebocoran:

| Kelas hit | Contoh | Vonis |
|---|---|---|
| Akses field | `$admin['password']` | bukan literal |
| Markup input | `type="password"` | bukan literal |
| Prosa spesifikasi | kalimat PRD yang menyebut "password" | bukan literal |
| Fixture/seed | akun uji di direktori test | bukan literal produksi |
| Literal sungguhan | nilai keras di kode yang dijalankan | baru temuan |

Tiap hit wajib ditelusuri ke file:baris dan diberi kelas di atas. Melaporkan "1 pola sandi literal" sebagai kebocoran tanpa klasifikasi = alarm palsu yang membakar kepercayaan pada gate.



## Jangan percaya "sudah dibangun" tanpa menemukan file sendiri (InlisLite P4→P6, 18 Okt 2026)

Klaim "ZIP final sudah dibangun" beberapa kali tidak cocok dengan pencarian cepat di workspace kartu / repo — file nyata ada di lokasi tak terduga (`/var/tmp/p6_release/…`, bukan workspace). Cek:
- Sebelum melaporkan "belum ada" ke owner, cari luas dulu: `find /root /var/tmp /tmp -xdev \( -path '*/node_modules' -o -path '*/vendor' \) -prune -o -name '*.zip' -size +50M -printf '%TY-%Tm-%Td %TH:%TM %10s %p\n'` — direktori build besar sering di `/var/tmp` atau `/tmp` untuk hindari isi workspace yang ikut ter-zip atau kuota disk.
- Begitu ketemu, verifikasi isi langsung (`zipinfo -1`, `zipinfo -l` untuk mode file di arsip, grep spesifik) sebelum mengutip klaim kartu apa pun ke owner.

## Kebijakan (worker `needs_input`)

- Worker **seharusnya** block untuk pertanyaan kebijakan/metrik, bukan menebak — itu kompetensi, bukan kegagalan.
- **Worker yang memblokir diri sendiri karena mendeteksi perubahan paralel (diff di luar tangannya) melakukan hal yang benar — itu pengaman serial, bukan kegagalan.** Jangan anggap `needs_input` di sini sebagai kegagalan capability. Sebelum unblock: buktikan penulis kedua benar-benar berhenti (`git status` bersih, worker lain mati/reclaimed, tidak ada run aktif lain menyentuh berkas yang sama), baru unblock dengan komentar bahwa konflik sudah selesai dan kartu lanjut dari state commit terakhir. Unblock tanpa membuktikan penulis kedua pergi = dua penulis pada berkas yang sama, dan merge-nya korup tanpa error di mana pun.
- Koordinator memutuskan atas mandat user. Format komentar keputusan: **opsi dipilih + guardrail** (angka mentah tetap dilaporkan, konstanta dibekukan, tanpa tuning threshold agar lulus, Analyst wajib audit ulang) + "ini keputusan final, jangan block lagi karena alasan ini".
- **Kredensial/fakta owner yang baru datang di tengah run: arahkan, jangan restart kartu.** Tulis nilainya ke
  berkas vault `0600` di profil koordinator (`~/.hermes/profiles/<profil>/.cleo/<app>_db.env`), uji koneksinya
  sendiri dulu (mis. DB: login OK + `0 tabel` = bersih), lalu kirim komentar kartu berisi **path berkas** +
  nilai non-rahasia (host/db/user/versi) + instruksi "baca berkas, jangan cetak, ulangi langkah X dengan sumber
  ini, dan hapus peninggalan jalur sementara". Komentar adalah kanal yang tahan requeue; chat koordinator tidak.
  Nilai rahasia tidak pernah masuk komentar, log, kartu, atau laporan — kalau sempat tercetak, akui sekali dan
  sarankan rotasi.
- **Kalau worker sudah menetap di sumber sementara, perintahkan pindah eksplisit**: hapus artefak instalasi jalur
  lama (mis. config + `install.lock`), ulangi wizard dengan nilai dari vault, lalu minta angka pembanding
  (jumlah tabel di DB target) sebagai bukti pindahnya benar. Hapus sumber sementara setelah terbukti.
- Keputusan nyata: round-trip bahasa (identitas > kekonyakan; makna > gaul), definisi ID-switch (mismatch identitas sebagai primer, transisi sah dilaporkan terpisah, angka mentah tetap ada), carryover empty-space (pengecualian tertulis).
- **Blokir karena SKILL menuntut pilihan (mode/izin) adalah keputusan koordinator, bukan capability worker.**
  Worker yang berhenti sebelum menyentuh berkas karena skill mewajibkan pemilihan mode (mis. skill desain
  meminta `DURING` vs `AFTER`) melakukan hal yang benar — jangan buat kartu FIX kode dan jangan eskalasi ke
  owner. Jawab di komentar kartu ("pakai mode during untuk sesi ini"), lalu hilangkan penyebabnya di sumber
  supaya kartu berikutnya tidak berhenti lagi: set default global skill itu (untuk `antislop`:
  `~/.config/antislop/settings.json` = `{"mode":"during"}`, satu baris, JSON divalidasi, rollback = hapus
  berkas), dan sebutkan perubahan config di luar repo itu pada laporan berikutnya.
- **Blokir karena dependency yang VERSI-nya dipatok spesifikasi: cari dulu salinan yang sudah memenuhi,
  baru eskalasi.** Kalau spec/PRD mengunci versi pustaka (mis. generator PDF wajib X 2.x, sementara
  package manager host hanya punya versi lawas), worker yang benar memblokir alih-alih mensubstitusi
  atau memalsukan output — itu competency, bukan kegagalan. Urutan koordinator:
  1. Telusuri worktree/vendor, cache paket, dan direktori sementara (/tmp, /var/tmp) untuk versi yang cocok; jangan mengunduh apa pun dulu. Salinan yang memenuhi spesifikasi sering sudah ada di luar workspace.
  2. Verifikasi versi, sumber, dan integritas (jumlah berkas, autoload, dependensi ikut).
  3. Jalankan smoke test terisolasi yang membuktikan pustaka itu BERFUNGSI pada versi itu — render nyata
     lalu periksa header/ukuran keluaran, bukan sekadar `exit 0`.
  4. Baru kalau tidak ada salinan yang cocok: eskalasi ke owner dengan 2 opsi + 1 rekomendasi.
  Jangan mem-vendor atau mengubah kebijakan proyek hanya untuk membuka blokir. Keputusan ditulis di
  komentar kartu: paket yang disetujui, lokasi persis, bukti smoke test, langkah lanjut yang dibatasi,
  dan bukti penerimaan.

## Audit & packaging (koordinator)

- **Audit sendiri, jangan percaya klaim:** `unzip -t`, scan konten terlarang (`.env`, venv, `node_modules`, `storage/`, `.mp4`, `__pycache__`), full test suite + gate dijalankan ulang, `Run.bat` ada, md5 tiap file kunci ZIP == workspace.
- **Satu akar, hitung isi, klasifikasikan hit rahasia — bukan hanya `unzip -t`.** Paket yang lolos CRC tetap bisa mengekstrak ke `app/app/...` (dua lapis) sehingga `Run.bat`/panduan menunjuk folder yang salah; sebut jumlah berkas + komponen path teratas sebagai bukti ("462 berkas, satu akar `app/`"). Jalankan `scripts/verify_release_zip.py <zip>` (CRC, jumlah, akar, nama terlarang, grep rahasia ber-kelas) sebelum mengirim; jangan mengarang hitungan dari output `zipinfo` yang tidak terbaca.
- **Hit grep rahasia di vendor = KELAS, bukan kebocoran.** `root: array{...}` di docblock Composer dan `type="password"` di markup cocok dengan pola sandi. Skrip di atas memberi kelas tiap hit (docblock/type-hint, markup, fixture, env-read, CANDIDATE-LEAK); hanya kelas terakhir yang dilaporkan sebagai temuan dan ditelusuri ke file:baris.
- **Rekonsiliasi koordinator yang angkanya benar ≠ gerbang tertutup.** Hitung ulang angka gate dari baris mentah membuktikan ANGKA itu, bukan status gerbang: gerbang tetap butuh verdict tertulis di berkas bukti dari profil gerbang, dan kartunya ditutup lewat `kanban_complete`. Angka yang benar tidak boleh dipakai sebagai dasar Promote kartu hilir, dan tidak membenarkan menjalankan ulang gate atas bukti yang tidak berubah — itu hanya memblokir lagi dan membakar budget kartu.
- **ZIP final wajib memuat SEMUA laporan verifikasi** — v16 melewatkan 4 laporan → v17 (temuan audit internal).
- Versi di-zip tak boleh ditimpa (builder menolak jika file ada); versi lama md5 tak berubah.
- Rebuild cepat: `cp zip-lama zip-baru` + `zip -u` overlay (2 detik) vs ekstrak-ulang-arsip-ulang (menit, bisa timeout).
- **Kirim ke user hanya setelah semua kartu `done` + audit bersih**; baru user beri penilaian manusia.
- **Diff ZIP vs sumber sebelum klaim paket benar:** bandingkan manifes ZIP lama vs sumber kini dua arah (`comm -23/-13`) — putaran rebrand mengganti font, ZIP lama membawa woff2 tak terpakai sekaligus melewatkan yang baru. Cek konsistensi font: semua `font-family` di CSS/PHP wajib punya file nyata di `assets/fonts/`, dan tiap file woff2 wajib direferensikan (nol referensi = jangan ikut paket).
- **Bersihkan artefak uji sebelum zip:** file debug sisa QA bisa membawa kredensial uji hidup (`tests/_debug_*.php`) — hapus dari repo SEBELUM packaging, scan nama debug/temp/log berisi secret.
- **Verifikasi upload Drive sebelum lapor sukses:** query by parent-id + bandingkan byte metadata Drive == byte file lokal, baru sebut sukses; lampiran chat tetap `MEDIA:<path lokal>`.

## Rakit rilis setelah verdict APPROVE (tag + ZIP dari SATU HEAD)

Verdict APPROVE hanya membuka pintu; paket belum ada sampai Anda merakit dan mengukurnya sendiri.
Skrip: `scripts/build_release_zip.sh <versi> <zip-keluar> <path...>` (git archive + ukur + sha256).

- **Pastikan repo utama tidak sedang checkout di branch worker.** `git branch --show-current` dulu; kalau
  menunjuk `fix/...`/`wt/...`, pindah ke `main` lalu `git merge --ff-only <branch-fix>`. Merge yang dijalankan
  dari branch worktree menghasilkan konflik semu dan riwayat ganda.
- **`git add -A` menyapu `.worktrees/` sebagai gitlink (mode 160000).** Git mencatat worktree kartu sebagai
  submodule hantu yang tidak ada di mesin lain. Tambahkan `.worktrees/` ke `.gitignore`, `git rm -r --cached
  .worktrees`, dan buktikan `git ls-files | grep worktrees` kosong sebelum commit rilis.
- **Rakit ZIP dari `git archive HEAD` dengan daftar path EKSPLISIT** (mis. `app public database vendor
  PANDUAN-*.md`), bukan `zip -r .` — supaya `.git`, `.worktrees`, `docs/evidence` besar, `storage/uploads`, dan
  `config/config.php` tidak ikut. Cetak byte, jumlah entri, dan `unzip -t`.
- **Verifikasi isi hasil EKSTRAK, bukan hanya CRC:** jumlah berkas, `php -l` (atau linter setara) seluruh berkas
  = 0 error, tidak ada `config.php`/`install.lock`, grep token/kredensial = 0 hit, lalu simpan `sha256sum` di
  sebelah ZIP dan kirim angkanya di laporan. ZIP rapi yang mengekstrak `config.php` produksi adalah kebocoran.
- **Tag harus menunjuk commit yang SAMA dengan sumber ZIP.** Commit pembersihan sesudah tag (mis. mengeluarkan
  `.worktrees`) membuat tag menunjuk pohon yang salah → `git tag -f -a <ver> <sha>` lalu buktikan dengan
  `git rev-parse --short <ver>` + `git describe --tags`.
- **Versi yang dilaporkan aplikasi harus ikut naik, dan itu bukan selalu di config.** Kalau `/health` membaca
  konstanta kode (`APP_VERSION`), deploy ulang paket lama tetap melaporkan versi lama walau config sudah
  disunting. Sebelum deploy: `grep -rn "<versi-lama>"`, naikkan di repo, commit, **rebuild ZIP**, pindahkan tag
  ke commit itu, lalu kirim ulang sha256 baru. Rilis yang beredar beda isi dengan yang terpasang = laporan versi
  yang tidak bisa direkonsiliasi owner.
- **Produksi tetap versi lama sampai deploy eksplisit.** Sebut versi yang masih berjalan di laporan, dan tawarkan
  deploy sebagai keputusan owner (backup DB + docroot → deploy → uji `/health`, login, PDF), jangan diam-diam
  men-deploy karena gate sudah APPROVE.

### Produksi 403 pada `curl` ≠ produksi mati

WAF hosting bisa menolak SEMUA permintaan non-browser untuk seluruh domain akun — bahkan dengan UA Mozilla
palsu, bahkan dari dalam server itu sendiri — sehingga `/`, berkas statis, dan `/health` kompak 403.

- **Sebelum mengeskalasi gangguan, buka dengan browser nyata:** `browser_exec` → `new_tab(url)` → baca
  `document.title`/isi + `performance…responseStatus`. 200 di browser = layanan sehat dan yang rusak adalah
  metode ukurnya.
- **Jangan melaporkan "produksi down" dari bukti `curl` saja**, dan sebutkan cara ukur yang dipakai. Alarm palsu
  memicu rollback/restart yang tidak perlu dan merusak kepercayaan pada laporan berikutnya.
- Uji juga satu domain lain di akun yang sama: kalau domain yang tidak Anda sentuh ikut 403, penyebabnya
  akun/hosting, bukan rilis Anda.

## Pitfall suite QA setelah putaran revisi (eVoting 7 Okt 2026)

- **Suite mati di setup = harness tidak tahan requeue.** Skrip review memanggil helper (`tests/harness/setup_webroot.php`) yang tidak ikut workspace → suite gagal sebelum menguji apa pun dengan error membingungkan. Tiap run QA: verifikasi harness ada / bangun ulang dulu, baru jalankan suite.
- **Asetsi basi setelah rebrand → merah ≠ regresi.** Rebrand warna/teks membuat tes warna lama gagal (navy `#0F2C59` vs ink baru `#0E2F27`). Grep SELURUH suite untuk token lama (warna, salinan, kelas) tiap kali desain berubah; pastikan UI benar dulu sebelum menyalahkan kode, dan jangan diamkan asetsi basi begitu saja — perbaiki tesnya.
- **Suite wajib mulai dari state instal pristiwa.** config sudah tertulis membuat alur installer gagal dengan 419 (bukan 403/redirect yang diharapkan) → reset webroot / deteksi `INSTALLED` sebelum tiap suite, atau sesuaikan ekspektasi dengan state sesungguhnya.
- **Dokumen pengguna = bagian audit.** Cocokkan seksi PDF panduan dengan langkah instalator sebenarnya (label `Langkah 1..5`, tombol, token sekali-lihat) sebelum masuk paket; panduan basi = defect rilis.

## Diagnose & recover stalls (evidence-led, read the source first)

- **Baca stream pesan worker + `task_runs`, jangan heartbeat saja.** Sebelum menyebut kartu blocked, ambil event terbaru dan `task_runs`; buktikan dengan pertumbuhan `count(messages)` state.db dalam interval terukur. Untuk `protocol_violation`, baca `task_runs.metadata.worker_output` — kolom `error` hanya ringkasan dispatcher yang bisa menyembunyikan penyebab sesungguhnya (mis. pesan guard loop). Bedakan exit 75/429 (kuota), exit 78 (auth/terminal), dan exit 0 tanpa `kanban_complete`. Jangan sebut akar masalah atau ambang kegagalan sebelum payload event + metadata run mendukungnya.
- **Bedakan DIAM, CRASH, dan LOOP BACA — hanya loop yang butuh reclaim paksa.** Ketiganya sama-sama
  berstatus `running`. Diagnosanya BUKAN jumlah pesan: worker yang membaca ulang bisa menambah ratusan
  pesan tanpa satu pun tulisan. Ukur komposisi tool — hitung call yang MENULIS (`write_file`, `patch`,
  `edit_file`, `multi_edit`) terhadap total, cek apakah berkas sumber berubah (`find <repo> -newermt
  '-30 minutes'`), dan apakah ada commit baru. Sinyal loop: nol tulisan + berkas yang sama dibaca
  berulang (khas: beberapa berkas dibaca 5× masing-masing) + komentar kartu identik berulang. Tindakan:
  `reclaim` → matikan PID worker → kirim arahan tertulis ke kartu → `dispatch --max 1`. Tapi jangan
  reclaim worker yang baru 5–10 menit membaca sumber: itu fase orientasi yang wajar.
- **Sinyal khas loop alat-skill, bukan loop berkas:** log profil memuat ratusan `skill_view` dan guardrail
  mencatat *"Blocked skill_view: returned the same result 5 times"*; konteks membengkak (~120k token) →
  kompresi tiap ~25 menit → jatah turn habis → run keluar `rc=0` TANPA `kanban_complete`. Tiga run berturut
  begitu membakar >1 jam dengan nol tulisan. Penangkal di brief kartu, bukan di nudge: **larang eksplisit
  `skill_view`/`skills_list`/`tool_search`** ("semua instruksi ada di kartu ini"), batasi baca 3–5 berkas,
  dan wajibkan satu call tulis dalam 10 menit pertama. Brief pertama yang hanya bilang "baca yang perlu"
  tidak menyembuhkan loop ini.
- **Loop yang bertahan setelah brief ketat = masalah PROFIL, bukan kartu → PINDAHKAN kartu, jangan
  briefing ulang.** Kalau dua run segar pada profil yang sama tetap 0 tulisan, `reassign <id> <profil-lain>
  --reclaim --reason "..."` ke profil yang riwayat `state.db`-nya menunjukkan call tulis tinggi, lalu
  `dispatch --max 1`. Sertakan di komentar kartu: branch+commit yang SUDAH ada dan larangan mulai dari nol
  ("lanjutkan dari branch itu"). Bukti keberhasilan = hitungan call tulis baru dalam beberapa menit, bukan
  status `running`.  Skrip probe:
  `scripts/worker_progress_probe.py` (komposisi tool + hitung baca-ulang + `skill_calls` + idle; tambahkan
  `--board <slug> --task <id>` agar ikut mencetak worktree kartu, `dirty_files`, dan `git diff --stat main...HEAD`
  — tanpa itu verdict "0 tulisan" bisa hanya berarti Anda melihat repo yang salah).
  **Skema `state.db` berbeda antar profil — periksa sekali, jangan menebak:** di profil worker tabel
  `messages` memakai `timestamp` (bukan `created_at`) dan `tool_name`; **tidak ada** tabel `tool_calls`.
  Error `no such table`/`no such column` berarti skema bergeser, bukan datanya kosong — jalankan `.tables`
  + `PRAGMA table_info(messages)` sekali per profil lalu pakai nama itu untuk semua hitungan komposisi tool.
- **Worker menulis di WORKTREE kartu, jadi repo utama selalu tampak bersih — ini sumber laporan palsu
  "0 berkas berubah".** Kartu ber-`workspace_kind=scratch` bekerja di
  `~/.hermes/kanban/boards/<board>/workspaces/<task_id>/repo` pada branch sendiri. `git log`/`git status`
  di repo proyek TIDAK melihat commit maupun berkas worker. Sebelum menyimpulkan "belum ada kerja":
  `select workspace_kind, workspace_path, branch_name from tasks where id='<id>'`, lalu
  `git -C <workspace_path>/repo log --oneline -3` + `git status --short` + `git diff --stat main...HEAD`.
  Kalau commit worker tidak ada di repo utama, itu normal — tetapi akui koreksinya terbuka bila laporan
  sebelumnya sudah menyebut "0 perubahan".
- **`reclaim` langsung melahirkan run baru.** Setelah reclaim, cek `current_run_id`/`worker_pid` sebelum
  `dispatch`: dispatch tambahan saat run baru sudah hidup = dua worker pada satu kartu. Untuk ganti profil,
  pakai `reassign ... --reclaim` (satu langkah), bukan reclaim lalu reassign.
- **Jangan `pkill -f "<pola>"` bila pola itu tertulis di perintah yang sama** — shell ikut cocok dengan
  baris perintahnya sendiri dan perintah Anda mati (`exit -15`) sebelum sisa rantai jalan. Ambil PID dari
  papan (`select worker_pid from tasks`) atau `ps -eo pid,args | awk '/<pola>/ && !/awk/ {print $1}'`, lalu
  `kill -9 <pid>`.
- **Jangan menaruh `time.sleep()` panjang di `execute_code`:** sel >300 detik mematikan kernel sesi dan
  seluruh state variabelnya. Untuk menunggu worker, tidur 3–4 menit per call, atau pakai `terminal` dengan
  `sleep` eksplisit di antara dua pengukuran.
- **Pulihkan setelah klasifikasi, bukan sebelum.** Perbaiki dulu penyebabnya, baru `hermes kanban unblock <id> --reason '...'`. `unblock` mereset `consecutive_failures` dan `last_failure_error` tapi TIDAK membuktikan worker spawn — konfirmasi status hasil + baris `task_runs` baru sebelum melapor jalan; jangan ulangi unblock+dispatch membabi buta pada crash loop.
- **Gagal tool = ubah strategi, jangan kirim ulang identik.** Kalau tool bilang argumen hilang/None, satu kali percobaan material berbeda (kode panjang → tulis ke file skrip, panggil dengan perintah pendek). Kalau tetap gagal, hentikan dan laporkan blocker terukur — narasi berulang bukan kemajuan.
- **Laporan ke pemilik = bukti dulu.** Perbarui hanya setelah ada perubahan status terverifikasi atau temuan berguna; pisahkan fakta terkonfirmasi vs hipotesis; jangan klaim akar masalah sebelum membaca sumbernya.

## Laporan bug pasca-pengiriman

- **Diagnosa dulu, baru kartu:** reproduce/read the failing path (code read +
  runtime probe) BEFORE dispatch; attach root cause + file/line evidence to the
  card so the worker measures instead of guessing.
- **Same-area fixes are sequential, not parallel:** link cards with
  `hermes kanban link` (parent → child) when several cards touch the same files —
  parallel siblings edit-race and corrupt each other.
- **Prove the fix at runtime** (HTTP-level call/TestClient returning 200), not
  only via the unit suite; then re-run full suite + gates.
- **Incremental overlay packaging:** diff base-manifest vs workspace to get
  changed+new files, overlay only those, verify byte-identical vs workspace,
  keep the forbidden-content scan, never overwrite a versioned ZIP.

## Pertanyaan "ada progress nyata, bukan cuma running?" — jalankan sendiri pembuktiannya

Pemilik sering menegur bahwa status `running` bukan bukti. Saat pertanyaan itu muncul, jawaban yang
diharapkan bukan ringkasan status, tapi bukti yang Anda jalankan sendiri di sesi koordinator. **Sebelum menyebut temuan terbaru, ambil snapshot live yang terlihat; bila output tool tidak terbaca/terpotong, ubah metode atau query menjadi ringkas dan ulang sekali dengan pendekatan berbeda. Jangan menjawab berdasarkan snapshot atau hasil terminal yang tidak dapat Anda lihat.**

1. **Pisahkan tiga lapis dalam jawaban:** (a) yang sudah Anda buktikan sendiri, (b) yang dihasilkan worker
   tapi belum digate, (c) yang belum ada sama sekali. Tulis (a) dan (c) eksplisit; jangan menghitung (b) sebagai (a).
2. **Jalankan probe mandiri, jangan hanya membaca output worker:**
   - kode → `php -l` / `node --check` per berkas inti;
   - aplikasi → `curl` endpoint nyata (health + rute karangan untuk 404) plus respons yang tidak mungkin
     lolos kalau layanannya mati;
   - artefak → ukuran + mtime dua kali sampling untuk melihat file benar-benar tumbuh.
   - **Probe memakai bentuk argumen dari CALL SITE, bukan karangan.** Buka pemanggilnya dulu
     (`grep -n -A10 '::build\|::render' app/controllers/*.php`) lalu susun payload sesuai kunci yang
     benar-benar dikirim. Probe dengan bentuk buatan sendiri memunculkan fatal error yang tampak seperti
     bug produk; melaporkannya sebagai defect = alarm palsu yang menyuruh worker memperbaiki kode yang
     benar. Kalau probe gagal, periksa bentuk payload Anda sebelum menyalahkan implementasi — dan kalau
     ternyata salah Anda, koreksi terbuka di laporan.
   - **Untuk kode yang memakai pustaka pihak ketiga, probe runtime menemukan bug-nya; sumber `vendor/`
     memberi API yang benar.** Error seperti `Call to undefined method Vendor\Adapter::foo()` berarti
     kode worker memakai API yang tidak ada di versi ter-vendor. Jangan menebak penggantinya dan jangan
     hanya meneruskan error ke worker: `grep -rn 'function ' vendor/<paket>/` untuk melihat signature
     nyata, lalu jalankan probe kecil yang membuktikan pemanggilan benar itu menghasilkan keluaran sah
     (cek header/ukuran, bukan `exit 0`), baru kirim snippet persisnya ke kartu. Sekaligus cek apakah
     paket memakai autoload bersarang (`vendor/<paket>/vendor/autoload.php`) — path autoload yang salah
     menghasilkan error yang tampak seperti masalah versi.
3. **Sebut biaya yang hangus.** Run yang crash/reclaim memakan jam adalah bagian dari bukti; akui, jangan disamarkan.
4. **Format closing:** status per kartu, angka yang Anda ukur ulang sendiri, temuan terbuka yang dibagikan,
   dan sisa waktu terhadap deadline. Klaim yang belum digate dinyatakan "produksi worker, belum sah" —
   bukan "selesai".

**Kalau owner menyebut kunci kartu yang tidak ada di `ORDER` ("apakah ada progres di V8?"), jangan mengarang
kartu itu.** Baca daftar kartu papan + konstanta `ORDER` driver dulu: sebut kunci yang benar-benar ada, nyatakan
kunci yang ditanyakan belum pernah dibuat, dan jawab dengan kartu yang memang berjalan. Menjawab kunci hantu
dengan status kartu lain adalah laporan palsu walau angkanya benar.

**Langkah nol sebelum menjawab: hitung apakah worker benar-benar MENULIS.** Pertumbuhan `count(messages)`
bukan bukti — yang berbukti hanya (a) jumlah call tulis, (b) berkas baru/berubah 30 menit terakhir di
repo, dan (c) commit baru. Ratusan pesan + nol call tulis + mtime berkas tidak bergerak = jawabannya
"belum ada progres nyata", sebut angkanya, lalu intervensi (lihat "Diagnose & recover stalls" → loop
baca). Jangan menyajikan `running` sebagai kemajuan hanya karena pesan bertambah.

- **`max_runtime` default kartu = 2880s (48 mnt)** — run kartu berat dipotong keras tiap 48 mnt (`reclaimed` beruntun) → worker makin sering kehilangan konteks → akhirnya `block` transient ("repeated hard reclaim at 48-minute deadline"). Diagnosa: `sqlite3 kanban.db "select status,outcome,datetime(started_at,'unixepoch','+7 hours') from task_runs where task_id='…' order by started_at"` → pola `reclaimed` tiap ~48 mnt = pasti ini.
- **Fix**: `sqlite3 kanban.db "update tasks set max_runtime_seconds=21600 where id='…'"` (6 jam; `kanban edit` tak punya flag-nya), komentar orientasi (hasil run terakhir + file yang sudah ada + "lanjut, jangan audit ulang"), `unblock`, `dispatch`.
- **Pencegahan**: saat `kanban create` kartu implementasi multi-jam → selalu `--max-runtime 21600` (lebih besar dari estimasi finish paling lambat), termasuk M4/M5 berikutnya.
- Progres terekam via komentar per unit, jadi run baru tetap lanjut dari file+komentar meski sesi hilang.

- **Jebakan approval gate deploy (VO2D-F1, 13 Okt):** worker headless menolak `systemctl restart <unit>` (single_query_mode=deny) dan memblokir kartu padahal semua bukti offline PASS. Fix koordinator: tambahkan entry allowlist presisi `"systemctl restart <unit>*"` ke `config.yaml` profile worker (pola unit tunggal, preseden aman) → unblock → worker langsung selesai deploy. Jangan minta owner restart manual kalau allowlist bisa dibuka koordinator.
- **Kalibrasi budget kartu QA/fitur UI:** 45m realistis; nudge koordinator pada ≥80% terbukti memaksa worker menutup kartu dalam budget (F4: nudge di 86% → complete di 96%).

## Audit board: path DB & kolom deadline/budget

- **Papan punya DB SENDIRI; `~/.hermes/kanban.db` adalah board default (bisa 0 baris).**
  Audit yang benar: `~/.hermes/kanban/boards/<board>/kanban.db`. Query ke DB default
  menghasilkan `rows: 0` sementara kartu jelas ada di `kanban list` — kalau query kosong padahal
  CLI menampilkan kartu, path DB-mu salah; cari dengan `find ~/.hermes -name '*.db' -path '*kanban*'`.
- **Board tidak menyimpan kolom deadline maupun budget.** Yang ada: `max_runtime_seconds` (hard cap
  per kartu) + `created_at/started_at/completed_at`. Jadi "deadline" yang bisa diklaim = cap runtime
  dan durasi kartu sebelumnya; angka lain harus disebut tidak ada di board, jangan dikarang.
  Budget direalisasikan dari kartu DONE: `completed_at − started_at` per kartu + `task_runs`.
  Rantai yang jalan SERIAL memberi deadline operasional = jumlah cap kartu (mis. 120+240+360+360+240
  ≈ 22 jam); tulis basis hitungannya, jangan hanya menyebut "deadline 22 jam".
- Tabel komentar bernama `task_comments` (bukan `comments`); selalu `PRAGMA table_info` sebelum query
  tabel yang bukan milikmu. **Tebakan nama kolom adalah sumber "data kosong" yang tak terbaca:**
  `task_comments` memakai `body` (bukan `content`), `tasks` tidak punya `block_reason` maupun `ended_at`
  (yang ada `block_kind`, `current_run_id`, `last_failure_error`, `consecutive_failures`), dan
  `task_runs.metadata` sering kosong walau kolomnya ada. Query yang mengembalikan 0 baris TANPA error
  hampir selalu berarti nama kolomnya salah, bukan datanya tidak ada — baca `pragma table_info` dulu,
  jangan menebak tiga kali.
- Resep audit lengkap (single-flight, budget, deadline, crash, efficiency) ada di
  `references/board-health-audit.md` — muat saat diminta "apakah board jalan nyata / progres /
  deadline / budget / urutan".

## Gate ditutup `done` padahal verdict BLOCKED = rantai mati (pola paling mahal)

Gejala: kartu hulu `done`, kartu hilir `blocked`, `running=0`, dashboard menampilkan 0 worker — papan tampak
"berhenti sendiri". Penyebab: kartu GATE ditutup `done` karena auditnya selesai, padahal berkas buktinya menulis
verdict BLOCKED. DAG menganggap prasyarat lulus, anak dipromosikan, anak menolak bekerja, dan tidak ada kartu
perbaikan di graf — jadi tidak ada apa pun yang bisa dijalankan. Diamnya bukan bug dispatcher.

- **Kartu gate HANYA `done` bila verdict APPROVE.** Audit selesai + verdict BLOCKED ≠ kartu selesai. Pilih:
  biarkan kartu terbuka untuk reviewer yang sama, atau pecah jadi rantai di bawah sebelum menutup apa pun.
- **`done` ≠ lulus.** Sebelum menyebut "prasyarat selesai" atau "proyek jalan", buka berkas bukti gate
  (`docs/evidence/**`) dan baca baris verdict; jangan menyimpulkan dari status kartu atau dashboard.
  **Verdict RE-AUDIT sering HANYA ada di komentar penutup kartu gate, bukan di `docs/evidence/**`:** baca
  `select body from task_comments where task_id='<gate>' order by id desc limit 1` sebelum menyimpulkan
  gate tidak menghasilkan apa-apa. Laporan gate yang tidak ditemukan di repo bukan bukti gate gagal.
- **Penyelesaian SENYAP: kartu gate `done` dengan `result` kosong DAN tanpa berkas verdict DAN tanpa komentar
  penutup.** Ini bukan gate lulus dan bukan gate gagal — worker menutup kartu sebelum menulis ringkasan. Jangan
  menutup mata dengan membaca status, dan jangan membuka ulang gate untuk minta ringkasan (itu membakar run kedua
  atas bukti yang tidak berubah). Yang benar: baca berkas ukur MENTAH yang ia tinggalkan (`*.json`, `*.tsv`, `*.txt`
  di `docs/evidence/<sprint>/`), hitung sendiri angka kuncinya (jumlah sel tidak nol, `max` selisih, hitung status
  HTTP, `min` kontras, jumlah host eksternal), lalu tulis verdict koordinator ke
  `docs/evidence/<sprint>/<gate>-verdict-koordinator.md` — angka, ambang, verdict, catatan minor, DAN satu paragraf
  "cacat proses" yang menyebut result kosong. Verdict koordinator atas bukti mentah sah sebagai dasar maju; verdict
  yang mengutip ringkasan worker yang tidak ada adalah karangan. Sampaikan cacat proses ini ke owner di laporan,
  jangan disembunyikan di berkas.
- **Recovery resmi = rantai tektokan eksplisit**, karena CLI tidak punya reopen untuk `done`
  (`promote` hanya `todo`/`blocked`, `unblock` hanya `blocked`/`scheduled`, `specify` hanya `triage`):
  1. Kartu FIX untuk produsen, parent = kartu deliverable aslinya; isi = temuan gate bernomor + ambang + bukti
     sebelum/sesudah yang bisa diukur ulang oleh orang lain.
  2. Kartu RE-AUDIT untuk reviewer yang sama (profil gate), parent = kartu FIX; wajib angka terukur + verdict tegas
     APPROVE/BLOCKED, dan dilarang memperbaiki aset (kalau memperbaiki, ia jadi produsen dan kehilangan independensi).
  3. `hermes kanban link <re-audit-id> <kartu-hilir-id>` supaya kartu hilir menunggu gate BARU, bukan gate lama
     yang bocor. Verifikasi edge di `task_links`, jangan percaya keluaran `link` saja.
  4. `dispatch --max 1`, lalu buktikan `spawned` tidak kosong + run id baru + pesan worker bertambah.
- **Jangan hapus riwayat gate yang salah tutup.** Biarkan `done`, tulis komentar: verdict BLOCKED, penyebab, dan
  ID kartu penggantinya. Menghapusnya membuat audit berikutnya mengulang kesalahan yang sama.
- **Jangan menutup gate gagal dengan `complete`** hanya untuk "merapikan papan"; papan rapi yang bohong lebih
  mahal daripada satu kartu menggantung.

## Kebalikannya: berkas gate menulis APPROVE tapi kartunya `blocked` — gate sedang minta keputusan

Pola kedua yang sama-sama berakhir di papan diam. Reviewer menyelesaikan audit, menulis verdict
"APPROVE + satu catatan non-blocking" di berkas bukti, lalu memanggil `kanban_block --kind needs_input`
karena ia sendiri tidak punya wewenang memberi pengecualian. Jangan ambil salah satu sisi sebagai kebenaran:

- **Status kartu menang atas teks berkas.** Verdict APPROVE yang berdampingan dengan temuan yang GAGAL
  ambang bukan lulus bersyarat — itu reviewer menyerahkan keputusan ke koordinator. Jangan pakai kalimat
  APPROVE itu sebagai dasar mempromosikan kartu hilir, dan sebutkan commit-nya secara eksplisit sebagai
  "tidak dipakai sebagai dasar lulus" di komentar kartu.
- **Jangan unblock gate-nya "supaya lewat".** Gate yang dijalankan ulang atas bukti yang tidak berubah akan
  memblokir lagi dan menghabiskan anggaran block-loop (`block_loop_detected`, limit 2). Biarkan gate
  `blocked`; yang maju adalah kartu FIX.
- **Default keputusan = PERBAIKI, bukan memberi pengecualian.** Pengecualian atas ambang terukur mengubah
  arti "lulus", jadi itu milik owner; sementara MENOLAK pengecualian tidak mengubah definisi apa pun dan
  hampir selalu lebih murah daripada eskalasi. Eskalasi ke owner hanya bila perbaikan mustahil atau biayanya
  melewati sisa deadline — sertakan angka gagal + dua opsi + satu rekomendasi.
- **Kartu FIX dibuat baru dan di-link sebagai parent TAMBAHAN gate** (`link <fix> <gate>`; parent lama tetap
  ada, `done` lama tidak perlu diubah). Keluaran `link` bukan bukti — verifikasi di `task_links` bahwa gate
  kini punya parent baru, dispatch fix-nya, dan biarkan gate `blocked` sampai fix `done`; baru `unblock`
  untuk re-audit oleh profil gate yang SAMA (jangan perbaiki sendiri, itu menghapus independensi).
- **Temuan yang menyentuh keselamatan pengguna, teks medis, atau disclaimer tidak pernah "non-blocking"**
  apa pun verdict yang ditulis reviewer. Begitu juga temuan yang menyentuh data pengguna atau keamanan.
- **Catat keputusan di kartu gate**: pengecualian ditolak, alasannya, id kartu fix, dan bahwa verdict lama
  tidak berlaku — supaya audit berikutnya tidak membaca berkas lama sebagai izin.

### Setelah fix `done`, gate TIDAK lepas sendiri — dan `block_kind` basi menipu pembacaan status

- **`blocked` adalah tahanan manual kecuali `block_kind=dependency`.** Semua parent `done` tidak melepas gate;
tanpa `unblock` eksplisit gate itu duduk berjam-jam sementara papan terlihat "sudah pulih". Begitu kartu FIX
`done`: ukur ulang sendiri → `unblock <gate> --reason "F<n> fixed: <angka sebelum> -> <sesudah>"` →
`dispatch --max 1` → buktikan run baru.
- **Jangan memakai `done` dari worker untuk menutup temuan gate.** Jalankan sendiri probe gate-nya (satu
perintah) dan kutip baris ringkasannya ("2.611 node teks 0 gagal, 84 field form 0 gagal"). Klaim worker =
hipotesis, termasuk klaim yang sudah menyertakan angka.
- **Status dibaca dari `status`, bukan `block_kind`.** `unblock` tidak membersihkan `block_kind`, jadi kartu
`running` bisa masih bertuliskan `needs_input` dan siapa pun yang membaca kolom itu menyimpulkan pemulihan gagal.
Klaim "tidak ada blocked" baru sah bila `count(status='blocked')=0` DAN tidak ada `block_kind` pada baris
non-blocked; bersihkan nilai basi dengan update sempit (`where status!='blocked'`) sebelum melapor.
- **Supervisor butuh kelas alert khusus `BLOCKED-BASI`** — kartu tertahan padahal semua parent `done` dan usia
hold >10 menit. Blokir jenis ini tidak memicu sinyal lain (tidak ada run mati, tidak ada 429), jadi tanpa
deteksi khusus papan diam berjam-jam. Dedupe per kartu; supervisor melapor, bukan membuka sendiri.
Detail + query verifikasi: `references/kanban-status-transitions.md`.

## Supervisor: dispatcher resmi, recovery sampai worker nyata

Script supervisor tidak boleh mempromosikan `todo` atau mengubah status langsung; itu bisa melompati dependency. Tiap siklus panggil hanya `hermes kanban --board <board> dispatch --max 1`, lalu verifikasi hasil `spawned`, status kartu, run baru, dan pertumbuhan pesan worker. Beri supervisor `PATH` eksplisit yang memuat direktori `hermes`, karena cron tidak mewarisi PATH shell interaktif. Jangan menganggap cron aktif atau dispatch sukses sebagai bukti kerja.

Saat kartu `blocked`/`triage`, jangan tinggalkan papan idle: baca sebab spesifik dari event/run, simpan komentar berisi kelanjutan dan acceptance yang belum lolos, lalu jalankan pola FIX → RE-AUDIT → kartu hilir ber-parent pada re-audit. `triage` tidak akan di-dispatch; pulihkan hanya melalui transisi Kanban yang didukung dan verifikasi status `ready`/`running`, jangan memanipulasi status DB kecuali jalur pemulihan resmi gagal dan perubahan audit-log terdokumentasi. Setelah tiap perpindahan kartu, tetap pantau sampai ada run aktif sungguhan atau laporkan blocker teknis terukur.

Jangan membuka kartu revisi dengan acceptance yang tak mungkin dipenuhi oleh aset/alat yang tersedia tanpa lebih dulu memeriksa repo dan tool aktual. Cari deliverable yang ada, verifikasi browser/Playwright/tool lewat path penuh bila cron/worker PATH berbeda, dan pecah scope revisi menjadi unit terukur yang memang bisa dikerjakan. Jika worker block karena scope terlalu besar, buat kartu revisi lebih kecil untuk profil yang sama dengan syarat bukti yang jelas; jangan sekadar unblock berulang hingga loop.

## `kanban edit --body` dapat mengosongkan body tanpa error

`--body "$(cat file-yang-belum-ada)"` berisi string kosong dan tetap sukses — body kartu terhapus, tanpa peringatan.
Simpan body setiap kartu ke berkas (sumber kebenaran yang bisa dipulihkan), dan setelah SETIAP `edit` jalankan
`kanban show <id>` untuk memastikan body masih berisi. Kalau kosong: pulihkan dari berkas/skrip pembuat kartu, lalu
verifikasi ulang — jangan lanjut dispatch dengan kartu berbadan kosong.

## Kartu yang nyangkut di `triage` tidak akan pernah di-spawn

`unblock` yang gagal dengan "unblock loop detected — needs a human decision" memindahkan kartu ke `triage`, dan
dispatcher hanya menyentuh `ready`. Pulihkan body dulu, pastikan parent barunya sudah terpasang, baru transisi
`triage` → `todo` (lewat `specify`, atau transisi admin + event `promoted`), lalu `kanban list` untuk verifikasi.
Tanpa perbaikan ini kartu itu diam selamanya walau seluruh graf lain sudah `done`.

**Run yang berakhir `blocked/needs_input` juga melempar kartu ke `triage`.** Jadi keluhan owner "tidak ada kartu
aktif" / "status masih blocked" pada papan yang tadinya jalan hampir selalu gejala ini — bukan worker mati dan
bukan dispatcher rusak. Urutan pemulihan yang terbukti (`unblock` dan `promote` sendirian TIDAK cukup, keduanya
menolak untuk kartu `triage`):

```bash
hermes kanban --board <b> specify <id> --author <koordinator>   # triage -> todo
hermes kanban --board <b> dispatch --max 1
sleep 20 && hermes kanban --board <b> show <id>                 # harus running + run baru
```

Sebelum transisi, pastikan penyebab blokirnya sudah dijawab di komentar kartu. Kartu yang dilepas tanpa jawaban
akan memblokir lagi dengan sebab yang sama lalu kembali ke `triage` — block-loop yang memakan satu run penuh
per putaran.

## Bukti "board jalan nyata" — empat lapis, jangan cukup satu

Saat menjawab pertanyaan status yang disertai screenshot/dashboard, jelaskan hanya indikator yang terlihat dan bedakan snapshot UI dari bukti runtime: angka worker/run/card pada gambar adalah tampilan saat diambil, bukan jaminan kondisi sekarang. Jika user hanya meminta deskripsi gambar, jawab isi visual secara ringkas tanpa melanjutkan audit proyek atau menyatakan status terkini.

Card `running` saja TIDAK membuktikan board hidup. Uji berurutan, hentikan di lapis
yang gagal:

1. **Dependency hard gate** — kartu anak tetap `todo`/`dependency_wait` sampai SEMUA parent
   `done` (`recompute_ready` di `kanban_db.py`). Kalau anak parent-nya belum `done` dan
   statusnya `todo`, rantai tidak mungkin paralel secara struktur.
2. **Satu run aktif per kartu** — `SELECT task_id,count(*) FROM task_runs WHERE status='running'
   GROUP BY task_id`; >1 = duplikasi.
3. **Claim hidup** — `current_run_id` + `worker_pid` + `claim_expires` di masa depan.
4. **Dispatcher tunggal di host** — dispatcher kini EMBEDDED di gateway
   (`kanban.dispatch_in_gateway: true`), jadi grep `kanban (dispatch|daemon)` bisa
   kosong walau dispatch berjalan; buktikan dari config gateway + satu proses gateway
   hidup, lalu grep cron semua profile. `hermes kanban daemon` standalone sudah
   deprecated (menolak start dengan pesan deprecation) — menjalankannya atau
   memaksanya berarti dispatcher KEDUA yang berebut klaim. Dispatcher kedua = work
   ganda; satu watchdog dispatcher sudah cukup.

Baru setelah itu buktikan worker benar-benar bekerja: `/proc/<worker_pid>` ADA **dan**
`count(messages)` di `state.db` bertambah dalam 60–90 detik. Hanya heartbeat = belum cukup.
**Kartu yang sudah `running` dengan worker hidup tidak boleh di-dispatch manual** — itu
pekerjaan duplikat yang membakar kuota, bukan kartu yang "dibantu".

## Pisahkan 3 kelas kegagalan sebelum intervensi

- **Kegagalan worker** — `task_runs.error` + `json_extract(metadata,'$.worker_output')` +
  log kartu `logs/<task_id>.log`.
- **Kegagalan infrastruktur** — drain/startup gateway, tool-argument truncation, 429/5xx proxy.
  Gejalanya tidak membuktikan worker rusak; re-dispatch worker hidup = pemborosan dobel.
- **Bug parser SDK** — exception yang TIDAK masuk kategori transient/streaming di
  `error_classifier.py` (mis. `IndexError` saat accumulate event SSE) bukan rate limit dan
  tidak memicu fallback otomatis. Cek daftar kategori itu sebelum menyebut akar masalah.

## Konkurensi: `max_in_progress` itu host-level, bukan per-board

`kanban.max_in_progress*` menghitung seluruh host. Menurunkannya demi "board ini saja" ikut
membatasi board lain yang sedang hidup (mis. board auto-clipper). Kalau memang perlu
membatasi, konfirmasi dulu bahwa pengurangan itu aman untuk semua board di host ini;
default: JANGAN sentuh — andalkan dependency gate + claim DB. Detail di
`kanban-rate-limit-resilience`.

## Selamatkan kerja tak-ter-commit sebelum re-dispatch (kartu crash-loop)

Kalau kartu `blocked` setelah beberapa crash, workspace masih menyimpan kerja worker yang BELUM
di-commit — dan run baru bisa me-restart dari nol atau workspace di-prune saat `done`. Commit
ULANG pekerjaan itu sendiri, dari sesi koordinator, SEBELUM `unblock` + `dispatch`:

```bash
git -C <repo> add -A && git -C <repo> commit -m "M<n> WIP: <apa yang diselamatkan>"
```

Laporkan commit hash + jumlah file + delta baris sebagai bukti bahwa crash tidak menghapus
apa pun. Lalu taruh BRIEF ANTI-CRASH di komentar kartu (komentar dibaca worker pada setiap
spawn, jadi tahan requeue): (a) akhiri setiap run dengan aksi kanban terminal + komentar
berangka — keluar bersih tanpa itu ADALAH protocol violation yang membakar budget retry;
(b) commit setelah tiap item checklist; (c) tool call pendek; (d) setelah 2x gagal dengan
tool yang sama, ganti tool — jangan kirim ulang call identik. Verifikasi re-dispatch benar-benar
spawn: baris `task_runs` terbaru + pertumbuhan `count(messages)` di `state.db` profil worker.

**Tambahkan TOOL-CHOICE MATRIX ke brief anti-crash** — `terminal` dengan heredoc panjang adalah
pemicu crash worker yang paling konsisten, tapi brief yang hanya bilang "tool call pendek" terlalu
vague untuk worker yang sedang loop. Tulis eksplisit, siap-tempel:

> Untuk kerja file: pakai `write_file`/`read_file`/`search_files`/`patch` — JANGAN heredoc besar
> via `terminal`. `terminal` HANYA untuk perintah 1 baris <100 karakter (`git status`, `php -l file`).
> Gagal tool 2x? Ganti tool, jangan ulang sama.

Dan tambahkan aturan tulis-berkas, karena worker yang menimpa berkas tanpa membacanya akan mengulang
call yang sama dan membakar kuota:

> Sebelum menimpa berkas yang SUDAH ADA: `read_file` dulu (1×), baru `write_file`. Berkas BARU boleh
> langsung `write_file`. Jangan kirim call tulis yang sama lebih dari 2× — kalau hasilnya tidak berubah,
> baca hasilnya, perbaiki penyebabnya, atau tulis ke path lain dan catat di komentar. Ulangi baca berkas
> yang sama maksimal 1× per run; kalau butuh lagi, tulis ringkasannya ke catatan kerja dulu.

Larang juga tool yang tidak ada di sesi worker (editor eksternal/Cursor-style). Worker yang mencoba
memanggilnya akan menghabiskan beberapa menit lalu berhenti dengan pesan menyerah — tulis eksplisit
"tulis langsung dengan `write_file`, jangan panggil editor eksternal".

Brief spesifik begini yang benar-benar mengeluarkan worker dari loop 26 menit yang sebelumnya
sudah menghabiskan 7 crash — bukan pengulangan prinsip umum. Satu perintah `unblock --reason <panjang>`
juga bisa terpotong dan membuat unblock jadi no-op diam-diam — alasan panjang → tulis ke komentar
terdekat, `--reason` pendek saja.

## Re-estimate budget kartu berikutnya dari durasi TERREALISASI

Budget yang ditulis saat kartu dibuat adalah ESTIMASI, dan bisa meleset 5x. Turunkan budget
kartu berikutnya dari kartu yang benar-benar selesai: `completed_at - started_at` per kartu DONE,
lalu pakai `max(estimasi, P75 durasi realisasi)`. Sebut rasionya eksplisit ("estimasi 120m,
realisasi 588m") supaya pembengkakan terlihat dan tidak diam-diam dibawa ke milestone
berikutnya. Kartu yang melewati budget tertulis >100% adalah sinyal untuk MENAIIKAN budget
kartu saudara berikutnya — bukan untuk memotong budget kartu yang sedang jalan.

## Ketahanan kuota (jendela 5 jam)

Lihat skill `kanban-rate-limit-resilience` untuk tangga 429; penambahan penting: pool 2-key per profil + watchdog cron per jam (deskripsi di skill itu).

## Jebakan hari-kerja panjang yang terbukti (eVoting 6 Okt 2026)

- **Security-scan capability block = pembunuh diam.** Worker yang `pip3 install`/apt kena `BLOCKED: Security scan` menggantung → 2× `crashed` → dispatcher `gave_up` (failure_limit=2) → kartu `blocked` permanen. Jangan serahkan instalasi prasyarat ke worker: **pasang dari sesi koordinator** lalu unblock dengan komentar akar+arah. (Playwright terpasang koordinator; suite-nya sendiri jalan via HTTP polos tanpa browser.)
- **Heartbeat menipu**: worker bisa `running`+heartbeat padahal call API menggantung (run 147: 17 mnt tanpa pesan, `request_timeout` tak mematikan). Metrik reliable = **pertumbuhan `count(messages)` state.db dalam 60-90 dtk**, bukan umur `timestamp` (kolom bisa basi) dan bukan heartbeat. Diam >10 mnt tanpa anak proses → kill + `kanban dispatch` respawn segar.
- **`auth.json` termutasi ulang** oleh worker lama saat-saat crash (entry kosong/`401` muncul lagi setelah dibersihkan) — bersihkan SETELAH worker diganti, baru verifikasi.
- **Entry pool `401`/kosong menghapus diri tiap rotate** = buang 1 attempt percobaan → buang entry mati; 1 key valid > 2 key satu mati.
- Reviewer menghitung berbeda (7 form vs 3) → **hitung definitive sendiri SEKALI**, catat di kartu, lanjut; jangan diulang-ulang = boros request.

## Gerbang yang bisa melaporkan angka PALSU (ContohProyek, 22 Okt 2026)

- **Dua gate/inspect concurrent = laporan degraded tanpa error.** Gejalanya: `inspect_artifacts=0`, `renders=0`, `changed_pct=None` padahal halaman sehat. Penyebab: session `playwright-cli` yang sama dipakai dua proses + folder output yang saling menimpa. Ran lokal terlihat "selesai" tapi angkanya tidak valid — HATI-HATI, output `exit 0` bukan jaminan angka benar.
- **Perbaikan yang terbukti (pakai ulang):** (1) session browser unik per proses (`playwright-cli -s=<uniq>`), (2) folder output unik per run (`gate/runs/<timestamp-pid>/`) plus `report.json` global, (3) file lock `gate/gate.lock` berisi PID — gate kedua MENUNGGU (bukan gagal) lalu jalan setelah lock lepas; keluar dengan exit 75 = "lock", bukan kegagalan skill.
- **Uji sendiri perbaikannya, jangan berasumsi.** Jalankan 2 gate paralel lewat subprocess; criteria sukses: keduanya `exit 0` dengan angka identik, dan yang kedua tercatat menunggu. Ini yang membuktikan claim "anti-tabrakan" bukan sekadar teorema.
- **Artefak 0 byte / render 0 = gejalanya, bukan penyebabnya.** Urutan wajib: open → resize → screenshot, dan pastikan file > 1KB sebelum dihitung.
- **Jangan pakai `&` di foreground tool** — Hermes menolak. Untuk uji paralel, pakai `subprocess.Popen` + `communicate()` di `execute_code`.

## Pitfall: kartu backfill/riwayat langsung dieksekusi dispatcher

Membuat kartu untuk pekerjaan yang SUDAH selesai (backfill W0 ke board proyek) tanpa `--initial-status blocked`
langsung memicu dispatcher: kartu masuk `ready`, worker `koordinator` spawn, dan request terbakar untuk pekerjaan
yang deliverable-nya sudah ada. Kejadian nyata ContohProyek v2, 23 Okt 2026: 3 kartu W0 ter-claim dalam hitungan detik.

Aturan:
- Kartu backfill/riwayat WAJIB dibuat dengan `--initial-status blocked`, lalu ditutup `complete --force --result "…"`
  (complete tanpa `--result` ditolak: "no result or summary evidence").
- Kartu gelombang berikutnya yang belum boleh jalan: `--initial-status blocked` juga — jangan mengandalkan
  `--parent` saja, karena root wave tanpa parent langsung `ready`.
- `block --kind dependency` TIDAK menahan kartu: bila semua parent sudah `done`, kartu auto-release ke `todo`.
  Untuk penahan manual (menunggu kredensial/GO owner) pakai `--kind capability` / `needs_input`.
- `block` tidak punya flag `--reason`; alasannya argumen posisional: `kanban block <id> --kind capability "…"`.
- Setelah seed, verifikasi `SELECT count(*) FROM task_runs WHERE status='running'` = 0 dan tidak ada proses
  `kanban_worker_client`, baru laporkan board siap.

## Wajibkan skill dengan ANGKA, bukan daftar (ContohProyek, 22 Okt 2026)

- **"Skill ter-install" ≠ "skill terpakai".** Preload di kolom `skills` kartu hanya menjamin file ada di disk. Bukti pakai = call-record nyata di `state.db` profil + artefak output. Klaim lama "5 skill dipakai semua worker" ternyata hanya 2 yang punya call-record (taste 20 call, playwright 12 call) — 3 lain nol. Audit klaim pakai data, bukan HOA.
- **Gate skrip sebagai penutup kartu:** satu skrip menjalankan kelima skill, menulis angka per skill ke `report.json` dengan status MEASURED / NOT MEASURED. Isi kartu: "wajib jalankan gate + tulis angka per skill di komentar penutup; kartu tanpa angka = belum selesai". Contoh hidup: `projects/example-site/scripts/design_gate.py`.
- **Chrome sebagai root butuh `--no-sandbox`** — `inspect.mjs` crash dengan "Running as root without --no-sandbox". Patch `skills/design-taste-frontend/scripts/lib/cdp.mjs` (guard `process.getuid() === 0`, bukan flag unconditional) di SEMUA profil yang memakai skill itu, bukan cuma profil yang sedang kerja.
- **Screenshot butuh browser terbuka dulu** — urutan: open → resize → screenshot. Tanpa open, file keluar 0 byte dan diff piksel jadi sampah.
- **Audit DOM bisa false positive.** SVG 0×0 di breakpoint mobile bisa BENAR bila elemen itu `display:none` (nav desktop diganti hamburger mobile). Cek rantai parent (`display`, `visibility`) sebelum menyatakan bug — dan laporkan koreksi klaim lama secara terbuka.
- **Komponen SVG wajib dimensi eksplisit** (`width`/`height` atau CSS) — inline SVG tanpa `viewBox`/size = kotak kosong di header.

## Proyek bermaniesto node: satu node = satu branch = satu PR

Dipakai saat pekerjaan datang sebagai PRD + manifest node (JSON dengan `dependsOn`, `wave`,
`touchPaths`, `requiresDecisions`) dan bukan sebagai kartu Kanban.

- **Hanya spek terbaru + manifest yang jadi instruksi.** Dokumen/spek versi lama = referensi audit,
bukan perintah kerja. Salin keduanya verbatim ke repo dan buktikan dengan md5 terhadap sumber, supaya
worker berikutnya tidak bekerja dari versi cache.
- **Gate wave-0 yang tertahan layanan eksternal → ganti dengan padanan lokal, jangan menunggu.** Kalau satu node gate
  (mis. staging) hanya gagal karena DB/hosting pihak ketiga yang kredensialnya tidak dipegang owner, dan owner bilang
  "buat lokal dulu", bangun instance lokal setara (DB baru + service + vhost port sendiri, lihat
  `self-hosted-web-service-ops` → "Staging paralel"), ukur dengan sapuan route, lalu tutup kartu gate dengan bukti itu.
  Gate yang menggantung pada hal di luar kendali membuat seluruh gelombang berikutnya terlihat "belum siap" padahal
  pekerjaannya sudah selesai. Pindahkan status "500 di hosting" menjadi temuan tertulis, bukan blocker board.
- **Jangan menulis kode fitur sebelum gate wave-0 ditutup**, walau terasa lambat. Kalau gate terhalang
aksi owner, isi waktu dengan artefak proses (dokumen discovery, PR, register keputusan, skrip
verifikasi) — bukan kode fitur yang bisa jadi sampah bila keputusan berubah.
- **Satu node satu branch, PR ke `integration/<versi>`.** Branch dasar berisi spek + manifest; tiap
node bercabang dari situ dan hanya membawa `touchPaths`-nya. PR yang acceptancenya belum penuh
dibuka sebagai **draft**, body-nya memuat: yang sudah lulus (dengan angka), yang belum, dan perintah
persis untuk menutupnya. Jangan merge sendiri — itu tugas reviewer/owner.

### Materialisasi manifest ke papan Kanban (wajib, bukan opsional)

Owner menuntut pekerjaan manifest tampil sebagai papan nyata — setiap node satu kartu, penanggung
jawab bernama, urutan gelombang, dan dependency yang bisa diperiksa. Narasi urutan di chat TIDAK
memenuhi permintaan itu.

1. **Satu papan per proyek:** `hermes kanban boards create <slug> --name "<Proyek>" --default-workdir <repo> --switch`.
   Papan punya DB sendiri di `~/.hermes/kanban/boards/<slug>/kanban.db`.
2. **Satu kartu per node**, body lewat `--body-file` (tujuan, scope `touchPaths`, done-when, bukti,
   nama branch, budget menit) — bukan `--body` satu baris. Cap runtime tetap `--max-runtime 21600`.
3. **Pasang parent saat CREATE (`--parent`, boleh berulang), jangan `create` dulu lalu `link`.**
   Dispatcher melepas kartu begitu dibuat; menautkan belakangan = balapan yang sudah kalah. Kalau
   terlanjur: `reclaim` → `link` → verifikasi edge di `task_links`.
4. **Gelombang yang belum boleh jalan ditahan — dan PILIH jenis penahannya, bukan asal `blocked`:**
   - **Urutan gelombang antar-node → `--kind dependency` + `--parent`.** Dispatcher melepas sendiri saat semua parent
     `done`; tidak butuh orkestrator dan tidak butuh daftar-ID manual.
   - **Menunggu GO owner untuk gelombang berikutnya → `--initial-status blocked`** (block_kind kosong). TIDAK ada
     yang melepasnya otomatis — release harus eksplisit (`unblock`).
   - **Owner/keputusan/kredensial/provider → `--kind capability`.** Juga tidak pernah auto-release; release hanya
     lewat daftar ID eksplisit di orkestrator. Jangan pilih jenis ini untuk urutan gelombang: orkestrator lalu
     terpaksa mencocokkan **judul** kartu (rapuh terhadap rename) padahal dependency sudah menyelesaikannya.
   Root wave tanpa parent tetap langsung `ready` — karena itu wajib ditahan eksplisit.
5. **Reviewer = kartu anak dari node** (parent = node), bukan kartu lepas; dependency itulah yang
   menahan review sampai induk `done`.
6. **Serialkan penulis `migrations/**`:** satu kartu saja per waktu; kartu migrasi berikutnya diberi
   catatan "rebase dari branch migrasi sebelumnya" di body, bukan diandalkan pada urutan dispatch.
7. **Verifikasi sebelum melapor:** edge di `task_links` sesuai rancangan, tidak ada kartu terkunci
   berstatus `ready`, dan `SELECT count(*) FROM task_runs WHERE status='running'` = 0.
8. **Laporan serah-terima board memuat ID kartu + penanggung jawab + urutan + status penahan** —
   itu yang dimaksud owner dengan "siapa saja yang bertugas kerja".

**Pitfall: `git add` dengan satu path yang belum ada membatalkan SELURUH add.** `touchPaths` sering
menyebut direktori yang belum dibuat (mis. `ops/**`). `git add docs/X.md ops scripts/a.sh` gagal
exit 128 dan tidak men-stage apa pun → `git diff --cached --quiet` benar → cabang mencetak
"SKIP (tidak ada perubahan)" dan node itu **hilang tanpa error**. Dua penangkal: filter path ke yang
benar-benar ada (`[ -e "$p" ] || continue`) dan, setelah loop, wajibkan `git status --porcelain` kosong
plus tiap node punya `git diff --stat HEAD~1 HEAD`. "SKIP" dari skrip sendiri adalah sinyal periksa,
bukan sinyal selesai.

## Topologi rantai: SERIAL bukan BINTANG — audit EDGE SET, bukan keberadaan link

Membuat N kartu anak yang semuanya ditautkan ke satu akar menghasilkan topologi BINTANG
(fan-out): begitu akar `done`, SEMUA anak dilepas dispatcher dalam siklus yang sama, jadi
beberapa worker berjalan paralel di profil berbeda. Rantai serial yang dimaksud ("tepat satu
worker aktif di seluruh papan") butuh edge BERURUTAN: S0→S1→S2→S3, bukan S0→S1, S0→S2, S0→S3.

- **Pola saat create:** untuk rantai serial, `--parent` menunjuk kartu SEBELUMNYA di rantai
  (kartu ke-2 parent = kartu ke-1; ke-3 parent = ke-2). Kalau id parent belum diketahui,
  create semua kartu dulu → `reclaim` tiap waiter → `link` berurutan.
- **Jangan** `create` semua kartu tanpa parent lalu `link` akar ke setiap anak: dispatcher
  bisa mengklaim anak dalam hitungan detik dan `link` ditolak ("child is already running"),
  sehingga perbaikannya berubah jadi perebutan klaim.
- **Perbaikan topologi yang terlanjur bintang:** `unlink` edge yang tidak tergolong, lalu
  `link` rantai berurutan. WAJIB `--board <slug>` pada `link`/`unlink` — tanpa flag itu CLI
  menulis ke board default yang bisa berbeda dan kosong, jadi perbaikan hilang tanpa efek
  pada papan target.
- **Verifikasi = BANDINGKAN edge set dengan topologi yang dimaksud**, bukan "link-nya ada":
  `SELECT parent_id, child_id FROM task_links`, lalu cek tiap anak punya tepat SATU parent
  yang benar dan kartu pertama tanpa parent. Anak dengan DUA parent tetap bisa jalan begitu
  salah satunya `done` — itu paralelisme tersembunyi.

Konsekuensi topologi bintang: aturan satu-worker-aktif runtuh diam-diam, aturan "perbaikan
satu area berkas bersifat serial" ikut runtuh (dua penulis pada berkas yang sama), dan
"deadline = jumlah budget kartu pada rantai serial" jadi angka bohong.

### Gate REVISE: kartu FIX harus jadi MATA RANTAI, bukan kartu sampingan

Kartu FIX yang dibuat setelah verdict REVISE sering ditautkan hanya ke gate-nya, sementara kartu hilir
sudah ber-parent gate itu juga — jadi saat gate `done`, fix DAN hilir dilepas pada siklus yang sama.
Worker hilir menemukan diff di luar tangannya, memblokir diri sendiri (`needs_input`) demi menjaga serial,
dan rantai berhenti sampai koordinator membuka blokir manual: jam kerja hilang tanpa error di mana pun.

- Sebelum `dispatch`, jadikan fix parent kartu hilir: `hermes kanban --board <b> link <fix> <hilir>`.
  Gate tetap boleh `done` (auditnya memang selesai); yang menahan hilir adalah fix.
- Verifikasi di `task_links` bahwa hilir punya FIX sebagai parent, bukan hanya gate lama.
- Kalau hilir terlanjur jalan paralel dengan fix: itu pengaman yang bekerja, bukan kegagalan worker.
  Setelah fix `done` + ter-commit, unblock hilir dengan komentar "penulis kedua sudah berhenti, lanjut dari
  commit <sha>"; jangan unblock selama fix masih menulis.
- Rantai ini bisa dijalankan sebagai satu perintah: `scripts/rework_chain.py` (buat FIX + RE-AUDIT + link +
  dispatch, dengan `--dry-run` untuk memeriksa isi kartu sebelum ada yang dibuat). Pakai itu, jangan
  merangkai `create`/`link` manual yang gampang melewatkan edge hilir.

### Sebelum membuat kartu FIX: periksa duplikat, lalu tetapkan SATU HEAD otoritatif

Reviewer gate sering membuat kartu FIX sendiri (parent = kartu gate) pada detik yang sama ia menulis verdict.
Koordinator yang membuat kartu FIX tambahan menghasilkan DUA branch untuk temuan yang sama; merge keduanya
bentrok di berkas yang sama dan menyita satu putaran penuh.

- **Cek kartu yang lahir dari gate sebelum `create`:** `select id,title,status,assignee,created_at from tasks
  where created_at > <waktu gate mulai>`. Kalau kartu FIX untuk temuan itu sudah ada, ambil alih kartu itu
  (komentar + dispatch), jangan buat yang baru.
- **Duplikat yang terlanjur ada: jangan hapus, tapi jangan biarkan menempel di papan.** Tidak ada `cancel`;
  tulis komentar `DITUTUP SEBAGAI DUPLIKAT` yang menyebut kartu penggantinya, lalu `hermes kanban --board <b>
  archive <id>` (tanpa flag `--reason` — alasan masuk ke komentar). Kartu `blocked` sisa selalu dibaca owner
  sebagai "pekerjaan tertahan" ("kenapa masih ada kartu blocked?"), jadi arsipkan hanya SETELAH lingkupnya
  benar-benar tertutup oleh verdict gate, dan sebut angkanya di laporan (`N done · 0 blocked · 1 archived`).
- **Tetapkan satu HEAD/branch acuan dan tulis di komentar kartu RE-AUDIT** (commit + nama branch + "abaikan branch
  duplikat"). Auditor yang mengukur branch lain memberi verdict yang tidak berlaku untuk kode yang akan dirilis;
  pastikan acuan itu benar-benar memuat tiap temuan (`search_files` untuk penanda/fungsi perbaikan di HEAD tersebut).
- **Konflik merge antar-branch perbaikan bukan pekerjaan koordinator:** `git merge --abort`, pilih satu branch yang
  sudah memuat semua perbaikan, jadikan acuan. Menyelesaikan konflik kode produk sendiri menghapus independensi
  koordinator dan bisa membawa perbaikan yang tidak pernah digate.

### Monitor boleh observasi dan dispatch, TIDAK boleh membunuh berdasarkan pola proses

Watcher dengan fungsi "bersihkan orphan worker" berbasis pola nama proses membunuh worker SAH yang baru lahir —
termasuk auditor yang baru berjalan 40 detik — dan jejaknya hanya satu baris `killed` di log. Aturan:

- Bunuh hanya PID yang diambil dari papan (`select worker_pid from tasks where id=<kartu>`), dan hanya setelah
  `max(timestamp)` pesan profil itu lebih tua dari ambang diam.
- Worker berumur <5 menit tidak pernah layak dibunuh, walau `ps` menampilkan proses ganda.
- Skrip laporan read-only tidak boleh punya jalur kill sama sekali.
- Kalau worker sah terlanjur dibunuh: `reclaim <kartu> --reason "..."` — dispatcher gateway akan melahirkan run
  baru; verifikasi `worker_pid` + `current_run_id` berubah dan pesan bertambah. Jangan dispatch tambahan di atas
  run yang sudah hidup, dan jangan hidupkan lagi watcher yang logikanya cacat.

## Kontrak bukti dari owner = isi kartu, bukan ringkasan chat

Saat owner memberi GO satu gelombang, ia hampir selalu melampirkan DAFTAR BUKTI (nol link rusak, N/N halaman 200,
login+ganti sandi jalan, logo terbaca di 32 px, Lighthouse ≥ ambang, screenshot). Daftar itu kontrak kerja:

- **Tempel verbatim ke tiap kartu** node yang disetujui (comment atau body), termasuk aturan branch/PR/no-self-merge.
  Worker tidak membaca chat koordinator; kartu adalah satu-satunya kanal yang tahan requeue.
- **Tambahkan kalimat escape:** “kalau bagian ini bukan lingkup kartu, tulis `di luar lingkup` + siapa yang menutup.”
  Tanpa itu worker memaksa mengerjakan bukti milik node lain (foto/favicon di kartu model data) atau mengklaim palsu.
- **Rekonsiliasi daftar owner dengan register keputusan sebelum dispatch.** Daftar “siap” dari owner bisa memuat node
  yang keputusannya masih DITUNDA (mis. node notifikasi email saat provider email belum dipilih). Register menang
  sampai owner menyatakan sebaliknya: tahan kartu itu, sebut alasannya, dan tanyakan sekali bersama pertanyaan
  terbuka lain dalam SATU form — jangan diam-diam mengerjakannya, jangan pula diam-diam membuangnya.
- **Berhenti di node terakhir yang disebut owner, lalu kirim laporan gate** (status per node + bukti berangka +
  yang belum terukur). Jangan menyambung ke gelombang berikutnya walau kartu-kartu berikutnya terlihat siap.

## Orkestrator 15 menit: gerbang provider + auto-release ber-guard

Papan yang sudah tersusun rapi belum berarti pekerjaan berjalan — dan papan yang "berjalan" lewat crash-loop
membakar kuota tanpa hasil. Pasang SATU cron no-agent yang BERAKSI, bukan sekadar melapor.

**Satu sumber kendali untuk dispatch.** Sebelum memasang cron atau supervisor baru, audit cron aktif, dispatcher, dan script yang sudah dipakai; jangan menjalankan watchdog kedua yang juga mempromosikan atau dispatch kartu. Gunakan state machine teruji di `scripts/orchestrator_monitor.py` sebagai dasar, bukan shell loop ringkas yang menebak status dari teks `kanban list`: teks berubah dan `todo` tidak selalu berarti dependency siap. Jika kebutuhan hanya laporan berkala, gunakan monitor pelaporan terpisah yang read-only; jangan beri kewenangan mengubah status atau dispatch. Verifikasi bahwa scheduler menerima jadwal, delivery, dan stop condition yang dimaksud sebelum menyebut monitor aktif; job berulang tidak otomatis berhenti saat proyek selesai kecuali ada mekanisme eksplisit dan telah diuji.

**Jangkar H+0 dari event pembukaan, bukan observasi terlambat.** Simpan timestamp tepat saat kartu pertama benar-benar dibuka/dispatch berhasil, beserta bukti run/start di Kanban. Jangan mengisi H+0 pada tick supervisor pertama yang kebetulan melihat kartu `running`; jika waktu pembukaan tidak tertangkap, tandai H+0 tidak diketahui dan minta keputusan owner, jangan mengarang durasi.
1. **Gerbang kesehatan provider sebelum dispatch.** Satu probe (`POST /v1/messages`, `max_tokens: 4`) memakai key
   profil worker; baca status + body, jangan pernah cetak token. 200 → boleh dispatch; 503/429 → jangan spawn apa
   pun, tahan kartu dengan `block --kind capability` + alasannya, dan laporkan "provider terhambat". Tanpa gerbang
   ini, tiap tick melahirkan worker yang mati <60 detik dan tiap kematian tetap memakan request.
2. **Auto-release rantai WAJIB ber-guard assignee.** Rilis kartu `blocked` (block_kind kosong) hanya bila SEMUA
   parent `done` **DAN** assignee-nya tidak punya kartu `running`. Tanpa guard kedua, dua kartu mendarat di profil
   yang sama sekaligus — termasuk dua penulis `migrations/**` — dan urutan serial yang baru dirancang hilang
   diam-diam (kejadian nyata: kartu `content-model` terlepas saat `auth-rbac` masih jalan).
3. **Setelah insiden 429: satu spawn per siklus** (`dispatch --max 1`), naikkan hanya setelah beberapa siklus bersih.
4. **Stall diukur dari pertumbuhan pesan, bukan heartbeat:** reclaim bila `select max(timestamp) from messages`
   di `state.db` profil assignee lebih tua dari 12 menit.
5. **Kartu yang ditahan karena provider dibuka otomatis saat probe 200** — jangan menunggu owner, tapi juga jangan
   unblock buta tiap tick (lihat `kanban-rate-limit-resilience`: hentikan auto-unblock setelah ~3 iterasi identik).
   Daftarkan kartu itu lewat **ID eksplisit** (`PROVIDER_HOLD_IDS`), bukan prefix judul — rename judul membuat
   release diam-diam berhenti. Dan probe-nya harus mencoba SEMUA entry pool sampai ada 200: entry #0 sah 401
   sementara entry #1 sehat, dan gerbang yang hanya membaca entry #0 menahan papan selamanya.
6. **Daftarkan sebagai cron no-agent — schedule POSISIONAL.** `--schedule`/`--prompt` tidak ada dan ditolak
   argparse (`unrecognized arguments`):
   `hermes cron create "15m" --name "<proyek> orkestrasi" --script <skrip>.py --no-agent --deliver origin --workdir <repo>`
   Skrip diletakkan di `~/.hermes/profiles/<profil>/scripts/`. stdout kosong = tidak ada kartu aktif → tidak ada
   pesan terkirim (tidak boros).
7. **Format laporan tick** (satu pesan, bukan narasi): baris `provider SEHAT/TERHAMBAT (<status>)`, hitungan
   `done · running · siap · tunggu-dep · blocked`, lalu satu baris per kartu `RUN/SIAP/TUNGGU-DEP/BLOCKED` dengan
   assignee + elapsed/budget + ⚠️ ≥80% / 🛑 >100%, ditutup baris `aksi:` berisi yang benar-benar dilakukan tick itu.
8. **Dua jam = dua cron dengan semantik berbeda.** Supervisor internal (2–5 menit, menangkap
   transisi macet sebelum anggaran hangus) dan laporan ke owner (15 menit, kontrak pelaporan)
   adalah DUA kontrol terpisah — jangan disatukan, dan jangan saling menggantikan. Kronologi:
   supervisor cepat menangkap kemacetan, laporan owner memenuhi kontrak pelaporan; salah satu
   tidak membuktikan yang lain.
   **Supervisor cepat hanya boleh berupa skrip `no_agent` tanpa LLM:** cron 2 menit versi agent
   = ratusan run per hari untuk pemeriksaan yang tidak mengubah apa pun, persis pemborosan
   request yang owner tolak. Aturan diam: skrip supervisor **tidak mencetak apa pun saat tidak
   ada anomaly** (stdout kosong = tidak ada pesan terkirim), jadi loop cepat hanya bicara saat
   ada reclaim, kegagalan beruntun, stall, kartu `blocked`/`triage` yang tak terjawab, atau dispatch fallback. Sebuah kartu yang mem-blokir dirinya sendiri menghentikan rantai serial sementara semua sinyal kesehatan terbaca NORMAL — `blocked` adalah kondisi alert, bukan keadaan idle.
   Hanya SATU sumber yang boleh dispatch: supervisor boleh reclaim + memancing dispatch,
   sedangkan skrip laporan owner TIDAK boleh pernah mengubah status atau dispatch.
9. **CLI cron: id job diambil dari `list`, dan create itu IDEMPOTEN — cek dulu, jangan ulang
   pada output yang tak terbaca.** `hermes cron create` tidak punya `--json` — argparse
   menolaknya, CLI mencetak usage dan keluar 0, sehingga job TETAP dibuat tetapi stdout-nya
   bukan JSON dan parsing gagal. Karena itu: **sebuah create yang output-nya terpotong/tak
   terbaca sudah BERHASIL membuat job** — sebelum mengulang perintahnya, jalankan `list` dulu;
   mengulang pada keadaan ragu menghasilkan DUA job dengan nama sama, dan dua supervisor
   kemudian reclaim/dispatch bersamaan (kerja ganda, satu-worker-aktif runtuh). Pola yang
   bekerja:
   ```bash
   hermes cron list --name <nama>            # ADA? kalau ya, jangan create — pakai id itu
   hermes cron create "2m" --name "<nama>" --script <file.py> --no-agent --deliver origin --workdir <repo>
   hermes cron list                          # hitung: tepat SATU job nama itu + schedule/enabled/deliver + JOB ID
   hermes cron run <job-id>                  # test-fire (hanya bila eksekusi dini harmless)
   hermes cron runs <job-id> --limit 5       # isi keluaran + tujuan delivery
   ```
   `--script` (dan `--monitor-script`) menerima NAMA BARE yang diresolve ke
   `~/.hermes/profiles/<profil>/scripts/`; path absolut ditolak. Verifikasi setelah create:
   job muncul di `list` dengan schedule/enabled/deliver yang benar, lalu test-fire SEKALI dan
   periksa ISI keluaran — "succeeded" tanpa isi bukan bukti terkirim.

Template siap pakai: `scripts/orchestrator_monitor.py` di skill ini (probe → release ber-guard → stall reclaim →
dispatch max 1 → laporan). Baca dan sesuaikan konstanta di kepala berkas sebelum dipasang di papan baru.

## Orkestrasi otomatis penuh: SATU driver proses, cron tinggal melapor

Saat owner bilang "jalankan orkestrasinya otomatis tanpa perlu saya unblock", jawabannya bukan menaikkan
frekuensi cron laporan. Laporan 15 menit adalah kontrak pelaporan (read-only); pembukaan kartu butuh
latensi detik. Pisahkan dua peran itu secara tegas:

- **Driver = satu proses python di background** (`terminal(background=True, persist_on_release=True)`,
  loop `sleep 120`). Dialah SATU-SATUNYA yang boleh `unblock`/`specify`/`dispatch`. Cron laporan tetap
  `--no-agent` dan tidak pernah mengubah status. Dua dispatcher = klaim ganda.
- **Template: `scripts/card_chain_driver.py`** — daftar kartu berurutan + assignee, siklus per kartu:
  unblock (bila `blocked`) → komentar konteks (bukti kartu sebelumnya + kontrak) → `specify` bila `triage`
  → `dispatch --max 1` → tunggu sampai `done`. Sunting konstanta di kepala berkas, jangan tulis loop ad-hoc.
- **Log harus satu baris per aksi dengan rc**: `UNBLOCK R1 rc=0`, `DISPATCH rc=0 → Spawned: 1 · <id> →
  <profil>`. Itu bukti orkestrasi berjalan; PID hidup saja tidak membuktikan apa pun.
- **Kartu tanpa `--parent` adalah `blocked` by design dan TIDAK akan pernah lepas sendiri.** Dispatcher hanya
  melepas anak ber-`block_kind=dependency`. Jadi driver wajib memegang daftar ID terurut sendiri; menunggu
  promosi otomatis = papan diam selamanya sementara semua sinyal kesehatan terbaca normal.
- **Stall: bunuh hanya kalau DUA syarat terpenuhi** — pesan terakhir worker di `state.db` lebih tua dari
  `IDLE_PANIC` (18 mnt) **dan** umur run ≥ `MIN_RUN_FOR_PANIC` (20 mnt). Syarat kedua mencegah membunuh run
  yang baru mulai orientasi. Batasi redispatch per kartu (3×), lalu driver keluar dan minta manusia — loop
  tanpa batas atas kartu yang sama membakar kuota tanpa hasil.
- **Self-stop ditulis di kode, bukan dijanjikan di chat:** keluar saat semua kartu terminal, atau saat
  butuh keputusan. **Semua kartu terminal ≠ proyek selesai:** sebelum mencetak "selesai", driver membaca verdict
  gate terakhir (berkas bukti ATAU komentar penutup kartu gate). Verdict REVISE/BLOCKED harus memicu rantai
  FIX/RE-AUDIT di kode atau keluar dengan status "butuh keputusan", bukan `exit 0` dengan pesan "semua kartu
  done" — driver yang hanya melihat kolom status akan mengumumkan rilis palsu. Simpan state ke JSON (`scripts/<proyek>_orch_state.json`) supaya driver yang mati bisa
  dilanjutkan tanpa mengulang kartu yang sudah `done`.
- **Patch pada driver yang sedang hidup TIDAK berlaku sampai prosesnya diganti.** Mengedit berkas skrip
  hanya mengubah cakram: proses lama masih memegang bytecode lama. Setelah patch: `kill <pid>` → jalankan
  ulang `terminal(background=True, persist_on_release=True)` → baca 2–3 baris log baru sebagai bukti versi
  terbaru yang benar-benar berjalan. Melaporkan aturan baru tanpa restart = aturan itu tidak pernah aktif.
- **Kartu `blocked` berulang SETELAH di-dispatch = sinyal REVISI, bukan sinyal unblock.** batasi buka-ulang
  per kartu (2 percobaan, dihitung di state JSON); pada percobaan berikutnya tanpa perubahan kondisi driver
  berhenti dan menyerahkan ke koordinator, yang menjalankan rantai revisi yang sama seperti manual:
  `scripts/rework_chain.py --board <b> --key <R> --parent <id> --findings <berkas> --downstream <id>`
  (FIX untuk produsen kartu induk → RE-AUDIT `code-analyst` dibuat `blocked` → `link` re-audit ke kartu
  hilir → `dispatch --max 1`). Unblock berulang pada kartu yang gagal dengan sebab sama hanya membakar
  kuota dan menyembunyikan bahwa yang dibutuhkan adalah kartu FIX.
- **Sebelum dispatch kartu "bangun X", inventariskan dulu X di repo.** Deliverable sering SUDAH ada dan
  ter-commit dari run sebelumnya (wireframe/desain, skrip ukur, dokumen): `git status` bersih + berkas ada =
  worker akan membakar budget untuk menduplikasi. Kirim komentar sebelum worker menulis: baca artefak yang
  ada, nilai tiap butir spek LULUS/GAGAL pada berkas itu dengan denominator, perbaiki HANYA yang GAGAL,
  jangan bangun ulang, kutip angka skrip ukur yang sudah tersedia. Ini kebalikan dari "jangan percaya sudah
  dibangun": keduanya menuntut Anda melihat isi direktori deliverable sendiri, bukan membaca status kartu.
- **Verba CLI-nya `create`, bukan `add`** (`hermes kanban add` ditolak: "not a `hermes kanban` command").
  Formulir kartu dari skrip: `create "<judul>" --assignee <profil> --parent <id> --body-file <path>
  --max-runtime 21600 --completion-contract local-only --initial-status blocked --json`; id diambil dari
  baris JSON terakhir stdout, dan assignee FIX lebih andal dibaca dari baris kartu induk di `tasks`
  daripada di-hardcode.
- **Angka budget/deadline dibaca dari BODY kartu** (`Budget: N menit`), bukan dari bobot yang Anda karang.
  Deadline = waktu kartu pertama mulai + Σ budget kartu, dan basis hitungan itu harus dicetak di laporan.
  Mengarang bobot relatif lalu menyebutnya "target" menghasilkan angka yang tidak bisa direkonsiliasi owner.
- **Tracker PRD (bila ada) disinkronkan dari driver, bukan manual.** `GET /prd-agent/context` memberi
  `checkpoints[].node_id` + `checkpointVersion`; `POST /prd-agent/checkpoint` menaikkan versi tiap panggilan,
  jadi kirim `checkpointVersion` terbaru dari respons sebelumnya (rantai, bukan angka tetap) dan cek `ok:true`
  per node. Judul node yang bertentangan dengan keputusan owner terbaru (mis. "upload 8 MB" padahal owner
  memutuskan 25 M) TIDAK ditulis ulang sendiri — ikuti keputusan owner dan sebutkan selisihnya sekali di laporan.

## Driver sekuensial berbasis cron 5 menit (sprint ≤1 hari)

Aturan "kartu harus berurutan, hanya SATU yang boleh terbuka" butuh dua lapis penegak: **struktur**
(rantai parent S0→S1→S2) dan **waktu** (sesuatu yang membuka kartu berikutnya saat pendahulu `done`).
Untuk sprint yang selesai dalam sehari, cron `--no-agent` 5 menit lebih murah dan lebih tahan daripada
proses background panjang: tidak ada PID yang mati di tengah malam dan tidak perlu restart setelah patch.
Template teruji: `scripts/serial_card_driver.py` (sunting konstanta `ORDER` di kepala berkas).

- **Guard single-flight di atas segalanya: kalau ADA kartu `running`/`queued` di daftar, keluar tanpa
  menyentuh apa pun.** Guard per-assignee saja tidak cukup — dua kartu dengan assignee berbeda tetap
  terlepas pada siklus yang sama dan aturan satu-worker-aktif runtuh diam-diam.
- **Maksimal satu pembukaan per pass**, lalu `return`. Loop yang membuka semua kartu "yang sudah siap"
  dalam satu tick mengubah rantai serial menjadi fan-out.
- **Driver tidak boleh mematikan worker.** Diam >15 menit hanya menghasilkan satu baris peringatan untuk
  koordinator; pembunuhan berbasis ambang diam tanpa syarat umur run sudah terbukti membunuh auditor sah
  yang baru berjalan beberapa puluh detik. Yang memutuskan kill tetap manusia/koordinator.
- **`consecutive_failures >= 2` → jangan dibuka otomatis**, cetak satu baris "butuh keputusan" dan berhenti.
  Membuka ulang kartu yang gagal dengan sebab sama hanya membakar kuota.
- **Diam total saat tidak ada aksi (stdout kosong)** supaya cron tidak mengirim pesan kosong tiap 5 menit;
  pass normal harus nol output. Uji dengan menjalankannya sekali saat ada kartu `running` — keluaran kosong
  adalah hasil yang benar, bukan bukti skripnya mati (buktikan dengan satu pass buatan saat tidak ada run).
- **Urutan ditulis sebagai konstanta `ORDER = [(key, task_id), …]`**, bukan dibaca dari judul kartu; rename
  judul akan menghentikan release diam-diam. Verifikasi relasi parent juga tetap dilakukan di `task_links` —
  driver mempercepat, bukan menggantikan dependency gate.
- **Gate REVISE menambah kartu di luar `ORDER`: tanpa memperbarui konstanta itu, rantai mati tanpa error.**
  Setelah membuat kartu FIX dan RE-AUDIT, tambahkan keduanya ke daftar `ORDER` driver DAN ke daftar bobot skrip
  laporan dalam satu langkah, sebelum `dispatch`. Tanda rantai mati: semua kartu lama `done`, kartu FIX `ready`,
  dan driver tetap diam tiap 5 menit karena ia hanya tahu empat kunci lama. Cron sudah terpasang bukan berarti
  daftarnya sudah benar — grep file skrip untuk id kartu baru sebagai bukti.
- **Komentar kartu lewat CLI: teksnya argumen POSISIONAL** (`hermes kanban --board <b> comment <id> "<teks>"`).
  `--body-file` tidak ada di subcommand ini; pemanggilan yang salah tetap keluar 0 dengan keluaran sependek satu
  baris, jadi verifikasi di `select body from task_comments where task_id='<id>' order by id desc limit 1`,
  bukan dari kode keluar.
- **Lokasi skrip & pemasangan:** berkas di `~/.hermes/profiles/<profil>/scripts/`,
  `hermes cron create "5m" --name "<proyek> DRIVER" --script <nama-bare>.py --no-agent --deliver origin`.
  `--script` menerima nama bare, bukan path absolut. Setelah create, **cek `hermes cron list --name`** — create
  idempoten dan create yang outputnya tak terbaca sering sudah berhasil.

## Menu skill & tool per kartu (jawaban untuk "siapa pakai skill apa")

Saat owner menyerahkan pengaturan proyek ("atur alurnya, skill dan tools apa saja"), yang ia minta adalah
kontrak kerja tertulis, bukan narasi chat.

- **Tulis menu ke komentar/body kartu:** maksimal 3 skill per kartu + satu baris alasan tiap skill, plus
  larangan eksplisit `skills_list` dan `skill_view` untuk skill yang sama lebih dari sekali. Brief yang
  hanya bilang "pakai skill yang relevan" tidak menyembuhkan loop baca; yang menyembuhkan adalah batas angka.
- **Tool wajib, sebut namanya:** `graphify_query` sebelum grep untuk pertanyaan struktur (satu panggilan
  offline vs 3–8 request API), `graphify_update` sesudah kode berubah, `work_state_write` (claude-mem)
  sebagai checklist lintas compaction, `save_memory` maksimal 3 keputusan per kartu, screenshot lokal untuk
  bukti visual. Skill terpasang ≠ skill dipakai — buktinya call-record di `state.db` (lihat "Wajibkan skill
  dengan ANGKA").
- **Assignee dipilih dari riwayat call tulis, bukan dari nama peran.** Profil yang di sprint sebelumnya
  menghabiskan puluhan menit membaca tanpa satu tulisan tidak diberi kartu desain hanya karena namanya
  cocok; alihkan ke profil yang `state.db`-nya menunjukkan call tulis tinggi.
- **Simpan kontrak itu di repo** (`docs/coordination/WO-*.md`) dan commit, lalu sebut commit-nya di laporan:
  pembagian peran, urutan kartu, budget per kartu, skill/tool per kartu, larangan, dan definisi bukti. Chat
  koordinator tidak terbaca worker berikutnya; berkas + komentar kartu yang bertahan.

## Register keputusan (DEC) untuk proyek bergerbang

Setiap keputusan punya STATUS eksplisit + daftar node yang diblokirnya: `FINAL` (disetujui pemilik),
`USULAN` (default spek, tinggal disetujui), `BUTUH-OWNER` (butuh fakta/kredensial milik pemilik),
`DITUNDA` (diputuskan belakangan, dengan konsekuensi graf ditulis).

- **Jangan mengarang fakta milik pemilik** (kontak resmi, akun payment gateway, kredensial email).
Tandai `BUTUH-OWNER`, blokir node terkait, tanyakan sekali dalam satu form, dan bila jawabannya kosong
catat "belum terjawab" + tanyakan lagi saat node itu masuk gelombangnya — jangan mengulang pertanyaan
tiap turn.
- **Keputusan ditunda harus menyebut efek graf + jalur alternatif**, bukan hanya "nanti". Contoh pola:
pembayaran ditunda → node pembayaran tetap blocked, tetapi node event tetap jalan dengan
`price_type=gratis`; akibatnya rilis tidak ikut tertahan oleh satu integrasi yang belum siap.
- **Verifikasi pemetaan DEC → node dari manifest** (bukan dari ingatan): hitung ulang node yang
`requiresDecisions`-nya berisi DEC itu, dan pastikan tidak ada DEC yatim.
- Keputusan ditunda yang membuat alur bergantung padanya (mis. verifikasi email) harus dicatat sebagai
**risiko**: sebut jalur pengganti yang tetap berfungsi sampai provider tersedia.

## Peran & cara memberi instruksi

- **Developer (program-developer):** implementasi; instruksikan ukur-sebelum-klaim, komentar per unit, block untuk kebijakan, jangan keluar spek.
- **Analyst (code-analyst):** reasoning `ultra`; review lens (Execution/Artifact); tuntut temuan bernomor `F1..` + bukti terukur; dia yang menyusun spek FIX.
- **Planner:** roadmap/spec di awal, sebelum produksi.