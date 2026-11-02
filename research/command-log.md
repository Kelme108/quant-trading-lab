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

## 2026-10-30 — Phase 1 brought up to the updated task (portfolio layer, multiple-testing penalty)

- Phase 1 had been built from the earlier task text. Added what the updated text requires; nothing under `user_data/` or the protected baselines was touched.
- `lab/config/gates.json` (still PROPOSED, not approved): decision renamed `candidate_for_forward_test` -> `candidate_for_portfolio`; net-profit bar is now `base_threshold_quote * (1 + 0.1 * variants_tested_in_family)` with `base_threshold_quote = 1.0` (1% of the 100 USDT wallet). The linear 10% step is a stand-in for a deflated Sharpe ratio, not an implementation of one; rationale in the file's `_rationale` field. `gates.decide()` takes `variants_tested_in_family`; `registry.count_prior_variants()` supplies it (same-family hypotheses registered before the one being judged).
- `lab/registry.py`: `experiments.pair` column (default `BTC/USDT`) with an in-place migration for databases created earlier; the local `research/lab.sqlite` was migrated when first opened. New `list_latest_decisions()`.
- `lab/config/scenarios.json` and `runner.enabled_pairs()/enabled_timeframes()`: only BTC/USDT 1h enabled. ETH/USDT and BNB/USDT are listed but disabled; BNB/USDT is a proposed third pair, to be confirmed after measuring its correlation with BTC.
- `lab/config/portfolio.json` (PROPOSED) and `lab/portfolio.py`: candidate must hold `candidate_for_portfolio` in every (enabled pair, exploration/validation) cell; min/max profit-per-day across cells >= 0.25; |correlation| with any already-included strategy <= 0.7 over daily returns built from the Freqtrade trade export; undefined correlation excludes. Considered in registration order, equal weights, an empty portfolio is valid. `final_test` rows are never read, and no snapshot can be created once `final_test_unlocked` is true. `runner.read_trades()` exposes the trade list from an export zip.
- `python -m unittest discover -s tests` — 95 tests, `OK` (61 before this change).
- NOT done, blocked: Phase 1a data expansion. The Docker engine was not running (`dockerDesktopLinuxEngine` pipe missing), so no `download-data` was possible. `user_data/data/binance/` still holds only BTC_USDT-1h.feather (2025-10-20 .. 2026-10-20).
- NOT done, needs a decision: per-pair `splits.json`. Re-deriving 60/20/20 on 5 or more years of BTC history (BTC/USDT on Binance goes back to 2017) puts the 2025-10-20 .. 2026-10-20 window, which the three baselines and the H-002 end-to-end run have already looked at, inside the new final_test.

## 2026-10-30 — Phase 1a data expansion (Docker back up)

- Backed up the previous BTC file to `user_data/data/archive/BTC_USDT-1h-20251020-20261020.feather` (SHA-256 `a1e3976eeabd44c7fe98fec3bf7dbec034ccb83640c1edc2c3af1eefe18b7bf`) before touching it, so the H-002 end-to-end manifest stays reproducible.
- `download-data --config /freqtrade/user_data/config.dryrun.json --pairs BTC/USDT --timeframes 1h --timerange 20170101- --data-format-ohlcv feather --prepend` (flags confirmed with `--help`). Then `--pairs ETH/USDT BNB/USDT` with the same options, without `--prepend`.
- `list-data --show-timerange`: BTC/USDT 1h 2017-08-17 04:00 .. 2026-10-20 16:00, 80309 candles. ETH/USDT 80544 candles and BNB/USDT 78607 candles (BNB from 2017-11-06) both run to 2026-10-30, ten days past BTC's end: per-pair split boundaries cannot share one end date.
- `research/validate_ohlcv.py` on the BTC file reports `valid: false`: 28 gaps, 0 duplicates, 0 invalid OHLC rows. All 28 fall between 2017-09-06 and 2023-03-24 (1 to 33 hours each, about 140 hours in total, consistent with exchange downtime). None is after 2023-03-24, so the 2025-10-20 .. 2026-10-20 window used by the baselines is intact. Gaps were not filled or interpolated. Whether gaps of this size are acceptable is a decision for the user; the validator was not loosened.
- Measured daily-return correlation with BTC (common days): ETH 0.787, BNB 0.635; over the last 365 days ETH 0.906, BNB 0.813. Three pairs are therefore far from three independent samples, and a result that holds on all three is weaker evidence of generalization than the count suggests. BNB/USDT stays only a PROPOSED third pair in `scenarios.json`; nothing was enabled there.
- Not done: `splits.json` is unchanged and still describes BTC/USDT 2025-10-20 .. 2026-10-20 (its `confirmed_range` no longer matches the file on disk; benchmarks slice by date, so they are unaffected). Waiting on the final_test decision recorded above.

## 2026-10-30 — decisions delegated by the user ("do what is best for the tests"), and a harness bug

- BUG FOUND, affects every earlier result: the lab ran backtests with `--stake-amount 100` on a `--dry-run-wallet 100`. After the first losing trade the balance drops below the stake and Freqtrade never opens another position. Same Donchian run on ETH/USDT validation, same fees: fixed 100 -> 1 trade (-0.99%); `unlimited` -> 284 trades (-38.22%, max underwater 50.19%). So "1 trade" for SmaTrendBaseline, DonchianBreakoutBaseline and the H-002 end-to-end run (2026-10-27) measured this artifact, not the strategies, and "inconclusive because too few trades" was wrong. Those results, including `20261027T143611Z-donchian-h002-explore` and the README/validation-run numbers, must not be used for any decision.
- Fix: `runner.run_backtest` now defaults to `stake_amount="unlimited"` (whole available balance, `max_open_trades=1`); manifest default is `unlimited`; regression test in `tests/test_lab_runner.py`.
- NOT fixed, needs the user: `user_data/config.dryrun.json` has `stake_amount: 100` and `dry_run_wallet: 100`, so a forward test in dry-run would stall the same way after its first loss. The file is hash-protected (`tests/test_protected_files.py`, `lab/guard.py`); changing it needs explicit approval.
- Final test: only data from 2026-10-21T00:00:00Z onward (open-ended), not the last 20% of the history. Reason: the 2025-10-20..2026-10-20 BTC window had already been backtested by the baselines, so a carved-out final test would have contained seen data.
- `splits.json` rewritten per pair: 75% exploration / 25% validation of all candles before the cutoff, boundaries on exact candles, `timerange` in unix seconds (the old date-only timeranges overlapped exploration and validation by hours). BTC exploration 2017-08-17..2024-07-04, validation 2024-07-04..2026-10-20.
- Gap tolerance: `validate_ohlcv.py` gained an optional `max_gap_hours` (default strict). `scenarios.json` sets 48 h; the 28 BTC gaps (largest 33 h) are tolerated, still counted in `gaps`, never filled.
- ETH/USDT and BNB/USDT enabled in `scenarios.json` (BNB: lowest measured correlation with BTC, 0.635 overall / 0.813 last year).
- An end-to-end run started before the stake fix was stopped; its experiment row `20261030T125953Z-donchian-h002-explore-btc-usdt` is marked `failed` and its partial raw files are kept for traceability. No manifest was written for it.

## 2026-11-02 — recursive-analysis parser fix and re-decision

- BUG: `runner._parse_recursive_stdout` scanned the whole stdout+stderr stream for `\d+.\d+%`, so log lines such as `Using fee 0.1000%` and `Price jump ... of 23.53%` were counted as recursive instability. Fix: only table rows (lines starting with `│`) are read. Regression tests: `tests/test_lab_runner_recursive.py`.
- Re-parsed the stored raw output of every experiment. Only 5 changed (False -> True): H-003 BTC/ETH/BNB, H-007 BTC/BNB. H-004 stays unstable (real table cells of 9-16%). H-002, H-005 and H-007 ETH were already stable.
- The 5 experiments were re-decided through `decide_experiment`: a new row in `decisions` (latest wins; earlier rows kept) and the previous `decision.json` kept as `decision.superseded-20261102T223636Z.json`. The `recursive_is_stable` metric was overwritten in `metrics`; its old value remains in the earlier decision's reasons.
- Outcome unchanged: all 5 stay `rejected` (H-003: profit and drawdown; H-007: drawdown, trades < 30, and lookahead on BNB). `H-007-exploration/facts.json`, `quant.md`, `risk.md` and `validator.md` were generated before this fix and still show the old recursive result for BTC and BNB.
