#!/usr/bin/env bash
# Baixa TODOS os instaladores que o Linux precisa para a linha B3, em ops/linux/downloads/ (ignorada pelo git):
#
#   clearinvestimentos5setup.exe     MetaTrader 5 da Clear (o que os robôs e o histórico usam; servidor ClearInvestimentos-DEMO)
#   mt5setup.exe                     MetaTrader 5 "normal" da MetaQuotes (conta real/hedging do dono, outras corretoras)
#   MicrosoftEdgeWebview2Setup.exe   componente que o MT5 usa nas telas internas (o script oficial da MetaQuotes instala)
#   python-3.14.10-amd64.exe         Python para Windows, que roda dentro do Wine e importa o pacote MetaTrader5
#   python-3.14.10-embed-amd64.zip   plano B do Python, se o instalador acima falhar no Wine
#   get-pip.py                       pip para o plano B
#
# Os instaladores não vão para o git: são programas de terceiros, mudam a cada versão do MT5 (o hash muda) e
# engordariam o histórico para sempre. Este script os busca nas fontes oficiais:
#   - MT5 (Clear e MetaQuotes): CDN oficial da MetaQuotes, download.mql5.com. A URL da Clear é a mesma que o site
#     da Clear usa (pasta xp.investimentos.cctvm, a CCTVM dona da Clear). Assinatura conferida em 2026-11-23: MetaQuotes Ltd.
#   - Python: python.org, com SHA-256 fixo abaixo (conferido contra a página de lançamento do python.org).
#
# Uso:  ops/linux/downloads.sh            (baixa o que falta; rode de novo quando quiser: não rebaixa)
#       ops/linux/downloads.sh --force    (rebaixa tudo, por exemplo para pegar um MT5 mais novo)
set -euo pipefail
. "$(dirname "$0")/env.sh"

PYVER=3.14.10
CLEAR_URL="https://download.mql5.com/cdn/web/xp.investimentos.cctvm/mt5/clearinvestimentos5setup.exe"
MQ_URL="https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe"
WEBVIEW_URL="https://msedge.sf.dl.delivery.mp.microsoft.com/filestreamingservice/files/c1336fd6-a2eb-4669-9b03-949fc70ace0e/MicrosoftEdgeWebview2Setup.exe"
PY_URL="https://www.python.org/ftp/python/$PYVER/python-$PYVER-amd64.exe"
PY_SHA="92480239264744fe0386a1bd8275786fefa126e3129e56a68e22b52c73329965"
PYZIP_URL="https://www.python.org/ftp/python/$PYVER/python-$PYVER-embed-amd64.zip"
PYZIP_SHA="90905e64a840557d8c1bc4f5b74db3d7ee85e3ffb217611cac1c7813acea4159"
GETPIP_URL="https://bootstrap.pypa.io/get-pip.py"

FORCE=0
[ "${1:-}" = "--force" ] && FORCE=1
mkdir -p "$DOWNLOADS"
command -v curl >/dev/null || { echo "curl não encontrado (sudo apt-get install -y curl)"; exit 1; }

fetch() {   # fetch <url> <arquivo> [sha256]
  local url="$1" out="$DOWNLOADS/$2" sha="${3:-}"
  if [ -s "$out" ] && [ "$FORCE" = 0 ]; then
    echo "  ok (já baixado)  $2"
  else
    echo "  baixando         $2"
    curl -fL --retry 3 --connect-timeout 20 -o "$out.part" "$url"
    mv "$out.part" "$out"
  fi
  if [ -n "$sha" ]; then
    echo "$sha  $out" | sha256sum -c --quiet - || { echo "SHA-256 NÃO confere em $2: apagando. Rode de novo."; rm -f "$out"; exit 1; }
  fi
}

check_exe() {   # todo .exe baixado tem que começar com "MZ" e, se houver osslsigncode, estar assinado pela MetaQuotes/Microsoft
  local f="$DOWNLOADS/$1" who="$2"
  [ "$(head -c2 "$f")" = "MZ" ] || { echo "$1 não é um executável do Windows (download corrompido?): apagando"; rm -f "$f"; exit 1; }
  if command -v osslsigncode >/dev/null 2>&1; then
    if osslsigncode verify -in "$f" 2>/dev/null | grep -q "$who"; then
      echo "  assinatura ok    $1 ($who)"
    else
      echo "  AVISO: não consegui confirmar a assinatura de $1 com osslsigncode (esperado: $who). Confira antes de instalar."
    fi
  fi
}

echo "Baixando instaladores em $DOWNLOADS"
fetch "$CLEAR_URL"   clearinvestimentos5setup.exe;   check_exe clearinvestimentos5setup.exe "MetaQuotes"
fetch "$MQ_URL"      mt5setup.exe;                   check_exe mt5setup.exe "MetaQuotes"
fetch "$WEBVIEW_URL" MicrosoftEdgeWebview2Setup.exe; check_exe MicrosoftEdgeWebview2Setup.exe "Microsoft"
fetch "$PY_URL"      "python-$PYVER-amd64.exe"     "$PY_SHA"
fetch "$PYZIP_URL"   "python-$PYVER-embed-amd64.zip" "$PYZIP_SHA"
fetch "$GETPIP_URL"  get-pip.py
echo "Pronto: $(ls "$DOWNLOADS" | wc -l) arquivos em ops/linux/downloads/"
