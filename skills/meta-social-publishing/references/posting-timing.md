# Riset Slot Posting — Decision Recipe

Kapan menggunakannya: sebelum mematikan kalender posting/penjualan apa pun
(platform mana pun, bahasa pasar mana pun). Aturan umum di SKILL.md: slot
dulu, kalender belakangan; setiap slot di kalender wajib membawa
alasannya.

## Langkah 1 — Kumpulkan dua lapis data (jangan campur)

1. **Data platform** (engagement per hari/jam): cari studi terbaru per
   platform — cari angka BESAR (jumlah post dianalisis), bukan blog opini.
   Contoh nyata: analisis Buffer atas 2,5 juta post Threads (2026):
   peak global Kamis 09:00 UTC±; hari kerja unggul telak;
   Sabtu/Minggu −23% s/d −38% vs hari kerja; malam 18:00–23:00 justru
   engagement terburuk di Threads.
2. **Data pasar lokal** (jam beli/jam baca audiens target): studi zona waktu
   + perilaku belanja pasar jangkauan produk. Contoh Indonesia: belanja
   spontan puncak 11:00–13:00 & 17:00–19:00 WIB; niat beli malam
   (produk hobi/tech) 19:30–21:00.

Kedua lapis BISA BERTENTANGAN (mis. "malam = jam beli" dari data lokal vs
"malam = engagement terburuk" dari data platform). Jangan pilih salah satu
satu-satunya — konflik = hipotesis yang wajib A/B test, bukan fakta.

## Langkah 2 — Mapping ke jenis konten

| Jenis konten | Slot dipilih dari | Alasan |
|---|---|---|
| Hard-sell + link checkout | peak engagement platform (hari kerja pagi/ siang) | butuh eyeball maksimum |
| Edukasi / soft-sell | jendela baca lokal (istirahat siang) | engagement sedang cukup, intent belajar tinggi |
| Eksperimen konversi malam | jendela beli lokal — TANDAI "eksperimen A/B", jangan patokan | sinyal platform menentang; butuh bukti klik/penjualan |

## Langkah 3 — Eksekusi + buktikan

1. Slot uji pertama = hari/hour terkuat dari langkah 1 platform.
2. Jadwalkan lewat cron one-shot (lihat SKILL.md §7), publish script
   menyimpan permalink ke log.
3. **Metrik penilaian per slot:** engagement (basis pembanding) DAN klik
   link/penjualan (basis keputusan). Engagement tinggi ≠ jual.
4. Satu siklus evaluasi terjadwal (mis. 7 hari, semua slot kebaca) →
   putuskan: pertahankan / geser / buang. Catat keputusan di akhir kalender.

## Aturan ringkas (selalu terapkan)

- Weekend untuk akun baru/tes baseline boleh, tapi JANGAN dijadikan
  andalan hard-sell (data engagement konsisten lebih rendah).
- Jam sangat pagi (05:00–07:00) hanya layak untuk pasar yang terbukti
  early-bird; default lewati.
- Setiap rekomendasi jam disebut beserta ZONA WAKTU + SUMBER (angka
  analisisnya), biar owner bisa audit.
- Kalender boleh menyisipkan eksperimen A/B — tapi tandai secara eksplisit
  sebagai eksperimen, jangan tertukar dengan slot terverifikasi.
