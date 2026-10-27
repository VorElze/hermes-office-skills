---
name: graphic-design-lane
description: "Use when handling a graphic design task as Reno: asset program, UI mockup, desain visual, atau generate gambar. Prosedur kerja + format deliverable."
version: 1.0.0
author: Reno
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [design, assets, mockup, imagegen]
---

# Lane kerja graphic designer (Reno)

## When to Use

Setiap tugas desain yang masuk (Kanban assignee `graphic-designer` atau chat langsung). Trikger kelas: icon/logo/favicon/illustration asset, mockup UI/poster/pamflet/sosmed, atau generate/edit gambar.

## Procedure

1. **Pilih tool sesuai deliverable** (skill terkait sudah terpasang — baca SKILL.md-nya dulu):
   - Gambar raster AI (text-to-image / edit) → skill `imagegen` (butuh `OPENAI_API_KEY`; kalau kosong → laporkan blocker, jangan menekan).
   - Ilustrasi vektor/asset program (icon, logo, ilustrasi UI) → `create-svg-illustrations`, `favicon-gen`, `ip-as-logo`.
   - Mockup/prototipe visual cepat → `quick-mockups`, `sketch`.
   - Poster cetak 1–2 warna → `mono-color`.
2. **Ubah referensi menjadi spesifikasi sebelum menggambar**: catat palet, susunan, bentuk, dan kegunaan. Jika pengguna meminta aset dipotong dari gambar yang dilampirkan, utamakan crop raster langsung dari gambar sumber—jangan menggambar ulang, menebak bentuk, atau mengganti desain; pisahkan tiap elemen relevan menjadi file sendiri. Laporkan koordinat crop/dimensi dan bahwa crop mempertahankan latar, teks, atau kisi yang masuk area. Jangan klaim itu logo vektor, transparan, atau siap-cetak. Jika pengguna meminta rekonstruksi presisi alih-alih crop dan detail tidak terbaca, minta sumber resolusi lebih tinggi/vektor.
3. **Kerjakan di workspace**: simpan artefak di direktori tugas/kerja (`$BH_AGENT_WORKSPACE` saat lewat browser; jika tidak ada, buat `~/projects/design-<slug>/`). Untuk crop langsung, gunakan Pillow: `Image.open(source).crop((x1,y1,x2,y2)).save(output_png)`; koordinat berasal dari piksel kiri-atas sumber. Tentukan kotak crop dari batas elemen visual, hindari memotong bagian logo/objek, dan buat tiap crop sebagai file tersendiri dengan nama deskriptif. Sebelum membuat versi transparan atau vektor dari screenshot, minta persetujuan/asset master karena tracing tidak menjamin identik.
4. **Validasi sebelum mengemas**: cek struktur SVG/XML, dimensi/viewBox, teks, warna, dan render visual di browser atau renderer yang tersedia; pastikan render/konversi benar-benar sukses sebelum menghitung atau menjanjikan PNG, mockup raster, maupun ZIP. Jika renderer tidak tersedia, jangan mengklaim keluaran raster atau arsip yang belum dibuat; serahkan hanya berkas sumber yang berhasil dibuat dan jelaskan batas verifikasi. Bila keluaran hanya vektor, laporkan ukuran kanvas/viewBox, bukan mengada-ada ukuran raster.
5. **Multi-file → ZIP** satu folder. Untuk satu file, penuhi kanal/tujuan yang diminta secara langsung: jika diminta Google Drive, unggah berkas spesifik tersebut memakai autentikasi Google Workspace yang terkonfirmasi, verifikasi hasil upload (ID, nama, link; pastikan akses link memadai), lalu kirim link di chat. Jangan menganggap Drive harus sudah berupa connector jika skill Google Workspace menyediakan CLI/API; cek profil/token resmi yang memang digunakan untuk akun itu dan jangan pernah menampilkan rahasia. Jika diminta Telegram, kirim sebagai lampiran Telegram lewat adapter/platform yang aktif, bukan berhenti di path lokal atau memberi instruksi agar pengguna melampirkannya sendiri. Pastikan file ada dan transfer sukses sebelum mengklaim selesai; jika kanal/tujuan tidak dapat dicapai, nyatakan blocker dengan spesifik dan minta keputusan hanya bila memang dibutuhkan.
6. **Laporan**: jumlah file, format, dimensi/viewBox, ukuran byte, path/attachment; bedakan aset yang dibuat dari yang belum dirender atau diverifikasi. Nyatakan sebagai konsep awal dan minta tinjauan bila diperlukan sebelum produksi massal.
7. **Skill baru**: kalau muncul prosedur desain yang bisa dipakai ulang, simpan ke skills milik Reno — jangan ke memori.

## Workflow UI/UX untuk produk yang sudah berjalan

- Sebelum mengubah repo, baca instruksi proyek, node/gate aktif, dependensi, dan cakupan file (`touchPaths` atau padanannya); catat status Git terlebih dahulu agar perubahan sebelumnya tidak tertimpa.
- Cocokkan setiap path yang diizinkan dengan file implementasi aktual. Jika manifest salah, ubah hanya dengan otorisasi eksplisit, lalu periksa lagi gate independen yang masih terbuka. Izin memperbaiki path bukan izin melewati gate lain atau mengubah file di luar cakupan.
- Saat owner sudah memberi keputusan eksplisit yang menyelesaikan blocker tertentu, laksanakan tepat keputusan itu tanpa meminta instruksi diulang; pertahankan blocker/gate lain yang belum selesai.
- Untuk audit produk menyeluruh, ikuti prosedur screenshot dan kritik route di `design-taste-frontend`; catat cakupan per route dan peran, dan jangan menyimpulkan panel terlindungi dari halaman publik atau CSS saja.

## Handoff

- Blokir bila: key imagegen kosong / tool tidak ada / brief tidak punya ukuran format. Laporkan blocker + apa yang sudah bisa dikerjakan.
- Deliverable visual untuk develop program → serahkan dalam format siap-ekspor ke repo dev (SVG/ PNG @2x / WebP), bukan hanya screenshot.

## Pitfalls

- **Aturan anti-"keluar garis" line-art (lesson coloring-book):** (1) pola/detail dalam bidang WAJIB `<clipPath>`; (2) wajah harus muat penuh di satu bidang utama — badan kecil → besarkan badan, jangan perkecil wajah; (3) motif menabrak zona wajah → tutup dgn elips/rect putih stroke-none atau potong garis motif (sample+split segmen), jangan kotak putih bersegi tajam (terbaca cacat); (4) mata kawaii = outline putih + pupil solid + catchlight `style="fill:#fff;stroke:none"`, bukan lingkaran datar; (5) buah bersisi biji/facet → biji hanya di pita atas, wajah di bawah kartu putih; (6) zoom QA per-batch setiap patch besar.
- `hermes skills install` bisa exit 0 sambil gagal (GitHub API limit) — selalu verifikasi dengan `hermes -p graphic-designer skills list` sebelum bilang terpasang.
- Skill imagegen milik OpenAI membaca `OPENAI_API_KEY` dari env; tanpa key, skill terpasang tapi tidak bisa menghasilkan gambar.
- **Jalur "AI look" gratis tanpa key (terbukti, coloring book): imagegen gratis TIDAK ada di katalog tool dan semua env key kosong → pakai pipeline: (1) render line-art vektor sendiri (SVG→PNG 512) sebagai source image, (2) submit img2img ke Stable Horde API (`POST /api/v2/generate/async`, anonymous demo credential from upstream; verify current API requirements and use official account credentials where required, `source_processing: img2img`, `source_image: base64`, `denoising_strength: 0.42`, model `Flat-2D Animerge`, sampler `k_euler`), (3) poll `/generate/check|status/{jid}`. Bentuk terjaga 100% + garis dirender halus ala ChatGPT. Poll JANGAN di foreground execute_code (limit 300s) — jalankan background `terminal(background=true)`.
- GAGAL jangan diulang: Pollinations free = model `sana` (selalu bergradasi, binarisasi/Sobel rusak); Horde text2img `Comic-Diffusion` (line art murni tapi subjek tidak terkontrol → jadi rubah/mandala); alpha-PNG embed tidak dirender cairosvg (halaman jadi kosong) → embed RGB putih + latar cover `#ffffff` agar kotak menyatu.
- **Eksperimen "AI look" (2026-10-13) DITOLAK user — jangan diulang tanpa izin baru:** pipeline img2img Stable Horde (Flat-2D Animerge, denoise 0.42, source = line-art vektor) + assembler `assemble_ai_book.py` (output_ai/) menghasilkan 31 hal A4 tapi user nilai "sangat berantakan" → versi vektor murni (SVG v5, `fruits.py`+`generate_book.py`) yang diminta kembali. Pollinations free (`sana`), Horde text2img `Comic-Diffusion`, binarisasi/Sobel juga sudah terbukti gagal. Kesimpulan: tanpa key imagegen premium, kualitas AI tidak menyamai vektor ter-QA — vektor adalah default yang aman.
- Jangan install skill ke profil lain secara tidak sengaja — selalu awali dengan `hermes -p graphic-designer`.
