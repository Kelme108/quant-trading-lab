#!/bin/sh
# Run in Git Bash on the WINDOWS PC, AFTER stopping everything (docs/migracao-linux.md, section 4). It packs the whole working
# folder into ONE tar file that keeps every byte (the frozen files must keep their Windows line endings or their hashes change).
#   ops/linux/pack-from-windows.sh            full copy (about 13 GB)
#   SLIM=1 ops/linux/pack-from-windows.sh     leaves out user_data/backtest_results/experiments (about 6 GB of intermediate exports
#                                             that only lab/runner.py writes; the exports that matter are copied to research/experiments)
# The tar goes next to the project folder: <parent>/<folder>-for-linux-<date>.tar, with a .sha256 beside it.
APP_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
PARENT="$(dirname "$APP_DIR")"; NAME="$(basename "$APP_DIR")"
OUT="${OUT:-$PARENT/$NAME-for-linux-$(date -u +%Y%m%d).tar}"
cd "$APP_DIR" || exit 1

echo "== refusing to pack while something still runs"
if docker ps --filter name=forward- --filter name=testnet- -q 2>/dev/null | grep -q .; then
  echo "bot containers are still running. Stop them first: for f in docker-compose.forward*.yml; do docker compose -f \$f stop; done"; exit 1
fi
if powershell.exe -NoProfile -Command "if (Get-CimInstance Win32_Process | Where-Object { \$_.ProcessId -ne \$PID -and \$_.Name -notmatch 'powershell' -and \$_.CommandLine -match 'lab\\.pipeline|continuous2|research-loop|bot-watchdog|watchdog\\.sh|--agent (scout|research|developer|quant|risk|validator)' }) { exit 1 }" >/dev/null 2>&1; then :; else
  echo "the research loop or the watchdog is still running. Stop it first (section 4 of the manual)."; exit 1
fi

echo "== sqlite integrity of every bot database"
python - <<'EOF' || exit 1
import glob, sqlite3, sys
bad = 0
for db in sorted(glob.glob("user_data/tradesv3.*.sqlite")):
    c = sqlite3.connect(db)
    ok = c.execute("pragma integrity_check").fetchone()[0]
    n, open_ = c.execute("select count(*), coalesce(sum(is_open), 0) from trades").fetchone() if c.execute("select name from sqlite_master where name='trades'").fetchone() else (0, 0)
    print(f"{ok:4} {db}: {n} trades, {int(open_)} open")
    bad += ok != "ok"
sys.exit(1 if bad else 0)
EOF

EXCLUDES="--exclude=__pycache__ --exclude=.pytest_cache --exclude=.venv --exclude=node_modules --exclude=$NAME/live/.venv"
[ "$SLIM" = "1" ] && EXCLUDES="$EXCLUDES --exclude=$NAME/user_data/backtest_results/experiments"
echo "== packing $APP_DIR -> $OUT (this takes a few minutes; the data are already compressed, so no gzip)"
# shellcheck disable=SC2086
tar -cf "$OUT" -C "$PARENT" $EXCLUDES "$NAME" || { echo "tar failed"; exit 1; }
( cd "$PARENT" && sha256sum "$(basename "$OUT")" > "$(basename "$OUT").sha256" )
ls -lh "$OUT" | awk '{print "size:", $5}'
cat "$OUT.sha256"
echo "Copy the .tar and the .sha256 to the Linux machine (scp, rsync or a USB disk) and follow section 5 of the manual."
