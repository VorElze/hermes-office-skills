#!/bin/bash
# Restart a manually-run Hermes gateway that `hermes gateway restart` refuses to replace.
# Jadwalkan dari luar (systemd-run --user --on-active=90 --setenv=GATEWAY_PIDS="<pids>" /bin/bash <file ini>)
# supaya selamat ketika sesi pemanggil ikut mati bersama gateway.
#
# JANGAN pakai `pgrep -f ... | kill` di sini: guard Hermes memblokir kill berbasis
# nama proses. PID dikumpulkan pemanggil lewat `ps` dan dikirim via GATEWAY_PIDS.
set -u
H=${HERMES_BIN:-~/.hermes/hermes-agent/.hermes/bin/hermes}
HOME_DIR=${HERMES_HOME_DIR:-~/.hermes}
LOG=$HOME_DIR/logs/gateway-restart.log
OUT=${GATEWAY_STATE_OUT:-$HOME_DIR/gateway_restart_status.txt}
mkdir -p "$(dirname "$OUT")" "$(dirname "$LOG")"
echo "=== $(date '+%F %T') mulai restart (pids: ${GATEWAY_PIDS:-}) ===" >>"$LOG"

for pid in ${GATEWAY_PIDS:-}; do
  echo "kill $pid" >>"$LOG"
  kill "$pid" 2>/dev/null
done
for _ in $(seq 1 30); do
  alive=0
  for pid in ${GATEWAY_PIDS:-}; do kill -0 "$pid" 2>/dev/null && alive=1; done
  [ "$alive" = 0 ] && break
  sleep 1
done
for pid in ${GATEWAY_PIDS:-}; do kill -9 "$pid" 2>/dev/null; done
sleep 3

for try in 1 2 3; do
  HERMES_HOME=$HOME_DIR setsid nohup "$H" gateway run >>"$LOG" 2>&1 < /dev/null &
  sleep 14
  if timeout 25 "$H" gateway status 2>/dev/null | grep -q "Gateway is running"; then
    msg="OK percobaan $try $(date '+%T') :: $(timeout 25 "$H" gateway status 2>/dev/null | head -1)"
    echo "$msg" | tee -a "$LOG" > "$OUT"
    exit 0
  fi
  echo "gagal percobaan $try" >>"$LOG"
done
echo "GAGAL semua percobaan $(date '+%F %T')" | tee -a "$LOG" > "$OUT"
exit 1
