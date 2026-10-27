---
name: meta-threads-oauth-lifecycle
description: 'Use when configuring Meta Threads OAuth and token refresh.'
version: 1.0.0
author: amanda
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [meta, threads, oauth, api, credential-handoff, token]
---

# Meta / Threads API — OAuth Lifecycle & Secure Handoff

Kelas kerja: menghubungkan kantor ke API Meta (khususnya Threads) untuk
publishing otomatis. Skill ini khusus OAuth app + token API.

## When to Use

Use whenever a task involves the Threads Graph API/OAuth (connect account, fix
permission errors, refresh/rotate tokens, debug publish/delete failures).

## Urutan kerja yang terbukti (Threads API)

1. Buat app dengan use case Threads API.
2. **Permissions & features**: klik **Add** pada `threads_content_publish` dan
   `threads_delete` (kalau butuh rollback) sampai status **Ready for testing**.
   Status dashboard ≠ izin di token.
3. Settings → Basic → isi dan simpan Redirect Callback URL sebelum OAuth flow.
4. App Secret (Settings → Basic → Show) diserahkan ke server via endpoint
   gated, TIDAK PERNAH lewat chat.
5. OAuth authorize → Approve → server tukar `code` ke short-lived, lalu
   `th_exchange_token` untuk long-lived 60 hari.
6. Refresh otomatis: `GET /refresh_access_token?grant_type=th_refresh_token&access_token=<token>`
   — token harus **≥24 jam**, jadi cron guard harus skip bila lebih muda.
7. Verifikasi izin nyata dengan tes publish (create container → publish →
   DELETE post → cek `me/threads` kosong).

## Pola handoff kredensial aman

- Endpoint gated di Apache conf terpisah, bukan vhost utama. Untuk vhost dengan
  `ProxyPass /` catch-all, kecualikan route via scoped `<Location> ProxyPass !`.
- Gate acak 32-char di `.gate` (640 root:www-data); pakai query `?k=` karena
  browser form tidak bisa mengirim Authorization header.
- PHP form POST simpan rahasia atomik (file 600), tidak pernah mengembalikan
  nilainya. Callback terpisah menukar code dan menampilkan hanya akun/scope/
  expiry, bukan token.
- Setelah selesai: disable conf, hapus endpoint/gate/secret, verifikasi tak
  ada secret tersisa dan probe publik tidak lagi mencapai endpoint.

## Pitfalls terbukti

1. User Token Generator tidak memberi izin custom; scopes yang ditambah di app
   perlu alur OAuth eksplisit.
2. Panjang token bukan bukti scopes. Bukti = API nyata (mis. DELETE success).
3. `debug_token` hostnya `graph.facebook.com`, bukan `graph.threads.com`.
4. PHP Apache bisa tidak punya curl extension: cek sebelum callback; bila hilang,
   pasang paket PHP curl yang cocok dan reload Apache.
5. Refresh GET-only; POST menghasilkan error 33.
6. Token <24 jam tidak dapat refresh (error 452/4279019).
7. Delete post perlu `threads_delete`; error code 10 berarti scope tidak ada
   pada token aktual.
8. `hermes cron create --script` menerima basename relatif ke profile scripts,
   bukan path absolut.

## Batasan platform

- Post maks 500 karakter; container 24 jam; 250 post/hari; edit tidak tersedia.
  Koreksi post = DELETE + repost (perlu `threads_delete`).
- Long-lived token 60 hari; tanpa refresh tepat waktu token expired dan harus
  OAuth ulang. Pasang cron refresh sebelum mengandalkan token produksi.
