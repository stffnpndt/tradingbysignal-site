#!/usr/bin/env python3
"""
Turn the portfolio backtest exports into the small data file the website uses.

Input  (not committed, see .gitignore):
    backtest-data/<key>_equity.csv   daily equity curve from the portfolio backtest
    backtest-data/<key>_trades.csv   one row per trade (not for the combined portfolio)
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
KEYS = ["tf-ichimoku", "mr-atr", "mr-rsi", "rsi-red-legs", "rsi-red-legs-qqq", "portfolio"]
START = {"portfolio": 50_000.0}  # combined backtest: $10,000 per sleeve


def build(key: str) -> dict:
    eq = pd.read_csv(os.path.join(SRC, f"{key}_equity.csv"), parse_dates=["date"]).set_index("date")
    tpath = os.path.join(SRC, f"{key}_trades.csv")
    tr = pd.read_csv(tpath, parse_dates=["start", "exit"]) if os.path.exists(tpath) else None

    start_cap = START.get(key, 10_000.0)
    years = (eq.index[-1] - eq.index[0]).days / 365.25
    final = float(eq.equity.iloc[-1])
    cagr = (final / start_cap) ** (1 / years) - 1

    # Longest time below a previous high (closed trades), in days.
    peak = eq.equity.cummax()
    under, longest, since = eq.equity < peak * (1 - 1e-9), 0, None
    for d, u in under.items():
        if u and since is None:
            since = d
        elif not u and since is not None:
            longest, since = max(longest, (d - since).days), None
    if since is not None:
        longest = max(longest, (eq.index[-1] - since).days)

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

    out = {
        "start": eq.index[0].strftime("%Y-%m-%d"),
        "end": eq.index[-1].strftime("%Y-%m-%d"),
        "multiple": round(final / start_cap, 2),
        "cagr": round(cagr, 4),
        "maxDdClosed": round(float(eq.dd.min()), 4),
        "maxDdIntra": round(float(eq.dd_intra_trade.min()), 4),
        "startCapital": start_cap,
        "longestUnderwaterDays": int(longest),
        "losingYears": sum(1 for y in years_out if y["ret"] < 0),
        "years": years_out,
        "curve": curve,  # [week, equity multiple, drawdown closed, drawdown intra-trade]
    }
    if tr is not None:
        wins = tr[tr.pnl > 0]
        losses = tr[tr.pnl <= 0]
        out.update({
            "trades": int(len(tr)),
            "winRate": round(len(wins) / len(tr), 4),
            "profitFactor": round(float(wins.pnl.sum() / max(-losses.pnl.sum(), 1e-9)), 2),
            "medianHoldDays": float((tr.exit - tr.start).dt.days.median()),
            "timeInMarket": round(float((eq.open_trades > 0).mean()), 4),
            "liquidations": int((tr.exit_signal == "Liquidated").sum()),
        })
    return out


def main():
    data = {k: build(k) for k in KEYS}
    with open(OUT, "w") as f:
        json.dump(data, f, separators=(",", ":"))
    for k, v in data.items():
        print(f"{k:18} {v['start']}..{v['end']}  x{v['multiple']:<8} CAGR {v['cagr']:.1%}  "
              f"DD {v['maxDdClosed']:.1%}/{v['maxDdIntra']:.1%}  underwater {v['longestUnderwaterDays']}d  "
              f"losing years {v['losingYears']}  trades {v.get('trades', '-')}  win {v.get('winRate', 0):.0%}  "
              f"liq {v.get('liquidations', '-')}")
        print("   " + "  ".join(f"{y['year']}:{y['ret']:+.0%}" for y in v["years"]))
    print(f"wrote {OUT} ({os.path.getsize(OUT) // 1024} KB)")


if __name__ == "__main__":
    main()
