---
name: screen-recording-qa
description: Use when the owner supplies a screen recording of a bug.
version: 1.0.0
author: amanda
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [qa, video, evidence, vision, ffmpeg, drive]
    related_skills: [team-dispatch, google-workspace]
---

# Screen-recording QA

## When to Use

Owner mengirim rekaman layar (tautan Drive atau file lokal) alih-alih
mereproduksi masalah langsung → review rekaman dulu sebagai bukti, baru
usulkan perbaikan. Hasil review yang berbukti jadi bahan kartu tugas /
rencana kerja.

## Procedure

1. **Ambil filenya.** Tautan Drive → `drive download FILE_ID --output <path>`
   sesuai setup local google-workspace (HERMES_HOME=profiles/<profile> +
   interpreter venv instal yang punya `googleapiclient` — resolve path venv
   saat runtime, id-nya berubah tiap `pm sync`). File lokal → langsung pakai.
2. **Probe sebelum ekstrak:**
   `ffprobe -v error -show_entries format=duration -show_entries stream=width,height -of default=noprint_wrappers=1 <file>`
   — durasi menentukan sampling, resolusi menentukan scaling.
3. **Sampling ~1 frame per 4 detik:**
   `ffmpeg -y -i in.mp4 -vf "fps=1/4,scale=1280:-1" -q:v 3 out/f%02d.jpg`
   Rekaman 1 menit → ±13 frame, cukup tanpa membakar satu call per detik.
4. **Analisis frame dalam batch 3** lewat `vision_analyze`, satu pertanyaan
   konkret per frame: layout, konsistensi warna, area terpotong/overflow di
   tepi layar, area kosong, artefak mode responsif. Jangan loop satu call
   per frame. Pastikan frame benar-benar ter-attach dan diperiksa sebelum
   menyebut isinya; balasan tool yang hanya mengonfirmasi pemuatan (= "image
   loaded") BUKAN bukti visual — kalau hasilnya demikian, ulangi batch itu.
5. **Setiap temuan wajib berlabel frame + fakta terukur** (indeks frame =
   jendela waktunya: f01 = 0–4 dtk, f02 = 4–8 dtk, ...; sebut breakpoint
   mana, elemen mana yang wrap/potong, di mana gradient terpotong). Bedakan
   jelas: fakta yang terlihat langsung di frame tsb, interpretasi, dan hal
   yang BELUM diperiksa (frame lain / halaman lain) — jangan menyimpulkan
   isi frame yang tidak di-ekstrak, dan jangan mengklaim "tidak ada masalah X"
   untuk frame yang tidak dianalisis. Owner mencocokkan temuan dengan apa
   yang ia lihat saat merekam — deskripsi kabur terbaca sebagai tebakan.
   Untuk video performa, ambil beberapa frame overlay yang berjauhan dan baca
   seluruh workload (`agents`, `moving`, resolusi/zoom, error), bukan hanya
   FPS. Satu angka FPS sesaat atau workload yang tidak cocok dengan syarat
   benchmark bukan hasil acceptance; laporkan sebagai observasi pengguna dan
   nyatakan jelas syarat yang belum terpenuhi.
6. **Klasifikasi temuan sebelum lapor:** petakan tiap temuan ke penyebab
   yang bisa diperbaiki (CSS overflow, breakpoint hilang, gaya komponen
   default) supaya output langsung jadi rencana perbaikan, bukan deskripsi
   piksel.
7. **Reproduksi & ukur sebelum menugaskan fix** (bila aplikasinya bisa
   dijalankan lokal): render halaman terdampak di viewport identik rekaman
   (Playwright: `p.goto(...)` + `getBoundingClientRect()` + `scrollHeight`)
   dan sampling piksel kolom bermasalah (PIL) sebagai bukti kuantitatif
   kedua dari vision. Angka baseline ini (mis. "gap panel→footer = 64px,
   scrollHeight − innerHeight = 145px") wajib masuk ke spec kartu sebagai
   KONDISI SEBELUM + kriteria penerimaan berangka — tanpa ini, reviewer
   hanya bisa menilai "kelihatan benar". **Tutup laporan akhir dengan satu
   PNG perbandingan**: frame rekaman (SEBELUM) berdampingan dengan render
   ulang Playwright halaman terkini (SESUDAH), kirim via `MEDIA:` — render
   ulang sendiri, sebab workspace kartu dibersihkan dispatcher begitu kartu
   `done`, jadi bukti worker lama tak tersedia saat laporan final.
8. **Frame & rekaman = bukti sementara, bukan deliverable** — simpan di
   scratch, biarkan hygiene pass berikutnya menghapusnya; jangan masukkan
   ke arsip ZIP yang dikirim ke owner.

## Pitfalls

- **Vision perlahan bila di-loop per frame** — batch 3 pertanyaan per call;
  satu rekaman 1 menit cukup dengan 13 frame, tidak perlu 60.
- **Indeks frame tanpa jendela waktu = temuan tak bisa ditelusuri** —
  owner butuh "frame f07 ≈ 24–28 dtk" untuk mencocokkan dengan yang ia
  rekam.
- **Scaling frame ke 1280 px** agar `vision_analyze` tidak membuang detail
  kecil (teks navigasi, label kolom) saat downscale internal.
- Jangan laporkan "terverifikasi" untuk temuan yang hanya muncul di SATU
  frame — konfirmasi dengan frame tetangga sebelum menandai sebagai bug
  nyata (bisa sekadar transisi animasi).
- **Overlay teks kecil di video wajib di-crop + upscale sebelum dibaca** —
  crop region overlay dengan `ffmpeg -vf "crop=W:H:X:Y,scale=2W:2H:flags=lanczos"`
  per frame, baru kirim ke vision; membaca overlay dari frame utuh penuh
  layar gagal/misread (downscale internal menelan teks kecil). OCR klasik
  (`tesseract`) tidak bisa membaca overlay tipis di atas canvas animasi —
  vision batch tetap jalurnya.
- **Angka dari video pemilik hanya sah sebagai acceptance jika workload-nya
  cocok kriteria** — fps berapa pun BUKAN lulus kalau jumlah agent/objek
  yang terbaca di overlay tidak memenuhi syarat (mis. "13 agent" saat
  overlay menunjukkan 1): laporkan sebagai bukti performa parsial + sebutkan
  syarat yang belum terpenuhi, jangan terima sebagai PASS tanpa konfirmasi
  owner yang eksplisit.
- **Video Telegram >20 MB tidak tersimpan di server** (file ditolak, path
  cache tidak ada) — minta user kirim tautan Google Drive; file publik Drive
  bisa diunduh langsung tanpa SDK: `curl -sL "https://drive.google.com/uc?export=download&id=FILE_ID"`
  (tanpa `confirm` token kalau <100 MB), verifikasi dengan `file` output
  (harus `ISO Media / MP4`), lalu rename dan proses dengan alur normal.
