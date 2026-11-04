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

## 2026-11-02 — baseline re-test, drawdown metric, bootstrap, manifest fingerprint

- H-001 (SmaTrendBaseline, frozen) re-tested under the corrected harness, exploration split, BTC/ETH/BNB, four cost scenarios (experiments `20261102T224114Z-h-001-exploration-*`). All three pairs `rejected`. Lookahead and recursive pass; 366-388 trades; net profit positive in the base scenario; max drawdown 50.4% (BTC), 46.5% (ETH), 44.0% (BNB) at base and 74-88% at stress. Costs are the problem together with whole-balance sizing.
- Docker engine runs in WSL (Docker Desktop on Windows was not running), so the run used a local shim in the session scratchpad that rewrites `docker ...` to `wsl docker ...`. No repository file was changed for that.
- FOUND: the gate reads `max_drawdown_account`, which Freqtrade computes at the point of largest ABSOLUTE loss. For compounding whole-balance runs it understates the worst relative fall. Example H-007 BNB base: 25.1% (gate) vs 51.3% (`max_relative_drawdown`, matches an independent recomputation from the trade list). Also H-004 BTC 7.8% vs 15.3%, H-005 BNB 42.9% vs 51.8%, H-004 BNB 42.1% vs 48.6%, H-002 ETH 73.6% vs 77.1%. No existing decision flips (all already failed on other gates). `runner._read_backtest_zip` now also returns `max_relative_drawdown_pct` and `experiment.run_experiment` stores it as `max_relative_drawdown_pct__<scenario>`. `gates.py` still reads `max_drawdown_pct`; switching the gate is a decision for the user.
- `lab/bootstrap.py`: seeded circular block bootstrap of the base-scenario trade sequence. H-005 and H-007 on all three pairs: P(max drawdown > 25%) is 66% to 99%, bootstrap drawdown p95 is 51% to 76%. Closed-trade equity only, so the real drawdown is at least this large.
- Manifests now try to record `docker_image_digest` and `ccxt_version` (`experiment.runtime_fingerprint`); a failure leaves them empty and does not fail the experiment.
- H-007 BNB lookahead flag (1 of 20 entry signals, trade window 2019-05-15 03:00 to 05-17 03:00): the entry logic was recomputed locally on the full series and on truncated series for every candle from 2019-05-14 to 05-18, with no difference and large margins on every condition. Not reproduced outside Freqtrade's analyzer; still unresolved, not declared harmless.
- FOUND: a container `trading-lab-freqtrade` (image `freqtradeorg/freqtrade:stable`, restart `unless-stopped`, command `trade ... SmaTrendBaseline`) starts with Docker in WSL. It is dry-run (log: "Dry run is enabled", empty keys), so no money is at risk, but it contradicts the pinned image and `restart: "no"` in docker-compose.yml and shares user_data. Left untouched; the user decides whether to remove it.
- Added `docs/config.production.example.json` (inert: dry_run true, initial_state stopped, no secrets, stoploss_on_exchange true) with a test that keeps it inert.

## 2026-11-02 — gate now reads the relative drawdown; independent engine cross-check

- `gates.decide` reads `max_relative_drawdown_pct__<scenario>` (worst peak-to-trough fall of the account) instead of `max_drawdown_pct__<scenario>` (Freqtrade's `max_drawdown_account`, taken at the largest absolute loss). Reason strings keep their format. gates.json is unchanged: its rule already says "fraction of peak balance". Missing metric fails closed.
- The metric was back-filled for all 19 completed experiments from their raw zips; each zip's `max_drawdown_account` was first checked against the stored value. 8 experiments with different reasons were re-decided (previous `decision.json` kept as `decision.superseded-*.json`; the 2026-10-27 invalidated run was skipped). No verdict changed: all remain `rejected`.
- Engine cross-check: see `research/engine-crosscheck-2026-11-02.md`. A plain-pandas re-implementation of H-001 reproduces Freqtrade's trades exactly on BTC (383/383) and ETH (388/388) and 364/366 on BNB (the 2 others are a floating-point tie in TA-Lib vs pandas). Tool: `research/tools/replicate_sma_baseline.py`.

## 2026-11-02 — H-008 (H-005 rule at 20% exposure) and a metric fix

- Exposure is now an explicit backtest parameter: `runner.run_backtest(exposure=...)` / `experiment.run_experiment(exposure=...)`. Below 1.0 it writes an overlay config (`tradable_balance_ratio`) next to the export and passes it as a second `--config`. Default 1.0 changes nothing. The value is stored as metric `exposure`.
- H-008 registered in the ledger BEFORE running: family VolatilitySqueezeBreakout, H-005 rule unchanged, exposure 20%. Rule for the number: largest 5% step for which the seeded block-bootstrap p95 closed-trade drawdown of the H-005 exploration trades is <= 25% on BTC, ETH and BNB at once (20%: p95 20/22/24%; 25%: 24/27/29%). Only exploration trades were used. Strategy file `VolatilitySqueezeBreakout_H008_v1.py` has signals identical to H-005 (test compares both on the same frame).
- BUG FOUND by H-008 itself: `compounded_profit_excluding_best` rebuilt the balance assuming every trade used the whole balance, so with exposure < 1 it reported 129.8 "without the best trade" against a total of 78.3. It now takes each trade's share of the balance from the export (stake_amount over the balance before it). Check: rebuilding ALL trades with the new rule reproduces Freqtrade's reported total (error < 0.2%, one near-zero case 2%); the old rule was off by up to 5.8x at 20% exposure. For full-exposure runs the two agree to about 1e-4 relative (stake is balance/(1+fee)). The metric was recomputed for all completed experiments from their zips and decisions regenerated; no verdict changed. H-002's stored values came from an older definition and differ more; those runs are invalid anyway.
- H-008 exploration: `candidate_for_portfolio` on BTC, ETH and BNB. Drawdown 12-14% at every cost scenario (stress 13.6/13.9/14.1%), 31/36/36 trades, profit without the best trade positive but concentrated (BTC 33.2 of 78.3, ETH 16.9 of 87.4, BNB 16.0 of 171.5). Expected: exposure scales drawdown, it does not create edge. The informative test is the validation split.

## 2026-11-02 — H-008 validation (read once)

- Experiments `20261102T234825Z-h-008-validation-*`, exposure 20%, frozen rule, no changes after the exploration result.
- BTC 12 trades, ETH 10, BNB 8 (gate: 30). Net profit at base +6.3 / +6.9 / +10.3 on 100 USDT, drawdown 2.4% / 7.7% / 2.7% (stress 2.7 / 8.2 / 3.0%), lookahead and recursive pass. Profit without the best trade: BTC -2.1, BNB -0.5 (fail), ETH +0.006 (barely positive). Decisions: BTC rejected, BNB rejected, ETH inconclusive. H-008 is not a candidate and is not re-run.
- Reading: the drawdown problem is solved by exposure, but the rule produces about 4-5 trades a year, so the validation split (2.3 years) cannot reach the 30-trade gate, and with so few trades the gain depends on one or two trades. Buy-and-hold over the same split: BTC +41.8%, ETH -20.9%, BNB +32.0%. The exploration result (31-36 trades over 7 years) was not repeated out of sample.
- Structural point for the user: a 30-trade minimum per split is unreachable for any slow 1h strategy on a 2.3-year split (it needs roughly 13 or more trades a year).

## 2026-11-03 — H-009 and H-010 (more active strategies, option 1)

- Sources read: the freqtrade-strategies repository (27 strategies, read as text, not run), the article's other four repositories (descriptions only), and the tradingstrategy.ai learn pages (backtesting, risk management, trend following). The MNQ table pasted by the user lists futures systems (shorts, overnight) with no rules, so nothing could be implemented from it. Useful from the docs: Donchian-style channel trend with a moving-average regime, volatility/fixed-share sizing, a higher significance bar (t-stat 3.0) and parameter-stability checks, "live Sharpe 30-50% below backtest".
- `bootstrap.choose_exposure` makes the exposure rule reproducible (it returns 0.20 for the H-005 trades, the value used for H-008).
- H-009 (WeeklyBreakoutRegime) and H-010 (UptrendPullbackRecovery) were registered with their rules, including the exposure rule, before any run. Procedure: calibration run (exploration, base cost, full exposure, trade count must be >= 30 on every pair) -> exposure by rule -> official experiment with 4 cost scenarios, lookahead and recursive -> decision. Calibration artifacts are in `research/experiments/calib-*` (not decisions).
- H-009: calibration 58 / 81 / 80 trades; exposure 25% (p95 drawdown 12 / 22 / 23%). Exploration at 25%: `candidate_for_portfolio` on BTC, ETH, BNB. Base net profit +113.8 / +61.8 / +133.6 on 100, drawdown 7.2 / 18.5 / 14.5% (stress 8.7 / 23.7 / 17.9%; ETH stress is close to the 25% limit), lookahead and recursive pass.
- H-010: calibration 145 / 187 / 173 trades, negative net profit on all three at full exposure (-35.7 / -73.0 / -44.2) with drawdown 61-84%. Exposure rule gave 10%. Exploration: `rejected`, net profit at base -1.7 / -9.1 / -1.6. No edge; the rule is not retried.
- Validation of H-009 NOT read yet. Trades per year in exploration are about 8 (BTC), 12 (ETH), 12 (BNB), so the 2.3-year validation split would hold roughly 19 / 27 / 28 trades against a gate of 30: an inconclusive count is likely whatever the profit does.

## 2026-11-03 — H-011..H-014 (TripleBottomReversal, EMASnapbackATR; 1h and 4h) and cleanup

- Registered H-011..H-014 in the ledger before any run (`research/tools/register_h011_h014.py`). Calibration + official run: `research/tools/calibrate_and_run.py`.
- H-011/H-013/H-014 dropped by the pre-registered rule (< 30 calibration trades on some pair; not retuned). H-012 rejected on BTC, ETH, BNB (negative net profit at base cost, recursive unstable). Validation and final test not read. Results and limitations: `docs/estrategias-h011-h014.md`; dossiers in `research/dossiers/`.
- Lab: `timeframe` threaded through `experiment.run_experiment` / `orchestrator.run_split` (read from the strategy file, default 1h). 4h candles downloaded for BTC/ETH/BNB; `scenarios.json` unchanged.
- Removed flawed, never-valid strategy files H-004 and H-006 (and their tests); recoverable from git (544a3d5).

## 2026-11-03 — Phase 0 of the 5-strategy plan (harness)

- Downloaded 1d candles; verified against 1h aggregates (0 mismatches) and the informative merge on the real engine (`research/tools/check_informative.py`: causal, 0 leaks). `startup_candle_count` applies to every timeframe used, so SMA(200) on 1d needs 200, not 4800.
- Cost scenario `base_2x` (exactly 2x the base total cost); fee accounting verified against exported trades (no double counting).
- New: `lab/{stats,returns,cycles,walkforward,causality,dataquality}.py`, `lab/config/holdout.json`, baseline `Sma200Baseline` (frozen by SHA), `research/baselines/sma200-cycles.json`. Prospective holdout = data from 2026-10-21; semi-contaminated window = last 12 months. No hypothesis registered, no validation/final-test read for any strategy. Details: `docs/harness-fase0.md`.

## 2026-11-03 — Step 0 (hygiene): archive and known defects

- `python -m pytest tests -q` before: 417 passed; after: 432 passed. Working tree not committed (user declined for now).
- Archived (moved, not edited) to `user_data/strategies/_archive/`: H-005, H-007, H-008, H-010, H-011, H-012, H-013, H-014 (8 files; tests to `tests/archive/`, paths adjusted, 49 tests still run). Kept in the strategy path: H-001/002/003 baselines, H-009, `Sma200Baseline`.
- Verified in the container (`docker compose run --rm freqtrade list-strategies`): `_archive/` is NOT loaded by default; `--recursive-strategy-search` would load it (and duplicate names), so the default is kept.
- Registry: new table `archived_strategies` (hypothesis, class, original/archive path, SHA-256, SHA source, UTC time). `hypotheses.status` and every decision are untouched; the ledger shows `[code archived]` after the status. Recorded with `research/tools/register_archive.py`. SHA source: manifest (H-005/007/008/010/012) or file at archive time (H-011/013/014 never had a manifest).
- `research/tools/rerun_archived.py`: `verify` (SHA vs registry and manifests) and `rerun <H-id>` (temporary copy into the strategy path, exploration only, validation/final_test refused, copy removed). Real check: H-010 BTC/USDT base reran with 145 trades, identical to the original record (`20261103T234059Z-rerun-h-010-btc-usdt`).
- H-007 BNB lookahead: reproduced and traced to an 11 h data gap (2019-05-15 03:00-12:00) plus the analyzer's truncation, not to the code. See `research/h007-bnb-lookahead-2026-11-03.md`. The 23.53% price jump is BNB's 2nd candle ever (2017-11-06) and unrelated. Ledger note appended; decision unchanged.
- `lab/strategy_check.py`: `warmup_warnings` (EMA/RSI/ATR/ewm(span) of period P needs `startup_candle_count >= max(400, 3*P)`); warning only, also `python -m lab.strategy_check <files>`. On existing strategies it flags only `BollingerMeanReversionBaseline` (RSI14, startup 200).

## 2026-11-03 - Step 1 (regime filter and controlled imports)

- `lab/strategy_check.py`: `ALLOWED_LOCAL_MODULES = {"regime_filter"}` (only `import regime_filter` / `from regime_filter import ...`; relative imports, `lab`, `os`, any other module still rejected); AST screen extracted to `_screen_tree`, reused by `check_helper_module_source` (regime_filter.py itself passes it).
- `user_data/strategies/regime_filter.py`: `vol_regime(window=30, ratio=1.5)`, `trend_regime(sma_days=200)`, `regime_on(...)`; pure, causal; 3 numeric parameters.
- Tests: `tests/test_regime_filter.py` (screen, behaviour, `lab.causality` prefix/corruption per function), `tests/test_regime_informative_container.py` (runs `research/tools/check_regime_informative.py` in the container: 4 generated strategies, real `merge_informative_pair`; prefix invariance, future corruption, visible-day check: all OK).
- Freqtrade imports the sibling module (backtests of the 4 ablation strategies ran, trades > 0); `list-strategies` is unaffected by `regime_filter.py`.
- Ablation 1.4 (`research/tools/ablation_regime.py`, IS only): no benefit under the pre-registered criterion, so `vol_regime` is OFF by default. Details: `research/regime-filter-ablation.md`.

## 2026-11-04 - Step 2, family 1: TSMOM (H-015 grid, H-016 chosen configuration)

- H-015 registered BEFORE any run (grid N x regime = 10, DSR N = 10, criteria fixed). Strategy, 9 tests, screen, lookahead/recursive clean on BTC/ETH/BNB. Grid explored on the IS with `research/tools/grid_explore.py` (reusable for later families): DSR 0.999, PBO 0.31, plateau, beats B&H and Sma200Baseline at base_2x, 89-96 trades per pair.
- H-016 (the selected cell, N=30 no regime) registered, then calibration (exposure 0.15) and official exploration experiment: `candidate_for_portfolio` on 3 pairs, all gates clear.
- Validation read ONCE via `research/tools/validate_once.py` (refuses a second read): BTC rejected, ETH candidate, BNB rejected; profit without the best trade negative on BTC and BNB. H-016 not approved. Family rejected, code archived (`_archive/`, tests in `tests/archive/`), registry and ledger updated. Report: `research/grids/H-015-report.md`.
- Tools added: `analysis_checks.py` (smoke + lookahead + recursive), `grid_explore.py`, `validate_once.py`, `register_h015.py`, `register_h016.py`.

## 2026-11-04 - Dashboard visual overhaul (skills ui-ux-pro-max, design-system, ui-styling)

- Skills read: nextlevelbuilder/ui-ux-pro-max-skill (`ui-ux-pro-max`, `design-system`, `ui-styling`). Their stack (React/Tailwind/shadcn) was NOT adopted: the portal stays plain HTML/JS, no build, strict CSP, read-only. Principles applied: 3-layer tokens (primitive -> semantic -> component), accessibility first (focus ring, 44px touch targets on coarse pointers, reduced motion, high-contrast mode, skip link), dense-dashboard density dial, consistent type scale, print styles.
- `lab/dashboard_assets/index.html` only: tokens re-layered (class names unchanged), polished cards/KPIs/nav/tables/buttons, comfortable|compact density toggle (localStorage), pt-BR menu names, readable measure for free-text table cells, sortable headers inherit header style.
- Bug fixed: opening the portal without a hash showed "Página não encontrada (#/undefined)"; it now opens on Visão geral.
- Verified: 68 dashboard tests, headless-Chrome screenshots of all 8 routes (dark and light). Mobile layout not verified visually (headless Chrome has a minimum window width); the media queries were left as they were.

## 2026-11-04 - Portal rebuilt (docs/portal-redesign.md)

- Audit of the existing portal and data (docs/portal-redesign.md). Kept backend, DB, gates, runner and the stdlib server; no new dependencies.
- New `lab/analytics.py` (win rate with Wilson CI, profit factor, expectancy, payoff, streaks, histogram, monthly returns, evidence score, signals) and a `strategies` block in the dashboard state (one row per strategy and stage, pooled over pairs; invalid hypotheses excluded). The evidence score is capped at 40 for small samples and at 60 when the gates rejected; win rate is not an input.
- New front-end `lab/dashboard_assets/portal.js` plus design tokens and components in `index.html`: Visao geral, Ranking, Explorador, Comparar, Backtests (backtest / dry-run / real kept apart), Sistema, Ctrl+K search. Old overview code removed; the summary sentence was corrected (it said validated hypotheses were still awaiting validation).
- Bugs found while building: CSS class `.stack` collided with `table.stack` (every table became a grid), empty-hash route, and `strategies` missing from the empty-state contract (caught by the contract test).
- Verified: 20 analytics tests, 9 portal-state tests, 68 dashboard tests, and `node research/tools/portal_e2e.mjs` (40 checks in real Chrome, no console errors). Mobile layout not verified visually.
