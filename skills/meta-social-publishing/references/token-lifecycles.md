# Meta token lifecycles & exchange recipes

Server-side only: exchanges below include the app secret — run them from the
server, never from client code. Report only token names/status, never values.

## Threads

| Token | Lifetime | How obtained |
|---|---|---|
| User (User Token Generator) | 60 days | App → Threads use case → Settings → tester accepted → Generate Access Token |
| Short-lived (OAuth code flow) | ~1 hour | `threads.net/oauth/authorize` + redirect callback (only for non-tester users) |

- Exchange short → long (server-side):
  `GET https://graph.threads.net/v1.0/access_token?grant_type=th_exchange_token&client_secret=<SECRET>&access_token=<SHORT>`
- Refresh (must be ≥24h old, not expired, app has `threads_basic`):
  `GET https://graph.threads.net/v1.0/refresh_access_token?grant_type=th_refresh_token&access_token=<LONG>`
  → new 60-day validity from refresh date. Not refreshed within 60 days = dead.
- Private-profile grants last 90 days.

## Facebook

| Token | Lifetime | How obtained |
|---|---|---|
| User short-lived | ~1–2 hours | Facebook Login / Graph Explorer |
| User long-lived | ~60 days | exchange below, server-side |
| Page (from long-lived user token) | no expiry | `GET /me/accounts` |
| Page (from short-lived user token) | ~1–2 hours | same call with short token — avoid |

Chain:
```
# 1. short -> long user token
GET graph.facebook.com/v26.0/oauth/access_token?grant_type=fb_exchange_token&client_id=<APP_ID>&client_secret=<SECRET>&fb_exchange_token=<SHORT>

# 2. Page tokens (no expiry when minted this way)
GET graph.facebook.com/v26.0/me/accounts?fields=id,name,access_token,tasks&access_token=<LONG_USER_TOKEN>
```

- Health probe before any scheduled publish:
  `GET /debug_token?input_token=<TOKEN>&access_token=<APP_ID>|<APP_SECRET>`
  → `is_valid`, `expires_at` (0 = never), scopes. Error 190 on any call =
  reconnect required (password change, app removed, Page role lost, secret
  reset) — not retryable.
- Permissions (dependency order): `pages_show_list` →
  `pages_read_engagement` → `pages_manage_posts`.

## Publishing endpoints

- Facebook: `POST graph.facebook.com/v26.0/{page_id}/feed` — `message`,
  optional `link`; schedule: `published=false` + `scheduled_publish_time`
  (window per current docs; older docs say 30 days, newer say 75 — check).
- Threads: create media container (`POST /{user_id}/threads`), then
  `POST /{user_id}/threads_publish` with the `creation_id`; confirm paths in
  `developers.facebook.com/docs/threads` before first run.
- Pin the Graph API version in every URL (v26.0 as of writing); unversioned
  calls silently fall back to the oldest live version.
