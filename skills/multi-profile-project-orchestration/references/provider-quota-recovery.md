# Provider quota & credential-pool recovery

Depth for the rate-limit/bench branch of Kanban orchestration. The always-on
rules stay in SKILL.md; use this file when a card stalls on a provider error or
the owner asks why the fleet is "kuning".

## Diagnose before reporting a quota wall

0. **Never "fix" a 429 by changing model or effort.** Model/effort are
   owner-controlled; the owner has issued this as a hard rule ("jangan pernah
   mengubah model tanpa persetujuan dari saya"). A 429 is always a
   credential/quota question — every diagnosis starts at the credential pool,
   never at `config.yaml` model fields. Swapping models to work around a limit
   also hides the real cause (an exhausted or misassigned key).
1. **Read the actual provider response status/body, not a shell pipeline exit code.** A returned `HTTP 429` proves that probe/key/model combination is currently rate-limited; it does not by itself prove a multi-day account wall. Use the response body/reset hint, timestamps, and per-key history to distinguish a short window from a longer cap. A local cooldown message is not an upstream probe result.
2. Use a bounded ladder: probe the configured model on the worker's primary key → probe a second model on that same key only to scope whether the limit is model-specific (never change the worker's configured model) → inspect all configured pool entries, sources, token lengths, cooldown metadata, and relevant `.env` overrides → fingerprint candidate secrets locally with SHA-256 only to test whether entries are genuinely distinct → probe each distinct candidate on the intended endpoint. Never expose values or prefixes. An env-seeded entry with `token_len=0` is not a usable independent backup; its environment variable may seed it again on spawn.
3. `auth reset` clears only local cooldown metadata; it cannot replenish upstream quota. Run it only when evidence points to stale local cooldown state; read back the profile pool after reset. A zero-entry reset result is not quota recovery. Do not repeatedly reset, probe, or dispatch when every distinct candidate returns 429.
4. **Confirm key independence before calling a pool a fallback.** Matching local SHA-256 fingerprints mean two labels/sources resolve to the same secret; count them as one candidate. Check `.env` assignments including `export` forms and env-seeded pool entries, but never print values. Do not copy credentials between profiles or modify another profile's pool to get around a worker limit.
5. **Probe each affected worker profile, not a coordinator's profile.** A healthy coordinator or another team's key does not establish that the worker's assigned key works; do not borrow it without explicit owner authorization. After any authorized key repair, verify the worker's own pool and probe, then spawn and confirm sustained heartbeat/progress before reporting recovery.
6. A retryable rate-limit exit may auto-requeue; a terminal exit can exhaust the card's retry budget. On repeated 429 with no distinct healthy authorized key, stop the retry storm: reclaim the worker if active, preserve the same card/worktree and evidence, record a typed transient block, and state the exact unblock condition (a successful probe using the worker's authorized key). Do not deploy or claim progress during the wait.
7. Never infer a multi-day provider limit from one paraphrased worker error. Require an actual response/reset indication and an independently observed probe; describe duration as provider-reported if present and label it unverified otherwise.

## Structural mitigation

- **Credential ownership map — verify it before blaming rotation.** The owner's
  allocation: coordinator profiles hold one primary + one backup that may
  alternate; every worker profile/team holds only its OWN key(s) for its quota
  tier; some team members deliberately share one team key. A backup key copied
  into worker pools is a leak: when the worker's primary exhausts, rotation
  falls through to a shared key that is ALSO exhausted — the classic 429 whose
  root cause is allocation, not capacity. Audit with local SHA-256 fingerprints
  only (never print key values or prefixes in chat), compare pools across
  profiles, `hermes -p <profile> auth remove anthropic <entry-id>` for foreign
  entries (back up `auth.json` first), then re-read each pool to confirm.
  Check `.env` overrides too — they may hold a stale pre-allocation key in
  `export KEY=...` form, so a `^KEY=`-only grep misses them; delete the
  override only after confirming the profile's auth pool is the intended
  source. An intentionally shared team key stays shared — confirm ownership
  with the owner before "deduplicating" it.
- **Reset windows are per-key, not per-fleet.** Each key renews on its own
  ~5-hour cadence, so a watchdog that probes all keys on one fixed interval
  either hammers green keys or misses the exact renewal moment. Track last-429
  timestamps per key and probe near each key's own observed window; keep the
  cheap path first (normal exit-75 requeue recovers for free). `auth reset`
  clears LOCAL cooldown metadata only — it does not replenish provider quota,
  so never present it as the fix for a genuinely empty key; rotate to a
  separately verified healthy key or wait out the window.
- **Two-key pool per heavy profile:** `hermes -p <profile> auth add anthropic
  --type api-key --api-key <KEY> --label <label>`. Manually added credentials
  outrank env-seeded ones. Two keys on the SAME host rotate smoothly but share
  one quota window — they buy continuity, not a second window. Point
  `ANTHROPIC_BASE_URL` per profile so both keys hit the intended endpoint.
- **Hourly healing watchdog:** `cronjob_manage` `schedule='every hour'`,
  `no_agent=true`, deterministic script that runs the reset/probe/unblock ladder
  on blocked-429 cards, SKIPS `needs_input` cards (decision requests, not
  failures), prints nothing while healthy, and emits one RAMPUNG line when the
  board empties. Pause/remove it when the workstream ends.
- **Never edit a running worker's `auth.json` in place.** The worker writes its
  own bench/cooldown state back during a run, so a concurrent coordinator write
  races and can truncate `credential_pool` to empty — the next spawn starts
  keyless. Confirm the card is NOT running first; if the write cannot wait, do a
  read-back loop (re-read 3×, rebuild from backup on mismatch) and prove a live
  chat probe immediately after.

## When the owner caps the pool (wait-out mode)

The goal shifts from capacity to waste control:

- Cut agent cron cadences down to the card's cadence, or make them `no_agent`.
- Push efficiency discipline into the card comment: one targeted RED/GREEN test
  per finding, the full suite only ONCE at the end, no re-reading the same files.
- Leave the short respawn cycle alone — ~1–3 requests per attempt is the
  cheapest probe of the reset moment.
- **Invariant that must survive:** progress comments persist across every limit
  hit, so waiting for a reset never means losing the round's context.
