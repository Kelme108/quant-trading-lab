---
name: owner-account-hedging
description: "Owner's REAL account (ClearInvestimentos-CLEAR) and the Clear demo are both HEDGING (raw margin_mode 2, read 2026-11-17); do not raise netting again"
metadata:
  node_type: memory
  type: user
  modified: 2026-11-17T22:34:56.635Z
---

**Account mode.** The owner said 2026-11-17: "minha conta é a hedging". When I raised netting again, they replied "hedging, ja foi falado."

- The real account reads raw `account_info().margin_mode == 2`: 0 = netting, 1 = exchange, 2 = hedging.
- It is on server ClearInvestimentos-CLEAR, terminal `C:\Program Files\MetaTrader 5\terminal64.exe`; live/.env.real MT5_PATH points there.
- An earlier label of mine said "netting". It was a bug in my check: I compared against an MT5 constant instead of the number.
- The demo (ClearInvestimentos-DEMO, terminal `C:\Program Files\Clear Investimentos MT5 Terminal`) is hedging too.

**How to apply:**
- Many robots per contract are fine on both accounts. Do not raise netting.
- When checking a mode, print the raw number.
- One terminal holds one account at a time. Logging the demo terminal into another account trips the robots' guard; they stop without orders, as at 14:20 on 2026-11-17.
- Related: [[b3-win-wdo-plan]].
