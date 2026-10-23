# Updating the results on the site

The site shows two kinds of results. Both are built into small JSON files in
`src/data/`; the raw inputs stay private in `backtest-data/` (git-ignored).

## Forward test (live trades since 13 Oct 2026)

Normally automatic: `site_updater.py` on the trading machine reads the closed trades
from the bridge logs, writes them as `backtest-data/trade_tracker.xlsx` into its own
clone, runs `scripts/build_forward.py` and pushes `src/data/forward.json` to `main`.
Trades it can't complete (e.g. opened before the oldest log) block the update until
they are fixed in its `site_fixes.csv`.

When changing `scripts/build_forward.py` by hand: pull first and keep the output format
(`portfolio.trades`, the `Trade Log` sheet with a `Strategy` header row, the column
names), since the updater relies on them. Commit the script; the updater rebuilds
`forward.json` on its next run.

By hand, with only the Trade Tracker:

1. Save the latest tracker as `backtest-data/trade_tracker.xlsx`.
2. `python3 scripts/build_forward.py` (optionally with an "as of" date, `YYYY-MM-DD`).
3. `npm run build`, check, commit `src/data/forward.json`, push to `main`.

A tracker row can hold several legs of a ladder; the number comes from the tracker's
"Legs" column (rows without it are estimated from the position size and `LIVE_LEG_USD`
in `scripts/build_forward.py`).

Rules: every trade closed on or after 13 Oct counts with its real entry (also one opened
shortly before), $10,000 per strategy, backtest position sizes and leverage, real entry and
exit prices, 0.1% fee per side (both booked at the close), no funding fees, closed trades only. The closed
trades are listed per strategy (date, coin, holding time, price move of the trade and
its effect on the strategy's balance, both after fees; legs for the ladder strategies);
no position sizes or open trades are published.

## Backtests

1. Put the portfolio backtest exports into `backtest-data/` as
   `<key>_equity.csv` and `<key>_trades.csv`, with key one of
   `tf-ichimoku`, `mr-atr`, `mr-rsi`, `rsi-red-legs`, `rsi-red-legs-qqq`.
2. `python3 scripts/build_backtests.py` (the combined portfolio is calculated from these).
3. `python3 scripts/build_forward.py --bands`, then `python3 scripts/build_forward.py`,
   so the forward test's range band matches the new backtests.
4. Build, check, commit `src/data/*.json`, push to `main`.
