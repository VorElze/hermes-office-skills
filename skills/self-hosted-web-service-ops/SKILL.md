---
name: self-hosted-web-service-ops
description: "Use when operating or diagnosing a self-hosted web service."
version: 1.0.0
author: amanda
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [web, apache, tls, proxy, cache, debugging, self-hosted]
    related_skills: [systematic-debugging, hermes-service-persistence]
---

# Self-hosted web service ops

Standing rules for running a web app served by a local backend (systemd)
behind an Apache TLS reverse proxy on the office server, and for diagnosing
user-reported access failures. Depth lives in
`references/tls-proxy-and-cache.md` (TLS accept-loop hang pattern, flood
verification, stale-asset diagnosis, first-run exposure recipe for a new web
app).

## When to Use

- User reports "tidak bisa dibuka / muter-muter / error" on an app we host.
- Deploying code changes to a proxied web app.
- Verifying certificate auto-renewal or proxy health.

## Owner-authorized full app removal

Use this when the owner explicitly asks to remove a hosted app, not merely to take it offline. Remove only that app's deployment; keep the Hermes gateway, shared state, and neighboring apps intact.

1. **Inventory ownership before changing state.** Record the exact project path and size (`du -sh`), Git origin/status (do not print `.env`), relevant service units in both system and user scopes, their `FragmentPath`/`WorkingDirectory`/`ExecStart`, enable symlinks, listen ports, active reverse-proxy route, and any rollback copies. Inspect unit files with secret-bearing `Environment=` values omitted. Identify external DB/volume/state paths separately; do not remove shared Hermes home, gateway/session state, or another app's data as part of this cleanup.
2. **Capture a narrow baseline.** Probe the target URL and representative neighboring routes with `curl -o /dev/null -w '%{http_code} %{size_download}\n'`; record listeners with `ss -ltnp`. This gives a before/after proof that the old route is gone and unrelated services survived.
3. **Stop and disable only the app's unit in its actual scope.** Use `systemctl --user` for a user unit and system `systemctl` for a system unit. Remove its enable symlink and unit after stop/disable; reload the matching manager (`systemctl --user daemon-reload` or `systemctl daemon-reload`). Do not infer service scope from the URL.
4. **Remove the app route without damaging shared vhost behavior.** Edit the active vhost and app-specific rollback copies, removing only the target rewrite/ProxyPass block. Preserve shared forwarding headers and neighboring mappings unless their ownership is proven exclusive to the removed app. Run `apachectl configtest` before reload, then reload Apache and probe the target plus the baseline neighboring routes.
5. **Delete only mapped app-owned files.** After the unit is stopped and no app process is serving, remove the exact project checkout and dedicated config/enable links. Delete external app data only if it is clearly app-owned and within the owner's stated scope; never erase shared DBs or gateway credentials by association. `rm -rf` removes filesystem paths but is not forensic secure erasure—state that distinction if the owner asks for "no trace" or secure deletion.
6. **Verify each layer independently before reporting.** Confirm project/config paths absent, unit file and enable link absent, no listener on the old port, no app-specific route in active or rollback configs, target URL now returns the expected unmounted response (usually 404), and neighboring routes retain their baseline status. Say explicitly if a generic shared directive remains or any data surface was intentionally preserved.

**Bound search output:** scope recursive searches to configuration directories and use `grep -RIlE` (file names only) before inspecting an exact candidate. Never print every matching line from an entire source tree; minified/vendor files can turn one match into hundreds of megabytes of output.

## Diagnosis ladder — NEVER blame client or server before the evidence

Run in order; each step names which side it exonerates:

1. **Backend from the server itself**:
   `curl -s -o /dev/null -w 'HTTP=%{http_code} time=%{time_total}\n' https://127.0.0.1:<port>/ --max-time 8`
   → timeout = backend hung/down; fast 200 = backend healthy.
2. **Proxy path** (with and WITHOUT trailing slash — test both URLs):
   `curl -s -o /dev/null -w ... https://<host>/office/ --max-time 8`
   → one variant failing while the other works = proxy config (redirect /
   location handling), not the app.
3. **Service active ≠ serving**: `systemctl is-active` only proves the process
   exists. Always pair it with `ss -ltnp | grep <port>` (backlog state) and
   `ss -tnp | grep <port>` (Established with growing Recv-Q = connections
   stuck unread; SYN-SENT from the proxy = accept queue full).
4. **Access log decides the side**: grep the Apache access log for the user's
   request in their reported timeframe.
   - Their GET/POST IS logged with 200/302 but the user sees failure →
     **client side**: stale browser cache, extension (ad-block/privacy shield),
     or wrong URL. Proof of stale cache: served asset byte length ≠ file on
     disk, and zero requests for `/assets/js/*` in the minute they loaded the
     page (cache hits never reach the log).
   - Their request is logged as 5xx/503/timeout, or absent entirely while
     others succeed → **server side**.
5. **Only then reproduce in a real browser** (`browser_exec`): open the exact
   URL the user used, inspect the DOM/modal state, read console/network. A
   clean render in our browser + clean server evidence = user's client.

Report the verdict with the measured evidence line (HTTP code + time, log
line, byte counts) — never "sepertinya dari sisi kamu".

### Proving login/auth works (before claiming a feature is "aktif")

- **A 503 behind a reverse proxy is almost always the UPSTREAM being down,
  not the host being remote.** Before hunting SSH keys or remote access,
  read the vhost config on THIS host (`grep -r ProxyPass
  /etc/apache2/sites-available/`) — the preview may be proxied to a loopback
  backend whose dev server died (`ss -ltnp | grep <upstream port>` to confirm).
  Starting that backend is the fix; no remote access needed.
- **Read login form field names from the HTML, never from convention**
  (`grep -o 'name="[^"]*"' <page>`): CSRF fields and the identity field vary
  per app (`_csrf` vs `csrf_token`, `identifier` vs `email`).
- **Prove login END-TO-END with a negative control:** cookie jar (`-c`), POST
  credentials, follow redirects (`-L`), then (a) assert a post-login-only page
  returns 200 for BOTH roles, (b) assert a wrong password stays on the login
  page, (c) assert an admin-only path gives 403 for the lesser role. A 302 back
  to the login form is a FAILED login — treat the redirect target as the truth.
- **`password_verify` == true is the bar for "login aktif", not a route
  existing or `status=active`.** Password hashes that pass through a shell
  get their `$` eaten (double-quoted string expands `$var`) and then no
  password will ever verify; verify `password_verify()` right after writing a
  hash and check `SELECT password_hash` starts with `$argon2id$`/`$2y$`.
- **A "locked out / terkunci" complaint may target the GATE in front of the
  app, not the app's own login.** A browser-native Basic-Auth dialog looks to
  the user like "the login page", so establish WHICH layer failed before
  debugging the app. The access log tells them apart: an
  `authentication failure ... Password` line means the gate rejected (username
  right, secret mistyped); no 401 at all means the gate passed and the app
  login is the failing layer. Validate a Basic-Auth credential with
  `htpasswd -vb <file> <user> <pass>` — `password_verify()` does NOT apply to
  htpasswd/APR1 hashes, so it returns false for a perfectly valid entry.
- **When a client cannot get past a gate and the secret must not be shared,
  remove the GATE, not the protection.** Back up the vhost, drop the
  `<Location>` Basic-Auth block, `apachectl configtest` + reload, then prove
  the site returns 200 with no credentials; keep the app's own login and RBAC
  as the real barrier. Tell the user plainly that the gate is temporary and
  restore it before release — an abandoned open gate is a real exposure, not
  a convenience.


## Staging paralel di host yang sama: DB sendiri, port sendiri

Dipakai ketika staging di shared hosting selalu 500 (`.env`/DB tidak ada, token API panel
tidak dipegang) dan owner memutuskan "database dibuat lokal dulu, uji jalan di server uji".
Jangan menunggu layanan eksternal: bangun instance kedua di sebelah preview yang sudah hidup.

1. **DB baru + GRANT ke user aplikasi yang SUDAH ADA**, jangan bikin user baru:
   `GRANT ALL PRIVILEGES ON <app>_staging.* TO '<appuser>'@'localhost'` + `FLUSH PRIVILEGES`.
   Tanpa grant, aplikasi mencetak pesan generik "Koneksi database tidak tersedia" — mudah
   salah dibaca sebagai password salah, padahal izin schema yang kurang.
2. **Salin pohon kode terpisah:** `rsync -a --delete --exclude .git --exclude node_modules
   <repo>/ <repo>-staging/`, lalu jalankan migrasi di salinan itu.
3. **`.env.local` MENIMPA `.env`** — mengedit `.env` saja membuat migrasi tetap memakai DB lama
   secara diam-diam. Patch KEDUA berkas, lalu percaya baris keluaran migrasi
   (`Database: <nama> @ host`) sebagai bukti, bukan isi berkas.
4. **Isi DB yang sudah dimigrasi dengan `--insert-ignore`:**
   `mysqldump -u root --single-transaction --no-create-info --insert-ignore <dev> | mysql -u root <staging>`.
   `--no-create-info` polos berhenti di baris seed pertama (`Duplicate entry '1' for key 'PRIMARY'`)
   dan meninggalkan tabel konten kosong sementara perintahnya terlihat selesai.
5. **Port sendiri + vhost sendiri, JANGAN subpath vhost yang sudah ada.**
   `ProxyPass /staging/ http://127.0.0.1:8098/` membuang prefiks, aplikasi melihat dirinya di `/`,
   lalu redirect root-absolute (`Location: /akun/login/?next=%2Fpanel%2F`) keluar dari mount;
   memasang `APP_URL` berprefiks TIDAK memperbaikinya. Vhost baru di port lain dengan DocumentRoot
   + proxy ke port backend memberi path root yang benar dan redirect yang benar.
6. **Periksa firewall sebelum memilih port:** `ufw status`, `iptables -S INPUT`. Bila `inactive`,
   semua port terbuka — tetap buktikan dengan `curl https://<ip-publik>:<port>/` (200), bukan loopback.
7. **Sapuan route + kontrol negatif auth** (bukan halaman depan saja):
   `for u in / /anggota/ /berita/ /faq/ /kegiatan/ /kontak/ /akun/login/ /healthz; do curl -sk -o /dev/null
   -w "$u %{http_code} %{size_download}\n" https://127.0.0.1:<port>$u; done` — byte 200-an kecil
   (mis. 1,8 KB untuk login) itu wajar, tapi halaman konten 200 dengan ukuran ~0 = shell kosong.
   Lalu: path terlindungi tanpa cookie → 302 ke login; password salah → 302 balik ke login tanpa sesi.
8. **Unit systemd baru:** tulis ke scratch lalu `install -m 644` (penulisan langsung ke
   `/etc/systemd/**` ditolak), baru `systemctl daemon-reload && systemctl enable --now <unit>`;
   verifikasi `is-enabled` + `is-active` + probe port.
9. **Akui tingkat eksposurnya.** Menyebut "staging" tidak membuatnya privat: kalau firewall host
   `inactive` dan vhost pakai TLS + `X-Robots-Tag: noindex`, halaman tetap publik-terbaca. Katakan
   itu ke owner dan tawarkan gate (basic auth / batas IP) sebelum data anggota sungguhan masuk.

## Always-on rules

- **For a new public web app, keep the backend loopback-only and establish authentication before adding any public proxy route.** Probe auth behavior with no credentials first: some apps hide the password form when no password is configured, so a passwordless first-run page can be open rather than a registration gate. Configure the secret via a root-only service environment or local bootstrap, verify unauthenticated access is denied, then expose through the existing TLS proxy.
- **Treat SSH tunnel/local bootstrap as the safe first-run path, not a competing deployment mode.** If upstream supports only a shared password and has no registration UI, create/configure it locally before opening the proxy; never leave a public setup window. Don't ask for passwords in chat or print them in reports.
- **Set the password before adding any same-host reverse-proxy route, never after.** A same-host proxy makes the app see the proxy's own loopback socket as the client, so a "local/private network only" first-run gate — which exists specifically to block remote setup — stops discriminating and admits every remote request as if it were local. The safe order is: loopback-only bind → seed the password (env file, settings API, or SSH-tunneled request) → prove unauthenticated requests are now rejected → only then add the proxy Location.
- **Verify the exact proxy mount path against the app's asset and API URL construction before choosing a subpath.** Check `<base>`, relative and root-absolute requests, redirects, cookies, and streaming; if subpath support is uncertain, use a dedicated hostname or root path rather than assuming `/app/` works.
- **Prove each layer separately before claiming the deployment works:** backend health on loopback, auth rejection without a session, successful login with a real browser/session, proxy TLS route, then feature checks for streams/WebSockets and privileged features such as terminal. A health 200 or installed dependencies does not prove all features work.
- **After every static/frontend change, send `Cache-Control: no-store, no-cache,
  must-revalidate, max-age=0` (+ `Pragma: no-cache`, `Expires: 0`) from the
  handler** — unversioned assets otherwise leave users on old JS for an
  arbitrary time and the symptom is a broken page, not a visible staleness.
  When a user IS already stuck on stale cache: `Ctrl+Shift+R` hard refresh,
  then DevTools → Network → Disable cache.
- **Never do the TLS handshake in the server's accept loop** — one klien that
  stalls mid-handshake blocks EVERY other connection (backlog fills → 503 while
  systemd says active). Do TLS per-connection in a worker thread with a
  handshake timeout; raise `request_queue_size`. See
  `references/tls-proxy-and-cache.md` for the pattern and the flood test.
- **Prove a hang fix with a reproduction loop, not a restart**: restart only
  restores service temporarily; flood the port with N stuck connects +
  half-handshake zombies and require normal requests to stay HTTP 200 while
  they are held open.
- **Serve redirects for bare paths** (`/office` → `/office/`) so URLs users
  type from memory work; verify both variants with curl after proxy changes.
- **Certificate checks are three facts, not one**: `systemctl list-timers`
  shows the renew timer enabled+active, the unit runs certbot with a
  `--deploy-hook` reloading the proxy, and `notAfter` on the live cert moved
  FORWARD since issuance (short-lived IP certs renew ≈ every 10 days).
  Quote the dates.
- **Secrets never in chat**: invite tokens, passwords, session cookies, and
  hash/salt values → `[REDACTED]`, always. Passwords stored as pbkdf2 hashes
  are irreversible — say so instead of "finding" them; give access via a
  one-time invite link (token_urlsafe, atomic consume-on-use, frontend clears
  `?invite=` from the URL after success, registration re-locks to closed
  afterward). The command that mints one may print the token to the terminal —
  do not relay it into chat.
- **Verify every fix with fresh measurements in the same turn** (curl status
  + time after restart, unit test count, log line) before reporting "sudah
  diperbaiki".

## Pitfalls

- Diagnosing from `curl` alone: our curl from the server bypasses the user's
  path (client cache, browser extension, external DNS). The access log is the
  only record of what THEIR browser actually sent — check it before concluding
  either side.
- Interpreting an empty/odd curl result for a bare-path URL as an outage —
  a 302/redirect or proxy Location quirk can make `-I`/HEAD behave differently
  than GET; always confirm with a full GET and print `redirect_url`.
- "Service active" as health proof — systemd restarts stay `active` while the
  accept queue is dead; pair with the port probe above.
- Telling the user to hard-refresh BEFORE the server sends no-store headers:
  they re-download the same stale-prone assets and the problem returns on the
  next change.
