#!/usr/bin/env python3
"""Verify one profile's `skills.auto_load`: 4 layers, exit 1 on any failure.

Usage (HERMES_HOME must be set before python starts):
  HERMES_HOME=~/.hermes/profiles/<id> python3 verify-autoload.py <id>
  HERMES_HOME=~/.hermes              python3 verify-autoload.py default

Layers:
  1. YAML shape      -- auto_load parses as a non-empty list[str]
  2. Loader API      -- resolve_auto_load_skills() agrees with the YAML
  3. Render          -- build_auto_load_prompt() reports missing == []
  4. No collisions   -- no auto_load name also sits in skills.disabled

Layer 3 measures what the agent actually loads. Layer 4 catches the
silent-skip case: resolve_auto_load_skills() does NOT consult
global_disabled_skill_names() (the skill loader does), so a colliding
name vanishes with only a warning.
"""
import os
import re
import sys
from pathlib import Path


def home_for(role: str) -> Path:
    if role == "default":
        return Path("~/.hermes")
    return Path(f"~/.hermes/profiles/{role}")


def yaml_items(home: Path) -> list[str]:
    """Parse skills.auto_load straight out of config.yaml (layer 1)."""
    cfg = home / "config.yaml"
    if not cfg.is_file():
        return []
    txt = cfg.read_text(encoding="utf-8")
    m = re.search(r"^skills:\n((?:[ \t]+.*\n|\n)*)", txt, re.M)
    block = m.group(1) if m else ""
    am = re.search(r"^  auto_load:\n((?:    - .+\n)+)", block, re.M)
    if not am:
        return []
    return [x.strip().strip("'\"") for x in re.findall(r"    - (.+)", am.group(1))]


def main(role: str) -> int:
    home = home_for(role)
    os.environ["HERMES_HOME"] = str(home)   # must precede agent imports
    sys.path.insert(0, "~/.hermes/hermes-agent")

    from agent.skill_commands import (  # noqa: E402
        build_auto_load_prompt,
        resolve_auto_load_skills,
    )
    from agent.skill_utils import get_disabled_skill_names  # noqa: E402

    expected = yaml_items(home)
    l1 = bool(expected) and all(isinstance(x, str) and x for x in expected)

    resolved = resolve_auto_load_skills()
    l2 = resolved == expected

    # build_auto_load_prompt() returns THREE values, not a string.
    _prompt, loaded, missing = build_auto_load_prompt()
    l3 = (not missing) and loaded == expected

    disabled = set(get_disabled_skill_names())
    clash = [n for n in expected if n in disabled]
    l4 = not clash

    print(f"profile            {role}")
    print(f"home               {home}")
    print(f"L1 YAML shape      {l1}  ({len(expected)} items)")
    print(f"L2 loader API      {l2}")
    print(f"L3 render          {l3}  loaded={len(loaded)} missing={missing}")
    print(f"L4 no collisions   {l4}" + (f"  CLASH={clash}" if clash else ""))

    if not l1:
        print("FAIL: skills.auto_load missing or not a list of non-empty strings")
    if not l2:
        print(f"  expected {expected}")
        print(f"  resolved {resolved}")
    if clash:
        print("FAIL: these names are in BOTH auto_load and skills.disabled")
        print("      (resolve_auto_load_skills() ignores disabled; the skill")
        print("       is dropped with a warning only -- fix config, not code)")

    ok = l1 and l2 and l3 and l4
    print("ALL PASS" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1]))
