# Manual de migração para Linux

Escrito em 12/11/2026 para o **Claude que vai rodar no Linux** e para o dono do projeto (Luiz). A ideia: o Claude do Linux lê este arquivo do começo ao fim e consegue montar tudo sozinho, sem adivinhar. Origem: PC Windows 11 com Docker Desktop (WSL2). Destino: Debian 12 ou 13 (serve também Ubuntu 24.04).

Se o dono só quer saber o que fazer: seções 4 e 5 (empacotar e extrair), seção 6 (conferir) e seção 7 (ligar os bots). A seção 8 (loop de pesquisa) gasta dinheiro de agente e só se liga com o aval dele.

## 0. Regras para quem executa (leia antes de rodar qualquer comando)

1. **Nunca dinheiro real.** Todos os bots são dry-run, sem chave de corretora. `real_money` em `lab/config/autopilot.json` fica `false`. Não crie `live/.env`, `live/config/live.json` nem `testnet/.env` com credenciais. A camada `live/` usa MetaTrader 5, que só existe no Windows: fica fora desta migração.
2. **Não edite os arquivos congelados** dos bots ativos: a estratégia, o `forward/config.hNNN.json` e o `docker-compose.forward.hNNN.yml` listados em `research/forward/H-*-freeze.json`. O hash de cada byte está registrado. Qualquer mudança vira hipótese nova, com relógio zerado.
3. **Não mexa** em `lab/config/gates.json`, `holdout.json`, `splits.json` nem no `final_test_unlocked`. São decisões do dono.
4. **Um lugar por vez.** Se os bots de cripto ou o loop de pesquisa rodarem nos dois computadores, a evidência duplica e os commits divergem. O Windows só volta a rodá-los depois de parar tudo no Linux (seção 13). O trabalho de B3/MT5 é outro assunto e continua no Windows (seção 1).
5. **Pare o loop antes de editar o repositório.** O guard (`lab/guard.py`) aborta um ciclo quando algo fora dos caminhos permitidos do agente muda durante o passo dele.
6. **Pergunte ao dono antes de:** ligar o loop de pesquisa (gasta dinheiro), apagar dados, mudar política ou limites, ou fazer `git push`.
7. **Se um teste ou verificação falhar, pare e relate.** Não "conserte" recriando um congelamento nem recalculando hash: isso destrói a evidência.
8. Este manual foi montado no Windows. **Não foi executado no Linux.** Os pontos dependentes de Linux (apt, systemd, permissões) seguem procedimentos padrão, mas a seção 6 existe para provar que deu certo. O verificador (`ops/linux/verify-migration.sh`) foi rodado no PC Windows e passou em tudo.

## 1. O que é o sistema, em um minuto

| Peça | O que faz | Como roda |
|---|---|---|
| **Freqtrade 2026.9** (imagem Docker `freqtradeorg/freqtrade:2026.9`) | Backtests e bots de dry-run, com preço real da Binance e ordens simuladas | `docker compose run --rm freqtrade ...` (backtest) e um contêiner por hipótese (`docker-compose.forward.hNNN.yml`) |
| **`lab/`** (Python no host) | Pipeline de pesquisa: scout → triagem → hipótese → implementação → checagens → calibração → exploração; registro em `research/lab.sqlite`; veredito do dry-run; portal | `python -m lab.pipeline ...`, `python -m lab.dashboard serve` |
| **Agentes** | Scout, research, developer, quant, risk, validator. Cada um é uma chamada `claude -p --agent <nome>` com a definição em `.claude/agents/<nome>.md` | O pipeline chama o CLI `claude`. Scout e research usam o modelo `opus`, os outros `sonnet` (`lab/agents.py`). Limites em `lab/config/budget.json`: 4 USD por chamada, 60 USD por ciclo |
| **Portal** | Painel somente leitura: pesquisa, dry-run, gráfico ao vivo | `127.0.0.1:8765` |
| **`ops/`** | `freqtrade_guard.py` (relatório de saúde, opcional), `vps/bootstrap-ubuntu.sh` (referência para VM Ubuntu), `linux/` (novo, desta migração) | cron ou systemd |
| **`live/`, `testnet/`** | Camada de execução real/testnet | **Fora do escopo.** Dinheiro real continua bloqueado |
| **Plano B3 (WIN/WDO via MT5)** | O dono decidiu em 12/11/2026 trazer o mini-índice e o mini-dólar da B3 (`docs/plano-b3-win-wdo.md`) | O MT5 com Python **só roda no Windows** (seção F0.3 do plano). A máquina Windows **continua existindo** para isso. A migração move só o laboratório de cripto (bots Freqtrade, loop de pesquisa, portal) para o Linux. Se a B3 avançar, a pesquisa dela pode rodar no Linux, mas o adaptador MT5 fica no Windows |

Mapa completo do projeto: `docs/funcionamento-geral.md` (seções 1 a 6 e 8). Decisões e histórico: `research/hypothesis-ledger.md`, `research/reviews/`.

**Estado no dia do empacotamento (12/11/2026):**
- 5 bots de dry-run ativos, todos multi-par (um contêiner por hipótese): H-100, H-101, H-102, H-103, H-104. Todos com `restart: "no"` e 0 trades ainda.
- 5 bots retirados por não operarem em 2 dias (H-001, H-009, H-016, H-043, H-047): congelamentos em `research/forward/retired/`, bancos guardados.
- Registro com 129 hipóteses. Suíte de testes: 684 testes, todos passam.
- Regra do dry-run (`lab/config/dryrun.json`): um bot sai sozinho se passar 2 dias sem fechar um trade. Veredito em `research/forward/verdicts.md`.
- O loop de pesquisa gastou cerca de 35 USD em 7 ciclos numa noite (11/11).
- Decisões do dono ainda abertas: ampliar o universo de pares, futuros em dry-run e ordens maker (`research/reviews/2026-11-12-revisao-day-trade.md`). **Não implemente nenhuma sem ele escolher.**

## 2. O que é específico do Windows e o que muda no Linux

| No Windows | No Linux |
|---|---|
| Docker Desktop com teto de memória de 15,5 GiB (`.wslconfig`) | Docker Engine nativo, sem teto. Cada bot usa cerca de 540 MiB |
| Git com `core.autocrlf=true`: os arquivos de trabalho têm CRLF e o git guarda LF. **Os hashes dos congelamentos foram calculados sobre os bytes com CRLF** | Copiar os bytes exatamente (tar) e ligar `core.autocrlf=true`. **Nunca recriar a pasta com `git clone`**: 26 dos 55 arquivos congelados mudam de hash |
| `claude.CMD` (npm global) | `claude` no PATH |
| `MSYS_NO_PATHCONV=1` em `lab/runner.py` | Inofensivo, fica |
| Scripts soltos de vigia e loop, e `keepawake.ps1` contra suspensão | `ops/linux/` e unidades systemd de usuário |
| Bots com `restart: "no"` (mudar o compose quebraria o congelamento) | `docker update --restart unless-stopped`, que muda o contêiner e não o arquivo |
| Python 3.14 | Python 3.11 ou mais novo, em um venv |
| Pacote `MetaTrader5` (só Windows) | Não usar. Os testes de `tests/live` passam com adaptadores falsos |
| Nenhum caminho fixo em `lab/` (usa `Path(__file__)`) | Nada a ajustar nos caminhos |

## 3. Pré-requisitos da máquina Linux

- **Hardware:** 4 vCPU, 8 GB de RAM (16 GB é folgado) e 40 GB livres. A cópia completa tem cerca de 13 GB (6 GB com `SLIM=1`).
- **Rede:** saída para `api.binance.com` (dados públicos, sem chave). Alguns provedores de nuvem nos EUA são bloqueados pela Binance (erro 451). Região Brasil ou Europa funciona.
- **Relógio em UTC e sincronizado.** A Binance rejeita requisições com o horário errado.

```bash
sudo apt-get update && sudo apt-get install -y ca-certificates curl git sqlite3 chrony jq python3 python3-venv python3-pip nodejs npm
sudo timedatectl set-timezone UTC && sudo systemctl enable --now chrony

# Docker Engine oficial (Debian). Para Ubuntu troque "debian" por "ubuntu" nas duas linhas marcadas.
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc         # <- debian
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null   # <- debian
sudo apt-get update && sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker "$USER"        # sair da sessão e entrar de novo para valer

# rotação dos logs dos contêineres
echo '{"log-driver":"json-file","log-opts":{"max-size":"20m","max-file":"5"}}' | sudo tee /etc/docker/daemon.json >/dev/null
sudo systemctl restart docker

# se for um notebook: nunca suspender
sudo systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target
```

Use o plugin `docker compose` (com espaço), não o antigo `docker-compose`. O CLI do Claude Code: instale conforme https://docs.claude.com/en/docs/claude-code/setup. No PC Windows foi usado `npm install -g @anthropic-ai/claude-code`. Para não precisar de `sudo`: `npm config set prefix ~/.npm-global` e ponha `~/.npm-global/bin` no PATH.

## 4. No Windows: parar tudo e empacotar

Os bots do Windows só voltam a rodar depois de a migração ser desfeita (seção 13). Peça ao Claude do Windows, ou faça à mão, nesta ordem:

1. **Parar o loop de pesquisa e o vigia** (processos `lab.pipeline`, `continuous2.sh`, `watchdog.sh` e qualquer `claude -p --agent ...`) e remover contêineres órfãos `freqtrade-run`.
2. **Parar os bots** com saída ordenada:
   ```bash
   for f in docker-compose.forward*.yml; do docker compose -f "$f" stop -t 30; done
   ```
3. **Escolher a hora:** de preferência quando nenhum bot tem posição aberta. O script de empacotamento e o verificador mostram quantas posições há. Com posição aberta o Freqtrade retoma do banco, mas a posição passa a ser acompanhada no Linux.
4. **Empacotar** no Git Bash, na raiz do projeto:
   ```bash
   ops/linux/pack-from-windows.sh            # cópia completa, cerca de 13 GB
   SLIM=1 ops/linux/pack-from-windows.sh     # sem user_data/backtest_results/experiments (6 GB de exportações intermediárias)
   ```
   O script recusa empacotar enquanto houver bot ou loop rodando, confere a integridade de todos os bancos SQLite, cria `<pasta>-for-linux-AAAAMMDD.tar` ao lado da pasta do projeto e grava o `.sha256`.

   O tar leva a pasta inteira, inclusive `.git` e o que o git ignora e o sistema precisa: `research/lab.sqlite` (o registro), `research/experiments/*/raw/` (as exportações de backtest que o placar e o portal leem), `user_data/data/` (candles) e `user_data/tradesv3.*.sqlite` (os bancos dos bots). Cópia por `git clone` perde tudo isso.
5. **Mover** o `.tar` e o `.sha256` para o Linux (`scp`, `rsync -P` ou disco externo).

## 5. No Linux: extrair e preparar

```bash
cd ~ && sha256sum -c Trade-Initial-for-linux-*.tar.sha256
tar -xf Trade-Initial-for-linux-*.tar            # cria ~/Trade-Initial com os bytes originais
cd ~/Trade-Initial

git config core.autocrlf true                     # OBRIGATÓRIO: sem isso o git acha que centenas de arquivos mudaram
git config core.fileMode false                    # OBRIGATÓRIO: um tar vindo do Windows marca tudo como executável
git config user.name  "Luiz Kelme"                # o pipeline faz commits; use a identidade que o dono indicar
git config user.email "<email do dono>"
git status --short | head                         # esperado: só os arquivos pendentes do PC (portal, testes). Centenas = autocrlf errado

chmod +x ops/linux/*.sh
python3 -m venv .venv && .venv/bin/pip install -r ops/linux/requirements-host.txt
docker pull freqtradeorg/freqtrade:2026.9
mkdir -p user_data/logs ops/state
```

**Permissões:** o contêiner roda como `ftuser` (uid 1000) e precisa gravar em `user_data/` e ler `forward/`. Se o usuário do Linux tem uid 1000 (o primeiro usuário normal), nada a fazer. Caso contrário: `sudo chown -R 1000:1000 user_data forward`. Se o git reclamar de "dubious ownership": `git config --global --add safe.directory ~/Trade-Initial`.

O `python` que os agentes usam (`python -m unittest`) é o do venv: os scripts de `ops/linux/` já colocam `.venv/bin` no PATH. Para uso manual: `source .venv/bin/activate`.

## 6. Conferir (critério de aceite)

```bash
ops/linux/verify-migration.sh           # cerca de 1 minuto, somente leitura
ops/linux/verify-migration.sh --full    # inclui os 684 testes (cerca de 6 minutos)
```

O resultado esperado é `ALL CHECKS PASSED`. O script não liga bot, loop nem agente. Se algo der FAIL:

| FAIL | Causa provável | O que fazer |
|---|---|---|
| `freeze: changed since the freeze` | Quebras de linha alteradas (cópia por git ou editor) | Apagar a pasta e extrair o `.tar` de novo. Garantir `core.autocrlf=true`. **Não** refazer o congelamento |
| `freeze: uncommitted changes in frozen files` | Quase sempre `core.fileMode` ou `core.autocrlf` sem ajustar (o git vê mudança onde só há bit de execução ou CRLF) | `git config core.fileMode false` e `git config core.autocrlf true`, e rodar de novo. Se persistir, extrair o `.tar` de novo |
| `tests/test_protected_files.py` | Mesma causa | Idem |
| `containers cannot write into user_data` | uid diferente de 1000 | `sudo chown -R 1000:1000 user_data forward` |
| `docker daemon does not answer` | Serviço parado ou usuário fora do grupo `docker` | `sudo systemctl start docker`; sair e entrar na sessão |
| `python modules` | venv sem pacotes | `.venv/bin/pip install -r ops/linux/requirements-host.txt`. Sem wheel para a versão pinada: instalar os mesmos nomes sem fixar a versão e rodar `--full` |
| `registry research/lab.sqlite missing` | Cópia incompleta | Extrair o `.tar` de novo; conferir o `.sha256` |
| `candle files` abaixo de 24 | Cópia incompleta | Idem |
| `unit tests` | Versão do Python ou de pacote | Ver a saída; relatar ao dono antes de mudar código |

Os avisos (`WARN`) de relógio e de `claude` não impedem os bots, mas o relógio deve ser corrigido (`chrony`), e o `claude` só é exigido pelo loop de pesquisa.

## 7. Ligar os bots e o portal

```bash
mkdir -p ~/.config/systemd/user
cp ops/linux/trading-lab-portal.service ops/linux/trading-lab-watchdog.service ~/.config/systemd/user/
systemctl --user daemon-reload
sudo loginctl enable-linger "$USER"          # os serviços de usuário sobem no boot, sem login
systemctl --user enable --now trading-lab-watchdog trading-lab-portal
```

As unidades esperam o projeto em `~/Trade-Initial` e o venv em `~/Trade-Initial/.venv`. Em outro lugar, use `systemctl --user edit <unidade>` e troque `WorkingDirectory` e `ExecStart`.

O vigia (`ops/linux/bot-watchdog.sh`) roda a cada 5 minutos e, para cada congelamento ativo, sobe os contêineres que faltam com `docker compose -f docker-compose.forward.hNNN.yml up -d`. Em seguida aplica `docker update --restart unless-stopped`, de modo que depois de um reboot o próprio Docker traz os bots de volta. Ele só inicia contêineres a partir dos compose existentes e não altera nenhum arquivo. Bots retirados nunca são religados. Se existir `ops/state/STOP.forward`, ele não liga nada.

Confira em até 5 minutos:

```bash
docker ps --filter name=forward- --format '{{.Names}} {{.Status}}'     # 5 contêineres: forward-h100 ... forward-h104
docker logs --tail 5 forward-h104                                      # "Bot heartbeat" a cada minuto
docker inspect -f '{{.HostConfig.RestartPolicy.Name}}' forward-h104    # unless-stopped
curl -s http://127.0.0.1:8765/api/dryrun | head -c 300                 # o portal responde
```

Erros isolados de candle da Binance (`code -1001`) são transitórios e o Freqtrade refaz sozinho. **Teste de reboot:** `sudo reboot`, e depois confira que os 5 contêineres voltaram sem intervenção.

## 8. Loop de pesquisa (gasta dinheiro de agente)

Só ligue depois que o dono disser que sim. O loop chama agentes `claude -p`: até 4 USD por chamada e 60 USD por ciclo (`lab/config/budget.json`).

1. **Login do CLI**, uma vez, como o usuário que vai rodar o serviço: execute `claude` interativamente e conclua o login que ele pedir. Não cole chaves nem códigos no chat.
2. **Teste barato:** `claude -p "responda apenas: ok"` deve responder sem pedir nada.
3. **Teste de um ciclo (opcional, alguns USD):** `.venv/bin/python -m lab.pipeline weekly --scout-count 2 --max-new 1`. Termina com um relatório em `research/pipeline/cycle-*.md`.
4. **Ligar o serviço:**
   ```bash
   cp ops/linux/trading-lab-loop.service ~/.config/systemd/user/ && systemctl --user daemon-reload
   systemctl --user start trading-lab-loop            # use "enable --now" só se o dono quiser que suba no boot
   tail -f ops/state/loop-*.log
   ```
5. **Parar com limpeza:** `touch ops/state/STOP_CYCLES` (o ciclo em andamento termina primeiro). **Parar já:** `systemctl --user stop trading-lab-loop`; depois remova contêineres órfãos: `docker ps -a --filter name=freqtrade-run -q | xargs -r docker rm -f`.

O loop faz, em sequência: `weekly` (scout, triagem, implementação, exploração; o autopilot de `lab/config/autopilot.json` pode congelar e subir bots novos em dry-run, até 20), `dryrun` (veredito e retirada automática de quem passou 2 dias sem trade), e a cada 4 ciclos `sources`. Três ciclos seguidos com `STOPPED` encerram o loop (guard ou orçamento): um humano olha o motivo. Gasto por ciclo: linha `Agent spend` no `research/pipeline/cycle-*.md` mais recente.

Os agentes e a base de conhecimento já vêm com o projeto: `.claude/agents/`, `research/guidance.md`, `research/knowledge/evidence.md` e o placar de day trade (`python -m lab.knowledge`).

## 9. Portal

`trading-lab-portal.service` serve `http://127.0.0.1:8765` somente em loopback. De outro computador, use um túnel: `ssh -L 8765:127.0.0.1:8765 usuario@servidor` e abra `http://127.0.0.1:8765`. **Depois de mudar qualquer arquivo `.py` em `lab/`, reinicie** (`systemctl --user restart trading-lab-portal`): os arquivos `.js` e `.html` são relidos a cada requisição, o Python não.

## 10. Rotina e comandos úteis

```bash
cd ~/Trade-Initial && source .venv/bin/activate
python -m lab.pipeline dryrun                  # recalcula o veredito e retira bots inativos; grava research/forward/verdicts.md
cat research/forward/verdicts.md               # rodando há quantos dias, trades, trades por dia
docker ps --filter name=forward-               # bots
docker logs -f forward-h104                    # log de um bot
ls -t research/pipeline/cycle-*.md | head -3   # últimos ciclos de pesquisa
python -m lab.knowledge                        # reescreve research/knowledge/scoreboard.md (placar de day trade)
python research/tools/forward_freeze.py H-104 --check    # o congelamento de um bot continua íntegro?
python -m unittest discover -s tests           # toda a suíte
```

## 11. Backup e manutenção

- **O que não se perde nunca:** `research/lab.sqlite`, `user_data/tradesv3.*.sqlite`, `research/forward/`, `research/experiments/`, `research/proposals/`. Faça backup fora da máquina.
- **Cron de backup dos bancos** (ajuste `BACKUP_DIR`), igual ao de `ops/vps/bootstrap-ubuntu.sh`:
  ```cron
  10 3 * * * cd ~/Trade-Initial && mkdir -p ~/backups && for f in user_data/tradesv3.*.sqlite research/lab.sqlite; do sqlite3 "$f" ".backup '$HOME/backups/$(basename "$f" .sqlite)-$(date +\%F).sqlite'"; done && find ~/backups -name '*.sqlite' -mtime +30 -delete
  ```
- **Logs:** `user_data/logs/*.log` crescem; o `bootstrap-ubuntu.sh` mostra uma regra de `logrotate` pronta.
- **Nunca rode `docker system prune -a`:** apagaria a imagem fixa `freqtradeorg/freqtrade:2026.9`. Para liberar espaço use `docker container prune` e `docker image prune` (sem `-a`).
- `ops/guard.forward.json` está **desatualizado** (lista contêineres antigos H-009 e H-016). Só ative o cron do guard depois de atualizar a lista de bots nele.

## 12. Armadilhas conhecidas

1. **Quebras de linha:** a causa de quase todo FAIL de congelamento. Cópia byte a byte e `core.autocrlf=true`.
2. **Dois computadores rodando.** Evidência duplicada e commits divergentes. Um por vez.
3. **Editar o repositório com o loop rodando:** `GuardAbort`. Pare o loop, edite, religue.
4. **`python: command not found` dentro de um agente:** o PATH do loop precisa ter `.venv/bin`. O `research-loop.sh` já faz isso.
5. **Contêineres `freqtrade-run` órfãos** depois de matar um ciclo: remova com o comando da seção 8.
6. **Portal mostrando dados velhos:** reiniciar depois de mudar Python.
7. **Erro de timestamp da Binance:** relógio sem sincronizar (`chrony`).
8. **Erro 451 ou "restricted location":** o IP do servidor está bloqueado pela Binance; mudar de região.
9. **Pouca memória:** `docker stats --no-stream`. Cada bot usa cerca de 540 MiB e cada backtest mais. Com 8 GB, ligue um pouco de swap.
10. **Commit às cegas:** o PC tinha arquivos do portal modificados por outra sessão e ainda sem commit. Não rode `git add -A` sem o aval do dono.
11. **Os bots têm `restart: "no"` de propósito.** Quem os religa é o vigia (e o Docker, depois do `docker update`).
12. **Mudanças no compose, overlay ou estratégia de um bot ativo** quebram o congelamento. Em vez disso: hipótese nova.

## 13. Voltar para o Windows (rollback)

1. No Linux: `systemctl --user stop trading-lab-loop trading-lab-watchdog` e `for f in docker-compose.forward*.yml; do docker compose -f "$f" stop -t 30; done`.
2. Se os bots operaram no Linux, copie de volta para o Windows os bancos `user_data/tradesv3.forward.h1*.sqlite` (com os contêineres parados). O congelamento é o mesmo nos dois lados, então a evidência continua.
3. No Windows, suba de novo cada bot ativo: `docker compose -f docker-compose.forward.hNNN.yml up -d`. A pasta do Windows ficou intacta porque a migração só copia.

## 14. Checklist final

- [ ] `sha256sum -c` do `.tar` passou e a extração foi feita sem erro
- [ ] `core.autocrlf=true`, identidade do git definida, `git status` mostra só os pendentes conhecidos
- [ ] `ops/linux/verify-migration.sh --full` termina com `ALL CHECKS PASSED`
- [ ] Bots do Windows parados antes de ligar os do Linux
- [ ] 5 contêineres `forward-h100` a `forward-h104` no ar, heartbeat a cada minuto, política `unless-stopped`
- [ ] Teste de reboot: os 5 voltaram sozinhos
- [ ] Portal responde em `127.0.0.1:8765` (e pelo túnel, se for o caso)
- [ ] Backup dos bancos agendado
- [ ] Loop de pesquisa ligado **somente** com o aval do dono, depois do login do `claude`
- [ ] Nenhuma chave de corretora no disco; `real_money` continua `false`

## Apêndice: arquivos desta migração (`ops/linux/`)

| Arquivo | Para quê |
|---|---|
| `pack-from-windows.sh` | Roda no Git Bash do Windows: confere que nada roda, checa os bancos e cria o `.tar` byte-exato com `.sha256` |
| `verify-migration.sh` | Critério de aceite no Linux (somente leitura); `--full` roda toda a suíte |
| `requirements-host.txt` | Pacotes Python do host (numpy, pandas, pyarrow, pytest), com as versões que passaram nos testes |
| `bot-watchdog.sh` | Vigia dos bots: sobe o que caiu e aplica a política `unless-stopped` |
| `research-loop.sh` | Loop contínuo de pesquisa (gasta dinheiro de agente) |
| `trading-lab-portal.service`, `trading-lab-watchdog.service`, `trading-lab-loop.service` | Unidades systemd de usuário |
