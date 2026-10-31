#!/usr/bin/env python3
"""Driver rantai kartu SERIAL berbasis cron (no-agent) — satu kartu aktif, tanpa kill.

Sunting konstanta di kepala berkas (BOARD, ORDER, WORKERS), pasang:
    hermes cron create "5m" --name "<proyek> DRIVER" --script serial_card_driver.py \
        --no-agent --deliver origin

Kontrak perilaku:
  * Ada kartu running/queued di ORDER  -> keluar TANPA menyentuh apa pun.
  * Tidak ada run aktif               -> buka MAKSIMAL satu kartu berikutnya, lalu keluar.
  * Tidak ada aksi                    -> stdout kosong (cron tidak mengirim pesan).
  * Diam >IDLE_MIN                    -> satu baris peringatan; TIDAK membunuh worker.
  * consecutive_failures >= FAIL_STOP -> cetak "butuh keputusan", tidak membuka lagi.

Aturan tetap: driver hanya membuka kartu yang pendahulunya `done`, dan hanya bila tidak ada kartu
lain yang berjalan. Dependency gate di Kanban tetap menjadi penegak utama.
"""
from __future__ import annotations

import os
import sqlite3
import subprocess
import time

# --- sunting di sini -----------------------------------------------------------------
BOARD = "<board-slug>"
ORDER = [                      # urutan tegas; JANGAN dibaca dari judul kartu
    ("V1", "t_xxxxxxxx"),
    ("V2", "t_xxxxxxxx"),
    ("V3", "t_xxxxxxxx"),
]
IDLE_MIN = 15                  # diam lebih lama -> peringatan saja, bukan kill
FAIL_STOP = 2                  # kegagalan beruntun -> minta keputusan manusia
# -------------------------------------------------------------------------------------

DB = os.path.expanduser(f"~/.hermes/kanban/boards/{BOARD}/kanban.db")


def sh(*args, timeout=180):
    r = subprocess.run(["hermes", *args], capture_output=True, text=True, timeout=timeout)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def load():
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True, timeout=15)
    con.row_factory = sqlite3.Row
    tasks = {r["id"]: dict(r) for r in con.execute("select * from tasks")}
    con.close()
    return tasks


def worker_idle_min(profile: str | None) -> float | None:
    if not profile:
        return None
    p = os.path.expanduser(f"~/.hermes/profiles/{profile}/state.db")
    if not os.path.exists(p):
        return None
    try:
        con = sqlite3.connect(f"file:{p}?mode=ro", uri=True, timeout=5)
        row = con.execute("select timestamp from messages order by rowid desc limit 1").fetchone()
        con.close()
        return (time.time() - float(row[0])) / 60 if row else None
    except Exception:
        return None


def main() -> None:
    tasks = load()

    # Guard single-flight: satu kartu saja boleh terbuka di SELURUH rantai.
    running = [k for k, tid in ORDER if tasks.get(tid, {}).get("status") in ("running", "queued")]
    if running:
        tid = dict(ORDER)[running[0]]
        idle = worker_idle_min(tasks[tid].get("assignee"))
        if idle is not None and idle > IDLE_MIN:
            print(f"! {running[0]} [{tasks[tid].get('assignee')}] diam {idle:.0f}m "
                  f"- perlu tindakan koordinator (cek state.db; jangan kill otomatis).")
        return

    for i, (key, tid) in enumerate(ORDER):
        t = tasks.get(tid, {})
        st = t.get("status")
        if st == "done":
            continue
        prev_done = i == 0 or tasks.get(ORDER[i - 1][1], {}).get("status") == "done"
        if not prev_done:
            return                      # menunggu pendahulu; diam
        if (t.get("consecutive_failures") or 0) >= FAIL_STOP:
            print(f"BLOCKED {key}: gagal {t['consecutive_failures']}x berturut - butuh keputusan.")
            return
        if st in ("blocked", "needs_input", "ready", "todo"):
            rc, _ = sh("kanban", "--board", BOARD, "unblock", tid,
                       "--reason", f"Driver: pendahulu selesai, {key} dibuka (satu worker).")
            rc2, out2 = sh("kanban", "--board", BOARD, "dispatch", "--max", "1")
            spawned = [l for l in out2.splitlines() if "Spawned:" in l or "->" in l]
            print(f"OPEN {key} ({tid}) unblock rc={rc} dispatch rc={rc2} "
                  f"{'; '.join(spawned[-2:])}")
        return                          # satu pembukaan per pass, lalu berhenti


if __name__ == "__main__":
    main()
