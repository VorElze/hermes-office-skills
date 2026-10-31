#!/usr/bin/env python3
"""Rantai revisi: FIX -> RE-AUDIT -> kartu hilir, lalu dispatch --max 1.

Dipakai saat verdict gate REVISE/BLOCKED, atau saat kartu berulang `blocked` setelah
di-dispatch (bukan crash-loop: itu jalur reclaim). Pola ini menggantikan unblock berulang.

Contoh:
  python3 rework_chain.py --board siraga --key R3 --parent t_2d154328 \
      --findings /tmp/r3-f.txt --downstream t_8feaba01 --dry-run

Urutan yang dilakukan (non dry-run):
  1. FIX        : assignee = produsen kartu induk (dibaca dari DB), parent = kartu induk
  2. RE-AUDIT   : assignee code-analyst, parent = FIX, dibuat `--initial-status blocked`
  3. link       : RE-AUDIT -> kartu hilir, supaya hilir menunggu gate BARU
  4. dispatch --max 1 + verifikasi edge task_links + status FIX `running`

Jangan menurunkan ambang gate dan jangan memberi pengecualian dari sini: pengecualian
milik owner. Temuan keselamatan/medis/kredensial tidak pernah ditunda.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys

ANTI_CRASH = """
Brief anti-crash (wajib):
- Tulis berkas dengan `write_file`/`patch`/`read_file`; JANGAN heredoc panjang lewat `terminal`.
- `terminal` hanya untuk perintah satu baris <100 karakter (mis. `php -l app/x.php`, `git status`).
- Menimpa berkas yang sudah ada: `read_file` 1x dulu. Berkas baru boleh langsung ditulis.
- Gagal tool 2x dengan cara sama: ganti tool, jangan kirim call identik.
- Akhiri run dengan commit + `kanban_complete` berisi angka sebelum -> sesudah. Keluar tanpa itu =
  protocol violation yang membakar budget retry.
"""


def db_path(board: str) -> str:
    return os.path.expanduser(f"~/.hermes/kanban/boards/{board}/kanban.db")


def sh(board: str, *args: str, timeout: int = 240):
    r = subprocess.run(["hermes", "kanban", "--board", board, *args],
                       capture_output=True, text=True, timeout=timeout)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def card(board: str, tid: str) -> dict:
    con = sqlite3.connect(f"file:{db_path(board)}?mode=ro", uri=True, timeout=15)
    con.row_factory = sqlite3.Row
    row = con.execute("select * from tasks where id=?", (tid,)).fetchone()
    con.close()
    return dict(row) if row else {}


def edges(board: str) -> set:
    con = sqlite3.connect(f"file:{db_path(board)}?mode=ro", uri=True, timeout=15)
    rows = set(con.execute("select parent_id, child_id from task_links").fetchall())
    con.close()
    return rows


def new_id(out: str) -> str:
    for line in reversed(out.splitlines()):
        line = line.strip()
        if line.startswith("{"):
            try:
                return json.loads(line).get("id", "") or ""
            except json.JSONDecodeError:
                continue
    return ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True)
    ap.add_argument("--key", required=True, help="kunci kartu, mis. R3")
    ap.add_argument("--parent", required=True, help="id kartu yang direvisi")
    ap.add_argument("--findings", required=True, help="berkas temuan bernomor dari gate")
    ap.add_argument("--downstream", default="", help="id kartu hilir yang harus menunggu gate baru")
    ap.add_argument("--assignee", default="", help="default: produsen kartu induk")
    ap.add_argument("--title", default="")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    p = card(a.board, a.parent)
    if not p:
        sys.exit(f"kartu induk {a.parent} tidak ada di board {a.board}")
    findings = open(a.findings).read().strip()
    if not findings:
        sys.exit("berkas temuan kosong — jangan buat kartu FIX tanpa temuan tertulis")
    prod = a.assignee or p.get("assignee") or "program-developer"

    body = f"""Revisi {a.key} — temuan gate/audit yang wajib ditutup.

Konteks mengikat: baseline proyek + ambang gate TIDAK boleh diturunkan. Tanpa deploy produksi
(completion_contract=local-only) kecuali owner menyatakan lain. Dilarang: CDN/aset eksternal,
kredensial di repo/log/kartu, `unsafe-inline`/`unsafe-eval`, menghapus data uji yang diputuskan owner.

TEMUAN (verbatim dari gate):
{findings}

DEFINISI SELESAI:
- tiap temuan ditutup dengan angka sebelum -> sesudah yang bisa diukur ulang pihak lain;
- "pre-existing" bukan lulus, dan ambang tidak diturunkan;
- temuan keselamatan pengguna, teks medis, kredensial, keamanan: tidak boleh ditunda;
- commit + `kanban_complete` dengan ringkasan angka + path bukti di `docs/evidence/`.
{ANTI_CRASH}"""
    fix_body = os.path.join("/tmp", f"{a.key}-fix-body.md")
    open(fix_body, "w").write(body)

    print(f"FIX     assignee={prod} parent={a.parent}")
    if a.dry_run:
        print(f"DRY-RUN: tidak ada kartu dibuat (body: {fix_body})")
        return 0

    rc, out = sh(a.board, "create", a.title or f"{a.key}-fix — tutup temuan gate",
                 "--assignee", prod, "--parent", a.parent, "--body-file", fix_body,
                 "--max-runtime", "21600", "--completion-contract", "local-only", "--json")
    fix_id = new_id(out)
    if rc != 0 or not fix_id:
        sys.exit(f"create FIX gagal rc={rc}: {out.strip()[:300]}")
    print("FIX id =", fix_id)

    ra_body = os.path.join("/tmp", f"{a.key}-reaudit-body.md")
    open(ra_body, "w").write(
        f"""Re-audit {a.key} setelah FIX {fix_id}. Profil gate yang SAMA, tanpa memperbaiki aset.

Ukur ULANG sendiri tiap temuan pada {fix_id} (klaim worker = hipotesis). Tulis verdict tegas
**APPROVE** atau **BLOCKED** di `docs/evidence/{a.key}-reaudit.md` beserta denominator
(mis. "23 rute 0x500", "overflow 390/768/1440 = 0/0/0 px").
Butir tanpa angka = TIDAK TERUKUR, bukan lulus. Jangan menurunkan ambang dan jangan memberi
pengecualian sendiri — kalau perlu pengecualian, tulis BLOCKED + satu kalimat usulan; koordinator
yang memutuskan. Kalau Anda memperbaiki aset, independensi hilang dan audit diulang.
""")
    rc, out = sh(a.board, "create", f"{a.key}-reaudit — verdict ulang", "--assignee", "code-analyst",
                 "--parent", fix_id, "--body-file", ra_body, "--initial-status", "blocked",
                 "--max-runtime", "14400", "--json")
    ra_id = new_id(out)
    print("RE-AUDIT id =", ra_id or f"(gagal rc={rc}) {out.strip()[:200]}")

    if ra_id and a.downstream:
        rc, out = sh(a.board, "link", ra_id, a.downstream)
        ok = (ra_id, a.downstream) in edges(a.board)
        print(f"link re-audit -> hilir rc={rc} edge_terverifikasi={ok}")
        if not ok:
            print("PERINGATAN: edge tidak ada di task_links — hilir bisa dilepas sebelum gate baru")

    rc, out = sh(a.board, "dispatch", "--max", "1")
    print("dispatch rc=", rc, out.strip().replace("\n", " / ")[:200])
    st = card(a.board, fix_id).get("status", "?")
    print(f"FIX status={st}")
    if st != "running":
        print("PERINGATAN: FIX belum running — periksa dispatcher/assignee sebelum melapor")
    return 0


if __name__ == "__main__":
    sys.exit(main())
