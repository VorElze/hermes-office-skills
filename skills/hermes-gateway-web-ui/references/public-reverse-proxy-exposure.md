# Exposing a loopback web UI to a public IP (reverse proxy)

Depth reference for publishing a self-hosted web UI (e.g. hermes-webui) behind
Apache TLS while keeping auth mandatory. Follow only after the UI is proven
healthy on loopback.

## Order of operations (never reorder)

1. Bind loopback first (127.0.0.1:port), start service, verify /health.
2. Create the first-run password BEFORE any public exposure. Some WebUIs
   auto-complete their onboarding wizard without ever asking for a password,
   so the login page renders but auth_enabled=false (open app). Verify with
   GET /api/auth/status plus negative probes: wrong-password POST to
   /api/auth/login must be 401, unauthenticated API must be 401. Never trust
   that the wizard gated anything.
3. First password is set from a local-network request only (enforced by the
   app): use an SSH tunnel (ssh -L port:127.0.0.1:port user@host) so the owner
   types the password in their own browser. Passwords never pass through chat.
4. Only then add the public reverse-proxy vhost.

## Apache sub-path recipe

    RewriteEngine On
    RewriteRule ^/prefix$ /prefix/ [R=301,L]
    ProxyPass        /prefix/ http://127.0.0.1:port/
    ProxyPassReverse /prefix/ http://127.0.0.1:port/
    RequestHeader set X-Forwarded-Proto "https"
    RequestHeader set X-Real-IP expr=%{REMOTE_ADDR}
    RequestHeader set X-Forwarded-For expr=%{REMOTE_ADDR}

- Trailing-slash mapping strips the prefix so the SPA sees root paths. The 301
  for the no-slash form is mandatory: the app injects a per-request base href,
  so without the slash every asset resolves against the site root and the app
  renders blank outside its prefix.
- RequestHeader set (overwrite), NEVER append: append lets a public client
  spoof X-Forwarded-For and defeat IP-based rate limits; the backend trusts
  loopback peers as its proxy implicitly.
- expr=%{REMOTE_ADDR} is valid mod_headers syntax; bare %{REMOTE_ADDR}s does
  not interpolate and forwards a literal value.
- Cookie Path=/ is prefix-safe. Check the auth cookie Path before assuming.
- apache2ctl configtest BEFORE reload. Never blind-reload a live vhost.

## Sub-path pitfalls in the frontend

- Login/401 redirects carrying an app-rooted next=/ escape the mount: after
  login the browser navigates to / (site root, Apache default page) while the
  session cookie is valid - the classic "login throws me out" report. Resolve
  the redirect against the mount point: strip the trailing /login from
  location.pathname to get the mount; keep already-prefix-qualified targets,
  prefix app-rooted ones, and preserve open-redirect guards for
  protocol-relative and absolute-URL targets.
- Test redirect logic without credentials: extract the function into a node vm
  context with a stubbed window.location and run a table of
  (pathname, next) -> expected result. One pass catches both the mount-escape
  and any open-redirect regression.
- Grep the SPA for absolute-path fetch calls and location.href assignments
  BEFORE choosing sub-path vs dedicated hostname. Apps whose fetches strip the
  leading slash and resolve against document.baseURI are prefix-safe.
- After deploys verify the SERVED page: base href, password-field id,
  stylesheet count. A 200 on /prefix/login does not prove the CSS loaded.

## Config and verification without credentials

- Repo-root .env is loaded by the launcher (bootstrap/start.sh), so one env var
  can drive both the frontend's injected config
  (window.__HERMES_CONFIG__.maxUploadBytes) and the backend guard
  (HERMES_WEBUI_MAX_UPLOAD_MB). Confirm it reached the LIVE process by reading
  /proc/<pid>/environ - a correct .env proves nothing until the service
  restarted and the var is in the process environment.
- Size/limit guards often run BEFORE auth: an oversized-upload probe returns
  401 (auth) rather than 413 (limit) when under the cap - that 401 IS the pass
  signal. A 502 through the proxy on huge bodies while the direct backend
  answers 401 is proxy body-piping noise (broken pipe after early auth
  rejection), not an app failure; compare direct-vs-proxied.
- Behind a loopback proxy, rate limits keyed on client IP see ONE shared
  address (127.0.0.1), so a few wrong passwords can lock out all users for the
  window. Acceptable for single-operator deployments; tell the owner.

## System-file edits

- Hermes write_file refuses sensitive system paths (/etc/...) by design. Use
  the terminal with a base64 round-trip (encode, base64 -d to temp, sudo
  install -m644 into place) instead of heredocs: nested quotes in Apache
  %{...} expressions and Python triple-quoted strings break heredoc scripts
  silently, and a broken edit to a live vhost is costly.
