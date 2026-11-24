# shellcheck shell=bash
# Ambiente comum dos scripts de ops/linux (equivale a ops/windows/_env.cmd). Use com:  . "$(dirname "$0")/env.sh"
#
#   ROOT          a raiz do repositório (duas pastas acima deste arquivo; nada depende de onde o clone está)
#   PY            o Python NATIVO do Linux: ROOT/.venv (criado por bootstrap.py), senão python3
#   WINEPREFIX    o "disco C:" do Wine onde ficam os terminais MetaTrader 5 e o Python para Windows
#                 (padrão ~/.wine-trade; troque exportando TRADE_WINEPREFIX antes de rodar qualquer script)
#   WPY_WIN       o Python para Windows dentro do Wine (C:\Python314\python.exe), o único que importa MetaTrader5
#
# O pacote MetaTrader5 só existe para Windows e conversa com o terminal por memória compartilhada; por isso o robô
# (live/run.py), o download de histórico e o gravador de ticks rodam no Python para Windows DENTRO DO MESMO prefixo
# Wine do terminal. Pesquisa, esteira, testes e portal rodam no Python nativo.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/../.." && pwd)"
export ROOT

PY="python3"
[ -x "$ROOT/.venv/bin/python" ] && PY="$ROOT/.venv/bin/python"
export PY

export WINEPREFIX="${TRADE_WINEPREFIX:-$HOME/.wine-trade}"
export WINEARCH=win64
export WINEDEBUG="${WINEDEBUG:--all}"          # o Wine fala muito no stderr; WINEDEBUG=warn+all para depurar
export WPY_WIN='C:/Python314/python.exe'          # barra normal: o Wine aceita e não há escape de "\" para errar
export WPY_UNIX="$WINEPREFIX/drive_c/Python314/python.exe"
export CLEAR_TERMINAL="$WINEPREFIX/drive_c/Program Files/Clear Investimentos MT5 Terminal/terminal64.exe"
export MQ_TERMINAL="$WINEPREFIX/drive_c/Program Files/MetaTrader 5/terminal64.exe"
export DOWNLOADS="$ROOT/ops/linux/downloads"

# Um thread de BLAS por processo (mesma razão do ops/windows/demo-b3.cmd: dezenas de robôs ao mesmo tempo).
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
export PYTHONIOENCODING=utf-8 PYTHONUTF8=1

# Se não há tela (servidor sem interface), o Wine precisa de um X virtual. Os lançadores usam isto.
wine_run() {
  if [ -z "${DISPLAY:-}" ] && [ -z "${WAYLAND_DISPLAY:-}" ] && command -v xvfb-run >/dev/null 2>&1; then
    xvfb-run -a wine "$@"
  else
    wine "$@"
  fi
}

# Python para Windows no Wine. A saída SEMPRE passa por um pipe (| cat): testado em 2026-11-23 (Wine 9), o Python do
# Windows morre ao iniciar ("init_sys_streams ... WinError 6 Invalid handle") quando a saída é um arquivo comum,
# que é justamente o caso dos logs dos robôs. Por um pipe funciona. stderr vai junto com stdout.
wine_py() {
  wine "$WPY_WIN" "$@" </dev/null 2>&1 | cat
  return "${PIPESTATUS[0]}"
}

# Roda um módulo do repositório no Python para Windows (Wine), com a pasta atual = raiz do repositório.
wpy() {
  [ -f "$WPY_UNIX" ] || { echo "Python para Windows ausente em $WPY_UNIX. Rode: ops/linux/install.sh mt5" >&2; return 1; }
  # wine_run: se o terminal ainda não estiver aberto, MetaTrader5.initialize(path=...) o abre, e ele precisa de uma tela
  ( cd "$ROOT" && { wine_run "$WPY_WIN" "$@" </dev/null 2>&1 | cat; exit "${PIPESTATUS[0]}"; } )
}
