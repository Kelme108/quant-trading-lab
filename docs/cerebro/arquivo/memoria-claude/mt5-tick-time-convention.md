---
name: mt5-tick-time-convention
description: "Clear MT5 tick time_msc (and requests) are the SERVER wall clock (B3/Sao Paulo time) counted as UTC, not real UTC; naive datetimes get shifted +3 h by the package"
metadata:
  node_type: memory
  type: reference
  modified: 2026-11-16T22:31:15.527Z
---

On the Clear demo terminal, tick `time_msc` is the B3 wall-clock time in ms counted as if it were UTC (like bar times; live configs use server offset -3). Requests to copy_ticks_range/copy_ticks_from use that same clock: to read 09:00-09:20 B3 time, pass aware datetime(…, 9, 0, tzinfo=UTC). A NAIVE datetime is read by the MetaTrader5 package as this machine's local time (BRT) and so lands 3 h later.

Found 2026-11-16: the day's last tick showed as 15:31 when converted as UTC→SP (the real close is 18:31). The first version of research/tools/b3_execution_cost.py had read 12:00-18:30 B3 time labelled 09:00-15:30; fixed and re-measured the same day (docs/plano-busca-padroes-b3.md section 9). Expired contracts (WINV26, WDOX26, …) are not selectable: only the current and next contract's ticks can be read.

**How to apply:** any new tick code: convert with timezone.utc for B3 wall time, never SP zone, never naive. Related: [[b3-pattern-search]].
