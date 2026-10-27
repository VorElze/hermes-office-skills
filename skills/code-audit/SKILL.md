---
name: code-audit
description: Audit delivered source for security and correctness issues.
version: 0.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [audit, security, code-review, findings, vulnerability]
    related_skills: [codebase-inspection, dogfood, requesting-code-review, systematic-debugging]
---

# Code Audit

Audit a codebase the user hands over (archive, directory, repo) and return a
prioritized findings report in which every non-trivial claim carries evidence:
a reproduction, a benchmark, or a code citation with file and line. The audit
is read-only — never edit the code under review.

## When to Use

- User sends source (zip/tar/dir) and asks what is wrong, for a security
  review, an analysis, or development feedback (any language).
- Pre-adoption review of third-party code before it is deployed.
- Gap analysis of a product against a named competitor.
- Re-audit after a board's implementer claims the findings are fixed —
  the downstream review card described in `references/board-handoff.md`.
  Round-2 technique (field-proven): prove a fix in three layers —
  (1) syntax (`node --check`), (2) behavioral fixture shaped like the
  SERVER's real payload (strings are not booleans: `probe_error:'state.db missing'`,
  `status:'unknown'`), (3) live==disk byte-for-byte (`md5sum` local vs
  downloaded bundle; `Cache-Control: none` rules out stale cache). When
  natural live data lacks the failing case (0 red avatars today), inject the
  fixture via route-intercept in YOUR OWN QA browser only — never mutate
  server or code. Raise an AC from FAIL to PASS only on that evidence, and
  record "not re-run" honestly for checks you skipped.

**Don't use for:** your own uncommitted diff before a commit
(`requesting-code-review`), testing a running web app through a browser
(`dogfood`), LOC/language metrics only (`codebase-inspection`).

## Prerequisites

- Extract archives into the scratch dir; never unpack over a tree the user owns.
- Running a foreign test suite needs a throwaway venv under scratch — never
  install the project's pinned dependencies into the system interpreter.
- Reproduction probes target a local copy only; no production or third-party
  systems, minimal non-destructive payloads.

## Procedure

1. **Extract and inventory.** Tree, line counts per file, entry points,
   dependencies, docs. *Done when* you can name the main modules and how the
   program runs before judging anything.
2. **Read intent first.** README, architecture docs, and manifests state
   claims ("fail-safe fallback", "learning loop", "celery worker"). Every
   claim becomes a verification target — docs describe intent, not behavior.
3. **Trace the boundaries.** Data flows at the edges: request → auth →
   handlers → queue/worker → storage → subprocess/media. Run the standing
   probes in `references/proof-recipes.md` (authz coverage, client-supplied
   paths, fallback reuse, queue dispatch proof, retention, feature truth).
4. **Prove before reporting.** Build the minimal reproduction from the
   recipe file; a finding without evidence is marked as suspicion, never
   stated as fact. Benchmarks use synthetic input scaled to realistic size,
   with extrapolation shown.
5. **Run the test suite.** Classify each failure: environment (missing
   dependency, version mismatch, missing system binary) vs product bug.
   Undeclared test dependencies are themselves a finding.
6. **Compare when asked.** For competitor gap analysis, fetch the official
   feature list (`web_search`/`web_extract` on the vendor site) rather than
   recalling it; organize the gap by impact vs effort.
7. **Write the report** in the user's language, using the format below.
8. **Deliver it as a file.** A long report in chat is unreadable past
   ~150 lines. Write the complete Markdown report to a file under the
   scratch dir with a self-describing name (`<product>-<version>-audit.md`),
   then hand it over as an attachment (`MEDIA:/abs/path`). Every finding
   lives in the file; the chat reply carries only the executive summary
   and the pointer. When the report drives follow-up work on a Kanban
   board, write the findings into the task bodies — assignees never see
   your conversation history, only the card. The full recipe for splitting
   the work into implementation and review cards, making long runs
   resumable, and preserving outputs lives in
   `references/board-handoff.md`. Record the verdict on the review card as a
  durable comment; do not try to push it back with `kanban_request_changes`,
  which only works for a run claimed from the `review` lane (the bundled
  `sdlc-review` skill owns that lane), and note that a parent already `done`
  cannot be reopened as a review either — routing the rework is a separate
  decision for the orchestrator.

## Report Format

- **Opening summary:** overall impression, count per severity, the three
  fixes to do first.
- **Findings ordered most → least dangerous**, each with: Title, Severity,
  Location (file, function, line), Issue, Impact, Evidence (snippet or
  repro steps with actual output), Fix (concrete corrected code), Confidence
  (certain / likely / needs verification).
- **Limits of the analysis:** what was not run or covered.
- **Close with what is genuinely good** in the code — specific, not filler.
- One bug class in two places is one finding with two locations, not two
  findings.

## Pitfalls

### Importer/parser & webroot secret (field-proven)
- **Golden compare harus dibangun ulang dua jalur**: runner Anda sendiri memakai parser produksi (read-only) ke DB uji baru, DAN jalur murni tool resmi (`mariadb < dump`) ke DB kedua; banding COUNT(*) nyata per tabel + nama tabel + metadata (columns/indexes/views/routines/FK) + jumlah/baris. Angka importir tidak pernah dikutip tanpa ulang ukur.
- **Idempotensi = run ke-2 TANPA reset DB** (jangan DROP antar run; DROP membuat semuanya jadi selalu "bersih"); wajib buktikan jumlah statement & hasil tetap sama.
- **Uji separuh importir**: jalankan loop parser+exec milik target lewat CLI runner sendiri; kegagalan DSN/format muncul di sana tanpa menyentuh app atau DB pihak lain.
- **Secret runtime di webroot**: bukti leak = Apache fixture sendiri (port/PID/dir sendiri, `AllowOverride All`, PHP handler opsional) + GET-only ke path `.token/.progress/.selesai/.log`; catat status+ukuran. Root `.htaccess` yang deny hidden file hanya saat target sekaligus dir DAN file (`RewriteCond -d` + `-f`) TIDAK menolak dotfile biasa — syarat ganda adalah bug deny-rule klasik.
- **Biaya pekerjaan sebelum background worker**: ukur fase pre-count dalam request POST terpisah (mis. `php8.3 -r` loop pratinjau parser) dan laporkan detiknya; scan sinkron >timeout hosting = temuan resilience.
- **Uji bypass token/CSRF lewat HTTP nyata = satu cookie-jar sesi** (urllib/curl -c -b); tanpa cookie, CSRF tiap GET berubah dan semua POST tampak 403 — itu false negative dari harness, bukan bukti keamanan.
- **Harness DSN wajib format yang valid** (`host=...;charset=...;dbname=...`); satu `;;` salah tempat memicu `getaddrinfo ... failed` yang bisa dikira bug produk. Bedakan dulu: format produksi (charset setelah dbname) = bug nyata reproduksi, config harness Anda sendiri = bug harness.
- **Guard terminal single-query mode** memblokir perintah berisi pola DROP/recursive-rm; tulis perintah itu ke skrip (`write_file` lalu jalankan), jangan mengulang percobaan yang sama.
- **Detail panjang di file `review_<peran>/`**, komentar kartu hanya summary + verdict + spek fix bernomor; server uji (Apache/php -S) wajib dihentikan sebelum complete dan disebut di handoff.

- **Baseline lint verification trap (PHP/Yii, field-proven)**: re-lint hanya file yang GAGAL di pohon hasil (subset) terhadap baseline itu **benar utk REGRESI** (bukti: set-subset `comm -23 <fail_app> <fail_base>` = 0), tapi **undercount jumlah kegagalan baseline** — karena baseline bisa punya file GAGAL yang sudah terhapus/di-upgrade di pohon hasil (p2: P1 klaim baseline 75 FAIL; lint penuh asli = 123; 48 file hilang di paket lama). Selalu lint **SELURUH** baseline (find penuh), lalu bandingkan dua set dengan `comm`/set-diff — bukan subset.
- **Apache `.htaccess` exposure test — fixture harus menyalin file `.htaccess` anak (field-proven)**: saat membangun fixture Apache (`AllowOverride All`, port/PID/dir sendiri), salin **semua** `.htaccess` relevan (root + subdir seperti `uploaded_files/.htaccess`) — tanpa itu, rule `php_flag engine off` tidak teruji dan payload tampak "BOCOR/RCE" padahal aslinya hanya source mentah yang dikirim (bukti: byte payload 24 B = source file mentah vs 10 B = output engine-ON; ukuran body membedakan dieksekusi vs tidak). Bersihkan PIDfile + `apache2 -k stop -f <conf>` setelah run.
- **`FilesMatch` match FILENAME, bukan path (trap klasik)**: root `.htaccess` dgn `FilesMatch "\.config\."` **tidak** menangkap `article/config/ded.php` — pattern `\.config\.` butuh substring literal `.config.` di NAMA file; dir `config/` tanpa dot = tidak match. Web shell/shell di direktori config/ karena itu ter-expose penuh walau ada "aturan blokir config". Selalu uji pola FilesMatch terhadap path nyata via fixture HTTP, jangan baca polanya saja.
- **`php -S` built-in server TIDAK menghormati `.htaccess` — bedakan "terproteksi" vs "terproteksi jika Apache+AllowOverride"**: file config yang 403 via Apache fixture bisa 200 via `php -S`; ini bukan bukti bocor di produksi TAPI juga bukan bukti aman — catat exposure sebagai **conditional** pada server config + tunjukkan keduanya. Keadaan paling berbahaya: sub-app **tanpa `.htaccess` sama sekali** (protection unconditional-off, terbukti 200 di Apache fixture pun).
- **Security review wajib scan pola web shell/backdoor (eval+base64/gzinflate, FilesMan, wsO) di seluruh non-vendor tree** — shell aktif di direktori config/ (field-proven: `article/config/ded.php`, 201 baris, login bcrypt + `eval(gzinflate(base64_decode(...)))` manager) lolos dari security review upstream yang fokus "kredensial/CSRF"; shell pre-existing (identik baseline dgn `cmp -s`) tetap masuk laporan dgn severity tinggi karena nilai handoff-nya melampaui cakupan review sebelumnya.
- **Jangan mengulang pekerjaan attempt sebelumnya yang sudah ada di workspace task** — baca dulu file bukti yang sudah terkumpul (out/txt/sh dari attempt lalu), verifikasi/lanjutkan; reclaim watchdog memotong sesi panjang jadi banyak attempt — state di workspace adalah memori sesungguhnya.
- **Terminal single-query memblokir pola `pgrep ... | kill` ("self-termination")** — ganti dengan `ps -C <nama> -o pid=,cmd=` untuk daftar, lalu `kill <pid>` eksplisit; jangan mengulang perintah yang sama 3x (loop-warning).
- **`pkill -f`/`pgrep -f` dengan pattern literal di argv MEMBUNUH SHELL SENDIRI** (field-proven 2×: exit -15 & -9) — skrip shell yang memanggilnya memuat string pattern itu di argv-nya, jadi `pkill -f 'apache_p5'` mencocokkan skrip itu sendiri. Solusi bracket trick `pgrep -f "apache_[p]5"` (regex `[p]` tak bisa mencocokkan dirinya sendiri), atau `ps -C`, lalu `kill <pid>` eksplisit.
- **`php -S` tanpa docroot `-t public` = SEMUA aset 404, halaman tanpa gaya, dan seluruh pengukuran visual/a11y/gate menjadi false-positive** (field-proven: violation kontras palsu, horizontal overflow palsu 908px di viewport 390, "broken-image", "few-pictures", s2c diff 84%) — karena router dipanggil dari root repo, `assets/` di-resolve salah. Sebelum gate visual/a11y/desain: curl SATU aset (`/assets/css/app.css` atau sebuah PNG) dan wajib 200 + ukuran nontrivial; kalau 404, restart server dengan docroot benar (`php -S host:port -t public router.php`), lalu ULANG gate dari nol — hasil sebelumnya invalid, jangan digabung.
- **Resolve kontras incomplete axe dengan compositing yang BENAR: blend dari lapisan TERBAWAH ke atas** (field-proven: loop terbalik menghasilkan 1.05:1 palsu vs nyata 5.59:1) — urutan layer = leluhur terjauh dulu, lalu tiap leluhur lebih dekat di-atas. Cek silang dengan probe langsung `getComputedStyle` leluhur berlatar solid (mis. section `.ak-hero--brand` = `rgb(0,96,86)`). Axe menandai elemen 1 huruf sebagai "content too short" dan elemen ber-rgba sebagai incomplete — itu bukan violation; hitung manual lalu catat angka. Untuk sampel piksel dari screenshot tanpa Pillow: decoder PNG stdlib WAJIB menangani filter byte scanline (0–4: None/Sub/Up/Average/Paeth) — dekode naif memberi piksel nol semua.
- **Backup/restore smoke: pakai `mysqldump --single-transaction --routines --triggers --databases <db>` — bukan tanpa `--databases`** (field-proven): dump biasa menghasilkan view yang **schema-qualified** (`dbname`.`table`), sehingga restore ke nama DB berbeda gagal `ERROR 1356` pada view turunan (contoh: `item_koleksi` → `v_stat_jumlah_koleksi`, 15/16 view), padahal restore ke nama schema yang SAMA sukses penuh 16/16. `--databases` menulis `CREATE DATABASE`+`USE` sehingga referensi ternormalisasi — jalur inilah yang diuji dan yang dijalankan owner.
- **Polling loop impor web: HTTP 410 pada `import.php` = SUKSES selesai ("import selesai, dinonaktifkan"), BUKAN error** (field-proven 1×: loop tidak break di 410, dikira gagal padahal `status=selesai`, `persen=100`, `galat=[]`, DB terisi 201 objek). Break dari polling saat 410 atau `status=selesai` di `.import.progress.json` — bukan hanya saat 200; 410 = auto-disable guard setelah tuntas.
- **Reproduce a documented recipe VERBATIM, never retyped**: extract the fenced code block from the delivered artifact (awk on ``` fences), then make its literal relative path work via `mount --bind <extract> <sandbox>/public_html/<proyek>3` instead of translating the path — retyping hides copy/paste defects (line-continuation `\`, extra flags). Pair it with a real run of the installer (`php8.3 -S` + fresh empty DB via root MySQL, unique DB name — no DROP allowed in single-query mode) so pre/post modes are measured, not assumed.
- **Proof the installer wrote `cpanel-akun.php` 640 → chmod recipe must preserve it**: a post-install `chmod -type f → 644` recipe silently raises the credential file from 640 to 644 (least-privilege undone by the runbook). After any resep/recipe change, rerun with the file EXCLUDED from the blanket chmod and stat it afterwards.
- **Ukur header `.htaccess` (Expires/CSP) via instans Apache uji sendiri, bukan server dev** (field-proven R3): `apache2 -f <conf-sendiri>` dengan daftar LoadModule minimal (mpm_prefork, authz/authn, dir, mime, alias, rewrite, expires, headers, php_module libphp8.1.so, env, setenvif), `Listen 127.0.0.1:<port>` + PID/ErrorLog di /tmp. Trap: (a) `unixd_module` dan `filter_module` built-in — memuatnya = syntax error, hapus dari config; (b) parent `.htaccess` ikut di-merge → beri `AllowOverride None` pada `<Directory>` parent, `AllowOverride All` hanya pada public/; (c) mod_php tidak eksekusi tanpa `<FilesMatch \.php$> SetHandler application/x-httpd-php</FilesMatch>` — tanpa itu index.php dikirim MENTAH (body berawal `<?php`); (d) salinan rsync menjaga perm ketat `.htaccess` (600) → `chmod 644` semua `.htaccess` + `chmod -R a+rX` tree; (e) worker www-data tak bisa traverse /root → salin repo ke /tmp, DocumentRoot kesana. Akhiri: `apache2 -k stop -f <conf>` + `rm -rf` dir uji (di dalamnya ada salinan `.env`!).
- **axe-core di bawah CSP `script-src 'self'`**: `page.addScriptTag({content})` DITOLAK — penolakan itu sendiri bukti CSP aktif (untuk temuan "CSP tanpa unsafe-inline"). Solusi: `page.route(BASE+'/_axe.js', fulfill({body: axeSource, contentType:'application/javascript'}))` lalu `addScriptTag({url: BASE+'/_axe.js'})` same-origin. Selalu catat per halaman: violations, passes, DAN incomplete (lihat memori: incomplete menyembunyikan kontras).
- **`ENV=x php s.php "$ENV"` mengirim string kosong** (field-proven): ekspansi `$ENV` terjadi sebelum prefix assignment berlaku pada command line yang sama — pass nilai literal (`php s.php 'cookie'`) atau export dulu di baris terpisah.
- **Gate WARN/FAIL di luar daftar baseline = temuan BARU, bukan NOT-FIXED** (field-proven R3): item baseline divonis FIXED bila semua item yang DISEBUT baseline beres, dan temuan baru (mis. hairline di file lain yang tak disebut R2) dinomori sendiri (R3-1, Low) dengan rekomendasi polish — jangan mem-block kartu rilis gara-gara WARN di luar scope temuan asli, tapi WAJIB dicatat jujur di laporan + handoff.
- **ZIP mode sweep: parse `unzip -Z -l` permission field by COLUMN, not regex** — `unzip -Z -l` prints `-rw-r--r--  3.0 unx   ... t-  ...`; matching `$1 ~ /..w/` also hits the `t-` flag field and matches 14k+ non-permission rows (noise). Use `substr($1,9,1)=="w"` on the 10-char mode only, and grep matches by path (exclude `assets/`, `vendor/`) — bulk inherited 664 vendor assets are covered by the runbook blanket 644 recipe, so classify as hardening note, not a new finding.
- **Manifest-diff shortcut for "did anything else change"**: `comm -3 <(sort manifest_old) <(sort manifest_new)` on per-file sha256 lists — 2 lines (= 1 file changed) proves every other byte incl. the 122 MB dump is untouched, no re-hashing needed.
- **Never present a guess as fact** — a claim you could not reproduce is
  labeled `likely`/`needs verification` with the reason.
- **Missing-dependency failures are not product bugs** — but a test importing
  a package absent from requirements is a real finding about the project.
- **Grep for actual call sites** before believing architecture claims: a
  configured queue with zero `.delay()`/`apply_async()` call sites is
  decorative; a config key written but never read is a dead feature.
- **Test the default configuration**, not only the secured one — opt-in auth
  (`API_TOKEN` empty in `.env.example`) means the default install is open.
- **Never reprint secrets or credentials** found in source; point at the
  location and recommend rotation.
- **Environment quirks are not findings** (a binary absent on your sandbox,
  a wheel that will not build on your Python version) unless they break the
  project's own stated support matrix — then say which matrix line breaks.
- **Do not soften a serious finding** to keep the report pleasant, and do not
  inflate severity to look thorough.
- **A green suite after a fix proves only what the new tests cover** —
  probe the surface the change *touched* but did not test: WebSocket and
  preflight routes on a router that gained an HTTP guard, the error code a
  docstring promises for a failure path, and any control keyed on client
  identity. Regressions ship comfortably behind a fully green suite.
- **Count the findings before writing the summary** — the severity tally in
  the opening and the numbered findings in the body must match exactly. A
  summary that says "7 Medium" over a body numbered M1–M8 reads as sloppy
  and costs trust in every other number in the report; derive the tally from
  the final list, not from memory of it.

## Verification

- Every Critical/High finding has command output or an exact snippet+line.
- The report names what was not covered and which confidence each claim has.
