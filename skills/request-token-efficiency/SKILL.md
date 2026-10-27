---
name: request-token-efficiency
description: "Keep every request lean: scope, format, and stop rules."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [efficiency, tokens, requests, discipline]
    related_skills: [prompt-master, task-progress-reporting]
---

# Request Token Efficiency

Standing discipline for every request in this office. The goal is fewer
re-prompts, fewer wasted turns, and fewer tokens per answer — not shorter
answers. A precise answer that lands first try is cheaper than a cheap
answer that needs three follow-ups.

Derived from the token-efficiency and diagnostic sections of the
`prompt-master` skill (nidhinjs/prompt-master, MIT). The full skill stays
available for prompt-engineering work; this skill is the always-on subset
that applies to everyday work.

## When to Use

- Every request, every work order, every Kanban card spec.
- Skip for: pure conversational replies where the user just asked a question.

## The 12 Patterns That Waste Requests

Fix these before sending a task. Do not restate them in the task itself.

| # | Pattern | Fix |
|---|---------|-----|
| 1 | Vague task verb ("help with the code") | Name the exact operation and target |
| 2 | Two tasks in one prompt | Split into two sequential tasks |
| 3 | No success criteria | Derive a binary pass/fail check |
| 4 | Emotional description ("it's broken") | Extract the concrete fault |
| 5 | Scope is "the whole thing" | Decompose into sequential steps |
| 6 | Assumes prior knowledge | Restate the required context inline |
| 7 | Invites hallucination | "State only what you can verify; mark uncertainty" |
| 8 | No mention of prior failures | Say what was already tried and did not work |
| 9 | No output format | Lock format, length, and filetype |
| 10 | Implicit length ("a summary") | Give a word or sentence count |
| 11 | No scope boundary | Name the allowed files, dirs, and tools |
| 12 | No stop condition for agents | Define checkpoints and approval triggers |

## Procedure

1. **Frame the request.** One sentence: outcome, scope, done-when.
2. **Lock the boundaries.** Which files, dirs, and tools may be touched; which are forbidden.
3. **Lock the output.** Format, length, and where it lands (file path, board card, report).
4. **State the evidence bar.** What proof counts as finished: test counts, file:line refs, screenshots, real command output.
5. **Define stop conditions.** When to pause and ask instead of guessing or expanding scope.
6. **Carry context forward.** Re-state the decisions that must not be contradicted. Never write "as discussed earlier" into a delegated spec.

## Pitfalls

- **Trimming the request is not trimming the work.** Removing a success
  criterion or a scope boundary to save tokens causes a re-prompt, which
  costs more than the tokens saved. Cut adjectives, not constraints.
- **Do not stack deliverables.** One task per card, one format per output.
  A request with two deliverables usually comes back with one of them
  done vaguely.
- **Do not add "double-check everything".** It inflates output and rarely
  catches what a real verification step would not.
- **Do not ask for hidden reasoning.** Request conclusions, evidence, and
  verification results instead — reasoning traces are not a deliverable
  and requesting them adds output tokens without adding reliability.
- **Do not paste full codebases as context.** Scope to the relevant file
  and function.

## Verification

- [ ] Task states outcome, scope, and a binary done-when.
- [ ] Allowed and forbidden surfaces are named.
- [ ] Output format and length are explicit.
- [ ] Evidence requirement is written into the task.
- [ ] Stop conditions are written into the task.
- [ ] No "as discussed", "as before", or other implicit context references.
