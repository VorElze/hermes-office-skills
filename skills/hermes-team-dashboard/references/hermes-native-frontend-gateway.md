# Community frontend to Hermes gateway (JSON-RPC) integration

Depth for step 6 of the adoption procedure - when the chosen UI talks to the
Hermes gateway itself (Studio/Hermes3D class projects) instead of consuming a
custom read-only feed. VERIFIED items were proven by running them; anything
else is upstream-documented and must be re-checked in the repo README before
promising it.

## Starting the backend it connects to (VERIFIED)

- A machine-level `hermes serve` may already be running on the default port
  and refuses a second instance outright: `Refusing to start: this host is
  already served by PID ...` (it names the owner port, e.g. 9119, and the
  profiles it covers). **Fix: add `--isolated`** (dedicated server scoped to
  that profile instead of routing to the machine-level one). Proof of health:
  `HERMES_BACKEND_READY port=<n>` in output plus `ss -tln` showing the bind:
  `hermes serve --isolated --host 127.0.0.1 --port <free-port> --skip-build`.
  `--host 127.0.0.1` is not optional - a non-loopback bind turns on the login
  gate and breaks token auth.
- **Pin the shared secret under a DEDICATED env name** (e.g.
  `HERMES3D_OFFICE_TOKEN=$(openssl rand -hex 32)` appended ONCE to
  `~/.hermes/.env`, deduped) and inject it on the serve command line as
  `HERMES_DASHBOARD_SESSION_TOKEN=...`. Never pin `HERMES_DASHBOARD_SESSION_TOKEN`
  itself in `.env`: the loader overrides it on every desktop launch and the
  app dies at boot (upstream-documented).
- Measured auth surface: `GET /api/status` = 200 without auth,
  `GET /api/profiles` = 401, raw WS upgrade to `/api/ws` WITHOUT token =
  **403**. So a frontend wizard saying "Timed out connecting to the gateway"
  is an auth/credential problem on the WS path, not a dead backend. Probe it
  yourself before debugging anything else:
  `curl -N -H 'Connection: Upgrade' -H 'Upgrade: websocket' -H 'Sec-WebSocket-Version: 13' -H 'Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==' http://127.0.0.1:<port>/api/ws`
  and diff 403 vs 101.

## Frontend wiring (upstream-documented; verify in-repo)

- Clone, `npm install`, `cp .env.example .env`. Gateway URL has two knobs:
  `NEXT_PUBLIC_GATEWAY_URL` is BUILD-TIME (needs `npm run build` after edits)
  while `HERMES3D_GATEWAY_URL` / `HERMES3D_GATEWAY_TOKEN` take effect on
  restart - prefer the runtime pair so later edits need no rebuild.
- Point at the SERVER ROOT, never the websocket path: the client appends
  `/api/ws` itself. Distinct fingerprints: `EPROTO` = `wss://` against a
  plaintext port, 403 = token mismatch, 401 = you hit the gated dashboard
  instead of the loopback serve.
- Connect wizard order: renderer choice, backend selector, gateway URL
  (password field = gateway token), Connect. Pick the backend matching the
  runtime (e.g. "Hermes Agent (direct)") BEFORE filling the URL, and re-read
  input values via JS before clicking Connect - React controlled inputs
  ignore a bare `.value` assignment unless the native setter + `input` event
  are dispatched.

## Sequencing (same rule as any panel swap)

Stage everything (install, env, backend probe) BEFORE touching the old panel;
test on a side port; keep the previous panel and its units untouched until the
new one renders the correct roster/status in a browser; only then cut over the
production port and archive the old directory. A frontend that boots is NOT a
verified integration - the gate is one character per profile showing real
card-derived status.
