#!/usr/bin/env python3
"""Jalankan perintah remote via SSH ke shared hosting cPanel, memakai password
dari vault tanpa pernah mencetaknya ke output/chat.

Pakai:
    python3 ssh_vault.py 'ls -la ~/public_html'
    python3 ssh_vault.py --host contoh.com --user aku 'git --version'

Password diambil dari entri vault (profil HERMES aktif) lalu diserahkan ke ssh
lewat SSH_ASKPASS, sehingga nilainya tidak pernah muncul di argv, stdout, atau
transkrip. Yang dicetak hanya stdout/stderr perintah dan exit code.

Butuh sshpass TIDAK perlu; cukup binary `ssh` dan python3.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile

DEFAULT_VAULT_HANDLE = "vault_<handle>"  # entri vault cPanel <proyek> (isi handle milikmu)


def _load_vault_store():
    """Import agent.vault_store dari instalasi Hermes aktif."""
    candidates = []
    env_root = os.environ.get("HERMES_HOME", "")
    if env_root:
        candidates.append(env_root)
    candidates.append("~/.hermes")
    for root in candidates:
        for dirpath, dirnames, filenames in os.walk(root):
            if "vault_store.py" in filenames and dirpath.endswith("agent"):
                sys.path.insert(0, os.path.dirname(dirpath))
                try:
                    from agent.vault_store import get_vault_store  # type: ignore

                    return get_vault_store
                except Exception:
                    continue
    # fallback: andalkan instalasi yang terdaftar di sys.path
    from agent.vault_store import get_vault_store  # type: ignore

    return get_vault_store


def _resolve_password(handle: str) -> str:
    get_vault_store = _load_vault_store()
    store = get_vault_store()
    secret = store.resolve_secret(handle)
    pw = secret.get("password") or secret.get("secret") or ""
    if not pw:
        raise SystemExit(f"Tidak ada password yang bisa di-resolve untuk handle {handle}")
    return pw


def run_ssh(host: str, user: str, command: str, handle: str, port: int = 22, timeout: int = 120) -> int:
    pw = _resolve_password(handle)

    fd, askpass_path = tempfile.mkstemp(prefix="askpass_", suffix=".sh")
    os.write(fd, b"#!/bin/sh\nprintf '%s' \"$HERMES_SSH_PW\"\n")
    os.close(fd)
    os.chmod(askpass_path, 0o700)

    env = dict(os.environ)
    env["HERMES_SSH_PW"] = pw
    env["SSH_ASKPASS"] = askpass_path
    env["SSH_ASKPASS_REQUIRE"] = "force"
    env["DISPLAY"] = env.get("DISPLAY", ":0")

    ssh_cmd = [
        "ssh",
        "-p", str(port),
        "-o", "StrictHostKeyChecking=no",
        "-o", "PreferredAuthentications=password",
        "-o", "PubkeyAuthentication=no",
        "-o", "NumberOfPasswordPrompts=1",
        "-o", "ConnectTimeout=10",
        f"{user}@{host}",
        command,
    ]
    try:
        proc = subprocess.run(ssh_cmd, env=env, capture_output=True, text=True, timeout=timeout)
    finally:
        try:
            os.remove(askpass_path)
        except OSError:
            pass

    print(f"=== EXIT: {proc.returncode} ===")
    if proc.stdout:
        print(proc.stdout)
    if proc.stderr.strip():
        print("--- stderr ---")
        print(proc.stderr.strip()[:1500])
    return proc.returncode


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", help="perintah yang dijalankan di host remote")
    ap.add_argument("--host", default="panel.example.com")
    ap.add_argument("--user", default="<proyek>660")
    ap.add_argument("--port", type=int, default=22)
    ap.add_argument("--handle", default=DEFAULT_VAULT_HANDLE)
    args = ap.parse_args()
    return run_ssh(args.host, args.user, args.command, args.handle, args.port)


if __name__ == "__main__":
    raise SystemExit(main())
