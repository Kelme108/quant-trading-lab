#!/bin/sh
# Acceptance checks for the lab on a fresh Linux machine. READ-ONLY: it starts no bot, no loop and no agent.
#   ops/linux/verify-migration.sh           quick checks (about 1 minute)
#   ops/linux/verify-migration.sh --full    also runs the whole unit-test suite (about 6 minutes)
# Prints PASS / WARN / FAIL per check and exits 1 when any FAIL. The manual (docs/migracao-linux.md) says what to do per FAIL.
APP_DIR="${APP_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
cd "$APP_DIR" || exit 1
[ -x "$APP_DIR/.venv/bin/python" ] && PATH="$APP_DIR/.venv/bin:$PATH"
export PATH PYTHONIOENCODING=utf-8
PY="${PYTHON:-python}"
IMAGE="freqtradeorg/freqtrade:2026.9"
FAILS=0
pass() { echo "PASS  $*"; }
warn() { echo "WARN  $*"; }
fail() { echo "FAIL  $*"; FAILS=$((FAILS+1)); }

echo "== host"
echo "info  $(uname -sm) | $(. /etc/os-release 2>/dev/null && echo "$PRETTY_NAME") | $(nproc) CPU | $(awk '/MemTotal/ {printf "%.1f GiB RAM", $2/1048576}' /proc/meminfo)"
if command -v "$PY" >/dev/null 2>&1; then
  "$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' && pass "python $("$PY" -V 2>&1) ($(command -v "$PY"))" || fail "python must be 3.11 or newer ($("$PY" -V 2>&1))"
  "$PY" -c 'import numpy, pandas, pyarrow, pytest' 2>/dev/null && pass "python modules numpy, pandas, pyarrow, pytest" || fail "missing python modules: pip install -r ops/linux/requirements-host.txt (inside the venv)"
else
  fail "no 'python' command (create the venv: python3 -m venv .venv && .venv/bin/pip install -r ops/linux/requirements-host.txt)"
fi
[ "$(timedatectl show -p NTPSynchronized --value 2>/dev/null)" = "yes" ] && pass "clock synchronised (Binance rejects a skewed clock)" || warn "clock not confirmed synchronised: install chrony"
command -v claude >/dev/null 2>&1 && pass "claude CLI found ($(claude --version 2>/dev/null | head -1))" || warn "claude CLI not on PATH: the bots work without it, the research loop does not"

echo "== docker"
if docker info >/dev/null 2>&1; then
  pass "docker daemon answers (user $(id -un) can use it)"
  docker compose version >/dev/null 2>&1 && pass "docker compose v2 ($(docker compose version --short 2>/dev/null))" || fail "docker compose plugin missing"
  if docker image inspect "$IMAGE" >/dev/null 2>&1; then pass "image $IMAGE present"; else warn "image $IMAGE missing: docker pull $IMAGE"; fi
  if docker image inspect "$IMAGE" >/dev/null 2>&1; then
    docker run --rm "$IMAGE" --version >/dev/null 2>&1 && pass "freqtrade runs: $(docker run --rm "$IMAGE" --version 2>/dev/null | head -1)" || fail "the freqtrade image does not start"
    # the image runs as ftuser (uid 1000): it must be able to write into the bind-mounted user_data
    docker run --rm -v "$APP_DIR/user_data:/freqtrade/user_data" --entrypoint sh "$IMAGE" -c 'touch /freqtrade/user_data/.write-test && rm /freqtrade/user_data/.write-test' >/dev/null 2>&1 \
      && pass "containers can write into user_data" || fail "containers cannot write into user_data: sudo chown -R 1000:1000 user_data forward ; see the manual, section 5"
  fi
else
  fail "docker daemon does not answer (service up? user in the docker group? log out and in again)"
fi

echo "== repository"
[ "$(git config core.autocrlf)" = "true" ] && pass "git core.autocrlf=true (required: the frozen files keep their CRLF bytes)" || fail "run: git config core.autocrlf true"
[ "$(git config core.fileMode)" = "false" ] && pass "git core.fileMode=false (a tar from Windows marks every file executable)" || fail "run: git config core.fileMode false (otherwise git reports every file as modified)"
[ -n "$(git config user.name)" ] && [ -n "$(git config user.email)" ] && pass "git identity set" || fail "set git user.name and user.email (the pipeline commits)"
[ -f research/lab.sqlite ] && n=$("$PY" -c "import sys; sys.path.insert(0,'.'); from lab import registry; print(len(registry.list_hypotheses(registry.connect())))" 2>/dev/null) \
  && [ "${n:-0}" -gt 0 ] && pass "registry research/lab.sqlite has $n hypotheses" || fail "research/lab.sqlite missing or empty"
nd=$(ls user_data/data/binance/*.feather 2>/dev/null | wc -l)
[ "$nd" -ge 24 ] && pass "$nd candle files in user_data/data/binance" || fail "only $nd candle files in user_data/data/binance (expected 24 or more)"

echo "== freezes (each active dry-run bot must be byte-identical to its freeze record)"
active=0
for freeze in research/forward/H-*-freeze.json; do
  [ -f "$freeze" ] || continue
  hid=$(basename "$freeze" -freeze.json); active=$((active+1))
  out=$("$PY" research/tools/forward_freeze.py "$hid" --check 2>&1) && pass "$hid freeze verified" || { fail "$hid freeze: $(echo "$out" | head -3 | tr '\n' ' ')"; }
done
[ "$active" -gt 0 ] && pass "$active active freezes" || warn "no active freezes (nothing to run in dry-run)"

echo "== bot databases (sqlite integrity, open positions)"
for db in user_data/tradesv3.forward*.sqlite; do
  [ -f "$db" ] || continue
  res=$("$PY" - "$db" <<'EOF'
import sqlite3, sys
c = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True)
ok = c.execute("pragma integrity_check").fetchone()[0]
n, open_ = c.execute("select count(*), coalesce(sum(is_open), 0) from trades").fetchone()
print(ok, n, int(open_))
EOF
)
  set -- $res
  [ "$1" = "ok" ] && pass "$(basename "$db"): integrity ok, $2 trades, $3 open" || fail "$(basename "$db"): $res"
done

echo "== protected files"
"$PY" -m unittest discover -s tests -p "test_protected_files.py" >/dev/null 2>&1 && pass "tests/test_protected_files.py" || fail "tests/test_protected_files.py (a protected file differs: almost always line endings; use the byte-exact copy, section 4)"

if [ "$1" = "--full" ]; then
  echo "== full unit-test suite (about 6 minutes)"
  out=$("$PY" -m unittest discover -s tests 2>&1 | tail -4)
  echo "$out" | grep -q "^OK" && pass "unit tests: $(echo "$out" | grep '^Ran')" || { fail "unit tests"; echo "$out"; }
fi

echo
[ "$FAILS" -eq 0 ] && echo "ALL CHECKS PASSED" || echo "$FAILS check(s) FAILED"
[ "$FAILS" -eq 0 ]
