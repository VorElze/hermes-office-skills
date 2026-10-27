---
name: meta-social-publishing
description: 'Use when automating Threads or Facebook Page posts via API.'
version: 1.0.0
author: amanda
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [social-media, threads, facebook, meta, api, tokens, oauth]
---

# Meta Social Publishing (Threads & Facebook Page)

## When to Use

Owner wants to sell/promote on **Threads** or a **Facebook Page** and needs
posting automated through official APIs (app creation, token acquisition,
posting, scheduling).

## Always-on rules

- **Token hygiene (office law):** tokens and app secrets never enter chat,
card comments, memory, or plain files. Server-side storage only; probes and
reports show key NAMES/labels/lengths, never values. A secret pasted in chat
is compromised → revoke + regenerate before continuing.
- **Least permission:** add only the use case/permission the task needs —
every extra permission adds review friction and slows the app going live.
- **Audit before promising:** verify a worker's real capability first (step 1)
instead of assuming from its job title.
- **Content lane ≠ publishing lane:** the content worker delivers
captions/calendars; the coordinator (or a script it controls) does the actual
publish API calls with server-side tokens.
- **Selling content shape (owner preference, standing):** a promotional
caption must SELL — product named, price stated when the listing states it
(owner often re-confirms price verbally — verify against the live listing
before publishing), checkout link at the end; no awareness-only filler.
Every selling post ships WITH a product pamphlet image, and consecutive
posts use different pamphlet CONCEPTS (not recolors) so the feed never reads
monotonous. Eyeball the rendered pamphlet once before scheduling it (price,
link, no forbidden claims) — byte checks don't read pixels.
- **Never inject a one-off post into a pre-populated FIFO queue.** If a
scheduled queue already holds numbered items, appending shifts every
slot — publish via a standalone one-shot script that takes the SAME publish
lock (`flock -n`) as the queue runner so they cannot race, and does its own
preflight → container → publish → permalink read-back → append to the
shared publish log.

## Procedure

### 1. Audit existing capability
Before answering "can worker X post to platform Y":
- Read the target profile's `SOUL.md` boundaries + `skills/` dir.
- Check credentials by key NAME only: parse `auth.json`/`.env` and print
  key names + value lengths; never print values.
- Grep all profiles for the platform API host
  (`grep -ri 'graph.facebook\|threads.net' ~/.hermes/profiles/`).
A content-only profile with no platform credentials = content lane ready,
publishing lane missing → say so plainly, then offer the setup path.

### 2. Create the Meta app (once per product)
`developers.facebook.com/apps` → **Create App** → use case **"Access the
Threads API"** → app name + email + business → Create app. Facebook Page
posting is a SEPARATE use case — add later via **Add use case**; do not
tick what the task does not need yet.

### 3. Grant permissions
**Customize use case → Permissions and features** → `+ Add`
`threads_content_publish` (`threads_basic` arrives "Ready for testing").
Add `threads_delete` too whenever any future correction/retraction is
plausible — Threads has no edit endpoint (correction = DELETE + repost), so a
token without delete strands every bad post.
Dashboard status ≠ scopes inside the token; only a live API call proves which
scopes a token actually carries.

### 4. Get the Threads token
Two routes — pick by how much you must guarantee:

**(a) User Token Generator (fast, scopes NOT guaranteed):** Settings → Add
Remove Threads Testers → account accepts (public Threads profile + Meta
developer account) → **Generate Access Token** → copy straight into
server-side storage. Grant `threads_content_publish` BEFORE generating or
publish scope is missing (live symptom: error 100/33). Scopes added in the
dashboard may still fail to arrive on regeneration (observed: `threads_delete`
missing → error code 10 on every regenerated token). Neither dashboard status
nor token byte-length proves anything.

**(b) Explicit OAuth flow (scopes guaranteed) — required for `threads_delete`
or any scope you cannot afford to miss:** save the Redirect Callback URL →
deliver App Secret server-side (never chat) → authorize link with the exact
scope list → server swaps `code` for short-lived, then `th_exchange_token` →
60-day token → refresh daily (≥24h age rule). Full recipe + pitfalls: skill
`meta-threads-oauth-lifecycle`. Do not skip the callback merely because it is
the owner's own account — own-account tokens go through (a) or (b) like any
other.

- Long-lived: up to 60 days; refresh while still valid and ≥24h old (needs `threads_basic`). Set a daily refresh job with enough safety margin before expiry, but do not infer success from the cron's `completed` status: inspect its output for a confirmed API refresh and expiry, then call `/me` or `debug_token` with the resulting token before replacing the stored token. On refresh failure, preserve the last known-good token; never overwrite it with an error response, empty value, or unvalidated candidate. Alert/reconnect while the existing token is still valid—an expired token cannot be revived by the refresh endpoint.
- Either route: server-side storage only; never chat/memory/plain files.

### 5. Get the Facebook Page token (server-side chain)
Permissions in dependency order: `pages_show_list` →
`pages_read_engagement` → `pages_manage_posts`.
Chain: short-lived user token → exchange with app secret
(`grant_type=fb_exchange_token`) → long-lived (~60d) → `GET /me/accounts` →
per-Page token. A Page token minted from a LONG-lived user token has no
expiry. Own Pages work without App Review; other people's Pages need
Business Verification + App Review. Recipes: `references/token-lifecycles.md`.

- **`hermes notify` DOES NOT EXIST** (verified 11 Okt 2026) — alert helper that calls it silently falls back to stderr, which nobody reads in cron output = total silence on failure. Correct command: `hermes send --to telegram:<chat_id>` (or `--to <platform>` for home channel); verify with `--json` (expect `"success": true`). An alert path that was never test-fired is an alert path that does not exist — always prove delivery (message_id returned) before trusting it.
- **Token-path handoff is a real integration boundary.** When PHP callback runs as `www-data` but workers read under `~/.hermes` (0700), PHP cannot atomically write the canonical file. Use a root-owned one-shot sync triggered by a dedicated `.path` unit watching a non-secret READY marker in the callback's writable drop directory; the service copies with `install -m 0600` to a temp file then `mv` atomically. Prove it with a mock token, verify `cmp`, permissions, unit `enabled+active`, then restore originals. Avoid writing a second token file without a tested sync; stale duplicate copies silently strand publishers on expired credentials.
- **Use a single canonical token path across OAuth callback, refresh job, and every publisher.** If a legacy backup copy must remain, define and test a one-way root sync from new OAuth output to canonical path. Never base API validity or 24h eligibility on file mtime alone; use `/me` health probe first.
- **mtime of a token file proves NOTHING about the token itself** (verified incident 11 Okt 2026): a token file restored/rewritten from a backup (e.g. during a handoff/wipe) resets the clock an age-check relies on, so the file looks "young" while the actual token is already expired. Never gate refresh on file mtime alone — health-probe `/me` (or `debug_token`) FIRST; only trust mtime as the >=24h refresh-skip heuristic AFTER confirming the token is actually alive.
- **Never overwrite a last-known-good token with an unverified refresh candidate.** The refresh response must be independently verified via `/me` (correct account identity, not just any `username`) BEFORE atomically replacing the stored token; on verification failure, preserve the old token untouched and alert. `os.replace`/atomic rename, never in-place truncate-then-write.
- **Expired (error 190) tokens cannot be revived by any refresh call** — refresh endpoint itself rejects them. Once a refresh cron has silently missed its window, only a manual OAuth re-run (owner click-through) recovers; design the cron so a miss is loud (exit non-zero + verified alert) rather than waiting for the 60-day cliff.

### 6. Publish + verify with measured evidence
- **Threads:** create a media container, then publish it; confirm by reading
  the user's threads back (`GET /{user_id}/threads?fields=id,text`). Verify
  endpoint paths against current docs
  (`developers.facebook.com/docs/threads`) before the first run.
- **Threads image post (pamflet):** container `media_type=IMAGE` with
  `image_url` = a PUBLICLY reachable HTTPS URL — the API fetches the image
  itself, so local paths/private dirs fail. Host assets in a dedicated dir
  served by its own Alias + `<Location> ProxyPass !` exemption (a catch-all
  `ProxyPass /` vhost swallows the path), copy PNGs in as root:www-data 644,
  then preflight `curl -o /dev/null -w '%{http_code} %{size_download}'` →
  require 200 AND size equal to the local file before scheduling any publish.
  Image containers need a longer processing wait than text (~15s verified
  working; ~10s was the earlier guidance — take the longer figure).
- **Facebook:** `POST graph.facebook.com/v26.0/{page_id}/feed` with
  `message` (+ optional `link`) → returns `{"id": ...}`. Schedule with
  `published=false` + `scheduled_publish_time` (window per current docs).
- **Pin the Graph version in every URL** — an unversioned call silently
  falls back to the oldest live version and breaks without an error.
- Evidence = returned post ID (and the read-back), reported to the owner.
  Re-probe token health before any scheduled publish: error 190 =
  "reconnect required", never retryable.

### 7. Schedule + hand off content
Coordinator stores tokens server-side; the content worker (social-media) delivers caption + calendar batches; a coordinator-run script or cron
performs publishes and reports post IDs.
- **Slot timing first, calendar second:** research platform + locale timing
  before fixing the calendar — decision recipe in
  `references/posting-timing.md`; embed the slot rationale in the calendar so
  the owner can audit it.
- **Timed publish = one-shot cron:** `hermes cron create 'M H D MON *' --name
  <unique> --script <basename.sh> --no-agent --deliver local
  --failure-deliver origin` (script basename resolves under the profile's
  `scripts/` dir). The publish script preflights everything itself: caption
  byte-count ≤500 (`wc -c`, abort on fail), image HTTP 200, then container →
  publish → permalink read-back, appending the permalink to a log the
  coordinator reads when reporting.
- For selling campaigns: **hard-sell captions and product pamphlets originate
  from the marketing specialist**; the social specialist adapts them to channel + slot. Chain the
cards marketing → social-media and verify deliverable paths exist before
  reporting.

## Pitfalls

- **Do not edit auto-generated vhosts by hand** (a conf marked "do not edit
  by hand" regenerates away) — and it is moot: the tester token flow needs
  no redirect URI.
- **"Ready for testing" ≠ public:** test tokens work only for added testers;
  publishing to the general audience needs the app live.
- **Never treat a token as alive:** password change, app removal, lost Page
  role, or secret reset invalidates it → probe with `debug_token` first,
  treat 190 as reconnect. Error 190 after the documented expiry is the normal
  end of the chain — no refresh path revives it. **Evidence hierarchy:** a
  token file's mtime, a cron's `completed` status, and a token's byte-length
  each prove NOTHING about validity; only a live API call (`/me` or
  `debug_token`) with that token does. A refresh cron that skips or fails must
  never overwrite the last known-good token — preserve it and alert while the
  old one still works, because once expiry passes the owner is forced into a
  manual reconnect (the exact friction the automation was built to avoid).
- **Token lifetimes drift:** docs warn lifetimes may change; detect expiry
  from the API (`expires_at`), not from memory of the docs.
- **Validate the caption byte budget inside the publish script, not after:**
  Threads caps 500 characters and UTF-8 emoji count as multiple bytes; `wc -c`
  on the exact payload is a conservative check that can never exceed the real
  limit. Abort before creating the container — a rejected container burns the
  firing cron slot with nothing published.
