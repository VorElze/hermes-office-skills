---
name: live-agent-office-operations
description: Use when debugging live agent office dashboards.
version: 1.0.0
author: codi
license: MIT
metadata:
  hermes:
    tags: [agent-office, live-state, navigation, visual-verification, kanban]
    related_skills: [codi-team-dispatch, systematic-debugging]
---

# Live Agent Office Operations

## When to Use

Saat membangun atau memelihara dashboard kantor agen 2D/3D, khususnya memeriksa aktivitas live, status agen, navigasi/avatar, atau meminta implementasi ulang memakai aset yang diberikan.

Use this workflow for office dashboards (2D/3D) that visualize agent state, navigation, seating, or work activity. Keep evidence tied to the exact runtime and agent; a healthy page or plausible screenshot alone does not prove correct activity.

## Procedure

0. **Identify the exact product before describing or changing it.** Inspect the user-provided screenshot, archive, project files, and prior-session records where available; state what is directly verified versus inferred. Do not rename a project or claim its stack from visual resemblance alone. For an asset archive, inspect its README and license and inventory image/sprite formats before proposing implementation.
1. **Agree the request budget first when quota is tight.** Give a short cost estimate (main-session probes vs worker dispatches), let the operator approve a cap, prefer cheap read-only probes over browser rounds and worker dispatches, and check the cap before each build/restart or new dispatch. On `stop`/`cancel`, halt immediately — stop dispatches and project services, do only the cleanup actually requested, and report verified final state.
2. **Establish the active task graph.** Inspect the Kanban root and all decomposed children, their parent/dependency links, assignees, latest heartbeat/event/comment, retry/failure state, and worker process. Distinguish a child waiting on a prerequisite from an idle worker. Check for explicit loop/block events and operator-input waits.
3. **Build the layout yourself; the asset pack's example scene is only reference.** When a user supplies a sprite/asset archive, slice it into individual sprites (PIL region detection or manual crops), but compose the office map from scratch — the archive's demo scene must never become the layout. Verify each sliced sprite visually before placing it.
4. **Capture a baseline before editing.** Record service/build identity, HTTP response, live agent count/state, and a fresh screenshot. If onboarding obscures the canvas, close its accessible control before capture (in Hermes3D: the `[aria-label="Close onboarding"]` element — Playwright's role-based lookup misses it because it is a `div`, so click by attribute). Do not infer positions or poses from HUD counters.
5. **Prove the specific failure path.** For pathfinding, probe start and target from the same live agent snapshot. Include cases where start and goal occupy different grid cells, blocked-goal behavior, final waypoint, pixel distance, and the consumer's arrival threshold/state transition. A degenerate same-cell path (`findFree` snapping both cells to one) does not prove arrival works.
6. **Compare navigation geometry with rendered geometry.** Derive furniture bounds after the same pivot/rotation/scale transforms used by rendering (AABB of the actual GLB, not the canvas footprint). Confirm the target lies at the rendered chair and outside desk/monitor bounds. Keep 2D-map reachability separate from 3D platform/elevation/collision evidence.
7. **Instrument narrowly when needed.** Capture agent ID, state, current position, target, path length, and distance to target from the live runtime. Prefer temporary probes over speculative code changes; remove debug hooks before the final build.
8. **Change only after root cause is supported by concrete evidence.** Preserve working agents and unrelated navigation behavior. If multiple causes are plausible, run discriminating probes first rather than stacking speculative fixes.
9. **Verify in layers.** Run typecheck/build, restart the intended service, verify active process/build ID and HTTP response, then inspect a fresh visual capture. Confirm the actual named agent is sitting in the rendered chair facing the workstation, not on furniture or stuck at a platform edge. For 2D-only builds, verify sprite/map rendering and interaction without loading or requiring 3D models. Report incomplete visual checks plainly.
10. **Prove movement by measurement, not screenshot.** Sample element positions (e.g. `style.left`) twice a few hundred ms apart and show the delta; for worker-to-desk behavior check the state attribute (`mode=sit`) and the badge color against the legend. Verify the busy worker persists in its seated position across the dashboard's periodic re-render (positions must survive the refresh that rebuilds avatars).
11. **Report progress and health honestly.** Give timestamp, root/child task IDs and statuses, measurable completed/remaining acceptance criteria, concrete evidence (file:line, numbers, counts), issues/actions, and a conditional ETA range. Before saying nothing is stuck or looping, inspect heartbeat ages, explicit loop events, failures/retries, and blocked-on-input state. Fresh heartbeats prove activity, not correctness or progress. Keep interval reports concise and only fire on real change.

## Pitfalls

- **When a delegated build fails mid-task (provider outage, timeout), verify what actually changed on disk before reporting** — check file mtimes against the run window and grep for the requested feature. Prepared assets (sliced sprites) often survive while the main file is untouched; salvage those and finish in the main session rather than re-dispatching the whole task.
- **Never force a fixed height on pixel sprites.** Always render with intrinsic aspect ratio (`height:auto` + width only); forced height stretches/warps objects and reads as "berantakan" (messy) to the user. Place furniture on shared baselines (same top value for a row) to look intentional.
- **Route 2D characters through corridors, not straight lines.** A straight start→desk line cuts through walls; send the character to a corridor waypoint on the room boundary first, then to the desk. The sitting target is the chair position, offset below/in front of the desk — not the desk center.
- **Persist animated entity positions across periodic re-render.** If the dashboard rebuilds avatars on a data refresh (e.g. every 20s), stash each character's position/mode in a runtime map and restore it on rebuild, or workers teleport and the busy worker stops looking seated.
- Do not treat a build timestamp, HTTP 200, or loaded asset chunks as proof of a visual fix; they establish deployment/availability only.
- **Trace the live-state path end-to-end before blaming the renderer.** Log agent IDs and counts at every boundary (settings/config key → presence request route → gateway/proxy connection → response payload → agent mapping → rendered array → HUD header/avatars). A placeholder/demo roster or a zeroed counter means the data path returned empty or failed upstream of render — a separate probe proving data at the gateway does NOT prove the UI path carries it. Match preferences against the key the runtime actually reads (a stored preference under a differently-normalized URL is dead config), and never accept seeded/random state or demo roster as fallback for a dashboard meant to show real activity.
- **Stop at the agreed request cap.** If the operator set a cap (or complained about request spend), further probes/dispatches need a fresh agreement; re-verifying the same finding with new evidence costs more than reporting the existing one honestly.
- Do not infer 3D lounge/platform reachability from a 2D map that omits platform geometry or elevation.
- Do not label a dependency-waiting TODO as a stuck worker; verify the task graph and parent completion condition first.
- Do not call a task healthy solely because it emits heartbeats; detect explicit loop events (`block_loop_detected`) and waits-for-input as separate states.
- Do not invent precise completion percentages from intuition. Tie them to acceptance criteria and label estimates as estimates.
- Screenshot capture on continuously animating WebGL pages can time out — retry with a longer timeout or `animations="disabled"`, falling back to CDP `Page.captureScreenshot`.
