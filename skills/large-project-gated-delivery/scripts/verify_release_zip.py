#!/usr/bin/env python3
"""Audit a release ZIP before it is sent to the owner or deployed.

Checks: CRC integrity, file count, top-level roots (double-nesting), forbidden
entries, and secret-pattern hits CLASSIFIED (docblock / markup / fixture /
reader / candidate leak). Only CANDIDATE-LEAK is reported as a finding.

Usage:
    python3 verify_release_zip.py <release.zip> [--root <expected-root>] [--allow-sql]

Exit codes: 0 clean, 1 review needed, 2 unreadable archive.
"""
import argparse
import json
import re
import sys
import zipfile
from collections import Counter

FORBIDDEN = [
    (re.compile(r'(^|/)\.env(\.(local|prod|production|dev|staging))?$'), 'env-file'),
    (re.compile(r'(^|/)\.git/'), 'git-dir'),
    (re.compile(r'(^|/)(id_rsa|id_ed25519|auth\.json|.*\.(pem|p12|pfx|key))$'), 'private-key'),
    (re.compile(r'(^|/)(node_modules|__pycache__|\.venv|venv)/'), 'dev-artifact'),
    (re.compile(r'\.sql$'), 'sql-file'),
]

SECRET = re.compile(
    r"(DB_PASS(WORD)?\s*=\s*['\"][^'\"]+"
    r"|-----BEGIN [A-Z ]*PRIVATE KEY-----"
    r"|\b(sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{30,}|AKIA[0-9A-Z]{16})\b"
    r"|password\s*[:=]\s*['\"][^'\"]{6,}['\"])",
    re.I,
)

TEXT_EXT = ('.php', '.md', '.json', '.ini', '.yml', '.yaml', '.sql', '.js',
            '.sh', '.txt', '.htaccess', '.env', '.example')


def classify(line, path):
    low = line.lower()
    stripped = line.lstrip()
    if 'array{' in line or '@param' in low or stripped.startswith(('*', '//', '#')):
        return 'docblock/type-hint'
    if 'type="password"' in low or "type='password'" in low:
        return 'markup'
    if any(k in path for k in ('/tests/', '/test/', '/fixtures/', '/seeds/', '/demo')):
        return 'fixture'
    if '$_' in line or 'getenv' in low or 'env(' in low:
        return 'reader'
    return 'CANDIDATE-LEAK'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('zip')
    ap.add_argument('--root', default=None, help='expected single top-level folder')
    ap.add_argument('--allow-sql', action='store_true', help='plain .sql is schema, not a dump')
    args = ap.parse_args()

    try:
        zf = zipfile.ZipFile(args.zip)
    except Exception as exc:                                    # noqa: BLE001
        print(json.dumps({'error': str(exc), 'zip': args.zip}))
        return 2

    names = zf.namelist()
    files = [n for n in names if not n.endswith('/')]
    roots = Counter(n.split('/', 1)[0] for n in files)
    out = {
        'zip': args.zip,
        'crc_ok': zf.testzip() is None,
        'files': len(files),
        'uncompressed_bytes': sum(i.file_size for i in zf.infolist()),
        'roots': dict(roots),
        'findings': [],
    }

    if len(roots) > 1:
        out['findings'].append({'class': 'multiple-roots', 'detail': dict(roots)})
    if args.root and list(roots) != [args.root]:
        out['findings'].append({'class': 'unexpected-root', 'detail': list(roots)})

    for name in files:
        for rx, cls in FORBIDDEN:
            if not rx.search(name):
                continue
            if cls == 'sql-file' and (args.allow_sql or name.endswith('schema.sql')):
                continue
            out['findings'].append({'class': cls, 'path': name})

    secret_classes = Counter()
    for name in files:
        if not name.endswith(TEXT_EXT):
            continue
        try:
            if zf.getinfo(name).file_size > 300_000:
                continue
            text = zf.read(name).decode('utf-8', 'replace')
        except Exception:                                       # noqa: BLE001
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if not SECRET.search(line):
                continue
            cls = classify(line, '/' + name)
            secret_classes[cls] += 1
            if cls == 'CANDIDATE-LEAK':
                out['findings'].append({'class': cls, 'path': name, 'line': i,
                                        'excerpt': line.strip()[:80]})
    out['secret_hits_by_class'] = dict(secret_classes)

    blocking = [f for f in out['findings'] if f['class'] != 'sql-file']
    out['verdict'] = 'CLEAN' if out['crc_ok'] and not blocking else 'REVIEW'
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if out['verdict'] == 'CLEAN' else 1


if __name__ == '__main__':
    sys.exit(main())
