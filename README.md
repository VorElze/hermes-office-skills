# Hermes Office Skills

Reusable agent skills for running AI-assisted offices, teams, and software projects. **86 skills**, shared as open files; choose only the ones relevant to your agents.

This collection combines general workflows (planning, writing, reviews, delivery, operations) with domain packs (Hermes operations, web development, design, marketing, sales, education, and networking). A subset documents **Hermes Agent** operations specifically; those skills are most useful for Hermes users and need adaptation elsewhere. Always inspect a skill before using it; tools and safety rules differ between agents. See `NOTICE.md` for provenance and license terms.

## Quick start

```bash
git clone https://github.com/VorElze/hermes-office-skills.git
```

Add the skill directories to your agent's documented skill path, or copy chosen directories into that path. **Do not copy the repository root as one skill**: each immediate subdirectory under `skills/` is an individual skill and has `SKILL.md`.

### Hermes

For one profile, copy selected skills:

```bash
mkdir -p ~/.hermes/profiles/<PROFILE>/skills
cp -r hermes-office-skills/skills/<skill-name> ~/.hermes/profiles/<PROFILE>/skills/
```

Or configure a shared directory using Hermes `skills.external_dirs` (see Hermes docs), then filter irrelevant skills with `skills.disabled`. Restart/reload the agent session to refresh the prompt. Test with `hermes -p <PROFILE> skills list --enabled-only`.

### Claude Code

Claude Code supports Agent Skills as `.claude/skills/<skill-name>/SKILL.md` in project scope or `~/.claude/skills/<skill-name>/SKILL.md` in user scope:

```bash
mkdir -p .claude/skills
cp -r hermes-office-skills/skills/<skill-name> .claude/skills/
```

Use current Claude Code documentation for supported frontmatter and discovery behavior.

### Codex

Codex supports skills in `.agents/skills/<skill-name>/SKILL.md` (project) or `~/.agents/skills/` (user):

```bash
mkdir -p .agents/skills
cp -r hermes-office-skills/skills/<skill-name> .agents/skills/
```

Verify against current Codex documentation; feature support may vary by release.

### Claude Desktop and other agents

Skill discovery varies by client/version. If the agent supports Agent Skills, put each selected directory in its documented skills folder. Otherwise paste `SKILL.md` as project/agent instructions or attach it as context. Tools cited by a skill may require adaptation.

## Selecting skills

Browse [docs/CATALOG.md](docs/CATALOG.md), `manifest.json`, or `skills/`. Suggested bundles:

**Core (safe for every agent)**: `brainstorming`, `writing-plans`, `planning-and-task-breakdown`, `incremental-implementation`, `spec-driven-development`, `constraint-driven-development`, `doubt-driven-development`, `source-driven-development`, `verification-before-completion`, `receiving-code-review`, `task-progress-reporting`

**Planning / product / documentation**: `idea-refine`, `documentation-and-adrs`, `domain-modeling`, `context-engineering`, `internal-comms`, `deprecation-and-migration`, `api-and-interface-design`, `portable-app-handoff`

**Software development / review / debugging**: `karpathy-guidelines`, `performance-optimization`, `security-and-hardening`, `live-react-runtime-qa`, `ponytail`, `ponytail-review`, `ponytail-audit`, `ponytail-debt`, `caveman-explore`, `caveman-review`

**Frontend / UI / visual design**: `frontend-design`, `ui-ux-pro-max`, `banner-design`

**Marketing / sales / social**: `marketing-strategy`, `sales-analysis-strategy`, `social-content-strategy`, `meta-social-publishing`

**Education / documents / data**: `markdown-pdf-pipeline`

**Hermes operations / team / networking**: `hermes-profile-provisioning`, `hermes-profile-hygiene`, `hermes-service-persistence`, `hermes-team-dashboard`, `hermes-gateway-web-ui`, `codi-team-dispatch`, `multi-profile-project-orchestration`, `cross-profile-cron-ops`, `kanban-rate-limit-resilience`, `large-project-gated-delivery`, `office-skill-distribution`, `skill-library-merge-dedupe`, `network-operations`, `service-availability-diagnosis`, `cpanel-shared-hosting-deploy`, `server-hygiene-cleanup`, `self-hosted-web-service-ops`

Skills listed above that are absent from `skills/` were held back (see `NOTICE.md`).

## Provenance and validation

Every skill is either first-party or matched against a verified upstream with permissive license terms; bundled license files are retained. Run the offline validator (checks structure, required files, portability and sensitive-data patterns):

```bash
python3 scripts/validate.py
```

## Contributing / issues

Found a licensing or provenance problem, or a leaked internal detail? Open an issue; it will be handled promptly.
