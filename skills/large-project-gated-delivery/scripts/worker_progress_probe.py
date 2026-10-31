#!/usr/bin/env python3
"""Probe: apakah worker benar-benar MENULIS, atau hanya membaca berulang.

Menjawab pertanyaan "statusnya running, tapi ada progres nyata?" dengan angka,
bukan dengan membaca status kartu. Read-only terhadap state.db profil worker
(opsional: read-only juga terhadap kanban.db papan).

Pakai:
    python3 worker_progress_probe.py --profile program-developer --minutes 30
    python3 worker_progress_probe.py --db /path/state.db --minutes 45
    python3 worker_progress_probe.py --profile graphic-designer --board siraga --task t_abc123

Flag --board/--task menambahkan lokasi worktree kartu + commit/berkas di branch-nya.
Itu wajib: worker menulis di worktree kartu, jadi repo proyek utama selalu tampak
bersih dan bisa memancing kesimpulan palsu "0 berkas berubah".

Keluaran ringkas (beberapa baris) supaya tidak terpotong oleh pemanggil.
Verdict: DIAM / LOOP BACA / LOOP SKILL / fase orientasi / MENULIS.
"""
import argparse
import collections
import json
import os
import sqlite3
import subprocess
import time

WRITE_TOOLS = {
    "write_file", "patch", "edit_file", "multi_edit", "apply_patch",
    "str_replace_editor", "write", "notebook_edit",
}
READ_TOOLS = {"read_file", "search_files", "view", "read"}
# Loop khas: model memanggil skill berulang -> guardrail "returned the same result
# 5 times" -> konteks membengkak -> kompresi -> turn habis -> rc=0 tanpa complete.
SKILL_TOOLS = {"skill_view", "skills_list", "tool_search", "tool_describe"}


def locate_db(profile=None, db=None):
    if db:
        return db
    return f"~/.hermes/profiles/{profile}/state.db"


def path_of(content):
    try:
        d = json.loads(content) if isinstance(content, str) else {}
    except Exception:
        return None
    if isinstance(d, dict):
        return d.get("path") or d.get("file_path")
    return None


def sh(cmd):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return (r.stdout or r.stderr).strip()
    except Exception as exc:  # pragma: no cover - diagnostik saja
        return f"(gagal: {exc})"


def report_workspace(board, task_id):
    """Cetak lokasi worktree kartu + commit/berkas di branch worker."""
    db = f"~/.hermes/kanban/boards/{board}/kanban.db"
    if not os.path.exists(db):
        print(f"WORKSPACE: kanban.db tidak ada di {db}")
        return
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        row = con.execute(
            "select workspace_kind, workspace_path, branch_name from tasks where id=?",
            (task_id,)).fetchone()
    finally:
        con.close()
    if not row:
        print(f"WORKSPACE: kartu {task_id} tidak ditemukan di board {board}")
        return
    kind, ws, branch = row
    print(f"WORKSPACE kind={kind or '-'} branch={branch or '-'} path={ws or '-'}")
    repo = os.path.join(ws, "repo") if ws else None
    if not repo or not os.path.isdir(repo):
        print("WORKSPACE: repo worktree tidak ada (mungkin kartu pakai repo utama)")
        return
    print("  git log: " + " | ".join(sh(["git", "-C", repo, "log", "--oneline", "-3"]).splitlines()))
    status = sh(["git", "-C", repo, "status", "--short"])
    dirty = len([l for l in status.splitlines() if l.strip()])
    print(f"  dirty_files={dirty}")
    print("  vs main: " + (sh(["git", "-C", repo, "diff", "--stat", "main...HEAD"]).splitlines() or ["(tak terbaca)"])[-1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="program-developer")
    ap.add_argument("--db", default=None)
    ap.add_argument("--minutes", type=int, default=30)
    ap.add_argument("--board", default=None, help="slug papan, untuk cek worktree kartu")
    ap.add_argument("--task", default=None, help="id kartu, untuk cek worktree kartu")
    args = ap.parse_args()

    path = locate_db(args.profile, args.db)
    if not os.path.exists(path):
        print(f"STOP: state.db tidak ada di {path}")
        return 1

    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    since = time.time() - args.minutes * 60
    rows = list(con.execute(
        "select tool_name, content, timestamp from messages "
        "where role='tool' and timestamp > ?", (since,)))
    last = con.execute("select max(timestamp) from messages").fetchone()[0]
    con.close()

    total = len(rows)
    writes = [r for r in rows if (r[0] or "") in WRITE_TOOLS]
    reads = [r for r in rows if (r[0] or "") in READ_TOOLS]
    skill_calls = sum(1 for r in rows if (r[0] or "") in SKILL_TOOLS)
    idle = round((time.time() - (last or 0)) / 60, 1) if last else -1

    print(f"window={args.minutes}m tool_calls={total} writes={len(writes)} "
          f"reads={len(reads)} skill_calls={skill_calls} idle_min={idle}")

    if args.board and args.task:
        report_workspace(args.board, args.task)

    if total == 0:
        print("VERDICT: DIAM — worker tidak memanggil tool sama sekali di jendela ini.")
        return 0

    written = collections.Counter(p for p in (path_of(r[1]) for r in writes) if p)
    for p, n in written.most_common(8):
        print(f"  WRITE {n}x {p}")

    read_counts = collections.Counter(p for p in (path_of(r[1]) for r in reads) if p)
    for p, n in read_counts.most_common(8):
        if n >= 3:
            print(f"  RE-READ {n}x {p}")

    if not writes and skill_calls >= 15:
        print("VERDICT: LOOP SKILL — skill_view/skills_list berulang, nol tulisan. "
              "Kirim brief yang melarang tool skill; bila tetap terjadi di run berikutnya, "
              "reassign kartu ke profil lain (--reclaim), jangan briefing ulang profil yang sama.")
    elif not writes and total >= 10:
        print("VERDICT: LOOP BACA — aktivitas tinggi, nol tulisan. "
              "Cek komentar identik, lalu reclaim + arahan tertulis + dispatch --max 1. "
              "Pastikan dulu worktree kartu (--board/--task) memang tidak berubah.")
    elif not writes:
        print("VERDICT: fase orientasi — jangan intervensi sebelum >10m tanpa tulisan.")
    else:
        print("VERDICT: MENULIS — ada progres. Verifikasi berkas/commit di worktree kartu sebelum melapor.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
