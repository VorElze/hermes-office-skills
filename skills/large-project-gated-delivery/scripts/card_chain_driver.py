#!/usr/bin/env python3
"""Driver rantai kartu Kanban: satu-satunya sumber dispatch untuk satu papan.

Membuka kartu berikutnya HANYA setelah kartu sekarang `done`, membunuh worker yang
benar-benar diam (bukan yang baru orientasi), dan keluar sendiri saat rantai selesai
atau butuh keputusan manusia. Cron laporan tetap terpisah dan read-only.

Pakai:
  1. Sunting CONSTANTS + CARDS (urutan sudah final, assignee per kartu).
  2. nohup python3 card_chain_driver.py > ~/.hermes/profiles/<p>/cache/scratch/orch.log 2>&1 &
  3. Bukti jalan: baris `UNBLOCK/DISPATCH ... rc=0` di log + `Spawned: 1` pada dispatch.
"""
import json
import os
import sqlite3
import subprocess
import time
from datetime import datetime

# ---- CONSTANTS -------------------------------------------------------------
BOARD = "<board>"
HERMES = "~/.hermes/bin/hermes"
HOME = os.path.expanduser("~")
DB = f"{HOME}/.hermes/kanban/boards/{BOARD}/kanban.db"
STATE = f"{HOME}/.hermes/profiles/koordinator/scripts/chain_state.json"

CARDS = [
    # {"label": "R1", "id": "t_xxx", "profile": "graphic-designer",
    #  "comment": "konteks: bukti kartu sebelumnya + kontrak + larangan"},
]

SLEEP = 120              # detik antar siklus
IDLE_PANIC = 18          # menit pesan terakhir worker dianggap mati
MIN_RUN_FOR_PANIC = 20   # jangan bunuh run yang baru mulai orientasi
MAX_REDISPATCH = 3       # per kartu, lalu serahkan ke manusia
AUTHOR = "koordinator"


# ---- helpers ---------------------------------------------------------------
def log(msg):
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


def kanban(*args, timeout=240):
    """Jalankan CLI kanban; cetak rc + baris terakhir supaya log jadi bukti."""
    p = subprocess.run([HERMES, "kanban", "--board", BOARD, *args],
                       capture_output=True, text=True, timeout=timeout)
    out = (p.stdout or "").strip() or (p.stderr or "").strip()
    tail = out.splitlines()[-1][:200] if out else ""
    log(f"{args[0].upper()} rc={p.returncode} {tail}")
    return p


def db():
    return sqlite3.connect(f"file:{DB}?mode=ro", uri=True, timeout=5)


def status(tid):
    with db() as c:
        row = c.execute("select status from tasks where id=?", (tid,)).fetchone()
    return row[0] if row else "missing"


def run_age_min(tid):
    with db() as c:
        row = c.execute(
            "select min(started_at) from task_runs where task_id=? and status='running'",
            (tid,)).fetchone()
    if not row or not row[0]:
        return None
    v = row[0] / 1000 if row[0] > 1e12 else row[0]
    return (time.time() - v) / 60


def idle_min(profile):
    """Umur pesan terakhir worker. Skema state.db beda antar profil: aman-gagal."""
    path = f"{HOME}/.hermes/profiles/{profile}/state.db"
    if not os.path.exists(path):
        return None
    try:
        c = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=5)
        row = c.execute("select max(timestamp) from messages").fetchone()
        c.close()
    except sqlite3.Error:
        return None
    if not row or not row[0]:
        return None
    try:
        v = float(row[0])
    except (TypeError, ValueError):
        return None
    v = v / 1000 if v > 1e12 else v
    return (time.time() - v) / 60


def load_state():
    try:
        with open(STATE) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_state(st):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    with open(STATE, "w") as f:
        json.dump(st, f, indent=2)


# ---- main ------------------------------------------------------------------
def main():
    state = load_state()
    for card in CARDS:
        tid, label, prof = card["id"], card["label"], card.get("profile", "")
        if state.get(label) == "done":
            continue
        state.setdefault("redispatch", {})
        log(f"--- {label} {tid} start={status(tid)}")

        while True:
            st = status(tid)
            if st in ("done", "archived"):
                state[label] = "done"
                save_state(state)
                log(f"{label} DONE -> lanjut")
                break

            if st == "blocked":
                kanban("unblock", tid, "--reason",
                       f"{label}: kartu sebelumnya selesai, gate tidak diturunkan")
                st = status(tid)
            if st == "triage":
                kanban("specify", tid, "--author", AUTHOR)
                st = status(tid)

            if st not in ("running", "ready", "todo"):
                log(f"{label} status tak tertangani: {st} -> berhenti, minta manusia")
                return 2

            if card.get("comment"):
                kanban("comment", tid, card["comment"], "--author", AUTHOR)
                card["comment"] = None  # sekali saja, tahan requeue lewat komentar
            kanban("dispatch", "--max", "1")

            # tunggu kartu ini selesai, sekaligus jaga stall
            while True:
                time.sleep(SLEEP)
                st = status(tid)
                if st in ("done", "archived"):
                    break
                age, idle = run_age_min(tid), idle_min(prof)
                log(f"{label} {st} run={age and round(age)}m idle={idle and round(idle)}m")
                if st == "blocked":
                    break  # tangani di loop luar
                if age is None or idle is None:
                    continue
                if idle < IDLE_PANIC or age < MIN_RUN_FOR_PANIC:
                    continue
                n = state["redispatch"].get(label, 0) + 1
                state["redispatch"][label] = n
                save_state(state)
                if n > MAX_REDISPATCH:
                    log(f"{label} stall {n}x -> berhenti, minta manusia")
                    return 3
                log(f"{label} STALL idle={round(idle)}m run={round(age)}m -> reclaim #{n}")
                kanban("reclaim", tid)
                kanban("dispatch", "--max", "1")

    log("semua kartu terminal -> driver keluar")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
