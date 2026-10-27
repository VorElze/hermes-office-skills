# Live React runtime census with Playwright

Use this read-only diagnostic when the live React UI disagrees with tests and the relevant transient state exists only in memory.

## Procedure

1. Open the app with a headless Playwright session, authenticate via the approved secret source, and never print credentials.
2. Scan `document.body.querySelectorAll('*')` for elements with own properties matching `__reactFiber$*`. Walk each fiber's `return` chain (up to depth 400) and its `memoizedState` hook list (up to 60 hooks).
3. Identify the authoritative runtime state map by schema: a plain object keyed by entity ID, values containing transient `state` and `status` fields (for example `walking`, `sitting`, `standing`). Note the owning hook's sync cadence. A ref may instead have `{current: [...]}` with positions/paths, but refs inside child hooks may not be reachable from a mounted DOM fiber.
4. Sample every ~5 seconds for ~150 seconds (or a duration appropriate to the transition). Record census counts and per-entity transition timelines; save a final screenshot.
5. Cross-check the runtime map against visual evidence and the app's acceptance criterion. For work-desk behavior, separately inspect whether agents are assigned desks, whether coordinates change while walking, whether paths reach their targets, and whether the exact sit predicate succeeds at arrival; never collapse these into one “navigation works” claim. Report the sample count/window and whether the target state appeared.

## Pitfalls

- Do not count profile metadata as runtime state: a `working` label may be static and unrelated to scene motion. Validate transient state fields before interpreting results.
- A shallow fiber walk (depth 60–80) may miss a hook; widen the walk before concluding the state is unreachable.
- If a ref scan returns null, use a reachable state mirror synced from the ref and state its cadence as the freshness bound.
- One snapshot cannot establish that a transition never occurs. Absence across a stated, sufficiently long sample window is stronger evidence, not proof beyond that window.
- `walking` does not prove movement; compare positions across samples when available. A long `walking` census with no `sitting` establishes a persistent transition failure during that window, but not its cause; capture arrival coordinates/path and evaluate the actual runtime predicate before choosing a fix.
- Keep the probe read-only; never write to fiber state or memoized props.
