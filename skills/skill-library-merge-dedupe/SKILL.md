---
name: skill-library-merge-dedupe
description: "Use when merging two skill libraries for OpenCode."
version: 1.1.0
author: Amanda
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [skills, library, dedupe, packaging, distribution]
    related_skills: [hermes-profile-provisioning, office-skill-distribution]
---

## When to Use

Use when the owner asks to combine two skill libraries into one bundle, or when
two candidate copies of one skill name need a single winner. Rolling an
already-curated set out across a multi-profile Hermes server is a different
task — see step 10 and `office-skill-distribution`.

# Merge Two Skill Libraries (dedupe + repackage)

Use when the owner asks to combine skills from two profiles/agents into one bundle,
especially for installing into OpenCode, Claude Code, or another Agent Skills host.

## Procedure

1. **Enumerate both trees** — walk every `SKILL.md` (category dirs like `creative/`,
   `devops/` are just containers). Key by **basename**, not relative path: the same
   skill often sits at top level in one profile and inside a category in the other.
2. **Classify by sha256 of SKILL.md**: identical / differing / unique-to-A / unique-to-B.
3. **Pick one winner per name:**
   - identical → keep either copy.
   - differing → line-set superset test: `lines(A) - lines(B)` empty ⇒ B is superset.
     If truly divergent, keep the larger/most recent version and log the decision.
   - Never ship two copies of one name — that is the overlap the owner complains about.
4. **Copy whole skill dirs** (copytree), not just SKILL.md — references/, scripts/,
   templates/ must travel with it.
5. **Flatten to one level**: `<out>/skills/<name>/SKILL.md`.
6. **Validate every SKILL.md**: YAML frontmatter parses, `name` == folder name,
   matches `^[a-z0-9]+(-[a-z0-9]+)*$`, length 1–64, `description` 1–1024 chars.
   Rewrite `name:` when it mismatches the folder.
7. **Package**: top-level folder inside the zip + `README.md` (install paths, inventory,
   dedupe log) + `install-windows.bat` (`xcopy /E /I /Y` to `%USERPROFILE%\.config\opencode\skills`) + `install-unix.sh`.
8. **Test the artifact, not the source**: extract the zip into a sandbox `HOME`, run the
   installer, assert N dirs each with a valid SKILL.md. Only then deliver.
9. Deliver as a real attachment (`MEDIA:/abs/path.zip`), never a `file:///` link.
10. **Rolling the merged set out to a multi-profile Hermes server is a
    different task from packaging it**: one shared directory + `skills.external_dirs`
    + per-role `skills.disabled`, never a copy per profile — see
    `office-skill-distribution`.

## OpenCode facts

- Discovery: `.opencode/skills/<name>/SKILL.md`, `~/.config/opencode/skills/<name>/SKILL.md`,
  plus the Claude/agents equivalents (`.claude/skills`, `~/.agents/skills`).
- `name` must equal the directory name; description ≤1024 chars; unknown frontmatter keys ignored.
- Permissions in `opencode.json` → `permission.skill` support `allow`/`deny`/`ask` + wildcards,
  so Hermes/server-only skills can ship in the same bundle and be hidden with `"hermes-*": "deny"`.

## Pitfalls

- **Zip swallowing itself**: building the zip from a dir that already holds a previous zip
  doubles the size silently. Build in a fresh `pkg/` dir, then `zip` from there.
- **No top-level folder** in the archive scatters 118 dirs into the user's Downloads.
  Always zip a single named folder.
- Copy of a profile's `skills/` may include non-skill dirs; filter on `SKILL.md` presence.
- Report the split (identical / differing / unique) with numbers — the owner judges by evidence.
