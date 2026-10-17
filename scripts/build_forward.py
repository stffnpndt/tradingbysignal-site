#!/usr/bin/env python3
"""
Forward test: replay the live trades since the restructuring with the same
rules as the backtests, and compare the result with what the backtest
typically did over a period of the same length.

Input  (not committed, see .gitignore):
    backtest-data/trade_tracker.xlsx   the Trade Tracker ("Trade Log" sheet)
    src/data/forward-bands.json        the backtest's range band, pre-calculated for up to
                                       three years (committed; rebuilt with --bands whenever
                                       the backtests change, which needs backtest-data/)
Output:
    src/data/forward.json              per strategy and for the combined portfolio:
                                       a daily curve, the backtest range band and a
                                       few figures. No trade list, no coins.

Rules, as in the backtests:
  * $10,000 per strategy, profits reinvested.
  * Position size = balance when the position opens / max positions; each leg is
    that x leverage / legs per position. Legs of one ladder share one size.
  * A tracker row can hold several legs of a ladder. The number of legs is the
    row's position size divided by the live size of one leg (LIVE_LEG_USD below,
    from the bridge settings); update that table when the live sizes change.
  * Real entry and exit prices from the tracker, 0.1% fee on every buy and sell.
  * Funding fees are left out, as in the backtests. Only closed trades count.
  * Combined portfolio: $10,000 in each strategy, back to equal shares monthly.

Run:  python3 scripts/build_forward.py [YYYY-MM-DD]   (optional "as of" date, default today)
      python3 scripts/build_forward.py --bands        (after new backtests: refresh the bands)
"""
import datetime as dt
import json
import os
import sys
from collections import defaultdict

import numpy as np
import openpyxl
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_backtests as bb  # noqa: E402

ROOT = bb.ROOT
TRACKER = os.path.join(bb.SRC, "trade_tracker.xlsx")
OUT = os.path.join(ROOT, "src", "data", "forward.json")
BANDS = os.path.join(ROOT, "src", "data", "forward-bands.json")
BAND_DAYS = 3 * 366

START = pd.Timestamp("2026-10-13")
CAPITAL = 10_000.0
FEE = 0.001
MIN_DAYS = 30  # draw the backtest band at least this far, so the funnel is visible early

# Same limits as in the backtests: (max positions, legs per position, leverage).
SETTINGS = {
    "tf-ichimoku": (2, 1, 2),
    "mr-atr": (8, 1, 2),
    "mr-rsi": (4, 3, 2),
    "rsi-red-legs": (8, 5, 2),
    "rsi-red-legs-qqq": (1, 5, 3),
}


# Live notional of one leg per strategy (bridge .env, Oct 2026), used only to
# count how many legs a tracker row contains.
LIVE_LEG_USD = {
    "tf-ichimoku": 19_880,
    "mr-atr": 1_985,
    "mr-rsi": 5_960 / 3,
    "rsi-red-legs": 5_960 / 5,
    "rsi-red-legs-qqq": 47_700 / 5,
}


def strategy_key(name: str, asset: str):
    n = (name or "").lower()
    if "qqq" in n or (asset or "").upper() == "QQQ":
        return "rsi-red-legs-qqq"
    if "ichimoku" in n:
        return "tf-ichimoku"
    if "atr" in n:
        return "mr-atr"
    if "red" in n:
        return "rsi-red-legs"
    if "rsi" in n:
        return "mr-rsi"
    return None  # e.g. CS Momentum, which is paused


def load_legs():
    ws = openpyxl.load_workbook(TRACKER, data_only=True)["Trade Log"]
    rows = list(ws.iter_rows(values_only=True))
    head = next(i for i, r in enumerate(rows) if r and r[0] == "Strategy")
    col = {name: i for i, name in enumerate(rows[head]) if name}
    legs = defaultdict(list)
    for r in rows[head + 1:]:
        if not r or not r[col["Strategy"]]:
            continue
        key = strategy_key(r[col["Strategy"]], r[col["Asset"]])
        opened, closed = r[col["Open Date"]], r[col["Close Date"]]
        entry, exit_ = r[col["Entry Price"]], r[col["Exit Price"]]
        if key is None or not isinstance(opened, dt.datetime) or not isinstance(closed, dt.datetime):
            continue
        if opened < START or not entry or not exit_:
            continue
        size = r[col["Position Size ($)"]]
        n = int(round(float(size) / LIVE_LEG_USD[key])) if isinstance(size, (int, float)) and size else 1
        n = max(1, min(n, SETTINGS[key][1]))
        legs[key].append({
            "n": n,
            "asset": r[col["Asset"]],
            "side": -1 if str(r[col["Position"]]).lower().startswith("short") else 1,
            "open": pd.Timestamp(opened),
            "close": pd.Timestamp(closed),
            "entry": float(entry),
            "exit": float(exit_),
        })
    return legs


def positions_from(legs):
    """Legs of the same coin that close on the same day form one position (a ladder)."""
    groups = defaultdict(list)
    for leg in legs:
        groups[(leg["asset"], leg["close"].normalize())].append(leg)
    out = []
    for g in groups.values():
        g.sort(key=lambda l: l["open"])
        out.append({"open": g[0]["open"], "close": max(l["close"] for l in g), "legs": g})
    return sorted(out, key=lambda p: p["open"])


def simulate(key, legs, days):
    max_pos, n_legs, lev = SETTINGS[key]
    positions = positions_from(legs)
    events = [(p["open"], 1, i) for i, p in enumerate(positions)] + \
             [(p["close"], 0, i) for i, p in enumerate(positions)]
    equity, size, results = CAPITAL, {}, []
    closed_by_day = defaultdict(float)
    for when, kind, i in sorted(events, key=lambda e: (e[0], e[1])):
        p = positions[i]
        if kind == 1:  # open: fix the leg size from the balance at this moment
            size[i] = equity / max_pos * lev / n_legs
            p["fees_in"] = FEE * size[i] * sum(leg["n"] for leg in p["legs"])
            equity -= p["fees_in"]
        else:
            pnl = 0.0
            for leg in p["legs"]:
                qty = size[i] * leg["n"] / leg["entry"]
                pnl += leg["side"] * qty * (leg["exit"] - leg["entry"]) - FEE * qty * leg["exit"]
            equity += pnl
            results.append(pnl - p["fees_in"])
        # record balance after each event; curve below takes the last one per day
        closed_by_day[when.normalize()] = equity
    curve, last = [], CAPITAL
    for d in days:
        if d in closed_by_day:
            last = closed_by_day[d]
        curve.append(last)
    return pd.Series(curve, index=days), results


def band(equity: pd.Series, horizon: int):
    """Percentiles of the backtest's return over every window of h days, h = 0..horizon."""
    eq = equity.asfreq("D").ffill()
    vals = eq.values
    out = []
    for h in range(horizon + 1):
        if h == 0:
            out.append((1.0, 1.0, 1.0))
            continue
        r = vals[h:] / vals[:-h]
        out.append(tuple(float(x) for x in np.percentile(r, [10, 50, 90])))
    return out


def build_bands():
    """Backtest range for every horizon up to BAND_DAYS, per strategy and the portfolio."""
    out = {}
    for key in list(SETTINGS) + ["portfolio"]:
        out[key] = [[round(a, 5), round(m, 5), round(b, 5)] for a, m, b in band(bb.load_equity(key).equity, BAND_DAYS)]
    with open(BANDS, "w") as f:
        json.dump(out, f, separators=(",", ":"))
    print(f"wrote {BANDS}")


def load_bands(horizon):
    with open(BANDS) as f:
        bands = json.load(f)
    if horizon >= len(bands["portfolio"]):
        raise SystemExit("Forward test is longer than the stored bands; run with --bands to extend them.")
    return {k: [tuple(x) for x in v[: horizon + 1]] for k, v in bands.items()}


def verdict(value, lo, hi, n_trades):
    if n_trades == 0:
        return "none"
    if value < lo:
        return "below"
    if value > hi:
        return "above"
    return "within"


def main():
    if "--bands" in sys.argv:
        build_bands()
        return
    as_of = pd.Timestamp(sys.argv[1]) if len(sys.argv) > 1 else pd.Timestamp(dt.date.today())
    legs = load_legs()
    days = pd.date_range(START, as_of, freq="D")
    horizon = max(len(days) - 1, MIN_DAYS)
    band_days = pd.date_range(START, START + pd.Timedelta(days=horizon), freq="D")
    bands = load_bands(horizon)

    data, sleeves = {}, {}
    for key in SETTINGS:
        curve, results = simulate(key, legs.get(key, []), days)
        sleeves[key] = curve
        data[key] = pack(curve, results, bands[key], band_days, as_of)

    # Combined portfolio: equal shares, rebalanced on the first day of every month.
    rets = pd.DataFrame({k: s / s.shift(1).fillna(CAPITAL) - 1 for k, s in sleeves.items()})
    alloc, period, total = {k: CAPITAL for k in SETTINGS}, None, []
    for d in days:
        p = d.to_period("M")
        if period is not None and p != period:
            t = sum(alloc.values())
            alloc = {k: t / len(alloc) for k in alloc}
        period = p
        for k in alloc:
            alloc[k] *= 1 + rets.at[d, k]
        total.append(sum(alloc.values()) / len(alloc))  # per $10,000, like the sleeves
    combined = pd.Series(total, index=days)
    all_results = [r for k in SETTINGS for r in data[k].pop("_results")]
    data["portfolio"] = pack(combined, all_results, bands["portfolio"],
                             band_days, as_of, start_capital=CAPITAL * len(SETTINGS))
    for k in SETTINGS:
        data[k].pop("_results", None)
    data["portfolio"].pop("_results", None)

    with open(OUT, "w") as f:
        json.dump(data, f, separators=(",", ":"))
    for k, v in data.items():
        print(f"{k:18} trades {v['trades']:3}  wins {v['wins']:3}  return {v['ret']:+.2%}  "
              f"band {v['band'][len(days) - 1][1] - 1:+.1%}..{v['band'][len(days) - 1][3] - 1:+.1%}  {v['verdict']}")
    print(f"wrote {OUT}")


def pack(curve, results, bnd, band_days, as_of, start_capital=CAPITAL):
    mult = curve / CAPITAL
    h = len(curve) - 1
    lo, _, hi = bnd[h]
    n = len(results)
    return {
        "start": START.strftime("%Y-%m-%d"),
        "asOf": as_of.strftime("%Y-%m-%d"),
        "startCapital": start_capital,
        "curve": [[d.strftime("%Y-%m-%d"), round(float(v), 5)] for d, v in mult.items()],
        "band": [[d.strftime("%Y-%m-%d"), round(a, 5), round(m, 5), round(b, 5)]
                 for d, (a, m, b) in zip(band_days, bnd)],
        "ret": round(float(mult.iloc[-1] - 1), 5),
        "trades": n,
        "wins": sum(1 for r in results if r > 0),
        "verdict": verdict(float(mult.iloc[-1]), lo, hi, n),
        "_results": results,
    }


if __name__ == "__main__":
    main()
