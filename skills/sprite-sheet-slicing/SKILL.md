---
name: sprite-sheet-slicing
description: "Use when splitting a sprite sheet into individual assets."
version: 1.0.0
author: Reno
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [image, spritesheet, pixel-art, assets]
---

# Pemotongan sprite sheet → aset satuan

## When to Use
Owner kirim 1 gambar gabungan (hasil generate AI / screenshot) dan minta dipisah jadi aset individual + layout terpisah dalam satu folder siap-program.

## Procedure
1. **Pasang grid koordinat** di atas salinan gambar (PIL: garis tiap 10/25/50 px, label angka tiap 100 px) lalu `vision_analyze` crop itu untuk estimasi bounding box. Jangan menebak koordinat tanpa grid.
2. **Validasi programatik** dengan numpy: connected-component atas mask latar (`bg = gray>185 & sat<22` untuk checkerboard) → bbox komponen nyata. Baca hasil detektor, jangan hanya percaya vision.
3. **Hapus latar checkerboard** dengan flood-fill dari TEPI gambar (`scipy.ndimage.label` ambil komponen nyambung ke border) — JANGAN global color-key: objek abu-abu (~213) berwarna sama dengan kotak latar. Buang blob bg <40px (sisa di dalam objek).
4. **Room/layout crop utuh** (RGB tanpa mask): furnitur menempel di lantai, masking akan merusak. Room bbox ditemukan dari profil piksel 'dark wall' per kolom/baris.
5. **Simpan @2x NEAREST** (`Image.resize(..., Image.NEAREST)`) untuk retina; asli tetap 1x native.
6. **Verifikasi**: contact sheet di atas latar magenta → sisa checkerboard langsung kelihatan; cek tiap sprite punya alpha (`getextrema()[0] < 255`); cek border tak didominasi abu; minta vision baca contact sheet sekali untuk potongan terlewat.
7. **Deliverable**: folder + ZIP + `manifest.json` (nama, w/h, src_box) + `galeri.html` + `README.md`. Laporkan jumlah file, dimensi, byte ZIP.

## Pitfalls
- numpy/scipy belum tentu terpasang → `pip install numpy scipy` dulu (PIL selalu ada).
- F-string + CSS/HTML → sintaks error; tulis template via konstanta `.replace()` atau write_file terpisah.
- Sumber JPG → tepi bawa artefak kompresi; catat di README, jangan klaim "bersih sempurna".
- Bilangan peka (`@2x`) pecah kalau dikutip di dalam string Python; pakai file terpisah.
- Gamma warna: bbox via vision bisa meleset 5-10 px — selalu rapikan dengan detektor piksel.
