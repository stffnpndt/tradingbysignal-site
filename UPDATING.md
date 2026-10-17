# Updating the results on the site

The site shows two kinds of results. Both are built into small JSON files in
`src/data/`; the raw inputs stay private in `backtest-data/` (git-ignored).

## Forward test (live trades since 13 Oct 2026)

Needs only the Trade Tracker.

1. Save the latest tracker as `backtest-data/trade_tracker.xlsx`.
2. `python3 scripts/build_forward.py` (optionally with an "as of" date, `YYYY-MM-DD`).
3. `npm run build`, check, commit `src/data/forward.json`, push to `main`.

Rules: $10,000 per strategy, backtest position sizes and leverage, real entry and
exit prices, 0.1% fee per side, no funding fees, closed trades only. No trade list
or coins are published.

## Backtests

1. Put the portfolio backtest exports into `backtest-data/` as
   `<key>_equity.csv` and `<key>_trades.csv`, with key one of
   `tf-ichimoku`, `mr-atr`, `mr-rsi`, `rsi-red-legs`, `rsi-red-legs-qqq`.
2. `python3 scripts/build_backtests.py` (the combined portfolio is calculated from these).
3. `python3 scripts/build_forward.py --bands`, then `python3 scripts/build_forward.py`,
   so the forward test's range band matches the new backtests.
4. Build, check, commit `src/data/*.json`, push to `main`.
