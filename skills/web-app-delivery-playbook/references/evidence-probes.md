# Probe pengukuran bukti (web app)

Resep siap tempel untuk kartu FIX dan kartu gate. Semua dijalankan lewat Playwright/
CDP terhadap **salinan lokal** (`php -S 127.0.0.1:PORT -t public`) setelah login nyata;
jangan mengukur dari curl domain ber-WAF.

## 1. Matriks luapan (rute × lebar)

```js
// WAJIB scrollTo + 2 rAF dulu: snapshot tanpa scroll melaporkan 0 palsu.
window.scrollTo(9999, 0);
await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
const de = document.documentElement, b = document.body;
const delta = Math.max(de.scrollWidth, b.scrollWidth) - de.clientWidth;
const widest = [...document.querySelectorAll('*')]
  .map(el => ({ el, w: el.getBoundingClientRect().width, r: el.getBoundingClientRect().right }))
  .sort((a, b) => b.w - a.w)[0];
({ delta, scrollX: window.scrollX,
  widest: widest && { tag: widest.el.tagName, cls: widest.el.className, w: widest.w } });
```

Simpan per sel: `rute, lebar, delta, scrollX, widest`. Lulus = `delta === 0` DAN
`scrollX === 0` di semua sel. Selisih 4–12 px tetap kegagalan, bukan “noise”.

## 2. Target sentuh 44 px

```js
const sel = 'a[href], button, input:not([type=hidden]), select, textarea, summary, [role=button]';
const rows = [...document.querySelectorAll(sel)].map(el => {
  const r = el.getBoundingClientRect();
  if (!r.width || !r.height) return null;
  const inline = getComputedStyle(el).display === 'inline' &&
                 !['block', 'inline-flex', 'inline-block'].includes(getComputedStyle(el).display);
  return { tag: el.tagName, txt: (el.textContent || '').trim().slice(0, 24),
           w: +r.width.toFixed(1), h: +r.height.toFixed(1), inline,
           cls: el.className, parentRowH: +(el.closest('tr')?.getBoundingClientRect().height || 0).toFixed(1) };
}).filter(Boolean);
const kurang44 = rows.filter(x => x.h < 44);
({ total: rows.length, kurang44: kurang44.length,
  kurang44_tanpa_inline: kurang44.filter(x => !x.inline).length,
  contoh: kurang44.slice(0, 10) });
```

Laporkan **dua** angka (`kurang44` dan `kurang44_tanpa_inline`). Tautan 20 px di baris
tabel 64 px lolos pengecualian WCAG inline, tetapi kalau owner minta 44 px mutlak,
pengecualian tidak dipakai dan angkanya harus 0.

## 3. Kontras (alpha-compositing)

Warna teks/latar sering `rgba(...)`. Ratakan dulu ke latar efektif (naik pohon DOM
sampai dapat latar opaque), baru hitung rasio. Laporkan `min`, `median`, `n`, dan
`gagal` (<4,5:1 untuk teks normal, <3:1 untuk teks ≥24 px / bold). Simpan per rute,
jangan hanya satu angka global.

## 4. Host asing

```js
// aktifkan sebelum navigasi
const cdp = await page.context().newCDPSession(page);
await cdp.send('Network.enable');
const hosts = new Set();
cdp.on('Network.requestWillBeSent', e => hosts.add(new URL(e.request.url).host));
// ... navigasi + interaksi ...
[...hosts].filter(h => h && h !== new URL(base).host);
```

Lulus = array kosong. Ini bukti keras “tanpa aset eksternal”, bukan klaim.

## 5. Matriks rute × identitas

Loop rute dengan dua sesi login (admin, petugas) + kasus negatif (role kosong, tamu)
dan ID yang tidak ada / terarsip. Catat `status`, `bytes`, `location` untuk redirect.
Lulus = `0 × 500` dan tamu benar-benar 302 ke `/masuk` — bukan 200.

## 6. Bentuk bukti sebelum vs sesudah (kartu FIX)

Satu berkas JSON yang bisa di-diff gate berikutnya:

```json
{ "kartu": "<id>", "basis": "<branch> @ <commit>",
  "ringkasan": { "kurang44_sebelum": 30, "kurang44_sesudah": 0,
                 "kurang44_tanpa_inline_sebelum": 311, "kurang44_tanpa_inline_sesudah": 0,
                 "layar_lebar_lulus": 30, "layar_lebar_total": 30,
                 "gagal_target": [], "gagal_luapan": [], "gagal_kontras": [] } }
```

Sertakan juga `baris_1440` per layar (`min/med/max`, `max_sebelum`, `lewat_76`). Baris
yang memang multi-baris (mis. catatan tindak lanjut 96–155 px) ditandai wajar, bukan
kegagalan baru.

## 7. Cek harness sebelum percaya angka 0

Kalau hasil “0 px / 0 pelanggaran” tidak bisa direproduksi dengan probe kedua,
tulis dua temuan: cacat UI-nya DAN cacat harness-nya. Simpan skrip probe ke
`docs/evidence/<sprint>/tools/` supaya gate bisa menjalankan skrip yang sama,
bukan menilai prosa.
