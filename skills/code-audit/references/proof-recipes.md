# Proof recipes

Standing probes for the audit procedure — each maps to one class of claim.
Run against an extracted local copy only; probes are read-only or write only
inside a scratch copy. Keep actual output for the report's Evidence field.

## 1. Authorization coverage (default config)

Claim: all writes require a token when configured.

1. Read `.env.example`; an empty auth-token default means the default install is open.
2. Enumerate each HTTP and WebSocket route; identify guards on both the router and endpoint. A route is guarded only if a dependency or middleware actually executes for that route. WebSockets need explicit handling because they do not follow normal HTTP dependency middleware.
3. Use TestClient: call `init_db()` if startup hooks do not run, then hit a destructive write with no credentials. A 2xx response proves the issue; do not infer from code alone if a safe local reproduction is available.
4. When auditing a guard that was *added*, connect to each WebSocket route
   too — a router-level dependency whose parameters are HTTP-only breaks
   the WebSocket handshake with a TypeError regardless of credentials, and
   a suite with no WebSocket test stays green over that break.

## 2. Client-supplied paths → local file disclosure

Claim: API inputs cannot make the server serve paths outside its storage root.

1. Trace request fields (`source_path`, filenames, batch items) to filesystem operations and file-serving handlers.
2. Chain ingestion to serving in TestClient: submit a batch with a safe local test path outside storage (for example a synthetic fixture under scratch), then GET the preview endpoint. Compare served bytes to the fixture. A match proves file disclosure.
3. Probe static routes with `../`, encoded traversal and nested prefixes. A 200 returning SPA fallback is not a traversal; compare response bytes to a local test fixture.

## 3. Fallback reuse (media/subprocess pipelines)

Claim: media processing degrades gracefully when an option is unsupported.

1. Find the primary command's distinguishing flag and check whether the fallback reuses the same argument list; identical unsupported arguments mean the fallback cannot work.
2. Check the actual binary's help and run a minimal command with the option, then run a supported inline/control equivalent. The control distinguishes unsupported option from a generally broken command.
3. Run the targeted render test. Quote the actual FFmpeg build/version and exact failing option, not a generic claim that FFmpeg is broken.

## 4. Queue / background-work dispatch proof

Claim: production uses a durable queue.

1. Search application code for actual dispatch call sites: `.delay(`, `apply_async`, `send_task` (exclude the queue's own docs and definitions).
2. If a worker service exists but dispatch has zero call sites, determine which code path executes work instead (`BackgroundTasks`, thread pool, in-process queue).
3. Find whether concurrency limits are actually read by an executor. A computed `max_parallel_*` field unused by scheduling is not a limit.
4. For each advertised config key, search writers and readers separately; a stored setting without an execution-path reader is a dead feature.

## 5. Retention / resource leaks

Claim: disk usage is bounded.

1. Locate deletion and cleanup operations; if they occur only on error paths, successful jobs may leak artifacts.
2. Enumerate per-job artifacts in the pipeline (source, normalized intermediate, extracted audio, transcript/scores, output, thumbnails) and identify cleanup for each.
3. Look for TTL, scheduled cleanup, or a retention knob. For large intermediate media, estimate storage growth from realistic job volume.

## 6. Error-path correctness in size/quota checks

Review rejection branches in execution order. If a file is unlinked and then `stat()`ed to format the error, reproduce with a synthetic file just over the limit; report the actual exception class. Capture size before deletion and use it in the message.

## 7. Benchmark the hot path with scaled synthetic input

1. Count candidate windows and determine nested/per-unit work before timing.
2. Generate synthetic input at realistic duration; print segment count, window count and elapsed time at small and target scales.
3. Report measured times and careful extrapolation, identifying the dominant per-window operations. Do not label extrapolated work as measured.

## 8. Test suite and failure classification

Run `python -m pytest -q -p no:cacheprovider` from the project root (or backend root if configured there). Classify failures:

- Missing module, incompatible interpreter/wheel or absent system binary: environment issue, not a product bug by itself.
- Test imports a dependency absent from project test/dev requirements: packaging/test reproducibility finding.
- Assertion failure with dependencies present: investigate as a product bug.

Use a disposable virtual environment in scratch; do not install foreign project pins into the system interpreter. Run targeted tests after installing only missing dev dependencies, and clearly state the subset and exclusions.

## 9. Re-audit after claimed fixes (downstream review card)

Claim: the implementer's fix closed the findings and introduced no regressions.

1. Take scope from the parent card's acceptance criteria, not the narrative.
   Re-extract the delivered artifact and re-run the whole suite from it;
   compare the pass/fail/skip tally against the baseline recorded in the
   original audit, and keep environment failures classified the same way.
2. For each claimed fix, find the regression test and judge whether it can
   fail: a test that would pass with the bug still present proves nothing.
3. Probe what the fix *touched* but the suite does not cover — an added
   router-level guard against a WebSocket route; a promised error code
   (the docstring says 503, the route returns 500); a concurrency path.
   `TestClient.websocket_connect` and `raise_server_exceptions=False` are
   enough to expose both.
4. Probe any control keyed on identity: for a rate limiter, replay past
   the limit once keyed normally (expect 429) and once with the identity
   header rotated per request (repeated 2xx proves the header is spoofable
   and the limit is not enforced).
5. Record failed verdict transitions: `kanban_request_changes` is refused
   unless the active run was claimed from the `review` lane, and a card
   already `done` cannot be reopened as a review. Findings still belong in
   a durable comment on the card; routing the rework becomes a separate
   decision.
