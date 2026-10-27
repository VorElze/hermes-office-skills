---
name: hermes-stream-stale-diagnosis
description: "Use when Hermes reports stale provider streams or timeouts."
version: 1.0.0
author: office
license: MIT
metadata:
  hermes:
    tags: [hermes, debugging, provider, timeout, stream, configuration]
    related_skills: [hermes-agent]
---

# Diagnose Hermes stream-stale failures

## When to Use

Load this when Hermes reports `Stream stale for Ns`, `No response from provider after Ns`,
`ReadError('Error reading post')`, or `Could not open a stream`. Skip it for Telegram
`ConnectTimeout` (network path, not provider stream) — check gateway transport logs instead.

## Proven diagnosis pattern

- Inspect per-profile request dumps (`sessions/request_dump_*.json`), not just gateway logs.
  Dumps can identify independent `rate_limit_error` / HTTP 429 failures.
- A measured coordinator request was 1,709,991 bytes with 1,121 messages. Replaying it against the
  configured endpoint returned SSE `message_start` after 37.7s. An explicit 120s timeout can
  override Hermes' context-aware default for large prompts; resolve the effective timeout with
  `hermes_cli.timeouts.get_provider_stale_timeout`, not by reading YAML alone.
- Distinguish 429 short-window limits from a slow prefill; they require separate mitigations.
  Hermes classifier already honors `retry_after` and has fallback classification.

## Safe prevention changes

Use CLI only; never edit YAML by hand:

```bash
HERMES_HOME=~/.hermes/profiles/<profile> hermes config set providers.anthropic.request_timeout_seconds 300
HERMES_HOME=~/.hermes/profiles/<profile> hermes config set providers.anthropic.stale_timeout_seconds 300
HERMES_HOME=~/.hermes/profiles/<profile> hermes config set compression.threshold_tokens 60000
```

Repeat for each intended profile. For global settings set `HERMES_HOME=~/.hermes` explicitly;
the active session's default HERMES_HOME may be a profile home.

Verify effective values by calling the real timeout resolver with the same `HERMES_HOME` and verify
compression via config loader. The multiplexer watches profile `config.yaml`/`.env` signatures and
reconciles changed profiles; confirm `Re-scanned profile` in gateway logs before considering a
restart. Do not restart a live gateway without need/authorization.

## Avoid unsafe fallback assumptions

`fallback_providers: []` means no fallback. Adding one through `hermes fallback add` uses an
interactive provider/model picker (`_require_tty`) and needs a valid credential for a distinct
provider. Never assume an env key exists from an old session or config comment; check only key names
and never print values. A fallback using the same shared rate-limited API key may not relieve 429s.
Do not configure fallback until the alternate provider credential and suitable model are verified.

## Pitfalls

- Correct Anthropic-compatible route in this deployment: `/anthropic/v1/messages`.
- Old request dumps can contain expired Authorization tokens; use a currently valid secret from
  the appropriate secret store, without logging it.
- Telegram `ConnectTimeout` is a separate network-path issue; check gateway recovery logs, don't
  confuse it with model provider timeout or API rate-limit errors.