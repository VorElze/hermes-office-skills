# Handing an audit to a Kanban board

Turning a findings report into tracked remediation work. The review card
below is a *downstream* card — ordinary implementation work with a
review-oriented spec. Reserve the `sdlc-review` skill for the dispatcher
review lane, where an implementer submits a `review_requested` handoff for
an independent verdict.

## 1. Split implementation from verification

- **One implementation card** carrying every finding, ordered by severity
  (Critical → High → Medium → Low), each with location, evidence, and fix
  inline in the body. The assignee has no access to your conversation —
  the card body must be self-contained.
- **One review card as its child**, created with `parents=[<impl_id>]` in
  the same create call. The field links the dependency automatically; a
  separate `kanban_link` call afterwards is redundant. The child stays in
  `todo` until the parent is `done`, then promotes to `ready` on its own.
- Put **checkable acceptance criteria** at the end of the implementation
  body (one line per verifiable outcome) so the reviewer can map each to
  evidence instead of re-deriving scope.

## 2. Make long runs resumable before they start

A single card that consumes many tool calls will hit a run limit (iteration
budget or provider rate limit) and be **retried as a fresh session with no
memory of the previous run**. Before dispatching:

- Instruct the worker, in the card body, to **comment its status to the
  board after each finding** (done / in progress / untouched + file
  locations) — the next run reads those comments to resume, not its own
  lost transcript.
- Estimate scope against the budget. If the work spans many findings,
  either split it across cards or tell the worker to batch edits and run
  tests in targeted subsets rather than re-verifying everything each round.
- Do not hunt for a task-level budget knob after a timeout — there is
  none: `hermes kanban edit` exposes only title/body/priority/result/
  summary/metadata, and the `agent.max_iterations` value in config.yaml
  does not necessarily equal what a spawned worker actually gets. The
  lever is the card body (resumability + smaller increments), not a field
  you can raise on the running task.
- Pin small, finishable increments to the top of the body; a run that dies
  mid-way should leave the next run an obvious entry point.

## 3. Preserve the output

Scratch workspaces are deleted when a task completes. If the patched
tree, diff, or generated artifact must survive for review or delivery:

- create the card with `workspace_kind: dir` (absolute `workspace_path`) or
  `worktree`, or
- require the worker to attach the result to the card before completing
  (`kanban_attach` with an absolute path) and name that artifact in the
  completion summary — a card that completes without its required
  attachment should be re-opened, not accepted on trust.

## 4. Review triggers

Do not notify on every heartbeat. Act when a card changes state:
`timed_out`/failure notifications get one steer comment (resume point +
budget guidance), `done` on the implementation card is the trigger to run
the child review card. Never recreate cards that already exist on the
board — inspect first with `kanban_show`.

## Pitfalls

- Writing findings only into chat: the assignee never sees them.
- Creating the child card without `parents`, then finding it stuck in
  `todo` — set the dependency at creation time.
- Letting a completed run's scratch workspace evaporate before the review
  can read the diff.
- Duplicating the board graph because a status notification looked like a
  request to decompose again.
