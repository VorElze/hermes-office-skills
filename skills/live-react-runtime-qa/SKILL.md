---
name: live-react-runtime-qa
description: "Use when a live React app disagrees with tests."
version: 0.1.0
author: <nama pemilik>, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [react, runtime, qa, playwright, debugging]
    related_skills: [dogfood]
---

# Live React Runtime QA

Use this workflow when automated tests pass but the running React application visibly fails. Establish runtime evidence before proposing a fix; this skill covers read-only state inspection and visual acceptance, not React internals beyond diagnosis.

## When to Use

- Live UI behavior differs from passing unit/integration tests.
- A transient state or transition must be measured in a running SPA.
- Source instrumentation is undesirable because the app is production-built or another worker owns the code change.

## Procedure

1. Reproduce the reported behavior in the live app and save a timestamped screenshot. If authentication is required, use the approved secret source; never print or persist credential values.
2. Inspect browser console and network errors, then identify the authoritative runtime state machine and its update cadence. Prefer existing diagnostics or DOM attributes; if unavailable, use the read-only React fiber method in `references/runtime-census.md`.
3. Sample state over a window long enough for the expected transition to occur. Record sample count, interval, per-state census, and per-entity transitions; one snapshot cannot establish that a transition never happens.
4. Compare runtime evidence to the screenshot and exact acceptance criterion. Distinguish “scene renders without errors” from “user-visible behavior works.” For assigned desk behavior, separately verify assignment count, movement/arrival, and the actual seated state; passing navigation probes or a worker's “working” metadata does not prove visual acceptance.
5. Report verified findings, bounded observation window, unresolved hypotheses, and exact next evidence needed. Keep the acceptance gate open until the target state is observed live.
6. **For performance numbers (FPS, frame time), audit the measurement environment before quoting the number.** Name the environment with every figure: host GPU present or software rasterization, dev vs production build, viewport size. A web app drawn by the browser is rendered on the *viewer's* machine — a number measured on a headless server bounds only that server's renderer, not what a visitor will experience. State which environment the claim covers; never present a server-side FPS as expected user FPS, or vice versa.

## Performance evidence

- Sample over a window (≥15s), never a single frame readout; report min/avg/max FPS plus sample count — min exposes frame-p spikes that average hides. When reading metrics from a recorded video, inspect multiple separated frames and report the exact observed FPS *and workload* (agent total, moving count, resolution, zoom); a high FPS measured while only one agent is active is not comparable to the acceptance workload — distinguish peak moving from sustained movement and flag which criterion is unmet. An owner may explicitly accept visitor-hardware evidence in place of a server benchmark; record that decision on the task and keep both figures labeled by environment.
- Diagnose the bottleneck class with a resolution sweep (e.g. 640×360 / 1280×720 / 1920×1080): FPS falling roughly inversely with pixel count = fill-rate bound (signature of software rasterization on a GPU-less host); FPS flat across resolutions = CPU/logic bound (framework overhead, simulation tick).
- An app's own FPS overlay (`requestAnimationFrame` loop, debug metrics toggles) is the preferred source when present — it reports authoritative in-engine numbers; a generic console probe is the fallback. Reusable probe: `scripts/browser_fps_probe.js` (paste into DevTools console, samples rAF deltas for 15s).
- Before judging an acceptance floor, verify the environment *can* meet it: a blank-page RAF ceiling near 60 on a GPU-less host means the renderer is the ceiling, not the app — report that as an environment constraint and ask for a decision (measure on target hardware / change floor), do not loop optimizations against a hardware wall.

## Pitfalls

- Validate the schema before counting: profile metadata such as `status=working` may look like runtime state but does not prove the agent is working in the scene.
- When behavior depends on arrival, sample long enough to include route completion; continuous `walking` does not prove movement, so compare coordinates or animation frames. If a seated transition never appears, do not infer the arrival gate is the root cause until measuring position/target/path and evaluating the exact live `maySit` predicates at arrival.
- Before claiming a transition never occurred, report the finite observation window and sample count; absence during a bounded window is evidence, not universal proof.
- A clean console or successful build is not visual acceptance; require a screenshot of the expected state.
- Keep probes read-only; do not mutate React fiber state or alter a worker-owned diff.
- Distinguish temporary access tunnels from deployment: a throwaway reverse proxy exposing an internal-only service for one measurement must be stopped after the measurement, and the owner must be told the port is unauthenticated while open — leaving it bound is an unplanned public endpoint.
- If the authoritative state mirror is reachable but a child-hook ref is not, report that boundary honestly and ask the code owner to instrument the ref locally; do not present a plausible-but-unmeasured root cause as confirmed.

## Verification

Acceptance evidence includes a timestamped live screenshot of the expected behavior, a runtime census over a stated observation window, and no relevant console/network errors. If the expected state was not observed, mark acceptance as failed or unverified, not complete.
