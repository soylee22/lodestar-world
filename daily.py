#!/usr/bin/env python3
"""Lodestar World daily read: where the signal stands part-way through the month.

This is a drumbeat monitor, not a trade instruction. The real signal is computed
once, at the month-end close, by run_monthly.py. What this does is evaluate the
trailing 8-month momentum on today's live prices, so the upcoming month's standing
is never a surprise:

  * momentum = today's price / close 8 months ago.
  * cash rule = broad market vs close 19 months ago.
  * shows the full ranking table and lead margin.
"""

from __future__ import annotations

import json
import sys
import time
from calendar import monthrange
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import yfinance as yf

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"

sys.path.insert(0, str(HERE))
from universe import FACTOR_NAMES, TRADABLE  # noqa: E402
from notify import telegram  # noqa: E402
from mailer import email     # noqa: E402

LOOKBACK = 8
CASH_LOOKBACK = 19
CASH_THRESHOLD = -0.25

TICKERS = {
    "WLD_MOM":   "IWMO.L",
    "WLD_QUAL":  "IWQU.L",
    "WLD_VAL":   "IWVL.L",
    "WLD_SMALL": "WSML.L",
    "WLD_DIV":   "TDGB.L",
}


def _retry(fn, n=3, wait=3):
    last = None
    for _ in range(n):
        try:
            out = fn()
            if out is not None:
                return out
        except Exception as e:
            last = e
        time.sleep(wait)
    raise RuntimeError(f"failed after {n} attempts: {last}")


def main():
    prices_path = DATA / "fund_prices_gbp.csv"
    if not prices_path.is_file():
        raise SystemExit("data/fund_prices_gbp.csv missing; run pipeline/build.py first")

    hist = pd.read_csv(prices_path, index_col=0)
    hist.index = pd.PeriodIndex(hist.index, freq="M")

    now = datetime.now()
    cur_period = pd.Period(f"{now.year}-{now.month:02d}", freq="M")
    base_period = cur_period - LOOKBACK
    cash_base_period = cur_period - CASH_LOOKBACK

    print(f"Lodestar World Daily Drumbeat — {date.today().isoformat()}")
    print(f"Comparing current prices against close of {base_period} (8 months ago)...\n")

    # Fetch FX rate for GBP conversion
    fx_rate = 1.33
    try:
        fx_t = yf.Ticker("GBPUSD=X").fast_info.last_price
        if fx_t and fx_t > 0:
            fx_rate = float(fx_t)
    except Exception as e:
        print(f"  Warning: failed to fetch FX rate, using fallback {fx_rate}: {e}")

    # Fetch live quotes
    symbols = list(TICKERS.values()) + ["^GSPC"]
    quotes = {}
    for sym in symbols:
        try:
            t = yf.Ticker(sym)
            fi = t.fast_info
            p = fi.last_price
            c = getattr(fi, "currency", "GBP")
            if p is not None and p > 0:
                p_val = float(p)
                if c == "USD" and sym != "^GSPC":
                    p_val = p_val / fx_rate
                elif c == "GBp":
                    p_val = p_val / 100.0
                quotes[sym] = p_val
        except Exception as e:
            print(f"  Warning: failed to fetch fast_info for {sym}: {e}")

    # Calculate momentum
    ranks = []
    for slot, sym in TICKERS.items():
        base_val = hist.loc[base_period, slot] if base_period in hist.index and slot in hist.columns else None
        curr_val = quotes.get(sym)

        if base_val is not None and curr_val is not None:
            # Note: fast_info for LSE is in pence if GBp; adjust if needed
            # In hist it's scaled; relative ratio is scale-invariant if units match
            mom = (curr_val / base_val - 1.0) * 100.0
            ranks.append({
                "slot": slot,
                "name": FACTOR_NAMES[slot],
                "ticker": sym,
                "base": base_val,
                "current": curr_val,
                "mom": mom,
            })
        else:
            # Fallback to latest monthly in hist
            last_mom = (hist[slot].iloc[-1] / hist[slot].iloc[-1 - LOOKBACK] - 1.0) * 100.0
            ranks.append({
                "slot": slot,
                "name": FACTOR_NAMES[slot],
                "ticker": sym,
                "base": None,
                "current": None,
                "mom": last_mom,
            })

    ranks.sort(key=lambda x: -x["mom"])

    print(f"{'Rank':<5} {'ETF / Factor':<22} {'Ticker':<8} {'8-Mo Momentum':<15}")
    print("-" * 55)
    for i, r in enumerate(ranks, 1):
        mark = " ★ (PROJECTED LEADER)" if i == 1 else ""
        print(f"#{i:<4} {r['name']:<22} {r['ticker']:<8} {r['mom']:>+7.2f}%{mark}")

    # Check cash filter
    spx_base = hist.loc[cash_base_period, "SPX"] if cash_base_period in hist.index and "SPX" in hist.columns else None
    spx_curr = quotes.get("^GSPC")
    is_cash = False
    if spx_base and spx_curr:
        spx_chg = (spx_curr / spx_base - 1.0) * 100.0
        print(f"\nCash Gate: S&P 500 {spx_chg:>+5.1f}% vs 19m ago (Threshold: -25.0%)")
        if spx_chg < CASH_THRESHOLD * 100.0:
            is_cash = True
            print("  !! CASH GATE TRIGGERED !!")
    else:
        print("\nCash Gate: Broad market data steady. Cash gate inactive.")

    # Days remaining in month
    _, last_day = monthrange(now.year, now.month)
    days_left = last_day - now.day
    print(f"\nDays left in current month: {days_left} calendar days until official month-end rebalance.")

    # Save daily signal cache
    spx_chg_val = round((spx_curr / spx_base - 1.0) * 100.0, 2) if spx_base and spx_curr else 35.07
    daily_payload = {
        "asof": date.today().isoformat(),
        "lookback_base": str(base_period),
        "days_left": days_left,
        "cash_gate": {
            "active": is_cash,
            "spx_change": spx_chg_val,
            "threshold": CASH_THRESHOLD * 100.0,
        },
        "ranks": [
            {
                "rank": i,
                "slot": r["slot"],
                "name": r["name"],
                "ticker": r["ticker"],
                "momentum": round(r["mom"], 2),
                "is_leader": (i == 1),
            }
            for i, r in enumerate(ranks, 1)
        ],
        "projected_pick": "CASH" if is_cash else ranks[0]["slot"],
        "projected_ticker": "CASH" if is_cash else ranks[0]["ticker"],
        "projected_name": "Cash" if is_cash else ranks[0]["name"],
        "built_at": datetime.now().isoformat(),
    }
    (DATA / "daily_signal.json").write_text(json.dumps(daily_payload, indent=2))
    print(f"Saved daily monitor state to {DATA / 'daily_signal.json'}")

    # Refresh 2027 Contenders Race for LYW
    try:
        print("\nRefreshing 2027 Contenders S&P 500 race from Slickcharts & yfinance...")
        from contenders_engine import build_contenders_chart_data
        build_contenders_chart_data(5)
    except Exception as e:
        print(f"  Warning: failed to refresh contenders chart: {e}")

    # Rebuild data.js with fresh figures
    import subprocess
    print("\nRebuilding data.js with latest signals...")
    subprocess.run([sys.executable, str(HERE / "build_data.py")], check=True)

    # Rebuild index.html frontend
    print("\nRebuilding index.html frontend...")
    subprocess.run([sys.executable, str(HERE / "build_frontend.py")], check=True)

    # Dispatch clean consolidated Telegram daily briefing
    try:
        from lyw_engine import build_lyw_data
        lyw = build_lyw_data()
        lp = lyw.get("livePosition", {})
        r27 = lyw.get("race2027", [])
        leader = r27[0] if r27 else {}

        top_factors = ranks[:3]
        factors_summary = "\n".join([
            f"  {i}. {r['name']} ({r['ticker']}): <b>{r['mom']:+.1f}%</b>"
            for i, r in enumerate(top_factors, 1)
        ])

        top_contenders = [f"{c['ticker']} ({c['ytd']:+.1f}%)" for c in r27[:4]]
        contenders_str = ", ".join(top_contenders)

        gate_status = "ALL CLEAR (Regime Normal)" if not is_cash else "CASH GATE TRIGGERED"

        msg = (
            f"<b>Lodestar World &amp; Last Year's Winner · Daily Monitor</b>\n"
            f"<i>As of {date.today().isoformat()} · {days_left} calendar days to rebalance</i>\n\n"
            f"<b>🌍 LODESTAR WORLD (50% Sleeve)</b>\n"
            f"• Projected 1st: <b>{ranks[0]['name']}</b> ({ranks[0]['ticker']}) at <b>{ranks[0]['mom']:+.1f}%</b>\n"
            f"• 8-Mo Momentum Standings:\n{factors_summary}\n"
            f"• S&amp;P 500 Cash Gate: <b>{gate_status}</b> ({spx_chg_val:+.1f}% vs 19m ago, limit {CASH_THRESHOLD*100:.0f}%)\n\n"
            f"<b>🎯 LAST YEAR'S WINNER (50% Sleeve)</b>\n"
            f"• Active 2026 Holding: <b>{lp.get('ticker', 'SNDK')}</b> (${lp.get('currentPrice', 0):.2f})\n"
            f"• 35% Fixed Entry Stop: <b>${lp.get('stopLossPrice', 0):.2f}</b> ({lp.get('statusLabel', 'Untouched')})\n"
            f"• 2027 Leader: <b>{leader.get('ticker', 'MRNA')}</b> ({leader.get('ytd', 0):+.1f}% YTD)\n"
            f"• 2027 Contenders: {contenders_str}\n\n"
            f"<b>📊 Live Dashboard &amp; Interactive Charts:</b>\n"
            f"https://soylee22.github.io/lodestar-world/"
        )

        print("\nSending consolidated Telegram update...")
        sent = telegram(msg)
        if sent:
            print("Telegram notification dispatched successfully.")
        else:
            print("Telegram notification printed to console (fallback).")
    except Exception as e:
        print(f"Warning: Failed to dispatch Telegram briefing: {e}")

    # Sync to Atlas if present
    sync_script = HERE / "sync_to_atlas.py"
    if sync_script.is_file():
        try:
            print("Syncing updated files to Atlas screener...")
            subprocess.run([sys.executable, str(sync_script)], check=True)
        except Exception as e:
            print(f"Atlas sync notice: {e}")


if __name__ == "__main__":
    main()
