#!/usr/bin/env bash
# Instalação completa num Linux novo, a partir de um `git clone`. Rode da raiz do repositório:
#
#   ops/linux/install.sh                 # padrão: sistema + python + mt5 + servicos (e roda a suíte de sanidade)
#   ops/linux/install.sh python          # só uma etapa (pode passar várias: python mt5)
#   ops/linux/install.sh tudo            # padrão + docker (linha cripto) + claude (CLI dos agentes)
#   ops/linux/install.sh --sem-testes    # pula a suíte de testes no fim da etapa python
#
# Etapas (todas podem ser repetidas sem estragar nada):
#   sistema   pacotes do sistema via apt (pede sudo): git, curl, Python, Xvfb, Wine 64+32 bits (WineHQ estável quando
#             a distribuição é Ubuntu/Debian/Mint; o Wine da própria distro nas outras derivadas do Debian, ex. Kali)
#   python    .venv nativo com requirements-research.txt (bootstrap.py). Se o Python do sistema for < 3.13, instala o uv
#             (astral.sh) e um Python 3.14 só para o projeto, sem mexer no Python do sistema
#   mt5       baixa os instaladores (ops/linux/downloads.sh) e monta o prefixo Wine (~/.wine-trade): MT5 da Clear,
#             MT5 normal da MetaQuotes, WebView2, Python 3.14 para Windows com MetaTrader5/numpy/pandas
#   servicos  copia as unidades systemd de usuário (ops/linux/systemd/) para ~/.config/systemd/user, SEM ligar nenhuma
#   docker    Docker Engine + Compose (só a linha cripto/Freqtrade usa)
#   claude    CLI do Claude Code (só a esteira e o pipeline de agentes usam; eles gastam dinheiro, ver CLAUDE.md)
#
# O que este script NUNCA faz: digitar senha de corretora, logar em conta, ligar robô, ligar a esteira, mexer em
# gates/splits. Depois dele, o dono abre o terminal da Clear UMA vez e entra na conta DEMO (docs/instalacao-linux.md).
set -euo pipefail
. "$(dirname "$0")/env.sh"
cd "$ROOT"

STEPS=()
TESTS=1
for a in "$@"; do
  case "$a" in
    --sem-testes) TESTS=0 ;;
    tudo) STEPS+=(sistema python mt5 servicos docker claude) ;;
    sistema|python|mt5|servicos|docker|claude) STEPS+=("$a") ;;
    -h|--help) sed -n '2,22p' "$0"; exit 0 ;;
    *) echo "etapa desconhecida: $a (use --help)"; exit 2 ;;
  esac
done
[ ${#STEPS[@]} -eq 0 ] && STEPS=(sistema python mt5 servicos)

say() { printf '\n\033[1m==> %s\033[0m\n' "$*"; }
has() { command -v "$1" >/dev/null 2>&1; }
SUDO=""; [ "$(id -u)" -ne 0 ] && SUDO="sudo"

# ------------------------------------------------------------------------------------------------ sistema
os_field() { ( . /etc/os-release 2>/dev/null; eval "echo \${$1:-}" ); }

wine_major() { wine --version 2>/dev/null | sed -E 's/^wine-([0-9]+).*/\1/' || true; }

install_wine() {
  local id like codename distro
  id="$(os_field ID)"; like="$(os_field ID_LIKE)"
  if [ -n "$(os_field UBUNTU_CODENAME)" ] || [ "$id" = ubuntu ]; then
    distro=ubuntu; codename="$(os_field UBUNTU_CODENAME)"; [ -z "$codename" ] && codename="$(os_field VERSION_CODENAME)"
  elif [ "$id" = debian ]; then
    distro=debian; codename="$(os_field VERSION_CODENAME)"
  else
    distro=""; codename=""
  fi
  $SUDO dpkg --add-architecture i386
  local src="https://dl.winehq.org/wine-builds/$distro/dists/$codename/winehq-$codename.sources"
  if [ -n "$distro" ] && curl -fsI "$src" >/dev/null 2>&1; then
    echo "Wine estável do WineHQ ($distro $codename), como o script oficial da MetaQuotes"
    $SUDO mkdir -pm755 /etc/apt/keyrings
    $SUDO curl -fsSL -o /etc/apt/keyrings/winehq-archive.key https://dl.winehq.org/wine-builds/winehq.key
    $SUDO curl -fsSL -o "/etc/apt/sources.list.d/winehq-$codename.sources" "$src"
    $SUDO apt-get update
    $SUDO apt-get install -y --install-recommends winehq-stable
  else
    echo "WineHQ não tem pacote para esta distribuição ($id ${codename:-?}): usando o Wine da própria distro"
    $SUDO apt-get update
    $SUDO apt-get install -y wine wine64 wine32:i386 || $SUDO apt-get install -y wine wine32:i386
  fi
}

step_sistema() {
  say "Pacotes do sistema"
  if ! has apt-get; then
    echo "Esta distribuição não usa apt. Instale à mão: git curl python3 (>=3.13) python3-venv sqlite3 xvfb unzip"
    echo "cabextract e Wine >= 9 (64 e 32 bits). Depois rode: ops/linux/install.sh python mt5 servicos"
    return 0
  fi
  $SUDO apt-get update
  $SUDO apt-get install -y ca-certificates curl git sqlite3 unzip cabextract xvfb xauth python3 python3-venv python3-pip \
       tzdata jq
  $SUDO apt-get install -y osslsigncode 2>/dev/null || echo "(osslsigncode indisponível: a assinatura dos instaladores não será conferida)"
  local m; m="$(wine_major)"
  # Wine < 10 (ex.: 9.0 do Debian/Kali) faz o instalador da MetaQuotes recusar com "A debugger has been found running
  # in your system" (testado em 2026-11-23). Abaixo de 10, instala/atualiza para o WineHQ estável quando a distro permite.
  if [ -n "$m" ] && [ "$m" -ge 10 ] 2>/dev/null; then
    echo "Wine $(wine --version) já instalado"
    if ! dpkg -l 2>/dev/null | grep -q 'wine32:i386\|winehq-'; then
      echo "AVISO: wine32 (32 bits) parece ausente; o instalador do MT5 é 32 bits. Tentando instalar."
      $SUDO dpkg --add-architecture i386 && $SUDO apt-get update && $SUDO apt-get install -y wine32:i386 || true
    fi
  else
    install_wine
  fi
}

# ------------------------------------------------------------------------------------------------ python
pick_python() {   # imprime um Python >= 3.13; instala um via uv se o sistema não tiver
  local c
  for c in python3.14 python3.13 python3; do
    if has "$c" && "$c" -c 'import sys, venv, ensurepip; sys.exit(sys.version_info < (3, 13))' 2>/dev/null; then
      command -v "$c"; return 0
    fi
  done
  echo "Python >= 3.13 com venv não encontrado no sistema: instalando um Python 3.14 do projeto via uv" >&2
  if ! has uv && [ ! -x "$HOME/.local/bin/uv" ]; then
    curl -LsSf https://astral.sh/uv/install.sh | sh >&2
  fi
  local uv; uv="$(command -v uv || echo "$HOME/.local/bin/uv")"
  "$uv" python install 3.14 >&2
  "$uv" python find 3.14
}

step_python() {
  say "Ambiente Python nativo (.venv)"
  local base; base="$(pick_python)"
  echo "Usando $base ($("$base" --version))"
  local args=(--research)
  [ "$TESTS" = 1 ] && args+=(--test)
  if ! "$base" bootstrap.py "${args[@]}"; then
    if [ -x "$ROOT/.venv/bin/python" ]; then
      TEST_FAIL=1; echo "AVISO: a suíte de sanidade teve falhas (veja acima). Sigo com as outras etapas."
    else
      echo "Falha ao criar o .venv (veja acima)."; exit 1
    fi
  fi
}
TEST_FAIL=0

# ------------------------------------------------------------------------------------------------ mt5 (Wine)
# Cada instalador do Windows roda numa sessão própria, sem herdar a entrada/saída deste script: testado em 2026-11-23,
# o instalador do MT5 no Wine fazia este script parar em silêncio (saída 0) logo depois dele.
run_installer() {
  local log="$ROOT/live/logs/install-wine.log"
  mkdir -p "$ROOT/live/logs"
  echo "  (saída do instalador em live/logs/install-wine.log)"
  # Sem tela, um instalador que abre uma janela de erro espera para sempre por um clique: 15 minutos e encerra o Wine.
  if ! timeout 900 setsid -w bash -c '. "$1"; shift; wine_run "$@"' _ "$ROOT/ops/linux/env.sh" "$@" </dev/null >>"$log" 2>&1; then
    echo "  o instalador terminou com erro ou passou de 15 minutos (ver o log acima)"
    wineserver -k 2>/dev/null || true
  fi
}

mt5_hint() {   # o instalador saiu sem instalar: as duas causas vistas na prática
  echo "O instalador $(basename "$1") terminou sem instalar o terminal. Causas conhecidas:"
  echo "  1. Wine antigo ($(wine --version)): com Wine < 10 o instalador recusa ('A debugger has been found running')."
  echo "     Instale o WineHQ estável (ops/linux/install.sh sistema faz isso no Ubuntu/Debian/Mint) e rode de novo."
  echo "  2. Faltou o Wine 32 bits:  sudo dpkg --add-architecture i386 && sudo apt-get update && sudo apt-get install -y wine32:i386"
  echo "  Para ver a mensagem do instalador, rode-o com tela:  WINEPREFIX=$WINEPREFIX wine \"$1\""
}

wait_for() {   # wait_for <arquivo> <segundos>
  local i=0
  while [ ! -f "$1" ] && [ $i -lt "$2" ]; do sleep 5; i=$((i+5)); done
  [ -f "$1" ]
}

install_win_python() {
  local exe zip
  exe="$(ls "$DOWNLOADS"/python-*-amd64.exe | head -1)"
  zip="$(ls "$DOWNLOADS"/python-*-embed-amd64.zip | head -1)"
  echo "Python para Windows: instalador oficial, modo silencioso, em C:\\Python314"
  run_installer "$exe" /quiet InstallAllUsers=0 'TargetDir=C:\Python314' PrependPath=0 Include_launcher=0 \
      Include_test=0 Include_tcltk=0 Include_doc=0 Shortcuts=0 AssociateFiles=0 || true
  wineserver -w || true
  if wine_py -c 'import ensurepip, venv' >/dev/null 2>&1; then
    wine_py -m ensurepip --upgrade >/dev/null 2>&1 || true
    return 0
  fi
  echo "O instalador não funcionou neste Wine: usando o Python embutível (plano B)"
  rm -rf "$WINEPREFIX/drive_c/Python314"; mkdir -p "$WINEPREFIX/drive_c/Python314"
  unzip -q -o "$zip" -d "$WINEPREFIX/drive_c/Python314"
  # o pacote embutível ignora site-packages até liberar "import site" no arquivo ._pth
  sed -i 's/^#\s*import site/import site/' "$WINEPREFIX"/drive_c/Python314/python3*._pth
  ( cd "$DOWNLOADS" && wine_py get-pip.py --no-warn-script-location )
  # com ._pth, "python -m live.run" não enxerga a pasta atual (testado em 2026-11-23): este .pth a coloca no sys.path
  mkdir -p "$WINEPREFIX/drive_c/Python314/Lib/site-packages"
  echo "import sys; sys.path.insert(0, '')" > "$WINEPREFIX/drive_c/Python314/Lib/site-packages/trade_cwd.pth"
}

step_mt5() {
  say "Instaladores (MT5 da Clear, MT5 normal, WebView2, Python para Windows)"
  "$ROOT/ops/linux/downloads.sh"
  has wine || { echo "Wine não encontrado: rode antes  ops/linux/install.sh sistema"; exit 1; }
  # Wine >= 10 é obrigatório. Testado em 2026-11-23 com o Wine 9.0 do Debian/Kali: o instalador do MT5 recusa ("A
  # debugger has been found running in your system") e o numpy do Python para Windows derruba o Wine
  # ("unimplemented function ucrtbase.dll.crealf"). O WineHQ estável (o que o script oficial da MetaQuotes usa) resolve.
  local m; m="$(wine_major)"
  if [ -z "$m" ] || [ "$m" -lt 10 ] 2>/dev/null; then
    echo "Wine $(wine --version 2>/dev/null) é antigo demais: o MT5 e o numpy precisam do Wine >= 10."
    echo "No Ubuntu/Debian/Mint:  ops/linux/install.sh sistema   (instala o WineHQ estável) e rode esta etapa de novo."
    echo "Em outra distro, instale o WineHQ estável (https://wiki.winehq.org/Download) com o pacote de 32 bits."
    exit 1
  fi

  say "Prefixo Wine em $WINEPREFIX"
  if [ ! -f "$WINEPREFIX/system.reg" ]; then
    # sem as janelas "instalar Wine Mono/Gecko?" (bloqueariam a instalação sem tela; o MT5 usa o WebView2 abaixo)
    WINEDLLOVERRIDES="mscoree,mshtml=" wineboot --init >/dev/null 2>&1 || true
    wineserver -w || true
  fi
  winecfg -v win10 >/dev/null 2>&1 || wine reg add 'HKCU\Software\Wine' /v Version /d win10 /f >/dev/null
  # uma falha de programa não abre a janela do depurador (sem tela ela esperaria um clique para sempre)
  wine reg add 'HKCU\Software\Wine\WineDbg' /v ShowCrashDialog /t REG_DWORD /d 0 /f >/dev/null 2>&1 || true
  echo "Wine: $(wine --version), Windows 10"

  if [ ! -d "$WINEPREFIX/drive_c/Program Files (x86)/Microsoft/EdgeWebView" ]; then
    say "WebView2 (telas internas do MT5)"
    run_installer "$DOWNLOADS/MicrosoftEdgeWebview2Setup.exe" /silent /install
    wineserver -w || true
  fi

  if [ ! -f "$CLEAR_TERMINAL" ]; then
    say "MetaTrader 5 da Clear (instalação automática; o instalador baixa o terminal, leva alguns minutos)"
    run_installer "$DOWNLOADS/clearinvestimentos5setup.exe" /auto
    wait_for "$CLEAR_TERMINAL" 120 || { mt5_hint "$DOWNLOADS/clearinvestimentos5setup.exe"; exit 1; }
    wineserver -k || true     # o instalador abre o terminal no fim; fechamos para seguir (o dono abre depois para logar)
  fi
  echo "ok  MT5 Clear:  $CLEAR_TERMINAL"

  if [ ! -f "$MQ_TERMINAL" ]; then
    say "MetaTrader 5 normal (MetaQuotes)"
    run_installer "$DOWNLOADS/mt5setup.exe" /auto
    wait_for "$MQ_TERMINAL" 120 || { echo "AVISO: o MT5 normal não instalou (só a conta real e outras corretoras usam)."; mt5_hint "$DOWNLOADS/mt5setup.exe"; }
    wineserver -k || true
  fi
  [ -f "$MQ_TERMINAL" ] && echo "ok  MT5 normal: $MQ_TERMINAL"

  if [ ! -f "$WPY_UNIX" ] || ! wine_py -m pip --version >/dev/null 2>&1; then
    say "Python 3.14 para Windows dentro do Wine"
    install_win_python
  fi
  say "Pacotes do robô no Python do Wine (live/requirements.txt)"
  ( cd "$ROOT" && wine_py -m pip install --disable-pip-version-check --no-warn-script-location -q -r live/requirements.txt )
  ( cd "$ROOT" && wine_py -c "import MetaTrader5, numpy, pandas, zoneinfo; zoneinfo.ZoneInfo('America/Sao_Paulo'); print('ok  Python do Wine:', MetaTrader5.__version__, 'numpy', numpy.__version__, 'pandas', pandas.__version__)" )
}

# ------------------------------------------------------------------------------------------------ servicos
step_servicos() {
  say "Unidades systemd de usuário (copiadas, NENHUMA ligada)"
  local dst="$HOME/.config/systemd/user"
  mkdir -p "$dst"
  for f in "$ROOT"/ops/linux/systemd/*; do
    sed "s#@ROOT@#$ROOT#g" "$f" > "$dst/$(basename "$f")"
    echo "  $(basename "$f")"
  done
  if has systemctl && systemctl --user daemon-reload 2>/dev/null; then
    echo "Para ligar, veja docs/instalacao-linux.md (seção 'Deixar rodando sozinho')."
    echo "Para os serviços seguirem rodando sem sessão aberta:  sudo loginctl enable-linger $USER"
  else
    echo "(systemd de usuário indisponível aqui; use os scripts ops/linux/*.sh direto)"
  fi
}

# ------------------------------------------------------------------------------------------------ docker / claude
step_docker() {
  say "Docker Engine (linha cripto)"
  if has docker; then echo "docker já instalado"; return 0; fi
  curl -fsSL https://get.docker.com | $SUDO sh
  $SUDO usermod -aG docker "$USER" && echo "Saia e entre de novo na sessão para usar docker sem sudo."
}

step_claude() {
  say "Claude Code (CLI dos agentes)"
  if has claude || [ -x "$HOME/.local/bin/claude" ]; then echo "claude já instalado"; return 0; fi
  curl -fsSL https://claude.ai/install.sh | bash
  echo "Depois rode 'claude' uma vez para entrar na sua conta."
}

# ------------------------------------------------------------------------------------------------ fim de linha (sempre)
# O hash de identidade de cada regra (b3/strategy.py, b3/markets.py, b3/freqtrade_adapter.py) é calculado sobre os BYTES
# do arquivo-fonte, e os ledgers de pesquisa foram gravados no Windows, onde o git faz checkout com CRLF
# (core.autocrlf=true). Um clone Linux comum tem LF: toda regra ganharia outro hash e deixaria de bater com o ledger
# (testado em 2026-11-23: P-004 virou 609c66fe9ff0 em vez de 1a24fd953697). Por isso o clone Linux usa a mesma
# configuração do Windows. Scripts .sh e unidades systemd continuam LF (.gitattributes).
ensure_crlf() {
  [ -d "$ROOT/.git" ] || [ -f "$ROOT/.git" ] || return 0
  [ "$(git -C "$ROOT" config core.autocrlf || true)" = "true" ] && return 0
  say "Fim de linha igual ao Windows (core.autocrlf=true), para os hashes das regras baterem com os ledgers"
  if [ -n "$(git -C "$ROOT" status --porcelain --untracked-files=no)" ]; then
    echo "O clone tem arquivos alterados; não vou refazer o checkout por cima deles. Faça commit/stash e rode de novo,"
    echo "ou clone de novo com:  git clone -c core.autocrlf=true https://github.com/Kelme108/quant-trading-lab.git"
    exit 1
  fi
  git -C "$ROOT" config core.autocrlf true
  git -C "$ROOT" rm -rq --cached .
  git -C "$ROOT" reset -q --hard
  echo "ok: checkout refeito com CRLF ($(git -C "$ROOT" status --porcelain | wc -l) arquivos diferentes do commit, esperado 0)"
}

chmod +x "$ROOT"/ops/linux/*.sh 2>/dev/null || true
ensure_crlf
for s in "${STEPS[@]}"; do "step_$s"; done

say "Fim"
. "$ROOT/ops/linux/env.sh"      # o .venv pode ter acabado de nascer: recalcula PY
"$PY" bootstrap.py --check || true
if [ "$TEST_FAIL" = 1 ]; then echo "ATENÇÃO: houve falha na suíte de sanidade; leia a saída antes de ligar qualquer robô."; fi
cat <<EOF

Próximos passos (docs/instalacao-linux.md):
  1. Abrir o terminal da Clear e entrar na conta DEMO (uma vez):   ops/linux/mt5-terminal.sh clear
  2. Portal:                                                     ops/linux/portal.sh   (http://127.0.0.1:8765)
  3. Ligar um robô de demo:                                       ops/linux/demo-b3.sh demo-b3-p032-win
EOF
