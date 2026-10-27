## 2026-10-20 — hardening and reproducibility

- `docker-compose.yml` changed from mutable `freqtradeorg/freqtrade:stable` to pinned `freqtradeorg/freqtrade:2026.9`.
- Compose restart policy changed to `no`; starting a forward test is deliberate.
- Tracked dry-run configuration changed to safe defaults: API disabled, loopback bind, blank local API credentials, spot mode, no margin setting.
- Added `research/validate_ohlcv.py`, `research/experiment-manifest.yaml`, `research/manifests/2026-10-20-sma-v1-reference-preserved.yaml`, `research/hypothesis-ledger.md`, and `research/validation-protocol-v2.md`.
- Added safety configuration tests and expanded strategy contract tests.
- SHA-256 recorded for baseline, config, dataset, and Compose file in the preserved manifest.
- JSON validation and Python compilation passed in the current host environment.
- Unit tests and OHLCV validation were not runnable in the current host Python because `pandas` is not installed.
- Docker Compose verification was not runnable in the current shell because Docker is not installed/available on PATH. WSL verification remains required.

## 2026-10-20 — diagnóstico

```text
Host/MSYS2: MINGW64_NT-10.0-26200
WSL: Kali Linux Rolling 2025.2, WSL 2
WSL Python: 3.13.3
WSL pip: 25.1.1
WSL Git: 2.47.2
WSL Docker: 28.3.3
WSL Docker Compose: v2.39.1
Espaço livre em D: aproximadamente 120 GB
```

## 2026-10-20 — validações locais

- `python3 -m unittest discover -s tests -v` — 3 testes passaram.
- `python3 -m json.tool user_data/config.dryrun.json` — passou.
- `docker compose version` — `v2.39.1`.
- `docker compose config --quiet` — passou.
- `docker compose pull` — passou; imagem oficial `freqtradeorg/freqtrade:stable` resolvida como Freqtrade `2026.9`.
- `freqtrade list-strategies` — `SmaTrendBaseline` com status `OK`.
- `download-data` — passou para Binance, BTC/USDT, spot, 1h, feather.
- `list-data --show-timerange` — 8.778 candles, `2025-10-20 00:00 UTC` a `2026-10-20 17:00 UTC`.

## 2026-10-20 — backtest

- Primeira tentativa — recusada porque 100 USDT × `tradable_balance_ratio` 0,99 = 99 USDT, menor que `stake_amount` 100.
- Correção — `tradable_balance_ratio` alterado para `1.0`.
- Execução intermediária com `minimal_roi: {"0": 0.0}` — descartada; ROI encerrou a operação imediatamente.
- Baseline corrigida — `minimal_roi: {"0": 100.0}` para que o cruzamento e o stop-loss governem as saídas.
- Backtest válido — `backtest-result-2026-10-20_18-08-58.zip`.
- Resultado observado — 1 operação, retorno `-1,534 USDT` (`-1,53%`), saldo final `98,466 USDT`, drawdown fechado `1,53%`; resultado inconclusivo por amostra mínima.

## 2026-10-20 — lookahead e dry-run

- `lookahead-analysis` — passou; 20 sinais analisados, `has_bias: No`, 0 sinais de entrada enviesados, 0 de saída e nenhum indicador enviesado.
- API habilitada no arquivo de configuração com credenciais locais fortes; chaves de exchange permanecem vazias.
- `docker compose up -d freqtrade` — container ativo, Freqtrade `2026.9`, modo `dry_run`, spot, whitelist BTC/USDT.
- Mapeamento do host — `127.0.0.1:8080->8080/tcp`.
- Teste HTTP inicial — conexão ao host ocorreu, mas o processo no container resetou a conexão porque ouvia em `127.0.0.1` dentro do container.
- Correção aplicada no arquivo — `api_server.listen_ip_address: "0.0.0.0"` dentro do container; o host continua publicado somente em `127.0.0.1`.
- Aplicar correção — `docker compose up -d --force-recreate freqtrade` ficou bloqueado pela política de segurança da sessão por recriar/expor serviço local; executar manualmente no WSL.

Nenhuma API privada, conta, depósito ou ordem real foi utilizada.

## 2026-10-27 — correção de drift de segurança e ambiente

- `user_data/config.dryrun.json` revertido para os defaults seguros: `api_server.enabled: false`, `listen_ip_address: "127.0.0.1"`, `jwt_secret_key`/`username`/`password` vazios. O arquivo havia ficado com a API habilitada em `0.0.0.0` desde o teste manual de FreqUI de 2026-10-20 e nunca foi revertido, o que fazia `tests/test_safety_configuration.py` falhar.
- Ambiente de execução confirmado: o host tem acesso direto a Docker/Compose via Git Bash (MSYS2) em `D:\Trade-Initial` / `/d/Trade-Initial`, sem depender do WSL. O WSL (`kali-linux`) está parado nesta máquina; o `.venv/` existente foi criado dentro do WSL e não funciona neste shell.
- `pandas` instalado no Python do host (3.14.0) via `pip install pandas` para permitir `python -m unittest discover -s tests -v` sem depender de container ou WSL.
- `python -m unittest discover -s tests -v` — 8 testes, todos `OK` após as duas correções acima.
- Confirmado via `--help`: `docker compose run --rm freqtrade backtesting --export-filename` está **deprecated**; usar `--export-directory` (diretório por experimento). `--fee` é aplicado nos dois lados automaticamente. `recursive-analysis` não tem flag de exportação estruturada (somente stdout); `lookahead-analysis` tem `--lookahead-analysis-exportfilename` (CSV).
- Comandos Docker com paths destinados ao container (`/freqtrade/user_data/...`) precisam do prefixo `MSYS_NO_PATHCONV=1` neste shell Git Bash, senão o MSYS2 reescreve o path e cria diretórios espúrios fora do projeto.
- `docker compose run --rm freqtrade list-data --datadir /freqtrade/user_data/data/binance --show-timerange` confirmado: BTC/USDT 1h, 8778 candles, `2025-10-20T00:00:00Z` a `2026-10-20T17:00:00Z`.
- Descoberta crítica: com `api_server.jwt_secret_key` vazio (o valor exigido por `tests/test_safety_configuration.py` na primeira correção), o schema de configuração do Freqtrade 2026.9 rejeita **todo** comando (`backtesting`, `lookahead-analysis`, `recursive-analysis`, não só `trade`/`webserver`) com `Invalid configuration. Reason: '' is too short` (`minLength: 32`), mesmo com `api_server.enabled: false`. Resolvido, com aprovação do usuário: `jwt_secret_key` passou a ser um segredo aleatório de 64 caracteres hex (gerado com `secrets.token_hex(32)`), nunca usado para autenticação de fato já que a API continua desabilitada e em loopback. `tests/test_safety_configuration.py` atualizado para exigir `len(jwt_secret_key) >= 32` e ausência da string `"SUBSTITUA"`, em vez de string vazia. `tests/test_protected_files.py` e `lab/guard.py` atualizados com o novo SHA-256 de `config.dryrun.json`.
- Confirmado rodando de verdade: `backtesting` e `recursive-analysis` completam normalmente contra `SmaTrendBaseline` no split de exploração (`20251020-20260527`) com a config corrigida. Formato real de saída do `recursive-analysis` é uma tabela por indicador com percentual de variação por `startup_candle` testado (`199`, `200`, `399`, `499`, `999`, `1999`); `0.000%` em todas as colunas (ou `-` quando não há candles suficientes) indica ausência de bias recursivo. Um artefato de backtest de verificação manual (`backtest-result-2026-10-27_14-25-48.zip`) foi gerado neste teste e preservado em `user_data/backtest_results/`, sem registro de experimento formal associado.
