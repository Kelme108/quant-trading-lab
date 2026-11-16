# ftshim: the Freqtrade interface the crypto strategies use, without Freqtrade

`b3/freqtrade_adapter.py` puts this folder on `sys.path` (only when the real `freqtrade` package is not
importable) so the strategy files in `user_data/strategies/` import unchanged:

- `freqtrade.strategy`: `IStrategy`, `informative`, `merge_informative_pair`, `stoploss_from_absolute`,
  `stoploss_from_open`, `timeframe_to_minutes`, and inert hyperopt parameter classes;
- `freqtrade.persistence`: `Trade.get_trades_proxy(pair=...)`, served by the adapter's own trade list.

`merge_informative_pair` attaches an informative candle once it has CLOSED (merge_asof on its close time). On
24-hour data this is exactly the Freqtrade rule (date + informative timeframe - base timeframe); on a B3 session,
where the 23:45 candle Freqtrade would join on does not exist, it is the same rule written so it still works.
