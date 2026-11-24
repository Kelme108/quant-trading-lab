# Runbook: do dry-run ao ao vivo

Este é o passo a passo operacional. As regras de quando é permitido avançar estão em [checklist-operacao-real.md](checklist-operacao-real.md), e nada aqui substitui aquele checklist. **Hoje nenhuma estratégia tem evidência fora da amostra, então dinheiro real continua bloqueado.**

## Os ambientes

| Ambiente | O que testa | Dinheiro | Onde está |
|---|---|---|---|
| Dry-run forward (H-009, H-016) | A estratégia com preço real e ordens simuladas | nenhum | `docker-compose.forward*.yml` |
| Binance Spot Testnet | A mecânica: chaves, ordens no servidor, stop na corretora, falhas | fictício | [testnet/README.md](../testnet/README.md) |
| MT5 demo (MetaQuotes) | O adaptador MT5: conexão, ordens, retcodes, journal | fictício | `live/` e `python -m live.run` |
| Binance real | — | **bloqueado** | não existe config; [test_live_readiness_safety.py](../tests/test_live_readiness_safety.py) impede `dry_run: false` fora da testnet |

## 1. Criar a VM no Azure (pelo portal)

1. **Virtual machines → Create.** Use estas opções:
   - Região: **Brazil South**.
   - Imagem: **Ubuntu Server 24.04 LTS**.
   - Tamanho: **B2als v2** (2 vCPU, 4 GB).
2. **Autenticação:** chave SSH, sem senha. O usuário de administração pode ser, por exemplo, `trader`.
3. **Portas de entrada:** só a **SSH (22)**. Depois de criar, restrinja a regra do NSG ao seu IP.
4. **Disco:** Standard SSD, 32 GB.
5. **Rede:** IP público **estático**. A chave de API da Binance real vai ser restrita a esse IP.
6. **Auto-shutdown: desligado.** O bot precisa rodar 24/7.

O custo é de cerca de US$ 52/mês sem compromisso (o cálculo foi feito em 05/11/2026).

## 2. Preparar a VM

```bash
ssh trader@<ip>
# copie ops/vps/bootstrap-ubuntu.sh para a VM (scp) e rode:
bash bootstrap-ubuntu.sh
```

O script instala o Docker, configura o relógio em UTC com chrony e o firewall só com SSH, ativa a rotação de logs, o cron do guarda (a cada 5 min) e o backup diário dos bancos SQLite, e no fim mostra o IP público. Ele não liga nenhum bot e não grava nenhuma chave.

O repositório é privado: no `git clone`, use um token do GitHub ou uma deploy key só de leitura.

## 3. Testnet (na VM ou no PC)

Siga [testnet/README.md](../testnet/README.md): crie as chaves em testnet.binance.vision, preencha `testnet/.env`, rode `docker compose -f docker-compose.testnet.yml up -d` e execute os testes T1 a T9.

Para ensaiar o kill switch automático, adicione ao cron:

```
*/5 * * * * cd ~/quant-trading-lab && python3 ops/freqtrade_guard.py --config ops/guard.testnet.json >> ops/state/guard-cron.log 2>&1
```

O [ops/guard.testnet.json](../ops/guard.testnet.json) tem `enforce: true`, limite diário de 5 USDT e limite total de 15 USDT. Para testar, crie `ops/state/STOP.testnet` e confira que o bot para em até 5 minutos.

## 4. MT5 demo (no PC Windows, com o terminal aberto)

1. **Troque a senha da conta MetaQuotes-Demo**, porque ela apareceu no chat.
2. Crie o `live/.env`. Ele é ignorado pelo git, e as credenciais nunca vão para o chat. Conteúdo:
   ```
   MT5_LOGIN=...
   MT5_PASSWORD=...
   MT5_SERVER=MetaQuotes-Demo
   MT5_PATH=C:\Program Files\MetaTrader 5\terminal64.exe
   ```
3. Copie `live/config/live.smoke.example.json` para `live/config/live.json`.
4. Rode `live\.venv\Scripts\python.exe -m live.run --check`. Ele só lê:
   - confirma que a conta é **DEMO**;
   - mostra o símbolo (BTCUSD) e o fuso estimado do servidor.
5. Preencha `broker.server_utc_offset_hours` com o fuso confirmado e rode o `--check` de novo.
6. Rode `live\.venv\Scripts\python.exe -m live.run`. A estratégia de smoke abre o volume mínimo com stop no servidor e fecha no candle seguinte. Acompanhe pelo terminal e pelo `live/journal.smoke.sqlite`.
7. Testes de falha:
   - matar o processo com a posição aberta e reiniciar: deve dar reconciliação ou modo seguro;
   - criar `live/STOP` com a posição aberta: o engine deve zerar.

Isto valida o adaptador, não a B3. Para WIN/WDO é preciso uma conta demo **netting** numa corretora B3 (Etapa 2.2 em diante de [prompt-execucao-tempo-real.md](prompt-execucao-tempo-real.md)).

## 5. Kill switch: como parar tudo

| Onde | Parar entradas e ordens | Zerar posições |
|---|---|---|
| Freqtrade (qualquer bot) | Criar o arquivo de STOP do guarda (`ops/state/STOP.<nome>`) com `enforce`, ou rodar `docker compose -f <arquivo> down` | Manual no site ou app da Binance: as posições ficam protegidas pelo stop na corretora. Para isso ser automático, seria preciso ligar a API do Freqtrade, o que hoje é decisão pendente |
| MT5 (`live/`) | Criar `live/STOP` (por exemplo `python -m live.core.killswitch live/STOP "motivo"`) | Automático: o engine cancela as ordens e fecha as posições enquanto o arquivo existir |

Nenhum dos dois volta a operar sozinho: o operador apaga o arquivo de propósito.

## 6. Antes do primeiro real (Binance)

Tudo abaixo precisa de evidência registrada:

1. **Estratégia com validação fora da amostra aprovada** e forward dry-run concluído dentro do esperado (checklist B, C e E).
2. **Testnet T1 a T9 registrados** em `research/forward/failure-tests.md`.
3. **Decisões do bloco A tomadas:** capital do piloto, perda máxima diária e total (que vão para o `ops/guard.live.json`), canal de alerta e situação fiscal.
4. **Chave de API real** com estas restrições:
   - só **Spot trading**;
   - **sem saque**;
   - **restrita ao IP fixo da VM**;
   - guardada só no `.env` da VM.
5. **A config real** sai de [config.production.example.json](config.production.example.json):
   - protegida por hash;
   - `initial_state: stopped`.

   Ligar `dry_run: false` fora da testnet exige mudar **conscientemente** o [test_live_readiness_safety.py](../tests/test_live_readiness_safety.py), num commit próprio aprovado por você.
6. **O guarda real** (`ops/guard.live.json`) roda com `enforce: true` no cron antes de o bot subir.
