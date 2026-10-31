#!/usr/bin/env bash
# Rakit ZIP rilis dari git archive + verifikasi dasar.
#
# Pakai:
#   scripts/build_release_zip.sh 1.1.0 docs/release/app-v1.1.0.zip app public vendor PANDUAN-INSTALASI.md
#
# Aturan yang dijalankan skrip ini:
#   - menolak jalan bila repo masih membawa .worktrees/ di indeks git (gitlink hantu)
#   - hanya mengarsipkan path yang disebut eksplisit (bukan `zip -r .`)
#   - mencetak ukuran, jumlah entri, hasil `unzip -t`, dan sha256
#   - memperingatkan bila ada config.php/install.lock atau token di dalam arsip
set -euo pipefail

if [ "$#" -lt 3 ]; then
  echo "pemakaian: $0 <versi> <zip-keluar> <path...>" >&2
  exit 2
fi

VER="$1"; OUT="$2"; shift 2
PATHS=("$@")

REPO="$(git rev-parse --show-toplevel)"
cd "$REPO"

if git ls-files --error-unmatch .worktrees >/dev/null 2>&1; then
  echo "GAGAL: .worktrees masih terlacak git. Jalankan:" >&2
  echo "  echo '.worktrees/' >> .gitignore && git rm -r --cached .worktrees && git commit -m 'chore(git): keluarkan .worktrees'" >&2
  exit 3
fi

for p in "${PATHS[@]}"; do
  if ! git cat-file -e "HEAD:$p" 2>/dev/null; then
    echo "GAGAL: path '$p' tidak ada di HEAD" >&2
    exit 4
  fi
done

BRANCH="$(git branch --show-current)"
HEAD_SHA="$(git rev-parse --short HEAD)"
echo "branch=$BRANCH head=$HEAD_SHA versi=$VER"

mkdir -p "$(dirname "$OUT")"
rm -f "$OUT" "$OUT.sha256"
git archive --format=zip --prefix="app/" -o "$OUT" HEAD "${PATHS[@]}"

SIZE="$(stat -c%s "$OUT")"
ENTRIES="$(unzip -Z1 "$OUT" | wc -l | tr -d ' ')"
CRC="$(unzip -t "$OUT" | tail -1)"
echo "byte=$SIZE entri=$ENTRIES crc=$CRC"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
unzip -q "$OUT" -d "$TMP"
echo "berkas_terekstrak=$(find "$TMP" -type f | wc -l | tr -d ' ')"

BAD=0
for f in config/config.php install.lock; do
  if [ -e "$TMP/app/$f" ]; then echo "BOCOR: $f ikut dalam arsip" >&2; BAD=1; fi
done
if grep -rIl -E 'PRD_AGENT_TOKEN|BEGIN OPENSSH|DB_PASSWORD=' "$TMP" >/dev/null 2>&1; then
  echo "BOCOR: pola kredensial ditemukan (klasifikasikan sebelum lapor)" >&2; BAD=1
fi

echo "--- isi teratas ---"
find "$TMP/app" -maxdepth 1 -mindepth 1 -printf '%f\n' | sort | head -20

sha256sum "$OUT" | tee "$OUT.sha256"
[ "$BAD" -eq 0 ] || exit 5
echo "OK: $OUT siap dikirim"
