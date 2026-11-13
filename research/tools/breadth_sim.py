"""Pre-registration aid: how do alternative exploration-breadth rules trade false positives against power?
Synthetic rules on the REAL 1h price paths of the 26 pairs (exploration windows only; no validation/holdout data).
Each synthetic rule enters at hours shared across pairs (market-wide activity -> correlated trades), holds 10 bars, long.
Its true expected CONSERVATIVE net per trade is set to mu_c (+ per-pair heterogeneity tau) by demeaning each pair's
10-bar forward return and adding mu_c + 0.45%. Per-pair gates approximate lab/config/gates.json: >= 30 trades,
net > 10 USDT at base (0.30%) and conservative (0.45%), base net excluding the best trade > 0, drawdown <= 25% at
optimistic/base/conservative, fixed stake 250 USDT on a 1000 USDT wallet."""
import json, sys
import numpy as np, pandas as pd
from pathlib import Path
ROOT = str(Path(__file__).resolve().parents[2])
sp = json.load(open(f"{ROOT}/lab/config/splits.json"))["pairs"]
PAIRS = list(sp)
ORIG = PAIRS[:9]
HOLD, STAKE, WALLET = 10, 250.0, 1000.0
COST = {"optimistic": .0015, "base": .0030, "conservative": .0045}
idx = pd.date_range("2017-08-17 04:00", "2024-07-04 19:00", freq="1h", tz="UTC")
fwd = {}
for p in PAIRS:
    d = pd.read_feather(f"{ROOT}/{sp[p]['source_data_path']}").set_index("date")["close"]
    a, b = pd.Timestamp(sp[p]["exploration"]["start_utc"]), pd.Timestamp(sp[p]["exploration"]["end_utc"])
    d = d[(d.index >= a) & (d.index <= b)]
    f = (d.shift(-HOLD) / d - 1).reindex(idx)
    f = f - f.mean()
    fwd[p] = f.to_numpy()
week = ((idx - idx[0]) // pd.Timedelta(days=7)).to_numpy()
SHARED = (sys.argv[3] if len(sys.argv) > 3 else "shared") == "shared"
def run(mu_c, tau, rng, q=0.01, r=0.35):
    active = rng.random(len(idx)) < q
    res = {}; pooled_w, pooled_net = [], []
    for p in PAIRS:
        f = fwd[p]
        act = active if SHARED else (rng.random(len(idx)) < q)
        cand = np.flatnonzero(act & (rng.random(len(idx)) < r) & ~np.isnan(f))
        take, nxt = [], -1
        for i in cand:
            if i >= nxt: take.append(i); nxt = i + HOLD
        take = np.array(take, dtype=int)
        mu_p = mu_c + (rng.normal(0, tau) if tau else 0.0)
        g = f[take] + mu_p + COST["conservative"]
        ok = len(g) >= 30
        nets = {}
        for s, c in COST.items():
            pnl = STAKE * (g - c); nets[s] = pnl.sum()
            eq = WALLET + np.cumsum(pnl); peak = np.maximum.accumulate(np.maximum(eq, WALLET))
            if len(eq) and ((peak - eq) / peak).max() > 0.25: ok = False
        base = STAKE * (g - COST["base"])
        ok = ok and nets["base"] > 10 and nets["conservative"] > 10 and (base.sum() - (base.max() if len(base) else 0)) > 0
        res[p] = (ok, nets["conservative"] > 0)
        pooled_w.append(week[take]); pooled_net.append(g - COST["conservative"])
    w = np.concatenate(pooled_w); n = np.concatenate(pooled_net)
    return res, w, n
def pooled_pass(w, n, rng, B=400):
    uw, inv = np.unique(w, return_inverse=True)
    s = np.bincount(inv, weights=n); k = np.bincount(inv)
    pick = rng.integers(0, len(uw), size=(B, len(uw)))
    means = s[pick].sum(1) / k[pick].sum(1)
    return np.quantile(means, 0.05) > 0
def rules(res, w, n, rng):
    passed = [p for p in PAIRS if res[p][0]]; posc = sum(res[p][1] for p in PAIRS)
    po = sum(p in passed for p in ORIG); pn = len(passed) - po
    return {"R0 16/26 (now)": len(passed) >= 16, "R1 13/26": len(passed) >= 13,
            "R2 pooled CI + 13/26 net>0": pooled_pass(w, n, rng) and posc >= 13,
            "R3 tiers 6/9 & 9/17": po >= 6 and pn >= 9, "R4 9 orig only 6/9": po >= 6}
reps = int(sys.argv[1]) if len(sys.argv) > 1 else 200
rng = np.random.default_rng(20261113)
rows = []
for tau in (0.0, 0.001):
    for mu in (-0.001, 0.0, 0.0005, 0.001, 0.002, 0.003):
        acc = {}
        for _ in range(reps):
            for k, v in rules(*run(mu, tau, rng), rng).items(): acc[k] = acc.get(k, 0) + v
        rows.append({"tau_pct": tau * 100, "mu_c_pct": mu * 100, **{k: v / reps for k, v in acc.items()}})
        print(rows[-1], flush=True)
pd.DataFrame(rows).to_csv(sys.argv[2] if len(sys.argv) > 2 else "breadth_sim.csv", index=False)
