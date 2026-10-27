---
name: hermes-gateway-web-ui
description: Use when connecting a web UI to the Hermes gateway.
version: 1.0.0
author: coordinator
license: MIT
metadata:
  hermes:
    tags: [gateway, websocket, web-ui, verification, debugging]
    related_skills: [hermes-agent, hermes-service-persistence]
---

## When to Use

Use this when installing or debugging a self-hosted web UI (Hermes3D, a custom dashboard, a gateway-connected frontend) that must talk to a Hermes gateway: when the UI reports "not connected", "no gateway", a 403, or a WebSocket timeout, and you must determine whether the backend or the browser is at fault.

# Connecting a self-hosted web UI to the Hermes gateway

## Always-on rules

1. **Prove the backend before touching the browser, then test the exact failing path.** A UI status label describes the browser's view, not the server's state. Probe the backend health endpoint first, but treat health as transport/liveness evidence only: it does not prove authenticated APIs, session retrieval, SSE, or WebSocket flows are healthy. Use DevTools Network/Console on the affected tab and correlate the failed request's URL, status/body, and timestamp with server logs before attributing cause.
2. **Never stop or reconfigure the existing gateway process** to make room. Run a second isolated instance instead (step 2).
3. **Do not report migration success until the new UI renders and is verified end-to-end.** Old services stay running until the new one is proven — then and only then remove them.
4. **Never print tokens/keys** into chat, screenshots, or report text; mask them (`***`, len only).

## Procedure

1. **Install the app** into a project dir (`git clone ... && npm install`).
2. **Start a backend** on a free port, isolated from the main gateway:
   `hermes serve --isolated --host 127.0.0.1 --port <free> --skip-build`
   (The default dashboard port is usually already taken by the running gateway — that is expected, not an error.)
3. **Create a dedicated token** for the app in `~/.hermes/.env` (dedupe to ONE entry), plus a copy under the profile scratch dir with `chmod 600`.
4. **Point the app's env at the backend** (`ws://localhost:<port>` + token + adapter type). Check whether the app re-reads `.env` at runtime or needs a restart.
5. **If you run the app as a production build** (`npm run build` + `npm start`), set the outbound allowlist env first (`UPSTREAM_ALLOWLIST=localhost,127.0.0.1`, plus `CUSTOM_RUNTIME_ALLOWLIST` if present) — production mode refuses any upstream host not listed (see Pitfalls).
6. **Verify the WebSocket handshake**: token must go in the **query string** — `?token=` → HTTP 101; Authorization/X-Session-Token headers → **403**. See `references/gateway-ws-protocol.md` for the exact curl.
6. **Verify the protocol with a Node probe** (`node ws_probe.js`) and expect `hello-ok` plus a profile list. This isolates server vs. browser in one shot.
7. **Isolate the browser: test the WS from a non-app page on the same origin** — navigate the browser to a plain endpoint (an API route that renders JSON), then from the console run `new WebSocket('ws://<host>/api/gateway/ws')` and wait for `onopen`. If it opens in milliseconds there but never opens inside the app, the network path is proven healthy and the fault is the app's own JS on that page.
8. **Localize the fault from the failing request.** If health fails, debug server availability, logs, and port. If health succeeds but an API fails, inspect its actual auth/session response and correlate server logs; if APIs succeed but streaming fails, test the stream/WebSocket handshake and gateway run state. Do not conclude the browser/UI is at fault solely because health succeeds, and do not recommend a restart without evidence it will address the failing layer.
9. **Verify visually** (screenshot of the rendered UI) before declaring done, then remove the old services.
10. **Remote access should prefer a private overlay network over public exposure.** For Tailscale, verify both client and server are in the same tailnet; install/authenticate Tailscale on the server, then expose a loopback-only WebUI with `tailscale serve` (not Funnel) or a localhost SSH tunnel. Confirm the exact Serve syntax with `tailscale serve --help`, test from a tailnet peer, and keep authentication enabled. A WebUI bound only to `127.0.0.1` is not reachable through the server's Tailscale IP unless a local reverse proxy/Serve forwards it. Decision table and the full install/approval/verification recipe: `references/private-remote-access-mesh-vpn.md`.
11. **Public-IP publishing is a separate gated phase** — see `references/public-reverse-proxy-exposure.md`: loopback first, first-run password BEFORE exposure (onboarding wizards can auto-complete with auth still off), negative auth probes, then the proxy vhost.

## Pitfalls

- **Send the WS token as `?token=`, not a header** — the gateway's WS auth only reads the query, so headers fail with 403 and look like an auth bug when the token is fine.
- **Use `{type:'req', method:'connect', id, params}`** for the gateway connect frame — a bare `{type:'connect'}` (or `method`-only) frame is rejected with close `1008 connect required`, which reads as "client never connected".
- **Fill React-controlled inputs with the native value setter** (`Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set` + dispatch `input`/`change`) — a plain `.value =` assignment leaves React state empty, so the form looks filled but submits nothing.
- **Don't patch `window.WebSocket` to sniff frames** on a page you are trying to connect — wrapping the constructor can break the handshake itself and send you chasing a bug you created; record passively or use CDP instead.
- **A UI label can be misleading while the backend is healthy** (e.g. "No local gateway found" after a successful server handshake) — trust the probe result over the label, and check the server's own logs for the browser's attempt.
- **Confirm which URL the browser actually dials** — apps often route through a local proxy path (`ws://localhost:3000/api/gateway/ws`) rather than the backend directly; verify at that hop.
- **Production builds gate outbound upstream hosts behind an allowlist** — with `UPSTREAM_ALLOWLIST` unset, connect fails browser-side with a generic `1011 connect failed` / `studio.gateway_url_blocked` while the server log says `refusing upstream connection: UPSTREAM_ALLOWLIST is empty in production`. Set it in the app's `.env` before testing production mode; dev mode doesn't enforce it, so a flow that worked in dev silently "breaks" in production for this reason alone.
- **A flood of `Maximum update depth exceeded` errors during connect starves the browser main thread** — `onopen` never fires, the handshake times out, and the UI reports a gateway failure that doesn't exist. Treat the gateway as healthy until the plain-page probe (step 7) proves otherwise, and never patch gateway code for a render-storm artifact observed only inside the app page.
