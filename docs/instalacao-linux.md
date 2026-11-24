# Instalar e rodar no Linux (do `git clone` ao robô de demo)

Escrito em 23/11/2026 para o dono e para qualquer Claude que vá rodar o projeto num Linux. Cobre a **linha B3 (WIN/WDO)**: pesquisa, esteira, portal, download de histórico, gravador de ticks e robôs de demo da Clear. A linha cripto (Freqtrade) tem o manual próprio em [migracao-linux.md](migracao-linux.md).

Resumo: **clone, rode um script, entre na conta demo uma vez.**

```bash
git clone -c core.autocrlf=true https://github.com/Kelme108/quant-trading-lab.git
cd quant-trading-lab
ops/linux/install.sh                      # pede a senha do sudo para os pacotes do sistema; leva de 15 a 30 min
ops/linux/mt5-terminal.sh clear           # abre o MT5 da Clear: entre na conta DEMO e marque "salvar senha"
ops/linux/portal.sh                       # portal em http://127.0.0.1:8765
ops/linux/demo-b3.sh demo-b3-p032-win     # liga um robô de demonstração
```

## 1. Regras antes de tudo

As de sempre ([cerebro/Regras-inviolaveis.md](cerebro/Regras-inviolaveis.md)): nada de dinheiro real, nenhuma senha em arquivo, a esteira gasta dinheiro de agente e só liga com o aval do dono. Duas regras são próprias do Linux:

- **Um robô roda em uma máquina só.** O mesmo robô ligado no Windows e no Linux, na mesma conta demo, manda as ordens em dobro e mistura os diários. Antes de ligar no Linux, desligue no Windows (crie `live\STOP` lá ou encerre a tarefa).
- **A esteira e o pipeline também rodam numa máquina só.** Dois ciclos ao mesmo tempo geram commits divergentes.

## 2. O que roda onde

O pacote Python `MetaTrader5` só existe para Windows e conversa com o terminal por memória compartilhada. Por isso o projeto usa dois Pythons no Linux:

| Parte | Roda em | Como chamar |
|---|---|---|
| Pesquisa, esteira, testes, portal, menu de saídas | Python **nativo** do Linux (`.venv`) | `.venv/bin/python -m ...` ou `source .venv/bin/activate` |
| Terminal MT5 da Clear e MT5 normal | **Wine** (prefixo `~/.wine-trade`) | `ops/linux/mt5-terminal.sh clear` ou `normal` |
| Robôs (`live/run.py`), download de histórico, gravador de ticks | Python 3.14 **para Windows dentro do mesmo Wine** | `ops/linux/demo-b3.sh`, `ops/linux/wpy.sh -m ...` |

O código é o mesmo do Windows, sem nenhuma mudança. O `b3/config/broker_mt5.json` aponta para `C:\Program Files\Clear Investimentos MT5 Terminal\terminal64.exe`, e esse caminho existe dentro do prefixo Wine.

## 3. Requisitos

- **Distribuição:** Ubuntu 22.04/24.04 ou mais nova, Debian 12/13, Linux Mint. Em outras, a etapa `sistema` não roda e você instala os pacotes à mão (lista no próprio script).
- **Wine ≥ 10 (WineHQ estável), com 32 bits.** A etapa `sistema` instala. O Wine 9 que vem no Debian/Kali **não serve**: o instalador do MT5 recusa ("A debugger has been found running in your system") e o numpy derruba o Wine (`ucrtbase.dll.crealf`). Testado em 23/11/2026.
- **Python ≥ 3.13** nativo. Se o sistema tiver um mais velho (Ubuntu 24.04 tem 3.12), o script instala um Python 3.14 só para o projeto via [uv](https://docs.astral.sh/uv/), sem tocar no do sistema.
- **Máquina:** 4 CPUs, 8 GB de RAM (16 GB com dezenas de robôs) e 15 GB livres. Com tela para o primeiro login no MT5. Num servidor sem tela, faça o primeiro login por `ssh -X` ou VNC. Depois disso, o terminal roda num X virtual (Xvfb).
- **Relógio sincronizado** (`timedatectl`). O fuso da máquina não importa: os agendamentos usam `America/Sao_Paulo` explicitamente.

## 4. Por que `core.autocrlf=true` (não pule)

O hash que identifica cada regra (`b3/strategy.py`, `b3/markets.py`, `b3/freqtrade_adapter.py`) é calculado sobre os **bytes** do arquivo-fonte. Os ledgers de pesquisa foram gravados no Windows, onde o git entrega os arquivos com CRLF. Num clone Linux comum (LF), toda regra ganharia outro hash e deixaria de bater com o ledger. No teste de 23/11/2026, a P-004 virou `609c66fe9ff0` em vez de `1a24fd953697`.

- Clonou com `-c core.autocrlf=true`: nada a fazer.
- Clonou sem: o `install.sh` liga a opção e refaz o checkout sozinho, desde que você não tenha mudado nenhum arquivo. Se mudou, ele para e explica.
- Scripts `.sh` e unidades systemd continuam com LF (`.gitattributes`), então rodam normalmente.

## 5. O que o `install.sh` faz

`ops/linux/install.sh [etapas] [--sem-testes]`. Sem etapas, roda `sistema python mt5 servicos`. Todas as etapas podem ser repetidas sem estragar nada.

| Etapa | O que faz |
|---|---|
| `sistema` | `apt`: git, curl, sqlite3, Xvfb, unzip, cabextract, osslsigncode, Python e **WineHQ estável** com 32 bits (o mesmo repositório que o script oficial da MetaQuotes usa) |
| `python` | `.venv` com `requirements-research.txt` (via `bootstrap.py --research --test`) e a suíte de sanidade (`tests/test_cerebro_vault.py tests/b3 tests/live`, cerca de 6 min). Uma falha na suíte não interrompe as outras etapas, mas o resumo final avisa |
| `mt5` | baixa os instaladores (seção 6); cria o prefixo `~/.wine-trade` (Windows 10, sem as janelas de Mono/Gecko e do depurador); instala o WebView2, o **MT5 da Clear** e o **MT5 normal** (modo `/auto`); instala o Python 3.14 para Windows em `C:\Python314` (plano B: pacote embutível + pip); instala `live/requirements.txt` (MetaTrader5, numpy, pandas, tzdata) |
| `servicos` | copia as unidades de `ops/linux/systemd/` para `~/.config/systemd/user/`, **sem ligar nenhuma** |
| `docker` | Docker Engine (só a linha cripto usa) |
| `claude` | CLI do Claude Code (só a esteira e o pipeline usam) |
| `tudo` | todas as anteriores |

Para usar outro prefixo Wine, exporte `TRADE_WINEPREFIX=/outro/caminho` antes de rodar qualquer script de `ops/linux/`.

## 6. Os arquivos de download

`ops/linux/downloads.sh` (chamado pela etapa `mt5`) baixa tudo para `ops/linux/downloads/`. A pasta é ignorada pelo git: são programas de terceiros, o hash dos instaladores do MT5 muda a cada versão e eles engordariam o histórico para sempre. `--force` baixa tudo de novo.

| Arquivo | Origem | Conferência |
|---|---|---|
| `clearinvestimentos5setup.exe` (MT5 da **Clear**) | `https://download.mql5.com/cdn/web/xp.investimentos.cctvm/mt5/clearinvestimentos5setup.exe` (CDN oficial da MetaQuotes, pasta da CCTVM dona da Clear) | assinatura MetaQuotes Ltd. (osslsigncode); conferida no Windows em 23/11/2026 |
| `mt5setup.exe` (MT5 **normal**) | `https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe` | assinatura MetaQuotes Ltd. |
| `MicrosoftEdgeWebview2Setup.exe` | Microsoft (mesma URL do script oficial `mt5ubuntu.sh` da MetaQuotes) | assinatura Microsoft |
| `python-3.14.10-amd64.exe` e `python-3.14.10-embed-amd64.zip` | python.org | SHA-256 fixo no script, conferido contra a página do python.org |
| `get-pip.py` | bootstrap.pypa.io | — |

Os instaladores do MT5 são "web installers": baixam o terminal na hora e por isso sempre trazem a versão mais nova.

## 7. Primeiro uso

1. **Logar na demo (uma vez):** `ops/linux/mt5-terminal.sh clear` → Arquivo › Abrir uma conta → servidor **ClearInvestimentos-DEMO** → login da demo, com **salvar senha** marcado. Nunca escolha um servidor com PRD ou REAL no nome. A senha fica guardada no terminal, dentro do prefixo Wine, e nunca no repositório.
2. **Conferir a conexão sem mandar ordem:** `ops/linux/wpy.sh -m live.run --config live/config/demo-b3-p032-win.json --check`
3. **Baixar o histórico** (o clone não traz dados de mercado):
   ```bash
   ops/linux/wpy.sh -m b3.data.mt5_history symbols  --attach b3/config/broker_mt5.json
   ops/linux/wpy.sh -m b3.data.mt5_history download --attach b3/config/broker_mt5.json --symbols 'WIN$N' 'WDO$N' --timeframes M1 M5 M15
   ```
   Detalhes e limites do servidor em [cerebro/areas/Dados.md](cerebro/areas/Dados.md).
4. **Robôs:** `ops/linux/demo-b3.sh --list` mostra quais estão rodando. Para ligar: `ops/linux/demo-b3.sh <nome>` ou `--all` (todos os `live/config/demo-b3-*.json`). Para parar todos: `touch live/STOP` (zera as posições e não manda nada novo; apague o arquivo para voltar). Os logs ficam em `live/logs/<nome>-task.log` e os diários em `live/journal.<nome>.sqlite`.
5. **Portal:** `ops/linux/portal.sh`. Num servidor, use `ssh -L 8765:127.0.0.1:8765 usuario@servidor` e abra http://127.0.0.1:8765 na sua máquina.

## 8. Windows → Linux

| Windows | Linux |
|---|---|
| `ops\windows\demo-b3.cmd <nome>` | `ops/linux/demo-b3.sh <nome>` |
| `ops\windows\esteira-cycle.cmd` | `ops/linux/esteira-cycle.sh` |
| `ops\windows\proxy-cycle.cmd` | `ops/linux/proxy-cycle.sh` |
| `ops\windows\tick-recorder.cmd` | `ops/linux/tick-recorder.sh` |
| `live\.venv\Scripts\python.exe -m ...` | `ops/linux/wpy.sh -m ...` |
| `python -m lab.dashboard serve --open` | `ops/linux/portal.sh` |
| Tarefas agendadas `TradeInitial-*` | timers systemd `trade-*` (seção 9) |

## 9. Deixar rodando sozinho (systemd de usuário)

A etapa `servicos` copia as unidades, mas não liga nenhuma. Para continuarem rodando com a sessão fechada: `sudo loginctl enable-linger $USER`.

```bash
systemctl --user enable --now trade-mt5-clear                    # terminal da Clear sempre aberto (depois do 1º login)
systemctl --user enable --now trade-portal                       # portal
systemctl --user enable --now trade-demo@demo-b3-p032-win.timer  # robô nos dias úteis às 08:40 BRT (um timer por robô)
systemctl --user enable --now trade-tick-recorder.timer          # ticks nos dias úteis às 19:05 BRT
systemctl --user enable --now trade-esteira.timer                # esteira de hora em hora: GASTA DINHEIRO, só com aval do dono
systemctl --user list-timers                                     # o que está agendado
journalctl --user -u trade-demo@demo-b3-p032-win -f              # acompanhar
```

As pausas são as mesmas do Windows: `ops/state/STOP_ESTEIRA`, `ops/state/STOP_PROXY_CYCLES` e `live/STOP`.

## 10. Problemas conhecidos e como foram resolvidos

| Sintoma | Causa | Solução no projeto |
|---|---|---|
| Hash de regra diferente do ledger; `tests/live/test_live_b3_demo.py` falha | checkout com LF | `core.autocrlf=true` (seção 4) |
| Instalador do MT5 fecha com "A debugger has been found running" | Wine < 10 | WineHQ estável; a etapa `mt5` recusa Wine < 10 logo no início |
| `unimplemented function ucrtbase.dll.crealf` ao importar numpy | Wine < 10 | idem |
| `init_sys_streams ... WinError 6 Invalid handle` | Python para Windows no Wine 9 com a saída indo direto para um arquivo | `env.sh` sempre passa a saída por um pipe (`wine_py`, `wpy`) |
| `No module named live` no Python do Wine | o Python embutível (plano B) ignora a pasta atual | `trade_cwd.pth` em `site-packages` |
| Instalação parada sem tela | instalador com janela de erro esperando um clique no Xvfb | cada instalador tem limite de 15 min e o diálogo de falha do Wine fica desligado |
| `wine32 is missing` | falta a arquitetura i386 | `sudo dpkg --add-architecture i386 && sudo apt-get update && sudo apt-get install wine32:i386` (a etapa `sistema` faz isso) |

## 11. O que foi testado

Teste em 23/11/2026, num Kali Linux (WSL2) **sem sudo** e com Wine 9.0:

- **Funcionou:**
  - clone limpo e a etapa `python`: 553 testes passaram, e o único que falhou passou depois do `core.autocrlf` da seção 4;
  - `bash -n` em todos os scripts;
  - download e conferência dos instaladores;
  - criação do prefixo Wine;
  - `pip install` do MetaTrader5 no Python do Wine;
  - `-m` enxergando o repositório;
  - bloqueio de Wine < 10;
  - portal (HTTP 200);
  - `demo-b3.sh --list`.
- **Não testado** (precisa de Wine ≥ 10 com sudo e de um login na demo): o MT5 instalado e aberto no Wine, o `import numpy` no Python do Wine e um robô conectado. Na primeira instalação numa máquina Linux de verdade, confira os passos 2 e 4 da seção 7 antes de ligar robôs em massa.

O que não vem no clone (dados, bancos, estado) e como reconstruir: [cerebro/Como-rodar-em-outro-ambiente.md](cerebro/Como-rodar-em-outro-ambiente.md).
