#!/usr/bin/env python3
"""no_agent watchdog template: catch hung workers + scrub dead pool entries.

Copy to ~/.hermes/profiles/<profile>/scripts/<name>.py, set CARD/PROFILE, and
register a cron job with no_agent=true, script=<name>.py, schedule='every 5m',
deliver='local' (stdout is delivered, so stay SILENT when healthy).

Logic (both actions cost zero requests):
1. Card 'running' but no message growth in PROFILE's state.db for IDLE_LIMIT
   seconds AND no child process executing (php/chrome/curl) -> worker hung on
   one API call (heartbeat keeps beating; configured timeouts may not fire)
   -> kill PID + `hermes kanban dispatch` for a fresh run. Progress survives
   because the worker comments per unit. If children EXIST, leave it alone:
   a real test runs minutes without messages.
2. credential_pool entry with an empty access_token -> delete it (it burns one
   rotation attempt). Entries sourced from env rebuild themselves on worker
   start; scrubbing here keeps the pool clean regardless.
"""
import json
import os
import sqlite3
import subprocess
import time

CARD = "t_REPLACE_ME"        # kanban card to guard
PROFILE = "REPLACE_ME"       # profile id owning state.db + auth.json
IDLE_LIMIT = 300             # seconds without messages = hung
WORK_CMD = f"hermes_cli.main -p {PROFILE}"

PDIR = f"~/.hermes/profiles/{PROFILE}"
DB = f"{PDIR}/state.db"
AUTH = f"{PDIR}/auth.json"
HERMES = "<HOME_ANDA>/.local/bin/hermes"


def main():
    actions = []
    try:
        r = subprocess.run([HERMES, "kanban", "show", CARD],
                           capture_output=True, text=True, timeout=30)
        if "running" in r.stdout:
            c = sqlite3.connect(DB)
            last = c.execute("SELECT max(timestamp) FROM messages").fetchone()[0]
            c.close()
            idle = time.time() - float(last)
            if idle >= IDLE_LIMIT:
                pids = subprocess.run(["pgrep", "-f", WORK_CMD],
                                      capture_output=True, text=True).stdout.split()
                has_kid = False
                for p in pids:
                    kids = subprocess.run(["ps", "--ppid", p, "-o", "args="],
                                          capture_output=True, text=True).stdout
                    if any(x in kids for x in ("php", "chrome", "curl")):
                        has_kid = True
                        break
                if pids and not has_kid:
                    subprocess.run(["kill", "-9"] + pids, capture_output=True)
                    time.sleep(3)
                    subprocess.run([HERMES, "kanban", "dispatch"],
                                   capture_output=True, timeout=90)
                    actions.append(f"kill+respawn {PROFILE} (idle {int(idle)}s)")
    except Exception as e:
        actions.append(f"err-liveness: {type(e).__name__}")

    try:
        d = json.load(open(AUTH))
        ents = d.get("credential_pool", {}).get("anthropic", [])
        clean = [e for e in ents if (e.get("access_token") or "")]
        if len(clean) != len(ents):
            d["credential_pool"]["anthropic"] = clean
            d["updated_at"] = time.time()
            tmp = AUTH + ".tmp"
            json.dump(d, open(tmp, "w"), indent=1)
            os.replace(tmp, AUTH)
            actions.append(f"pool {len(ents)}->{len(clean)} entries")
    except Exception as e:
        actions.append(f"err-pool: {type(e).__name__}")

    if actions:
        print(" | ".join(actions), flush=True)   # silent when healthy


if __name__ == "__main__":
    main()
