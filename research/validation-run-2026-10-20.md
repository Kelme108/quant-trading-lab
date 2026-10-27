# Validation run notes — 2026-10-20

## Changes applied

- Pinned Docker image from `stable` to `freqtradeorg/freqtrade:2026.9`.
- Disabled the API by default and removed local API credentials from the tracked dry-run config.
- Removed the unused `margin_mode` setting from the spot configuration.
- Changed Compose restart policy to `no` so starting a forward test is deliberate.
- Added an OHLCV validator, manifest template, hypothesis ledger, and protocol v2.
- Extended strategy contract tests for causal indicators, zero volume, NaN startup values, and binary signal columns.
- Preserved the frozen baseline and all existing result artifacts.

## Verification in this environment

- JSON configuration validation: passed.
- Host Python unit tests: blocked because the active host Python has no `pandas` module.
- Host OHLCV validation: blocked because the active host Python has no `pandas` module.
- Docker Compose validation: blocked because Docker is not available in this shell (`docker: command not found`).

## Required WSL verification

Run these commands from WSL after Docker and the project dependencies are available:

```bash
cd /mnt/d/Trade-Initial
python3 -m unittest discover -s tests -v
python3 research/validate_ohlcv.py user_data/data/binance/BTC_USDT-1h.feather
docker compose config --quiet
docker compose run --rm freqtrade list-strategies \
  --config user_data/config.dryrun.json
```

Do not interpret this record as evidence that the new validation commands passed; the
blocked checks must be rerun in WSL.
