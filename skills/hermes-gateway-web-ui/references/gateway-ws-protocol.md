# Gateway WebSocket protocol — verification recipes

All commands assume `TOKEN` loaded from the env entry (never echoed).

## 1. Handshake probe (token in query — correct)

```bash
TOKEN=$(grep '^HERMES3D_OFFICE_TOKEN=' ~/.hermes/.env | cut -d= -f2)
curl -s -i -N -m 5 \
  -H 'Connection: Upgrade' -H 'Upgrade: websocket' \
  -H 'Sec-WebSocket-Version: 13' \
  -H 'Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==' \
  "http://127.0.0.1:9120/api/ws?token=$TOKEN" | head -1
# expect: HTTP/1.1 101 Switching Protocols
```

Sending the same token as `Authorization: Bearer` / `X-Session-Token` / `X-Auth-Token` headers returns **403** — the gateway WS auth reads only the query. Origin headers are accepted; a proxy hop usually is too.

## 2. Protocol probe (proves the full path, server-side only)

```js
// ws_probe.js — node ws_probe.js
const WebSocket = require('/path/to/app/node_modules/ws');
const token = require('fs').readFileSync('~/.hermes/profiles/<profile>/cache/scratch/.h3d_token','utf8').trim();
// target the hop the browser uses (app proxy) or the backend directly
const frame = {type:'req', method:'connect', id:'c1',
               params:{token, client:{id:'probe', mode:'browser'}}};
const frames = [];
const ws = new WebSocket('ws://127.0.0.1:3000/api/gateway/ws');
ws.on('open', () => setTimeout(() => ws.send(JSON.stringify(frame)), 2500));
ws.on('message', d => frames.push(String(d).slice(0,400)));
ws.on('close', (c, r) => frames.push(`CLOSE ${c}:${r||''}`));
ws.on('error', e => frames.push('ERR ' + String(e).slice(0,120)));
setTimeout(() => { console.log(JSON.stringify(frames, null, 1)); process.exit(0); }, 14000);
```

Success = a `res` frame with `ok:true` and `payload.type:'hello-ok'` (`adapterType`, `features.methods`, profile list). That response proves the whole chain: env token → proxy → gateway → backend.

Failure signatures:

| Result | Meaning |
|---|---|
| `close 1008 connect required` | frame shape wrong — must be `type:'req'` + `method:'connect'` + string `id` |
| `close 1006`, no frames | hop rejected/crashed — check the app's dev-server log at that moment |
| HTTP 403 on upgrade | token sent as a header — move it to `?token=` |
| `probe OK, browser fails` | server healthy; fault is in the UI (form state, JS, or the URL it dials) |
| `1011 connect failed` + server says `UPSTREAM_ALLOWLIST is empty` | production allowlist gate; set `UPSTREAM_ALLOWLIST=localhost,127.0.0.1` in app env, restart, retry |
| App page floods `Maximum update depth exceeded`, but WS opens on a plain same-origin page | frontend render/persistence loop starving the app socket; transport is healthy, fault is app code |

## 3. Correlating with server logs

The app's server log is the ground truth for what the *browser* did: it prints the upstream settings (adapter type, URL, `token=present`), the bridge startup, the `connect frame` line (`client.id`, `hasToken`), and any `upstream closed ... hadConnect=` line. `hadConnect=false` means the browser never sent a connect frame at all — the failure is client-side regardless of what the UI reports.

## 4. Isolating browser transport from application JavaScript

1. Navigate the browser to a plain same-origin endpoint that does not mount the app's UI (an API route rendering JSON works).
2. From that page's console, open the socket the app dials and await `onopen`:
   ```js
   const ws = new WebSocket('ws://127.0.0.1:3000/api/gateway/ws');
   ws.onopen = () => console.log('transport open');
   ws.onerror = e => console.log('transport error', e);
   ```
3. If it opens in milliseconds there but never inside the app, transport and proxy are proven healthy — the fault is app JS on that page (console errors, render loops), and backend/token changes are wasted effort without new evidence.
4. Before retesting a production build, set its outbound allowlist (`UPSTREAM_ALLOWLIST=localhost,127.0.0.1`) — production gates upstream hosts that dev mode never checks, so a URL that worked in dev is rejected as `studio.gateway_url_blocked` even with a healthy handshake.
