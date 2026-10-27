---
name: hermes-team-dashboard
description: "Use when building a live Hermes worker status panel."
version: 1.0.0
author: codi
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [dashboard, panel, realtime, monitoring, systemd, web]
---

# Hermes team status panel

## When to Use

Use when the user asks to see who on the team is working and what they are
doing — a web panel, status board, "kantor virtual", or monitoring view of
Hermes profiles and kanban activity. Also when fixing an existing panel whose
status/activity display has stopped updating.

Build a **read-only** web panel over Hermes internal data (worker roster, live
activity, recent events, optional 3D/denah view). Never expose write endpoints,
command execution, or anything that can touch a worker or the router.

## Procedure

1. **Collect data (read-only), in this order:**
   - Workers: glob `~/.hermes/profiles/*/profile.yaml` → `display_name`,
     model; `hermes profile list` for gateway/model state.
   - Cards: `hermes kanban list --json` — parse with
     `json.loads(s, strict=False)` (card bodies contain raw control chars), or
     sqlite `~/.hermes/kanban/boards/*/kanban.db` (tables `tasks`,
     `task_runs`, `task_events`, `task_comments`).
   - **Live activity (the load-bearing source):** `task_events` rows
     (`kind=heartbeat|claimed|completed|commented`, `created_at` epoch) joined to
     `task_runs.profile`, PLUS each profile's `state.db` →
     `sessions.last_activity_at`. Rule: heartbeat ≤5 min or session activity
     ≤10 min ⇒ "sedang bekerja". Return them as SEPARATE counts
     (`kanban_busy`, `session_busy`, `total_busy`) and tag each desk with its
     source — never one unlabeled number (see Pitfalls).
2. **Serve:** single-file stdlib server (`ThreadingHTTPServer`), token in
   `?token=` enforced on `/` *and* `/api/*` (401 without); inject the token into
   the HTML as a `__TOKEN__` replacement so the frontend fetch authenticates.
   Cache payload ~4 s, frontend refresh ~8 s.
3. **Frontend:** one `index.html` (inline CSS/JS) with stat cards, per-worker
   desks (status dot + current task), event feed. Optional 3D view as a lazy
   ES module so WebGL only exists while its tab is open.
4. **Verify BEFORE reporting done:**
   - `curl` API with token → 200 and JSON shows `active_profiles`/`feed`
     populated when someone actually works; without token → 401.
   - `node --check` every JS file, then in the browser call the render/load
     function via JS and assert the counts — a parse error in an inline script
     leaves the page silently empty while curl still returns 200.
   - `systemctl --user is-active <unit>`.
5. **Persist:** user unit in `~/.config/systemd/user/<name>.service`
   (`WantedBy=default.target`, `Restart=always`), then
   `systemctl --user daemon-reload && enable && start`.

## Adopting an existing upstream panel instead of building

For frontends that speak the Hermes JSON-RPC gateway directly (Studio/
Hermes3D-class), see `references/hermes-native-frontend-gateway.md` for the
verified backend-start recipe (`hermes serve --isolated`), token pinning, and
the 403-vs-101 WS probe.

When the user points at a repo whose look they like ("saya suka UI/UX ini,
berikan untuk kantor kita"):

1. **License first**: clone to scratch, read LICENSE — MIT/Apache lets you
   deploy and modify; refuse copyleft silently. Prefer zero-dependency
   stacks (stdlib Python + local JS) so nothing needs installing.
2. **Read the data contract before running it**: how agents are fed (file
   poll / SSE webhook / API), where its bridge assumes `HERMES_HOME` and the
   kanban boards live, how many agent slots and `home` positions the
   frontend maps support.
3. **Add the auth gate BEFORE it ever listens publicly** — upstream
   dashboards ship with none. Token via env var; read the secret from
   `token.txt` in a tiny launcher script so no unit file or repo file ever
   contains it; enforce on `/`, the office page AND `/api/*`.
4. **Test on a side port, then promote to the production port** so the
   user's saved link and token stay identical. Move the old panel aside as
   `<dir>-v1-archive` (rollback target), never delete it; keep two systemd
   units (server + data emitter) both `enable`d.
5. **Verify in-browser before reporting**: page loads with token / 401
   without, agent count == roster size, `working` count == live cards, then
   screenshot — numbers equal to the kanban, not "it rendered".
6. **Replacing a UI framework, preserve the user's link and secure data path.** Stage the candidate in a separate directory/port; inspect LICENSE, install dependencies, identify auth and backend path, adapt the emitter to the actual board DB/profile roster, then test before cutover. If the old panel is token-gated, the replacement must stay gated before any public bind. Use a dedicated gateway session token (never overwrite `HERMES_DASHBOARD_SESSION_TOKEN`), bind `hermes serve` to loopback, and publish only over the user's authenticated/restricted path. Cut over the same public port/token only after browser+API verification; archive old files for rollback, then remove old units/processes after the new service is proven.
7. **Live backend data must outrank all demo motion.** In `json_file`/API mode, animation may move avatars between poses but must never randomize agent status, task text, meeting counts, or chat bubbles. Update every periodic callback, not just the initial data loader; sample status counters repeatedly over 10+ seconds and ensure they remain identical to the API payload.
8. Before saying a visual change is live, verify the rendered result, not just
   the response: hard-reload a browser holding the old build, inspect console
   errors, and assert roster count + status counts + notification text match
   the API payload. A 200 alone is not proof the new UI loaded.

## Pitfalls

- **A live payload can still be overruled by the demo behavior loop — the panel looks "error" while every server check is green.** Replacing the agent array is only half the fix: upstream dashboards run a periodic simulation (`updateBehavior()`-style timer) that re-randomizes every `state.status` (meeting/working/walking), overwrites the real task string with canned phrases, spawns random chat bubbles that bury the floor, and writes hardcoded notification text ("Gathering in meeting room… x/5 attending"). Symptom the owner reports as "terlihat seperti error": counters jumping (4 working · 2 meeting · 4 walking against 2 real cards) and bubble spam. Gate the ENTIRE simulation on the data mode: live mode may only move positions (status/task come from the payload untouched), and the bubble spawner + every notification string/title get a live variant that states the truth ("N bekerja · M standby — data Kanban live"). Verify by sampling the counters 3× over ~10 s: they must be identical.
- **Patch one canonical file, sync it, then checksum before restarting.** Copying a stale source over the live directory silently reverts a fix that just landed (copy-back killed a notification patch and restored the old counters in one move). Pick the deploy path as canonical, edit it, push to any mirror, and compare md5 of both copies as the last step before `systemctl --user restart`.
- **Serve HTML/JS with `Cache-Control: no-store` or the fix never reaches the owner.** Browsers keep the previous `office.html` after a server-side fix, so the owner still screenshots the old bug. Send `no-store, must-revalidate` for `.html/.js/.css` (and `/`) in the response override, and tell the owner to hard-refresh once (Ctrl+F5).
- **A broken-panel report arrives as a video: diagnose the browser state, don't argue from server logs.** Service `active`, HTTP 200, `NRestarts=0` and an empty JS error array can all be true while the page is wrong. Pull the report (Drive link when Telegram rejects >20 MB), extract frames with `ffmpeg -vf fps=1/3`, vision-analyze them, then sample the live page via JS (`agentStates` counts, notification text, `bubbles.length`) and diff against the API payload — that separates a browser-side demo-state problem from a data problem.

- **Answering `/?token=` with a JSON short-body breaks the page** (the
  handler returns `{"ok":true}` instead of serving HTML). Plant the cookie
  inside an overridden `send_response()` so the normal static-serving path
  keeps running; then verify HTML is actually returned and that a later
  fetch (no query string) authorizes via the cookie.
- **Live data must REPLACE, not merge.** Frontends that push incoming
  agents into a built-in demo array keep the demo avatars forever (16 shown
  vs 11 roster). Patch the apply function to delete ids absent from the
  payload — from `AGENTS`, `agentStates` and `agentStats` — before applying.
- **From a profile session `HERMES_HOME` points at the profile dir**, so a
  board glob under it finds nothing and everyone reports Standby. Glob the
  global home too (`~/.hermes/kanban/boards/*/kanban.db`), dedupe, and
  prove with one worker showing `working` while its card is `running`.
- **New roster members need a home position**: `getHomePosition` style
  maps default to center, stacking every unmapped avatar at (0,0). Extend
  the map for every roster id and keep a round-robin fallback.
- **Emitter pushes on change only** — diff the payload, POST the webhook
  when it changed, fall back to writing the served JSON file when the
  webhook is down; a 10 s blind push loop is wasted traffic.
- **Card status alone makes the panel lie.** Once every card is `done` while
  workers keep chatting/running cron, a status field derived from cards freezes
  at 0. Activity must come from heartbeats + `sessions.last_activity_at` —
  Chat and cron runs emit no card-status change. If showing chat/session activity too, include it explicitly as a separate source and separate count; never silently include the coordinator's own current conversation in a number labeled as workers working. Treat `sessions.last_activity_at` as a short-lived active-session signal (not proof of task progress) and label it accordingly.
- **User units have no shell PATH.** Without
  `Environment=PATH=<HOME_ANDA>/.local/bin:...` in the unit, a
  `subprocess.run(["hermes", ...])` fails silently and the payload degrades to
  `model: "?"`/`gateway: "unknown"`. Add PATH, then re-check the API JSON.
- **Bare ES-module specifiers need an import map** (`import ... from 'three'`
  dies with "Failed to resolve module specifier" unless the served HTML has
  `<script type="importmap">`).
- **Restart the unit after editing server-side Python** — files served from
  disk (HTML/JS) hot-reload, Python does not.
- **Get exact `old_string` from the file before patching a minified one-line
  HTML** (grep it out, assert it is present); a guessed match silently does
  nothing while you believe the edit landed.
- **Serve token-gated pages over LAN IP only after binding `0.0.0.0`** and
  confirm the public URL responds — user opens the panel from other devices.
- **Never collapse session and card activity into one unlabeled "busy"
  number.** Expose `kanban_busy` / `session_busy` / `total_busy`, tag each desk
  with its source (`sesi aktif` vs kartu), and state the rule in the stat
  subtext ("kerja kartu ≤5 mnt · sesi ≤10 mnt"). Counting chat sessions
  silently made the board claim "2 sedang bekerja" while zero cards ran (the
  coordinator's own chat counted); deleting sessions then showed 0 while the
  user was actively working — either way the number was unexplainable.
- **Prove an animation/3D loop with counters, not pixels.** `canvas.toDataURL()`
  reads a cleared drawing buffer and reports "static" while rendering is
  healthy, and full-page screenshot hashes can match too. Instrument the frame
  function with `window.__frame`/`window.__rendered` counters, sleep, assert
  they advanced and `window.__frameErr` is 0; screenshots only confirm
  composition, not motion.
- **Bound service restarts inside foreground cells.** Run
  `systemctl --user restart X` under a short timeout followed by `is-active` in
  the same call; a restart cell that hangs past the tool timeout kills the
  kernel state mid-turn and leaves you unable to reply — after any such
  timeout, re-check the unit state first thing, before reporting anything else.
- **Prove panel "live-ness" against the label, not just against emptiness.**
  A connected panel whose numbers don't move is still broken to the user.
  Verify all three layers each fix: API JSON (`active_profiles`/`feed`
  populated when work is happening), frontend counts (call `load()` manually
  via JS and assert `statBusy`/`feed` children render), and desk classes
  (`.desk.busy` matches `active_profiles`) — a missing frontend patch shows
  correct API numbers while desks stay grey, and the user reports "tidak
  berjalan real time".
- **Feed "terbaru" must show relative time.** A feed built from card history
  alone reads as stale-but-latest during idle hours; emit `rel` ("7 jam
  lalu"/"baru saja") next to the timestamp so the user can tell idle from
  broken without asking.
