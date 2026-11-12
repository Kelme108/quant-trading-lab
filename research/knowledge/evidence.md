## Outside evidence on intraday crypto (curated 2026-11-12; read before proposing)

What published research supports, in our own words, with the source. It is a map of where an intraday edge has been
DOCUMENTED and where it has not; never a promise of returns, and never a reason to skip the lab's gates. Advertised bot
results are not evidence and are not listed. Treat every entry as a mechanism to test, not as a result.

1. Intraday time-series momentum (documented, peer reviewed). Shen, Urquhart and Wang, "Bitcoin intraday time-series
   momentum", Financial Review 57(2), 2022 (https://centaur.reading.ac.uk/100181): the return of the first half-hour of a
   trading session predicts the return of the last half-hour, in and out of sample; the effect is strongest in the sessions
   with the highest volume or volatility, and the authors attribute it to liquidity provision. It extends Gao, Han, Li and
   Zhou's result for the S&P 500 ETF. Lab translation: define a session (crypto trades 24/7: e.g. the UTC day, or the US
   cash session 13:30-20:00 UTC), measure the first part of it, and trade the end of the SAME session only when the first
   part was large and volume or volatility was high. Positions close at the session end: a natural day trade.
2. Most intraday technical rules do not survive costs (documented). Svogun and Bazán-Palomino (2022,
   https://ideas.repec.org/a/eee/intfin/v79y2022ics1042443122000816.html) tested 69 moving-average and breakout rules on
   daily and 1-minute crypto data: costs cut the profitable rules, most for Bitcoin and Ethereum. An Erasmus thesis found
   profitable daily rules after data-snooping corrections but no excess return from the intraday ones. A 2026 preprint
   (https://arxiv.org/abs/2602.10785, not peer reviewed) put the break-even of an intraday EMA crossover on Bitcoin near
   0.4% per transaction. The lab's own scoreboard shows the same: every rule trading 100+ times a year per pair had a gross
   move per trade near zero. A frequent rule built from common indicator crossings is the default failure.
3. Predictability is weak and time-varying (documented). A 2025 study of 16 large cryptocurrencies at intraday frequencies
   (Central European Economic Journal, https://reference-global.com/2/v2/download/article/10.2478/ceej-2025-0003.pdf)
   found most of them highly unpredictable, with predictability that comes and goes. State why the rule's condition picks
   the periods when the effect is present (a regime or activity condition), and how it behaves when it is absent.
4. Hour-of-day patterns are in VOLATILITY and VOLUME, not in returns (documented). Hansen, Kim and Kimbrough
   (https://arxiv.org/abs/2109.12142, preprint): on centralised exchanges volatility is highest in the first hour of the UTC
   day and in the hour after 16:00 UTC; volume follows the regions where users trade. Baur, Cahill, Godfrey and Liu
   (Finance Research Letters 31, 2019) document time-of-day and day-of-week effects in Bitcoin returns and volume. Use the
   hour as an ACTIVITY filter (when moves are large enough to beat the 0.30% round trip), not as a return signal by itself.
5. Jumps are frequent, cluster, and are mostly negative; their direction afterwards is not settled (documented). A 2024
   study of six cryptocurrencies on seven exchanges (https://link.springer.com/article/10.1007/s42521-024-00116-1) finds
   jumps on up to 58% of trading days, negative jumps dominating in number and size, and intraday jumps that influence the
   end-of-day return. Whether the price continues or reverses after a jump is open: a continuation rule and a reversal rule
   are two different hypotheses, each with its own mechanism; never assume one.
6. Funding-rate extremes (practitioner work only, mixed). Blog-level tests disagree, and the lab has no derivatives data
   (spot only). Do not propose rules that need funding, open interest or liquidation data.

What this means under the lab's limits (spot, long only, 15m/1h, 0.30% base round trip):
- The trigger must pick bars where the expected ABSOLUTE move is large (above about 1%): a high-volume or high-volatility
  session, the first hours after a jump, the end of a session that started with a large move. Loose triggers that fire on
  ordinary bars are noise after cost (item 2 and the scoreboard).
- Many trades should come from MANY PAIRS and rare-but-real triggers, not from loosening the trigger on one pair.
- Long-only intraday momentum lost money in 2022-2024 in the lab: state what the rule does in a falling market (stand
  aside under a regime condition, or a mechanism that also works in chop).
