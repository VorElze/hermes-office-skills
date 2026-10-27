---
name: smarthome-device-integration
description: "Use when connecting Hermes to smart-home device ecosystems."
version: 1.0.0
author: codi
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [smarthome, tuya, google-home, smartthings, iot, api]
---

# Smart-home integration

## When to Use

Use when the user wants Hermes to see or control home devices (lights, AC,
sensors) through any ecosystem: Google Home, Bardi Smart Home, Tuya/Smart Life,
SmartThings — including diagnosing why an account link fails.

## Route decision table

Re-verify each row against CURRENT official vendor docs before repeating it —
vendor access rules change often. Never assert access from memory.

| Ecosystem | Server-side route from a Linux host? | Basis |
|---|---|---|
| Google Home | **No.** Home APIs are Android (Kotlin) / iOS (Swift) client libraries; Smart Home Actions is the reverse direction (Google calls YOUR API); Device Access covers Nest devices only. Enabling the API in Cloud Console grants no connection by itself. | official Google developer docs |
| Tuya, incl. white-label apps (Bardi) | **Only if the console project's account link accepts the user's app.** `Link Tuya App Account` accepts Tuya Smart / Smart Life only; white-label apps run in a separate account namespace. | official Tuya docs |
| Bardi directly | **No public user API found.** Ask the vendor (support contact on the app-store listing). | vendor |
| SmartThings | **Yes** — REST API `GET /v1/devices`, `POST /v1/devices/{id}/commands`; auth via PAT (short-lived) or Service Integration OAuth for permanent use. Recommended route, **not yet verified end-to-end in this environment**. | official SmartThings docs |

## Procedure

1. **Identify the stack from the user's screenshots** (app names, device list)
   before proposing any route.
2. Confirm the route with a search of OFFICIAL vendor developer docs.
3. Account/console setup is the user's step (they hold the logins) — guide
   screen-by-screen and read their screenshots for exact state; you never log
   in yourself.
4. **Read-only first:** list devices + status, prove with real command output
   before claiming anything works.
5. Credentials land in `.env` on the server only — never echoed, never in
   chat, cards, or panels.
6. Every CONTROL action (switch, temperature, brightness) needs explicit
   approval first; read-only probes don't.
7. Label each capability honestly: verified working / configured-but-untested /
   vendor-must-confirm.

## Pitfalls

- **Same email across two Tuya-family apps proves nothing.** Accounts are
  isolated per namespace and data center; differing device lists = different
  account space. Stop there — do NOT advise pairing devices into another app to
  "make them show up"; that breaks the working voice/app setup and is
  effectively irreversible.
- **Instant "QR code expired" means wrong app or wrong data center, not slow
  scanning.** The console's own text names the accepted apps and region
  precondition — read it back to the user verbatim.
- **Tuya account → data-center mapping is registration-based, not
  location-based.** Consult the vendor's mapping table instead of inferring the
  region from where the user lives.
- **Never present an untested route as validated.** Mark it
  "recommended, untested here" with the doc source, and verify read-only before
  any control claim.
- **The user's exact post-action error text/screenshot is the primary
  diagnostic** for account/region mismatches — ask for it rather than guessing
  the cause.
