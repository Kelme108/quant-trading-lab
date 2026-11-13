"""Snapshot Binance spot order books for the lab's pairs: half-spread and the cost of a market order of a given size.
Public endpoint, no account. Usage: python research/tools/book_cost.py out.json samples interval_s"""
import json, sys, time, urllib.request
PAIRS = "BTC ETH BNB XRP ADA LTC LINK DOGE SOL AVAX DOT TRX NEAR UNI BCH XLM FIL AAVE INJ HBAR OP APT ARB SUI ATOM ETC".split()
SIZES = [250, 1000, 5000]
def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "lab-cost-probe"}), timeout=20) as r:
        return json.load(r)
def walk(levels, notional):
    left, cost_qty, spent = notional, 0.0, 0.0
    for p, q in levels:
        p, q = float(p), float(q)
        take = min(q, left / p)
        spent += take * p; cost_qty += take; left -= take * p
        if left <= 1e-9: return spent / cost_qty
    return None
out = []
n, dt = int(sys.argv[2]), float(sys.argv[3])
for i in range(n):
    t = time.time()
    for b in PAIRS:
        d = get(f"https://api.binance.com/api/v3/depth?symbol={b}USDT&limit=100")
        bid, ask = float(d["bids"][0][0]), float(d["asks"][0][0]); mid = (bid + ask) / 2
        row = {"t": t, "pair": b, "half_spread_bp": (ask - bid) / 2 / mid * 1e4}
        for s in SIZES:
            a = walk(d["asks"], s); bb = walk(d["bids"], s)
            row[f"buy_{s}_bp"] = None if a is None else (a / mid - 1) * 1e4
            row[f"sell_{s}_bp"] = None if bb is None else (1 - bb / mid) * 1e4
        out.append(row)
    if i < n - 1: time.sleep(max(0, dt - (time.time() - t)))
json.dump(out, open(sys.argv[1], "w"))
print(len(out), "rows")
