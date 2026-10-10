#!/usr/bin/env python3
"""
Turn the portfolio backtest exports into the small data file the website uses.

Input  (not committed, see .gitignore):
    backtest-data/<key>_equity.csv   daily equity curve from the portfolio backtest
    backtest-data/<key>_trades.csv   one row per trade
Output:
    src/data/backtests.json          summary statistics, yearly returns and a
                                     weekly equity / drawdown curve per key

Only aggregates are published: no trade list, no coins, no entry or exit dates.

Run:  python3 scripts/build_backtests.py
"""
import json
import os

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "backtest-data")
OUT = os.path.join(ROOT, "src", "data", "backtests.json")
KEYS = ["tf-ichimoku", "mr-atr", "mr-rsi", "rsi-red-legs", "rsi-red-legs-qqq"]


def build(key: str) -> dict:
    eq = pd.read_csv(os.path.join(SRC, f"{key}_equity.csv"), parse_dates=["date"]).set_index("date")
    tr = pd.read_csv(os.path.join(SRC, f"{key}_trades.csv"), parse_dates=["start", "exit"])

    start_cap = 10_000.0
    years = (eq.index[-1] - eq.index[0]).days / 365.25
    final = float(eq.equity.iloc[-1])
    cagr = (final / start_cap) ** (1 / years) - 1

    wins = tr[tr.pnl > 0]
    losses = tr[tr.pnl <= 0]
    pf = wins.pnl.sum() / max(-losses.pnl.sum(), 1e-9)
    hold = (tr.exit - tr.start).dt.days

    yearly = eq.equity.resample("YE").last()
    prev = [start_cap] + list(yearly.values[:-1])
    years_out = []
    for (y, end), p in zip(yearly.items(), prev):
        part = eq[eq.index.year == y.year]
        years_out.append({
            "year": int(y.year),
            "ret": round(end / p - 1, 4),
            "dd": round(float(part.dd_intra_trade.min()), 4),
            "partial": bool(part.index[0].dayofyear > 7 or (part.index[-1].month, part.index[-1].day) < (12, 25)),
        })

    # Weekly curve: last equity of the week, worst drawdowns within the week,
    # so short spikes are not smoothed away.
    wk = eq.resample("W-SUN").agg({"equity": "last", "dd": "min", "dd_intra_trade": "min"}).dropna()
    curve = [[d.strftime("%Y-%m-%d"), round(float(r.equity) / start_cap, 4), round(float(r.dd), 4),
              round(float(r.dd_intra_trade), 4)] for d, r in wk.iterrows()]

    return {
        "start": eq.index[0].strftime("%Y-%m-%d"),
        "end": eq.index[-1].strftime("%Y-%m-%d"),
        "multiple": round(final / start_cap, 2),
        "cagr": round(cagr, 4),
        "maxDdClosed": round(float(eq.dd.min()), 4),
        "maxDdIntra": round(float(eq.dd_intra_trade.min()), 4),
        "trades": int(len(tr)),
        "winRate": round(len(wins) / len(tr), 4),
        "profitFactor": round(float(pf), 2),
        "medianHoldDays": float(hold.median()),
        "timeInMarket": round(float((eq.open_trades > 0).mean()), 4),
        "liquidations": int((tr.exit_signal == "Liquidated").sum()),
        "years": years_out,
        "curve": curve,  # [week, equity multiple, drawdown closed, drawdown intra-trade]
    }


def main():
    data = {k: build(k) for k in KEYS}
    with open(OUT, "w") as f:
        json.dump(data, f, separators=(",", ":"))
    for k, v in data.items():
        print(f"{k:18} {v['start']}..{v['end']}  x{v['multiple']:<8} CAGR {v['cagr']:.1%}  "
              f"DD {v['maxDdClosed']:.1%}/{v['maxDdIntra']:.1%}  trades {v['trades']}  win {v['winRate']:.0%}  "
              f"PF {v['profitFactor']}  hold {v['medianHoldDays']}d  inMkt {v['timeInMarket']:.0%}  liq {v['liquidations']}")
        print("   " + "  ".join(f"{y['year']}:{y['ret']:+.0%}" for y in v["years"]))
    print(f"wrote {OUT} ({os.path.getsize(OUT) // 1024} KB)")


if __name__ == "__main__":
    main()
