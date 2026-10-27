---
name: chat-silence-diagnosis
description: "Use when the assistant is silent or late on a chat channel."
version: 1.0.0
author: codi
license: MIT
metadata:
  hermes:
    tags: [telegram, gateway, diagnosis, latency, rate-limit, troubleshooting]
    related_skills: [kanban-rate-limit-resilience, systematic-debugging]
---

# Chat silence diagnosis

When the user says "kenapa kamu terdiam?" / "you never replied", prove WHICH
layer stalled before saying anything. Three independent layers can each cause
apparent silence — inbound transport, model API, outbound send — and they have
different fixes. A reply that is late is not a reply that was lost.

## When to Use

- The user says the assistant is silent, unresponsive, or "terdiam" on a chat
  channel (Telegram, TUI, or any messaging platform).
- A reply arrived far later than the message was sent and the user asks why.
- The user re-asks the same complaint within one incident — re-verify state
  instead of repeating the previous diagnosis.
- Pre-emptive: before claiming "your message never arrived".

## Procedure (in order — each step narrows the cause)

### 0. Profile-level silence (worker/clone silent while gateway lives)

When the complaint targets a specific profile ("saya chat codi, dia terdiam")
and NOT the gateway itself, skip straight to proving the profile is alive by
MESSAGE GROWTH, not by process existence:

```bash
# 1) did MY message arrive? (role='user' rows, newest first)
python3 -c "import sqlite3,time; c=sqlite3.connect('~/.hermes/profiles/<profile>/state.db'); now=time.time(); [print(id, int(now-ts),'s', pmid, repr(body)[:120]) for id,ts,pmid,body in c.execute(\"select id,timestamp,platform_message_id,substr(content,1,120) from messages where role='user' order by timestamp desc limit 5\") ]"
# 2) is it producing? sample count twice ~70s apart — growth = alive
python3 -c "import sqlite3,time; c=sqlite3.connect('...state.db'); print(c.execute('select count(*) from messages').fetchone()[0], int(time.time()-c.execute('select max(timestamp) from messages').fetchone()[0]))"  # run, wait 70s, run again
```

- **Growth (+N messages, last_age < ~60s) = service ALIVE, reply is queued**,
  not dead. The single most common false alarm: one session = one turn, so
  while the profile is finishing an earlier long job, an incoming chat reply
  waits its turn. Explain the queue with evidence instead of restarting.
  (No process named after the profile ≠ dead either — the gateway multiplexes;
  check PID 1336002-class gateway plus state.db, never `ps | grep <profile>` alone.)
- **Check whether the user's own message exists** (id + platform_message_id
  above). Present-but-unanswered = queued; absent = transport (go to step 1).
- **Duplicate platform_message_id rows** (same pmid, two ids) = retry
  duplication, harmless — note it, don't treat as double-processing.
- Sample periods: `messages` older than ~10 min with no growth while a turn
  should be running = then continue to steps 2-3 (API layer).

### 1. Did the message reach the gateway at all?

```bash
grep -a 'inbound message' ~/.hermes/profiles/<profile>/logs/gateway.log | tail -25
```

- **Per-profile gateway.log, NOT the global `~/.hermes/logs/gateway.log`**
  — inbound chat lines live in the profile's log; the global one mostly holds
  plugin/network lines and can return zero hits (grep the wrong file and you
  will wrongly conclude every message vanished).
- Present with timestamps: this is the evidence that messages arrived. If a
  message is genuinely absent here, THEN investigate transport (held/redispatch
  lines, adapter rebuild).
- `polling heartbeat: N update(s) queued but not consumed (stuck probe)` =
  inbound DID arrive but the adapter loop is not dispatching it — diagnose as a
  transport/rebuild stall (step 4), not as a missing message.

### 2. Were replies actually produced?

```bash
grep -a 'response ready' ~/.hermes/profiles/<profile>/logs/gateway.log | tail
```

Compare last `response ready` time vs last `inbound message` time. The gap IS
the user's perceived silence — quote both timestamps in the report.

### 3. Check the model API layer (the usual culprit)

For proxy-backed provider errors, distinguish transient upstream failures from credential faults before changing anything. Read the profile's retry settings and auth pool metadata without printing secret values; preserve the configured model and effort. For a bounded one-token probe, read keys from the profile auth store directly into process memory and send one request per distinct credential to its configured `base_url`, with `max_tokens: 1`; never put keys in command arguments, output, files, or logs. Space probes briefly and report each HTTP status with a timestamp. A 502/5xx or `upstream stream error` is transient endpoint/upstream evidence, not proof of invalid credentials; matching 5xx responses from multiple credentials on the same endpoint implicate their shared path, not the individual keys. Do not rotate, reorder, reset, or replace credentials based on a lone 5xx sample. If the bounded probe remains 5xx, report the provider-path escalation as unresolved and re-probe later; do not claim the issue is fixed until a real API call succeeds.


```bash
grep -aE '429|RateLimitError|Retrying API call' ~/.hermes/profiles/<profile>/logs/errors.log | grep <date> | tail
```

- `Retrying API call in 600s (attempt 1/3)` means silence is **expected, not a
  hang**: default rate-limit backoff is 600s per attempt, up to 3 attempts.
  Report the remaining wait as an ETA, do not keep polling.
- `Stream stale for 120s ... Killing connection` = a hung upstream stream.
  It retries only a bounded number of times: after ~6 consecutive stale attempts
  the loop dies with `Non-retryable client error: Provider has been
  unresponsive ... Switch models or start a new session` and the turn ends
  without a reply. Count stale lines since the last successful `API call #`
  (`grep -a 'Stream stale' .../agent.log | grep <date> | wc -l`); a rising
  count means the provider is dead for that model/session, not that progress
  is slow — recommend a fresh session rather than waiting, and NEVER a model
  switch: the abort text itself suggests "Switch models or start a new
  session", but model/effort changes require explicit owner approval, so a new
  session on the SAME model is the only autonomous remedy. A /new also does
  not repair the provider path — it only clears the aborted turn.
- Behind a proxy endpoint, also read the timeout knobs:
  `providers.<p>.stale_timeout_seconds` / `request_timeout_seconds` (grep the
  profile config — current fleet setting 120/120; earlier 300/300 produced
  minutes of mute per attempt). Every attempt against a stream the
  proxy holds open burns the full stale window before the retry, so a
  provider that hangs (not 429s) turns into MINUTES of apparent per-turn
  silence with no error in chat. When stale counts rise while the proxy
  answers 200 on a probe, the diagnosis is "provider hangs → each attempt
  waits out stale_timeout", not "gateway dead" — report the wait as ETA and
  name the knob. Changing these knobs fleet-wide still needs owner approval
  first; once approved, set both keys on EVERY operational profile including
  `default` and verify by per-profile readback plus a zero-`Stream stale`
  window in `errors.log`.
  - A card crash landing at EXACTLY the old stale window (last heartbeat → worker exit = `stale_timeout_seconds`) is the watchdog killing a stream-hung run — but compare the run's SPAWN time against your config-change time before crediting your fix: config is read when the worker spawns, so a run spawned before the change keeps the OLD budget and dies once at the old point, while the dispatcher's auto-retry spawns the next run on the new config. Confirm the fix by watching that next run pass the former crash point (heartbeat continuity + zero stale lines), not by re-rolling the knob or re-diagnosing the crash as a new failure.
- If no 429, check whether a turn is STILL RUNNING rather than dead:
  `grep -a 'API call #' .../logs/agent.log | tail` — recent timestamps mean
  healthy, just slow. `Turn ended` after the last inbound = turn finished;
  absence after inbound = still in flight.

### 4. Network/transport layer (secondary — verify before blaming it)

```bash
grep -acE 'ConnectTimeout' ~/.hermes/logs/gateway.log   # count
# adapter rebuilds = fatal, they delay polling:
grep -aE 'Fatal telegram adapter error|queued for background reconnection' ~/.hermes/logs/gateway.log | tail
```

Telegram `ConnectTimeout` flapping is common and self-healing — messages still
arrive through it (proved by step 1). Only cite it as the cause when step 1
shows messages MISSING or held. An adapter rebuild (`updater.stop() did not
finish`) delays polling but queues rather than drops updates.

### 5. Check for send-side blocks (only when producing but not delivering)

`Forbidden: bot was blocked by the user` on startup notifications = user
blocked the bot at some point; harmless for inbound, fatal for outbound. Note
it, ask the user to unblock — do not treat it as the cause of missed messages
that DID get inbound-logged.

### 6. Report format the user expects

Evidence-first: a compact timeline (inbound vs response-ready timestamps),
root cause named with its log line quoted, ETA or current state, then remedy
if any. Separate confirmed facts from hypothesis.

## Pitfalls

- **Never diagnose from one log.** Inbound lives in profile gateway.log,
  API errors in errors.log, turn progress in agent.log, network in global
  gateway.log — grep a single file and you get a plausible wrong story.
- **Network noise ≠ model failure.** Telegram ConnectTimeout is the transport
  to Telegram, not the LLM (see kanban-rate-limit-resilience); but dismissing
  it as "just noise" without step 1 is equally wrong — prove messages arrived.
- **A rate-limited turn is not a dead turn.** While `Retrying API call in
  600s` is pending, the turn holds the session and will resume; restarting the
  gateway or re-sending the message mid-backoff wastes quota and duplicates work.
- **Don't declare a turn hung without a timestamp.** Run `date`, then compare
  to the newest `API call #` line; API latencies of 20–70s per call are normal
  for large-context turns, and multi-call turns legitimately run minutes.
- **Don't restate the same diagnosis twice** if the user re-asks within the
  same incident — check whether the earlier backoff/rebuild already resolved
  (look for `recovered` / `confirmed healthy` lines) before repeating the old
  cause.
- **Don't judge liveness from `ps`.** A profile can be fully busy with zero
  processes matching its name (gateway hosts the turn); message-count growth
  over a ~70s window is the only reliable liveness proof.