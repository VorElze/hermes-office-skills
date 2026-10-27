---
name: live-web-release-verification
description: "Use when verifying a web service before going live publicly."
version: 1.0.0
author: codi
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [web, release, security, tls, verification]
---

# Live web release verification

Use this workflow when a web app is deployed or exposed publicly. Separate local tests from production proof; report only what was actually checked.

## When to Use

- A web service is switching from a test port/localhost to a public URL, or a new listener replaces a live service.
- A release claims HTTPS, CSRF/auth, or live-status features not yet proven on the public endpoint.
- A deliverable ZIP/archive is about to be handed over after code changes — verify it contains current sources, not just that it unzips.
- The user asks "is it live / does chat work / is it reachable publicly" — run this before answering.

Do NOT use for pure local unit-test runs with no deployment intent.

## Procedure

1. **Read the app's own workflow and acceptance criteria first.** Identify canonical public URL, service/unit, health/API routes, authentication mechanism, and allowed sensitive paths. Do not infer request field names or security design from memory; inspect the current handler/client.
2. **Establish a baseline before deploy.** Record current unit state, listener/PID, and a bounded health request. Keep the existing service running while building/testing a replacement on a separate port. For scripts, use an absolute script path or set the project working directory explicitly; a relative path from the wrong cwd can fail before the app starts and says nothing about live health.
3. **Review security findings before release.** Test each critical finding with a harmless request; sensitive source, key, configuration, logs, and report paths must not be served. Test traversal encodings as well as direct paths. Never print, copy into an artifact, or send credentials/private keys. A self-signed private key must remain outside public web roots and must never be included in a distributable ZIP.
4. **Test negative and positive auth paths.** Submit a state-changing request without the required CSRF/auth proof and expect rejection; then obtain the legitimate token exactly as the app does (including cookie jar for double-submit CSRF) and make one bounded valid request. Read the handler and frontend for exact field names and header names—do not guess them. For asynchronous chat, require a response from the target profile, not just an accepted/queued HTTP response.
5. **Verify the public live endpoint, not only localhost or a test port.** Use the actual public URL. For self-signed TLS, validate with the intended certificate trust anchor (`curl --cacert <cert>`), not `-k`, which hides certificate-chain/name failures. Check expected TLS endpoint, routes, API shape, and that plaintext HTTP is refused if HTTPS-only is intended. Do not claim public reachability from a loopback test.
6. **Switch services safely.** Back up the old unit/config, avoid two listeners claiming one port, perform the brief cutover, then immediately verify the new unit is active and the public health/API request succeeds. If verification fails, restore the known-good service; never leave an unverified replacement as the sole listener.
7. **Verify user-visible behavior.** Check the actual browser at desktop and mobile sizes for layout, console errors, and core interactions. For live status, compare API source fields with the runtime lease/state store and Kanban fallback; distinguish genuinely idle profiles from a broken detector. For avatar seating, verify each active profile is at its unique desk and every roster member has a valid slot.
8. **Package only after release QA.** Rebuild the deliverable from current sources; verify archive integrity, required files, forbidden secrets, and byte/hash parity for included files. An older ZIP passing `unzip -t` is not evidence that it contains current sources.
9. **Report with evidence and limits.** State exactly which URL, routes, status codes, profile counts, chat reply, TLS validation, browser sizes, and archive checks passed. Separate verified from unverified; never label an isolated test as live or call a queued message a successful reply.

## Reusable pitfalls

- A grep for a reply keyword can match the user's own prompt; filter to messages from the target profile before asserting an end-to-end response.
- A 403 on the positive path often means the CSRF cookie/header pair is mismatched; inspect the implementation and use the cookie jar, not a similarly named response-body token.
- An HTTP 200 on a sensitive path is a release blocker even if the main page works; verify the exact path surface before publishing.
- A running Kanban card, service, or cron is not proof of progress or correctness; inspect recent output, live endpoint behavior, and task evidence.
- A stale artifact may be structurally valid yet omit all changed files; compare its manifest and file hashes against the current source tree.
- An absent runtime lease means the profile is idle, not that status detection is wrong; compare API `source`/status with the source-of-truth lease before concluding.

## Reporting

For active multi-worker delivery, keep progress reports concise and evidence-based: local time + title; each card's ID/name/status/estimated completion; concrete files/tests/measurements since last report; blockers and action; and explicitly say “tanpa perubahan” when nothing changed. Do not report completion until the live acceptance checks and final artifact checks pass.