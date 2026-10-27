#!/usr/bin/env python3
"""Basic repository hygiene validation; not a license/legal audit."""
from pathlib import Path
import re, sys
root=Path(__file__).resolve().parents[1]
skills=root/"skills"
errors=[]; names=[]
secret=re.compile(r"(?i)(gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|Bearer\s+[A-Za-z0-9._-]{20,}|-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----)")
private=re.compile(r"(?i)(/root/(?:projects|\.hermes)|telegram:direct:\d{9,12}|\b(Mave|Dean|Rendra|Laras|Bima)\b|profiles/(?:codi|amanda)|vault_[0-9a-f]{12}|opus-5-5|sonnet-5\b|\d{9,12}\.bot)")
if not skills.is_dir(): errors.append("missing skills/")
else:
    for d in sorted(skills.iterdir()):
        if not d.is_dir(): continue
        names.append(d.name)
        f=d/"SKILL.md"
        if not f.is_file(): errors.append(f"{d.name}: missing SKILL.md"); continue
        text=f.read_text(errors="replace")
        if not text.startswith("---\n") or text.count("---")<2: errors.append(f"{d.name}: missing YAML frontmatter")
        if not re.search(r"^name:\s*",text,re.M): errors.append(f"{d.name}: missing name")
        if not re.search(r"^description:\s*",text,re.M): errors.append(f"{d.name}: missing description")
        for p in d.rglob("*"):
            if not p.is_file() or p.suffix.lower() not in {".md",".py",".sh",".txt",".json",".yaml",".yml"}: continue
            body=p.read_text(errors="replace")
            if secret.search(body): errors.append(f"{p.relative_to(root)}: possible secret")
            if private.search(body): errors.append(f"{p.relative_to(root)}: possible private path/ID")
if len(names)!=len(set(names)): errors.append("duplicate skill directory")
print(f"skills: {len(names)}")
if errors:
    print("FAIL")
    print("\n".join(f"- {e}" for e in errors))
    sys.exit(1)
print("PASS: basic structure and secret/path patterns only (not a license audit)")
