---
name: hermes-profile-provisioning
description: "Provision Hermes profiles with dev skills, plugins, tools."
version: 0.1.0
author: Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [profiles, skills, plugins, provisioning, toolchain]
    related_skills: [hermes-agent, hermes-agent-skill-authoring]
---

# Provisioning Hermes profiles for development work

Equip one or more Hermes profiles (e.g. an implementer and a reviewer
profile) with the skills, plugins, and OS/toolchain packages needed for
Python and fullstack web development — then VERIFY every claim.

## When to Use

- "Install skill/plugin X for profile Y", "give the coder profiles dev
tools", or "set up this server for development".
- A new profile is being hired as a Kanban worker for coding tasks.
- The user asks to "recruit / hire" a new worker profile (brainstormer,
  planner, implementer) with its own persona and model — see step 0.
- Don't use for: authoring a new SKILL.md (see
`hermes-agent-skill-authoring`), or per-session project deps inside a repo
(put those in the project's own venv/lockfile).

## Procedure

Order matters: system packages first (they don't touch Hermes state), then
Hermes-level installs, then verification. Each step has a check.

### 0. Recruiting a worker profile (clone-based hire)

To hire a new teammate with inherited credentials and its own soul:

```bash
hermes profile create <id> --clone --description '<1-2 sentence role>'
```

Keep the description free of quotes and apostrophes — it passes through
nested shells, and one `'` inside aborts the command with `unexpected EOF`.

`--clone` copies codi's `config.yaml` + `.env` + SOUL.md + skills, so the
hire inherits the working provider (provider proxy anthropic), fallback chain,
credentials, and `agent.max_turns`. Messaging channels are deliberately NOT
cloned (one bot token cannot be held by two gateways — the CLI refuses
without `--clone-channels`). Then, in order:

1. **Overwrite the cloned SOUL.md.** It currently holds *your* soul —
   `read_file` it in full first (write_file refuses without a fresh read),
   then write the new persona: identity (matching the team's seniority
   register, e.g. "Principal … 15+ years"), role boundaries vs other
   profiles, thinking style, deliverable format, handoff path.
2. **Set model + reasoning:**
   `hermes -p <id> config set model.default claude-<mid-model>`,
   `hermes -p <id> config set model.provider anthropic`,
   `hermes -p <id> config set agent.reasoning_effort high`.
   The reasoning set prints `not a recognized config key … did you mean
   agent.reasoning_echo` — it still lands correctly in the `agent:` block;
   confirm with `hermes -p <id> config get agent.reasoning_effort`.
   **Pick the model by cost-of-wrong, not seniority:** opus only where a
   mistake is expensive (code, security audit); sonnet + effort tiered by
   role (high for analysis/strategy, medium for content) for everything
   else — every hire shares one request quota fleet-wide, so an all-opus
   fleet converts hires into rate-limit pressure. Revisit per-person if
   real output is weak; upgrading one profile is one `config set`.
3. **Verify end-to-end:** `hermes -p <id> chat -q '<asks its name/role>'`,
   then read the assistant reply from the PER-PROFILE state DB at
   `~/.hermes/profiles/<id>/state.db`; the root `state.db` has no
   sessions for a new profile. One-shot stdout often omits the reply.
   Also re-check `hermes profile list` shows the model.
4. Profile **id** must be lowercase alphanumeric; a friendly display name
   (`Harry`) rides on the id (`harry`) — do not try to make the id mixed-case.
   To set/change a display name on an existing profile (presentation-only —
   the id, alias, Kanban assignee, and paths stay untouched), there is no CLI
   verb; call the API from the Hermes source tree:
   `python3 -c "import sys; sys.path.insert(0,'<hermes-source-root>'); from hermes_cli.profiles import set_profile_display_name; print(set_profile_display_name('<id>','<Display>'))"`.
   That function imports `ruamel.yaml` at call time — importing the module
   itself can succeed while the call fails with `ModuleNotFoundError`; install
   with `pip3 install ruamel.yaml`, verify `python3 -c 'import ruamel.yaml'`,
   then invoke.
   `hermes profile list` then renders `Display (id)`; do NOT rename the id
   to chase a call sign — it breaks Kanban assignees and routing history.

Check: run `hermes -p <id> config get` once per key — `model.default`,
`agent.reasoning_effort`, and `agent.max_turns` — and confirm each intended
value; passing several keys in one invocation fails argument parsing.

Also give each new hire its own lane skill (`skills/<name>/SKILL.md` with
frontmatter) for role boundaries and handoff format; identity belongs in
`SOUL.md`, reusable task procedure in the skill. Verify by listing the
profile's skills.

### 1. Inventory before installing

```bash
hermes profile list                 # profiles + gateway state
hermes -p <profile> skills list     # what that profile already loads
hermes -p <profile> plugins list    # installed + enabled/disabled
python3 --version; node --version; which docker redis-server ffmpeg
```

Decide target per profile: implementer profiles want build skills (TDD,
backend framework, frontend design, web testing); reviewer profiles want
code-review/diagnosis skills. A skill list already containing a near-duplicate
(e.g. a builtin `test-driven-development`) means skip the registry install.
**Check:** every planned install target is classified "missing" before you
install anything.

### 2. System packages (apt / pip / npm)

```bash
apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
  build-essential pkg-config libffi-dev libssl-dev libpq-dev sqlite3 \
  libsqlite3-dev libmagic1 redis-server curl jq unzip zip
# fullstack extras:
curl -fsSL https://get.docker.com | sh && systemctl enable --now docker
systemctl enable --now redis-server && redis-cli ping   # expect PONG
pip3 install fastapi 'uvicorn[standard]' pydantic pytest httpx ruff mypy \
  alembic 'sqlalchemy[asyncio]' uv
npm install -g pnpm typescript eslint prettier
python3 -m playwright install chromium   # NOT `playwright --version`
```

**Check:** verify each with its real probe — `redis-cli ping` → `PONG`,
docker → `docker version`, Python packages → `python3 -c 'import fastapi'`.
Never infer success from an exit code alone (see Pitfalls).

### 3. Skills per profile

Preferred path: `hermes -p <profile> skills install <identifier> --yes`.

When the GitHub API path is exhausted (see Pitfalls), fall back to the
local-copy path:

```bash
git clone --depth 1 <repo> /scratch/skill-src   # git ≠ GitHub API rate limit
# find the actual SKILL.md locations — repo layouts vary (skills/<cat>/<name>/
# or <name>/SKILL.md at root); never guess paths
cp -r /scratch/skill-src/<path-to-skill> ~/.hermes/profiles/<p>/skills/<name>
```

Copy the skill's whole directory (its SKILL.md plus any linked files it
ships). Then
**check:** `hermes -p <profile> skills list | grep <name>` shows the skill
`enabled`.

When several profiles should get the same skill set, share instead of copy:
one directory in a shared folder, exposed to every profile through
`skills.external_dirs`, with per-role relevance enforced by
`skills.disabled`. That keeps a single editable copy (no fleet drift) and
keeps irrelevant skills out of each profile's prompt (token savings), which
copy-per-profile can never do. `hermes -p <id> config set skills.<key> '<json>'`
writes both keys and `config get` reads them back, even though the setter
prints `not a recognized config key … saved anyway` for nested keys. The
per-role map, the verification ladder, and the traps live in
`office-skill-distribution`.

### 3a. Copying skills into the default profile

The `default` profile is a special case: it is rooted at `~/.hermes`, not
`~/.hermes/profiles/default`. Its skills live under `~/.hermes/skills/`;
worker profiles use `~/.hermes/profiles/<id>/skills/`. Resolve the actual
profile home with `hermes profile show <id>` before constructing paths; never
infer the default profile path from worker-profile conventions.

To copy a source profile's entire skill library into default without duplicating
or overwriting silently:

1. Inventory both trees recursively by each `SKILL.md` parent directory's
   basename. The default tree may categorize skills one directory deeper
   (`productivity/<skill>/SKILL.md`), so compare skill names, not relative paths.
2. Hash each `SKILL.md` (SHA-256) and classify names as identical, different,
   source-only, or destination-only. Leave identical copies untouched; copy
   source-only skill directories preserving their relative category paths; for
   differing copies, back up the destination first and replace the whole skill
   directory with the chosen source version. Preserve destination-only skills.
3. Copy the complete skill directory, including `references/`, `scripts/`, and
   `templates/`; do not flatten profile skills or copy only `SKILL.md` into the
   category-based Hermes library.
4. Verify by walking the destination again: every source skill name exists and
   each destination `SKILL.md` hash matches the source. Re-list the target
   profile's skills and report counts for identical, updated, new, and retained
   destination-only skills. Keep the backup path available for rollback.

### 3b. Fleet-wide skill version sync (update an existing skill across already-hired workers)

When the canonical copy of a skill (usually the coordinator's own profile, e.g.
`amanda`) is newer or carries more content than what already-hired workers hold —
e.g. after the coordinator iterated on a SKILL.md directly — propagate it to every
worker profile in one pass:

```bash
SRC="~/.hermes/profiles/<source>/skills/<name>"
for p in <worker1> <worker2> ...; do
  DST="~/.hermes/profiles/$p/skills/<name>"
  rm -rf "$DST" && cp -a "$SRC" "$DST"
  echo "$p: $(sha256sum "$DST/SKILL.md" | cut -c1-8) files=$(ls -1 "$DST" | wc -l)"
done
```

Use `rm -rf` + full-directory copy, not a partial overlay of just `SKILL.md`: a
skill may ship `references/`, `scripts/`, or `templates/` subdirectories that must
move together, and a stale leftover file from the old version can survive a
partial copy. Verify by **sha256 hash and file count**, never by mtime or byte
size alone — every profile should report the same hash prefix as the source and
the same file count.

Before choosing the source, diff first (`diff <src>/SKILL.md <dst>/SKILL.md`): a
newer/larger file is not automatically the correct one to propagate. If the delta
is substantive (new sections, not just a version bump), sync it; if the copies
diverged deliberately or the delta is trivial, pick the correct copy on purpose
rather than assuming newest-mtime wins.

### 3d. Fleet-wide plugin deployment (one source, every profile)

A plugin that must behave identically across the fleet needs a single source directory and a
copy step, because a profile's plugin directory is a separate copy, not a link:

```bash
SRC="<HOME_ANDA>/.tools/<plugin>"                 # canonical source
for t in ~/.hermes/plugins/<plugin> ~/.hermes/profiles/*/plugins/<plugin>; do
  [ -d "$t" ] || continue
  for f in __init__.py graph_query.py plugin.yaml; do
    [ -f "$SRC/$f" ] && cp -a "$SRC/$f" "$t/$f"
  done
done
```

Copy the whole file set, not just the entry point — a plugin usually ships a helper module
and a manifest, and a partial copy leaves the profile running stale code. Verify by hash,
not by presence:

```bash
sha256sum "$SRC/__init__.py" ~/.hermes/profiles/*/plugins/<plugin>/__init__.py
```

Every hash must match. A file that merely exists proves nothing about its content.

**Do not copy a directory onto itself.** When the canonical source is itself a profile's
plugin directory (e.g. the coordinator's), `rm -rf "$DST" && cp -a "$SRC" "$DST"` deletes
the source and then fails to copy it — the skill or plugin silently vanishes from that
profile. Stage the canonical copy in a temp directory first, or use a separate source
path, and re-verify the file count afterwards.

After changing plugin code, reload gateways without a restart:

```bash
python3 -c "import sys; sys.path.insert(0,'<hermes-source-root>'); from gateway.control_socket import reload_gateway_plugins; from pathlib import Path; \
print([(p, (reload_gateway_plugins(Path('~/.hermes'), profile_home=Path(f'~/.hermes/profiles/{p}')) or {}).get('reloaded')) for p in '<profiles>'])"
```

A profile with no running gateway may report `reloaded: False` — that is expected, not a
failure. Verify such a profile by calling the hook in-process against that profile's
`HERMES_HOME` instead of assuming the reload failed.

### 3e. Making a skill always-on across the fleet

To have a skill injected into every session of every profile, two things are needed per
profile: the skill directory, and the profile's own `config.yaml` listing it under
`skills.auto_load`. Copying the directory alone leaves the skill available but not loaded.

A profile's `config.yaml` overrides the global one, so a profile that sets its own
`skills` block without `auto_load` silently loses the global setting — check each
profile's effective value, not the global file. Verify by reading the skill's text out of
a real session's stored system prompt: a skill that is installed but not referenced there
is not actually injected. Stage source copies outside profile destinations before deleting
or replacing any destination; if source and destination resolve to the same directory, a
remove-then-copy sync deletes the canonical skill before it can be restored.

### 3f. Installing a skill does not guarantee a dispatched worker will USE it

To actually bind a skill to a specific task, do BOTH:

1. Confirm it is installed on the assignee's profile (step 3 or 3b).
2. Name it explicitly in the card itself. The `skills` TEXT column on the board's
   `tasks` table is the structured channel — check `hermes kanban create --help`
   for the exact flag in your installed version (flag shapes vary per subcommand,
   and a wrong flag exits 0 without creating anything). When the flag is absent or
   uncertain, the portable fallback that always works is a line in the card body
   or first comment: *"Consult and follow skills `<name>`, `<name>` at task start;
   for each finding, cite which rule from each skill you applied."*

Check: after dispatching, require the worker to name the skill and the specific
rule it applied, per finding, in its progress comment — installation alone is not
proof of use, exactly as a green install list is not proof a worker loaded it.

### 4. Plugins per profile

```bash
hermes -p <profile> plugins install <plugin>    # installs DISABLED
hermes -p <profile> plugins enable  <plugin>    # required, per profile
```

`install` output saying "Plugin installed but not enabled" is normal —
enabling is a separate step and must be repeated for each profile.

**Check:** `hermes -p <profile> plugins list` shows `enabled` for every
plugin. A `not enabled` row after enable means the enable failed — read the
full error, don't re-run blindly.

### 5. Final verification report

Re-run step 1's inventory and report only what the re-run printed: skill
names + `enabled`, plugin names + `enabled`, package probes with their real output. Anything unverified or failed is
reported as not done, with the exact blocker — partial completion stated
honestly beats a green summary.

### 6. Worker skill-learning conventions

When configuring a team's long-term workflow, give each worker a standing
instruction to inspect relevant skills at task start and distill genuinely
reusable task-class methods after substantive completions. Keep skills scoped
to procedures/pitfalls; keep identity and permanent role boundaries in
`SOUL.md`; keep project-specific results in the project workspace. Never
require a new skill for every trivial task — that creates one-off clutter.

### 7. Rotating provider keys across existing profiles (owner-supplied scripts)

When the owner ships provider keys as setup scripts (one file per team
group, each embedding one key), install them per profile — never execute the
scripts: they overwrite the GLOBAL key in the top-level Hermes home (destroying
every profile's rotation, including the coordinator's, which owners mark
"JANGAN DISENTOH"), and their bundled Claude settings JSON is malformed anyway.

   register which profile ID maps to which key/group before touching anything,
   and confirm each target profile has no active run (`hermes kanban list` by
   assignee) — a running worker rewrites its own `auth.json`.
2. Backup `.env` + `auth.json`, replace the key in `.env` (also force
   `ANTHROPIC_BASE_URL` to the intended endpoint), and replace the profile's
   `credential_pool.<provider>[]` with a single dedicated entry (drop old
   keys; clear `last_status` and `model_cooldowns`).
3. **Read-back verify in a retry loop** (write → sleep → re-read → entry
   count AND token must match): a concurrent worker has emptied this file for
   minutes mid-install, and a silently empty pool breaks the profile until
   its next spawn. Repeat cleanup AFTER the worker is replaced — and check the
   entry's `source` field first: an entry with `source=env:ANTHROPIC_...` is
   REBUILT on the next worker start (often with an empty token) when that
   variable is missing/empty in the worker environment, so deleting it while
   the old worker still runs looks like the cleanup "keeps failing". Fix the
   env source (`.env` value present, one key line only), then clean, then
   verify a few seconds later.
4. Prove it end to end: probe the key on EVERY model that profile runs
   (opus-tier profiles need an opus probe — quota is often per-model), run
   one real `hermes -p <profile> chat -q` per profile, and diff a
   hash of the coordinator's `.env`/`auth.json` before vs after to show it
   untouched. Report the roster as display name | profile ID | masked key |
   model | effort | probe+chat result.

## Pitfalls

- **Profile-scoped commands must carry `-p <target>`.** `hermes skills install`/`uninstall`/`config set` run against the ACTIVE profile when `-p` is omitted — an install silently lands on the wrong profile. Always pass `-p <profile>`, verify with `hermes -p <profile> skills list`, and re-list the active profile to catch an accidental install.
- **`hermes profile rename <old> <new>` changes the profile ID, not a display name.** It moves the directory and alias and breaks any Kanban assignee/skill path bound to the old id. To set a friendly display name on an existing profile (presentation-only — id, alias, assignee, paths stay), call the API from the Hermes source tree:
  `python3 -c "import sys; sys.path.insert(0,'<hermes-source-root>'); from hermes_cli.profiles import set_profile_display_name; print(set_profile_display_name('<id>','<Display>'))"` — the source root is one of `~/.hermes/installs/<hash>/environments/<hash>/workspace`.
- **When a hire needs image generation**, check which env var that skill actually reads: the OpenAI `imagegen` skill needs `OPENAI_API_KEY` — an Anthropic key does not enable it. If the owner will enter keys manually, leave credential fields empty instead of cloning the source profile's key.
- **`hermes skills install` can exit 0 while failing.** The GitHub API
  limit (60 req/hr unauthenticated) surfaces as `Error: Could not download`
in stdout with exit code 0. Always verify by listing skills afterward;
  setting `GITHUB_TOKEN` in `.env` or `gh auth login` raises the limit to
  5,000/hr. Working fallback: `git clone` the source repo (different quota)
  and copy skill folders in by hand.
- **URL-based skill installs can hang past their timeout** while resolving
  dependencies. Prefer the repo-copy path for bulk installs, or run them one
  at a time with an explicit timeout.
- **Skill copies can land nested** (`skills/<name>/<name>/SKILL.md`) when a
  registry install partially completed first. After copying, walk the tree
  for `SKILL.md` files and remove the stray inner directory.
- **The `default` profile's skills live in `~/.hermes/skills/`, not
  `~/.hermes/profiles/default/skills/`.** Worker-profile path conventions
  silently point at an empty directory for default, so a copy "succeeds" while
  the profile loads nothing. Resolve the profile home with
  `hermes profile show <id>` first, and note that default categorizes skills
  one level deeper than worker profiles — match on skill NAME, not relative path.
- **Plugin enable can fail with a duplicate-workspace error** (`Two workspace
  members are both named <pkg>`), usually left by an interrupted earlier
  install. Fix by `plugins remove` + `install` + `enable`. Never edit
  `state.db` or delete install-workspace dirs by hand to force it.
- **Editing `config.yaml` by hand requires byte-exact block matching.**
  Read the file first (indentation differs from the docs' example — a
  guessed `enabled:` block writes nothing or corrupts plugin config). Prefer
  `hermes -p <profile> config get plugins.enabled` to see the current shape.
- **Don't trust `--version` of a Python-installed CLI on PATH.** Playwright
  installs as a Python module: probe `python3 -m playwright --version`, not
  `playwright --version`.
- **Never claim an install before re-listing it.** The failure mode this
  skill exists to prevent: a report saying "skills installed" when the
  registry silently refused every one.
- **Every new profile needs `agent.max_turns` checked.** The fleet standard
  is 500 (`hermes -p <id> config get agent.max_turns`); profiles created or
  cloned before that decision may carry 150, which tool-heavy Kanban cards
  burn in under an hour and report as `timed_out … Iteration budget
  exhausted` — users misread this as an API quota wall. Align the value at
  hire time so downstream quota debugging starts clean.
- **A directory under `profiles/` is not proof of a profile.** Orphan
  directories (leftovers that still hold a `config.yaml`) sit beside real ones
  and silently join any `os.listdir('profiles')` loop, redirecting every probe
  — including overwriting a `homes['default'] = …` entry you set up first.
  Take the roster from `hermes profile list`/`profile show`, and when building
  a path map from a listing use `setdefault` semantics so a stray name cannot
  clobber an entry you already assigned. An orphan's config can also hold
  stale edits; never treat it as authoritative state.
