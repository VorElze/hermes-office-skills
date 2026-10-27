# User guide

## 1. Get repository

```bash
git clone https://github.com/VorElze/hermes-office-skills.git
cd hermes-office-skills
```

Anyone can clone this public repository without authentication. Provenance and licensing for every included skill were reviewed before publication (see `NOTICE.md`).

## 2. Choose skills

Browse `docs/CATALOG.md`, `manifest.json`, or `skills/`. Each skill folder is one unit; required references/scripts stay beside `SKILL.md`. Start with role bundles in root README; enable only what agent needs.

## 3. Install per agent

### Hermes

Project/user paths and syntax may vary by Hermes version. Typical profile copy:

```bash
mkdir -p ~/.hermes/profiles/<PROFILE>/skills
cp -R skills/<skill-name> ~/.hermes/profiles/<PROFILE>/skills/
```

For all profiles, Hermes supports shared external skill directories in its configuration (check installed version's docs). Avoid copying duplicate folders to every profile. Inspect with `hermes -p <PROFILE> skills list --enabled-only`; reload session.

### Claude Code

```bash
mkdir -p .claude/skills
cp -R skills/<skill-name> .claude/skills/
```

Or install in `~/.claude/skills/` for user scope, per current Claude Code docs. Skill name folder must contain `SKILL.md`.

### Codex

```bash
mkdir -p .agents/skills
cp -R skills/<skill-name> .agents/skills/
```

Use `~/.agents/skills/` for user-wide scope when supported by installed release. Restart or reload the Codex session and verify discovery.

### Claude Desktop / other clients

Do not assume Claude Code paths apply to Claude Desktop. Check client docs for Agent Skills support and discovery path. If unsupported, paste chosen `SKILL.md` into project instructions or attach as context; include needed references. Recheck any command/tool names that your client cannot provide.

## 4. Adapt to available tools

Skills describe a workflow, not bundled executable tools. Before use:

1. Read `SKILL.md` and required `references/`.
2. Check tool names, shell commands, path examples, permissions, OS and versions.
3. Replace placeholders like `<PATH_ANDA>`, `<PROFILE>`, `<nama klien>` with local values. Never store secrets in skill files.
4. Remove instructions that conflict with policy or target agent's capabilities.
5. For network, deletion, publishing, deployments, credentials, payments or external messages, keep explicit human approval.

## 5. Automatic vs manual

Discovery and invocation are platform-dependent. Hermes typically injects available skill summaries and agent may load relevant skill when task matches; this is not guaranteed. Claude Code/Codex may discover skills automatically when placed in documented folders. Other agents may require manual selection or context attachment. Installing a folder does not install MCP servers, CLIs, SDKs, credentials, browsers, or permissions.

## 6. Update

```bash
cd hermes-office-skills
git pull --ff-only
```

Review changed instructions before copying updates to production agents. Pin a commit/tag for reproducibility.

## 7. Remove

Delete selected skill folder from the agent's skills directory, then reload session. For shared folder, remove skill from agent's disabled/allow list as applicable.

## 8. Contribute safely

- One folder per skill, clear `SKILL.md` frontmatter and concise description.
- Use generic paths and examples; avoid internal names, customer data, private prompts, tokens and account IDs.
- Declare source, license, required tools, OS, side effects and approval gates.
- Run `python3 scripts/validate.py`.
- Submit PR with behavior, testing and provenance.

## 9. Troubleshooting

- Skill missing: path must be `<skills-root>/<skill-name>/SKILL.md`; reload agent and inspect its documented discovery path.
- Skill listed but tool call fails: install/configure tool separately; skill file does not provide tool access.
- Wrong skill auto-selected: reduce installed set or configure exclusions; descriptions determine matching.
- Claude Desktop differs from Claude Code: use Desktop-specific docs; do not assume `.claude/skills` is supported there.
