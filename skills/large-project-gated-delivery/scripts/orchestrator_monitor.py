#!/usr/bin/env python3
"""Orkestrator papan Kanban: gerbang provider + auto-release ber-guard + stall reclaim.

Template untuk cron no-agent (stdout = pesan yang dikirim ke owner). Kosongkan stdout
(= tidak print apa pun) saat tidak ada kartu aktif supaya tidak ada pesan terkirim.

Pasang dengan:
  hermes cron create "15m" --name "<proyek> orkestrasi" \
      --script orchestrator_monitor.py --no-agent --deliver origin --workdir <repo>

Konstanta yang WAJIB disesuaikan: BOARD, PROBE_PROFILE, PROVIDER (base_url/provider id),
PROBE_MODEL, PROVIDER_HOLD (prefix kartu yang ditahan karena provider), KEEP_BLOCKED,
BUDGET (menit per kartu), STALL_MIN.

Prinsip yang tidak boleh dilanggar:
  * token hanya dibaca dari auth.json, tidak pernah dicetak
  * jangan dispatch apa pun saat probe != 200
  * release hanya bila semua parent done DAN assignee tidak sibuk
  * stall diukur dari max(timestamp) messages state.db, bukan heartbeat
  * setelah 429: maksimal satu spawn per siklus
"""
from __future__ import annotations

import json
import os
import shutil
import sqlite3
import subprocess
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

# ---- sesuaikan ----------------------------------------------------------------
BOARD = os.environ.get("KANBAN_BOARD", "<board-slug>")
PROBE_PROFILE = os.environ.get("PROBE_PROFILE", "program-developer")
PROVIDER_BASE = os.environ.get("PROVIDER_BASE", "https://api.example-proxy.com/v1")
PROBE_MODEL = os.environ.get("PROBE_MODEL", "claude-<model>")
MAX_DISPATCH = int(os.environ.get("MAX_DISPATCH", "1"))
STALL_MIN = int(os.environ.get("STALL_MIN", "12"))
PROVIDER_HOLD: tuple[str, ...] = ()          # prefix label, mis. ("W1-01", "W1-02")
PROVIDER_HOLD_IDS: tuple[str, ...] = ()      # alternatif tahan-rename: ("t_03ecd0c7", …)
KEEP_BLOCKED: tuple[str, ...] = ()           # kartu yang menunggu owner/kredensial
BUDGET: dict[str, int] = {}                  # {"design-system": 240, ...}
# -------------------------------------------------------------------------------

WIB = timezone(timedelta(hours=7))
H = shutil.which("hermes") or os.path.expanduser("~/.hermes/hermes-agent/.hermes/bin/hermes")
DB = os.path.expanduser(f"~/.hermes/kanban/boards/{BOARD}/kanban.db")


# --- kanban helpers ------------------------------------------------------------
def k(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([H, "kanban", "--board", BOARD, *args],
                          capture_output=True, text=True, timeout=300)


def snapshot():
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True, timeout=15)
    con.row_factory = sqlite3.Row
    tasks = {r["id"]: dict(r) for r in con.execute("select * from tasks")}
    links = [tuple(x) for x in con.execute("select parent_id, child_id from task_links")]
    con.close()
    parents: dict[str, list[str]] = {}
    for p, c in links:
        parents.setdefault(c, []).append(p)
    return tasks, parents


# --- probe (1 request per entry; token tidak pernah dicetak) ---------------------
def probe() -> tuple[bool, str]:
    """Coba entry pool berurutan sampai ada 200; laporkan kode per entry.

    Satu entry bisa mati (401) sementara entry lain sehat — memprobe entry #0 saja
    membuat gerbang menahan papan selamanya padahal worker bisa jalan.
    """
    path = os.path.expanduser(f"~/.hermes/profiles/{PROBE_PROFILE}/auth.json")
    try:
        pool = json.load(open(path))["credential_pool"]
    except Exception as exc:
        return False, f"kredensial tak terbaca: {type(exc).__name__}"
    entries = []
    for lst in pool.values():
        for e in lst or []:
            key = next((e.get(f) for f in ("access_token", "api_key") if e.get(f)), None)
            if key:
                entries.append(key)
    if not entries:
        return False, "pool kosong"
    verdicts: list[str] = []
    for idx, key in enumerate(entries[:4], start=1):
        body = json.dumps({"model": PROBE_MODEL, "max_tokens": 4,
                           "messages": [{"role": "user", "content": "ok"}]}).encode()
        req = urllib.request.Request(
            f"{PROVIDER_BASE}/v1/messages", data=body,
            headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                     "content-type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                return True, f"HTTP {r.status} entry#{idx}"
        except urllib.error.HTTPError as exc:
            verdicts.append(f"#{idx} {exc.code}")
        except Exception as exc:           # timeout / DNS / TLS
            verdicts.append(f"#{idx} {type(exc).__name__}")
    return False, " ".join(verdicts)


# --- sinyal aktivitas worker ---------------------------------------------------
def last_epoch(profile: str):
    p = os.path.expanduser(f"~/.hermes/profiles/{profile}/state.db")
    if not os.path.exists(p):
        return None
    try:
        con = sqlite3.connect(f"file:{p}?mode=ro", uri=True, timeout=10)
        row = con.execute("select max(timestamp) from messages").fetchone()
        con.close()
    except Exception:
        return None
    if not row or row[0] is None:
        return None
    v = row[0]
    try:
        if isinstance(v, (int, float)) or str(v).replace(".", "", 1).isdigit():
            f = float(v)
            return f / 1000 if f > 1e12 else f
        return datetime.fromisoformat(str(v).replace("Z", "+00:00")).timestamp()
    except Exception:
        return None


def label(task: dict) -> str:
    return task["title"].split("—")[0].strip()


def budget_of(title: str):
    for key, minutes in BUDGET.items():
        if key in title:
            return minutes
    return None


# --- jalan ---------------------------------------------------------------------
def main() -> None:
    tasks, parents = snapshot()
    if not any(t["status"] in ("running", "ready", "todo", "blocked") for t in tasks.values()):
        return                                   # papan tidur -> tidak ada pesan

    now = time.time()
    actions: list[str] = []
    healthy, why = probe()

    # 1. buka kartu yang ditahan karena provider, hanya saat sehat
    #    cocokkan lewat ID eksplisit (PROVIDER_HOLD_IDS) atau prefix label — ID lebih tahan rename
    if healthy and (PROVIDER_HOLD or PROVIDER_HOLD_IDS):
        for t in tasks.values():
            if t["status"] != "blocked":
                continue
            if t["id"] in PROVIDER_HOLD_IDS or label(t).startswith(PROVIDER_HOLD):
                if k("unblock", t["id"]).returncode == 0:
                    actions.append(f"buka {label(t)} (provider sehat)")

    # 2. auto-release rantai ber-guard assignee
    tasks, parents = snapshot()
    busy = {t["assignee"] for t in tasks.values() if t["status"] == "running"}
    for t in tasks.values():
        if t["status"] != "blocked" or t["block_kind"]:
            continue
        if any(x in t["title"] for x in KEEP_BLOCKED) or t["assignee"] in busy:
            continue
        ps = parents.get(t["id"], [])
        if ps and all(tasks[p]["status"] == "done" for p in ps):
            if k("unblock", t["id"]).returncode == 0:
                actions.append(f"release {label(t)}")
                busy.add(t["assignee"])

    # 3. stall -> reclaim (bukan heartbeat)
    for t in tasks.values():
        if t["status"] != "running":
            continue
        last = last_epoch(t["assignee"])
        if last and (now - last) / 60 > STALL_MIN:
            k("reclaim", t["id"])
            actions.append(f"RECLAIM {label(t)} diam {(now - last) / 60:.0f}m")

    # 4. dispatch hanya bila provider sehat
    if healthy:
        r = k("dispatch", "--max", str(MAX_DISPATCH), "--json")
        try:
            for s in (json.loads(r.stdout or "{}").get("spawned") or []):
                actions.append(f"spawn {s.get('task_id') or s.get('id')}")
        except Exception:
            pass

    # 5. laporan
    tasks, _ = snapshot()
    by = lambda st: [t for t in tasks.values() if t["status"] == st]  # noqa: E731
    done, running, ready, todo, blocked = by("done"), by("running"), by("ready"), by("todo"), by("blocked")
    out = [f"{BOARD} — {datetime.now(WIB).strftime('%d %b %H:%M WIB')}",
           f"provider {'SEHAT (' + why + ')' if healthy else 'TERHAMBAT (' + why + ')'}",
           f"done {len(done)} · running {len(running)} · siap {len(ready)} · "
           f"tunggu-dep {len(todo)} · blocked {len(blocked)}"]
    for t in running:
        b = budget_of(t["title"])
        mins = (now - float(t["started_at"] or now)) / 60
        flag = "🛑" if b and mins > b else ("⚠️" if b and mins > 0.8 * b else "")
        out.append(f"• RUN {label(t)} [{t['assignee']}] {mins:.0f}m/{b or '?'}m {flag}".rstrip())
    out += [f"• SIAP {label(t)} [{t['assignee']}]" for t in ready]
    out += [f"• TUNGGU-DEP {label(t)} [{t['assignee']}]" for t in todo]
    out += [f"• BLOCKED {label(t)} — {t['block_kind'] or 'manual'}" for t in blocked]
    out.append("aksi: " + " · ".join(actions) if actions
               else "tidak ada kartu yang bisa jalan sekarang." if not running and not ready
               else "tidak ada aksi baru.")
    print("\n".join(out))


if __name__ == "__main__":
    main()
