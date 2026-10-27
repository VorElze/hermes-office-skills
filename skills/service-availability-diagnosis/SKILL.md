---
name: service-availability-diagnosis
description: 'Use when a site appears down: prove path vs outage first.'
version: 1.0.0
author: codi
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [networking, diagnosis, monitoring, availability, blackhole]
---

# Service availability diagnosis: SITE vs PATH

When a probe from our host fails, "the service is down" is the LAST thing to
claim, not the first. A failed local probe only proves OUR path failed. The
classic failure: reporting a site as down while it serves HTTP 200 to the rest
of the world, blaming the school/hosting for a problem on our side.

## When to Use
Use when a remote site/service probe fails or reports "down", when building
or reviewing an availability monitor, or when deciding whether to alert the
site owner about an outage. Remember: local failure proves the PATH, not the
site.

## Diagnosis procedure (in order)

1. **Measure locally with evidence**: bounded `curl` (see pitfall below), record
   DNS/IP, TCP/HTTP result, timestamp. One failed local probe = "our path
   failed", never "site down".
2. **Get independent external vantage points.** Multi-node HTTP checker:
   ```bash
   curl -sS -H 'Accept: application/json' \
     'https://check-host.net/check-http?host=<url-encoded-https-url>&max_nodes=6'
   # take request_id, wait ~12-20s, then:
   curl -sS -H 'Accept: application/json' \
     'https://check-host.net/check-result/<request_id>'
   ```
   Count nodes by outcome: success(200), failure, **and pending/no-data** —
   only nodes that actually returned a sample count as evidence.
3. **Classify with four states, not two**:
   - `UP` — local probe succeeds.
   - `PATH_BLOCKED` — local fails, external nodes 200 → the site is healthy;
     report "our route/ASN is blocked", never blame the site owner.
   - `SITE_DOWN_SUSPECTED` — local fails AND multiple independent external
     samples fail → only now suspect a real outage (verify once more before
     reporting; check DNS still answers as a supporting signal).
   - `INCONCLUSIVE` — the external checker returned no usable samples (API
     error/403/rate-limit). Checker failure ≠ site failure; claim nothing,
     re-measure later.
4. **Prove a path/blackhole diagnosis with packets**: `tcpdump -ni <iface>
   'host <ip>'` while probing — SYN leaves our interface, retransmits, no
   SYN-ACK *and* no RST = blackhole/dropped, not refused. Narrow the blast
   radius: probe the rest of the target subnet and a control IP on an
   unrelated network; if the whole /24 is silent but controls are fine, the
   fault is the route to that range, not the single host. State ASN/provider
   attribution as a HYPOTHESIS unless the evidence isolates that segment.
5. **Respect intermittency**: sample success/failure has a time window, not a
   verdict. Report the observed range (e.g. "reachable 09:04–09:26, blocked
   since ~09:50") instead of generalizing from one sample; re-measure before
   calling a condition persistent.

## Availability monitor pattern

A cron probe that reports "DOWN" on local failure will eventually slander a
healthy service. Reuse `scripts/availability_monitor.py` (adapt HOST/STATE
paths):

- Emit output **only on state transitions** (compare persisted state file;
  same state → empty stdout, exit 0) so chat gets alerts, not spam.
- Classify with the four states above; `INCONCLUSIVE` must say "claim
  nothing, re-measure" — an alerting monitor must be allowed to say "I don't
  know".
- Message must name the audience: a PATH_BLOCKED alert should explicitly say
  NOT to report a site outage to the owner.
- **Verify the monitor by running it twice**: run 1 must produce a
  classification backed by the evidence in its own message; run 2 (no state
  change) must be silent. Reset the state file before testing so the
  transition path is exercised.

## Pitfalls

- **Python HTTP clients can fail where curl succeeds.** Sites/WAFs may reset
  or 403 `urllib` while `curl` (or a browser UA) gets 200 — probe with bounded
  `/usr/bin/curl`, or send a browser `User-Agent` + correct `Accept` headers
  to JSON APIs (e.g. DoH resolvers need `Accept: application/dns-json`,
  check-host 403s a default urllib UA). Never conclude "site down" from a
  client-fingerprint failure.
- **Failed anonymity/VPN hops prove nothing about the site.** When testing
  alternate routes (Tor, consumer VPN/WARP, public proxies) for reachability:
  if the hop works for general sites (google 200) but not the target, the
  target likely filters by exit reputation/ASN — that is a property of the
  target's firewall, not evidence the site is down or that the route class is
  universally broken. Record per-target results; don't generalize to "X never
  works".
- **Don't route authenticated traffic through random public relays** — a
  generic proxy is a MITM by construction; never forward cookies/passwords
  through one. Real alternates for blocked authenticated flows: a jump host
  on a non-filtered ASN, or the provider/ISP fixing the route.
- **Verify a claimed alternate path with a target-specific probe**: HTTP 200
  on the actual URL (plus egress IP evidence), not "installed and connected".
  A tunnel that carries google traffic but not the target has not passed.

## Evidence bar for reports

Every availability claim to the user carries: timestamp, local result,
external node tally (success/failed/pending), and the observation window.
Measured vs unmeasured stays explicit — the user reviews evidence, not
conclusions.
