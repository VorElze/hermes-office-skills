# TLS proxy & static-asset depth

## The accept-loop TLS hang pattern (503 while `systemd` says active)

Failure mode: `srv.socket = context.wrap_socket(...)` (or wrapping before
`serve_forever`) does the TLS handshake INSIDE the main accept loop. One
client that connects and stalls mid-handshake (browser closed, phone moved
network) freezes accept for everyone: backlog fills (`ss -ltnp` Recv-Q ==
queue size, `SYN-SENT` from the proxy) → Apache returns 503 even though the
unit never went down.

Diagnosis signature (all four together = this bug):

- `ss -ltnp | grep <port>` → established connections with large, growing
  `Recv-Q` (data sent by client, never read by a blocked main thread).
- `curl https://127.0.0.1:<port>/ --max-time 8` → timeout while
  `systemctl is-active` prints `active`.
- Apache error/other_vhosts_access log → 503 or absent entries for the
  user's URL during the window.
- Process exists (`ps`) but does not respond — thread dump (py-spy) optional.

Fix shape (Python stdlib `ThreadingHTTPServer`):

```python
class TLSThreadedHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    request_queue_size = 128          # backlog; stdlib default 5 is tiny
    handshake_timeout = 10            # seconds

    def process_request_thread(self, request, client_address):
        try:
            request.settimeout(self.handshake_timeout)
            tls = context.wrap_socket(request, server_side=True)
        except Exception:
            self.shutdown_request(request)   # drop stalled klien, accept continues
            return
        tls.settimeout(getattr(Handler, "timeout", 30))  # keep-alive/read cap
        try:
            self.finish_request(tls, client_address)
        except Exception:
            self.handle_error(tls, client_address)
        finally:
            self.shutdown_request(tls)
```

Key: the LISTENING socket stays raw TCP; `wrap_socket` runs per-connection in
the worker thread, so a slow handshake costs one thread for ≤10s, never the
whole server.

## Prove the fix with a flood test, not a restart

Restart only masks the hang. Reproduction loop (run after every such fix):

```python
import socket, ssl, urllib.request
ctx = ssl.create_default_context(); ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
stuck = []
for _ in range(20):                 # connect, then say nothing
    s = socket.socket(); s.settimeout(2)
    s.connect(("127.0.0.1", PORT)); stuck.append(s)
zombie = []
for _ in range(10):                 # connect + 1 garbage byte + stall
    s = socket.socket(); s.settimeout(2)
    s.connect(("127.0.0.1", PORT))
    s.send(b"\x16\x03\x01\x00\x05garbage"); zombie.append(s)
ok = 0
for _ in range(5):                  # normal traffic must stay 200 DURING the flood
    try:
        ok += (urllib.request.urlopen(
            f"https://127.0.0.1:{PORT}/", context=ctx, timeout=8).status == 200)
    except Exception as e:
        print("gagal:", e)
print(f"survived flood: {ok}/5")     # expect 5/5; any <5 = hang still present
for s in stuck + zombie: s.close()
```

Accept criteria: `5/5 HTTP 200` while all 30 hostile sockets are held open.
Before the fix the same script yields 0/5 (server wedged).

## Stale asset diagnosis (user's browser runs old code)

Checklist when our fresh browser renders fine but the user's does not:

1. Access log for their IP in their load minute: if HTML 200 is logged but
   `/assets/js/*` requests are ABSENT, their browser served JS/CSS from disk
   cache (cache hits never reach the log).
2. Byte compare: `curl -sI <url>/assets/js/<file>` `Content-Length` (or GET
   byte count) vs `wc -c` on disk — mismatch = proxy/log serving old bytes,
   match + absent requests = pure client cache.
3. Fix at the server for all future changes: emit from the request handler's
   `end_headers`:
   `Cache-Control: no-store, no-cache, must-revalidate, max-age=0`,
   `Pragma: no-cache`, `Expires: 0`.
4. User-side recovery (only after the header is live): `Ctrl+Shift+R`, then
   DevTools → Network → Disable cache. Without step 3 the hard refresh fixes
   once and the next deploy re-breaks them.

A service worker or a privacy/ad-block shield (Brave/Edge) can also pin or
block requests — if log shows requests they are failing on and our browser is
clean, have them check the shield icon in the address bar; do not diagnose
this from screenshots alone (a screenshot without DevTools/console proves
nothing about cause).

## URL-shape checks after any proxy change

- Test BOTH `https://<host>/office` and `.../office/` with a full GET; print
  `redirect_url`. The bare form should 302 to the slashed form — users type
  URLs from memory and a 404/timeout there reads as "site down".
- `curl -I` (HEAD) can behave differently than GET behind some proxy rules —
  never conclude outage from HEAD alone.

## First-run exposure of a new web app (ordered, each step gated on proof)

Adding a proxy `Location` is the LAST step, never the first. Order:

1. **Run the app loopback-only** (systemd user unit; a `--foreground`/
   `--no-browser` bootstrap under a supervisor so it doesn't double-fork;
   `Linger=yes` must already be set for user units to survive reboot).
   Confirm `GET /health` on `127.0.0.1` returns 200.
2. **Establish auth before any public route exists.** First read the app's
   own auth code/docs for first-run behavior — apps differ:
   - shared-password apps with no registration UI hide the password form
     when no password is set (public first visit = open, or a dead login
     page). Configure the secret in a root-only env file, or bootstrap it
     from a local/private-network request, per the app's gate.
   - apps that gate first-run setup to local origins need the seed request
     to come from loopback/LAN; a remote seed is refused by design.
3. **Prove the gate unauthenticated:** probe a sensitive route without a
   session from the loopback listener → must be 401/403/redirect-to-login,
   never 200. Then log in for real (browser or cookie jar) and confirm 200.
4. **Add the proxy route** on the existing TLS vhost. Before choosing a
   subpath (`/app/`), verify the app builds URLs root-absolute (`fetch('/x')`,
   `<base href="/">`, `location.origin + '/x'`) — subpath-unaware apps break
   on static assets, API calls and redirects. If any root-absolute usage is
   found or uncertain, use a dedicated hostname or root path instead.
   Proxy requirements: no response buffering for streaming (SSE/chunked),
   WebSocket upgrade headers if the app uses WS, and both bare/slash URL
   variants tested per the section above.
5. **Feature-prove, don't health-prove:** after exposure check the privileged
   paths individually — SSE/stream endpoints return `text/event-stream` and
   stream progressively through the proxy, terminal/shell endpoints are
   auth-gated, static assets load with correct MIME, and the session cookie's
   domain/path matches the mount. `/health` 200 proves none of this.

Report each step with its measured evidence; a dependency-install log or a
health 200 alone never authorizes step 4.
