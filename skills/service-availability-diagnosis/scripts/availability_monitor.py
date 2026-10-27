#!/usr/bin/env python3
"""Availability monitor: SITE vs PATH classification, alerts only on change.

Usage: AVAIL_HOST=example.com AVAIL_STATE=/tmp/state.txt python3 monitor.py

States (see SKILL.md): UP / PATH_BLOCKED / SITE_DOWN_SUSPECTED / INCONCLUSIVE.
Exit 0 always; prints only when the state file value CHANGED (anti-spam).
Adapted from the absensi monitor probe — verify by running twice: first run
should classify, second (no change) should be silent.
"""
import json
import os
import socket
import subprocess
import time
import urllib.parse
import urllib.request

HOST = os.environ.get("AVAIL_HOST", "example.com")
STATE = os.environ.get("AVAIL_STATE", "/tmp/availability_monitor_state.txt")
BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")


def direct_probe():
    """Bounded curl probes (urllib/WAF fingerprint failures are a known pitfall)."""
    try:
        ip = socket.gethostbyname(HOST)
    except Exception as exc:
        return False, f"DNS failed: {exc}"
    try:
        with socket.create_connection((ip, 443), timeout=5):
            pass
    except Exception as exc:
        return False, f"DNS {ip}, TCP 443 failed: {exc}"
    for _ in range(2):
        r = subprocess.run(
            ["/usr/bin/curl", "-sS", "-o", "/dev/null", "-w", "%{http_code}",
             "--max-time", "8", f"https://{HOST}/"],
            capture_output=True, text=True, timeout=12)
        if r.returncode == 0 and r.stdout.strip() == "200":
            return True, f"HTTPS 200 from this host (IP {ip})"
    return False, f"DNS {ip}, TCP 443 ok, HTTPS not 200"


def external_probe():
    """Multi-node check; returns (alive, detail, have_samples)."""
    ok, failed, check_err = [], [], ""
    for _ in range(3):
        try:
            url = ("https://check-host.net/check-http?host="
                   + urllib.parse.quote(f"https://{HOST}/", safe="")
                   + "&max_nodes=4")
            req = urllib.request.Request(
                url, headers={"Accept": "application/json", "User-Agent": BROWSER_UA})
            with urllib.request.urlopen(req, timeout=15) as r:
                rid = json.loads(r.read().decode()).get("request_id")
            if not rid:
                failed.append("no request_id")
                continue
            time.sleep(12)
            req2 = urllib.request.Request(
                f"https://check-host.net/check-result/{rid}",
                headers={"Accept": "application/json", "User-Agent": BROWSER_UA})
            with urllib.request.urlopen(req2, timeout=20) as r:
                result = json.loads(r.read().decode())
            got = False
            for node, values in result.items():
                if not isinstance(values, list) or not values:
                    continue
                first = values[0]
                if not isinstance(first, list) or len(first) < 4:
                    continue
                got = True
                if first[2] == "OK" and str(first[3]) == "200":
                    ok.append(node.split(".")[0])
            if not got:
                failed.append("no node samples")
        except Exception as exc:
            check_err = f"checker: {exc}"
        if len(set(ok)) >= 2:
            break
        time.sleep(2)
    if ok:
        return True, f"external 200 from {', '.join(sorted(set(ok)))}", True
    if failed or check_err:
        return False, "; ".join((failed[-3:] + ([check_err] if check_err else []))), bool(failed) or bool(ok)
    return False, "no external samples", False


def classify(local_ok, local_detail):
    if local_ok:
        return "UP", local_detail
    ext_alive, ext_detail, have_samples = external_probe()
    if ext_alive:
        return "PATH_BLOCKED", (
            f"OUR PATH BLOCKED (site is NOT down): {local_detail}. "
            f"Site healthy from outside: {ext_detail}. Do NOT report an "
            f"outage to {HOST}'s owner; diagnose our route/ASN instead.")
    if not have_samples:
        return "INCONCLUSIVE", (
            f"Cannot determine: {local_detail}; external checker gave no "
            f"samples ({ext_detail}). Claim nothing; re-measure later.")
    return "INCONCLUSIVE", (
        f"Cannot determine: {local_detail}; external checks did not prove "
        f"the site down ({ext_detail}). Re-measure before reporting.")


def main():
    local_ok, local_detail = direct_probe()
    state, detail = classify(local_ok, local_detail)
    try:
        with open(STATE) as f:
            previous = f.read().strip()
    except FileNotFoundError:
        previous = ""
    if state == previous:
        return 0
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    with open(STATE, "w") as f:
        f.write(state)
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{state}] {HOST} ({ts}): {detail} (previous={previous or 'none'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
