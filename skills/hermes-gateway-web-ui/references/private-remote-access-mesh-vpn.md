# Private remote access to a loopback web UI (mesh VPN / Tailscale)

Depth reference for making a loopback-bound web UI reachable from a phone or
laptop on another physical network — without publishing the port publicly.

## Decision table

| Situation | Method | Exposure |
|---|---|---|
| Client can reach the host's LAN IP | Bind `0.0.0.0` on the LAN + host firewall | LAN only |
| Client is outside the LAN, owner has a tailnet | Tailscale Serve → `127.0.0.1:port` | Private overlay only |
| Client is outside everything, SSH reachable | SSH local port forward | Private only |
| No overlay, no SSH, owner wants it anyway | Public reverse proxy | **Public — needs explicit approval** |

Never open the app port in a public firewall to satisfy a "remote access"
request; the overlay path is strictly better and is what the owner asked for
when they say "saya berada di luar jaringan".

## Server-side Tailscale install

Use the signed OS repository, not a `curl | sh` bootstrap:

```bash
curl -fsSL https://pkgs.tailscale.com/stable/ubuntu/<codename>.noarmor.gpg \
  -o /tmp/tailscale-archive-keyring.gpg
install -m 0644 /tmp/tailscale-archive-keyring.gpg /usr/share/keyrings/tailscale-archive-keyring.gpg
curl -fsSL https://pkgs.tailscale.com/stable/ubuntu/<codename>.tailscale-keyring.list \
  -o /etc/apt/sources.list.d/tailscale.list
apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get install -y tailscale
systemctl enable --now tailscaled
```

`<codename>` must match the host's `/etc/os-release` (`jammy` on 22.04) — a
mismatched suite path is a silent 404 that looks like "no network access".

## Device approval is a user gate

`tailscale up` returns a login URL and exits; the server joins only after the
OWNER approves that device on their own tailnet account.

- Run `tailscale up --hostname=<name>` in a **persistent** process (the URL
  expires, and a foreground `tailscale up` that gets cancelled prints
  `context canceled` and yields nothing).
- Hand the URL to the owner and wait — do not poll-loop or substitute an auth
  key unless the owner explicitly authorizes that method.
- Approval proof: `tailscale status` lists the device as connected and
  `tailscale ip -4` returns a 100.x address (not "NeedsLogin").

## Exposing a loopback app to the tailnet

Serve (not Funnel) forwards a tailnet-only URL to a local port:

```bash
tailscale serve --help          # syntax varies by version — read it first
tailscale serve --bg 8787       # example shape; confirm flags before running
tailscale serve status          # verify what is actually published
```

- **Serve = tailnet-only. Funnel = public internet.** Never enable Funnel for
  a private-access request; the app may have no authentication and would be
  world-reachable.
- The app must stay bound to `127.0.0.1` — Serve proxies from the host, so
  widening the app's own bind defeats the purpose.
- Keep the app's own authentication enabled; the overlay authenticates
  devices, not users of the app.

## Verification order

1. App answers on loopback from the server (`curl -sS http://127.0.0.1:<port>/`).
2. `ss -ltnp | grep <port>` shows the listener still on `127.0.0.1`.
3. `tailscale status` shows server and client online in the same tailnet.
4. `tailscale serve status` shows the expected mapping.
5. The OWNER opens the generated private URL from the client device and
   confirms the page renders.

Only after step 5 can remote access be reported as working — steps 1–4 prove
configuration, step 5 proves reachability.
