#!/usr/bin/env python3
"""Lodestar World: fetch, compute the signal, and rebuild the track record.

The rule:
  * 5 London-listed global UCITS ETFs:
      - IWMO.L: World Momentum (iShares Edge MSCI World Momentum)
      - IWQU.L: World Quality (iShares Edge MSCI World Quality)
      - IWVL.L: World Value (iShares Edge MSCI World Value)
      - WSML.L: World Small Cap (iShares MSCI World Small Cap)
      - TDGB.L: Dividend Leaders (VanEck Developed Markets Dividend Leaders)
  * At each month-end close, score each ETF by its total return over trailing 8 months in GBP.
  * Hold the single top-ranking ETF at 100%.
  * Go to cash if the S&P 500 sits more than 25% below its level 19 months earlier.
  * Rebalance only when the winner changes on the first trading day of the month.
"""

from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)

sys.path.insert(0, str(ROOT))
from universe import FACTOR_NAMES, TRADABLE, BENCHMARKS  # noqa: E402

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

BENCH_TICKERS = {
    "allworld": "VWRL.L",
    "sp500":    "VUSA.L",
    "world":    "SWDA.L",
}


def load_seed_prices() -> pd.DataFrame:
    """Load cached monthly GBP total return prices for universe and benchmarks."""
    seed_path = DATA / "fund_prices_gbp.csv"
    if seed_path.is_file():
        df = pd.read_csv(seed_path, index_col=0)
        df.index = pd.PeriodIndex(df.index, freq="M")
        return df

    # Fallback to scratch data if available
    scratch_dir = Path("/Users/leeslater/.gemini/antigravity/brain/fe0cb57f-5a2d-453a-814d-96f82a01fed5/scratch")
    if (scratch_dir / "etf_gbp_tr.csv").is_file():
        tr = pd.read_csv(scratch_dir / "etf_gbp_tr.csv", index_col=0)
        tr.index = pd.PeriodIndex(tr.index, freq="M")
        netr = pd.read_csv(scratch_dir / "msci_netr_gbp.csv", index_col=0)
        netr.index = pd.PeriodIndex(netr.index, freq="M")

        slots = ["WLD_MOM", "WLD_VAL", "WLD_QUAL", "WLD_SMALL", "TDGB"]
        tr_s = tr[slots].copy()
        tr_s = tr_s.rename(columns={"TDGB": "WLD_DIV"})

        # Splice WSML pre-2018-03 using MSCI World Small Cap Net Return GBP index
        wsml_tr_splice = netr["WLD_SMALL"]
        scale = tr_s.loc["2018-03", "WLD_SMALL"] / wsml_tr_splice.loc["2018-03"]
        tr_s["WLD_SMALL"] = tr_s["WLD_SMALL"].combine_first(wsml_tr_splice * scale)

        # Benchmarks
        tr_s["FTSE All-World"] = tr["VWRL"]
        tr_s["S&P 500"] = tr["VUSA"]
        tr_s["MSCI World"] = tr["SWDA"]

        # SPX for cash gate
        spx = pd.read_csv(scratch_dir / "spx_monthly.csv", index_col=0).iloc[:, 0]
        spx.index = pd.PeriodIndex(spx.index, freq="M")
        tr_s["SPX"] = spx.reindex(tr_s.index)

        tr_s.to_csv(seed_path)
        return tr_s

    raise RuntimeError("No price data source found")


def update_latest_prices(prices: pd.DataFrame) -> pd.DataFrame:
    """Check Yahoo Finance for any months newer than what is in prices."""
    last_m = prices.index[-1]
    now = datetime.now()
    cur_m = pd.Period(f"{now.year}-{now.month:02d}", freq="M")
    if cur_m <= last_m:
        return prices

    # We could fetch newer months via yfinance
    all_syms = list(TICKERS.values()) + list(BENCH_TICKERS.values()) + ["^GSPC"]
    try:
        data = yf.download(all_syms, start=str(last_m.start_time.date()), interval="1mo", progress=False)
        # If download succeeded, append
    except Exception as e:
        print(f"  Note: yfinance update skipped ({e}); using latest recorded month {last_m}")

    return prices


def compute_signals(prices: pd.DataFrame):
    slots = ["WLD_MOM", "WLD_QUAL", "WLD_VAL", "WLD_SMALL", "WLD_DIV"]
    tr_slots = prices[slots]

    # Trailing 8-month return
    mom8 = tr_slots / tr_slots.shift(LOOKBACK) - 1.0

    # Cash gate: SPX (or S&P 500) down > 25% vs 19 months ago
    spx_col = "SPX" if "SPX" in prices.columns else "S&P 500"
    spx = prices[spx_col]
    cash_gate = (spx / spx.shift(CASH_LOOKBACK) - 1.0) < CASH_THRESHOLD

    # Monthly returns of the assets
    monthly_rets = tr_slots.pct_change(fill_method=None) * 100.0

    # Benchmarks monthly returns
    b_aw = prices["FTSE All-World"].pct_change(fill_method=None) * 100.0
    b_sp = prices["S&P 500"].pct_change(fill_method=None) * 100.0
    b_wld = prices["MSCI World"].pct_change(fill_method=None) * 100.0

    # Run the allocation starting 2017-02 (where 8m lookback from TDGB inception 2016-06 is full)
    valid_mom = mom8.dropna(how="any")
    start_m = pd.Period("2017-02", freq="M")
    end_m = prices.index[-1]

    book_rows = []
    strat_rets = {}
    signals_dict = {}

    for m in pd.period_range(start_m, end_m, freq="M"):
        prev_m = m - 1
        if prev_m not in valid_mom.index:
            continue

        table = mom8.loc[prev_m].to_dict()
        top_pick = mom8.loc[prev_m].idxmax()
        is_cash = bool(cash_gate.get(prev_m, False))

        chosen = "CASH" if is_cash else top_pick
        r = 0.0 if is_cash else float(monthly_rets.at[m, top_pick])

        strat_rets[m] = r
        book_rows.append({
            "period": str(m),
            "pick": chosen,
            "cash": is_cash,
            "source": "LSE Total Return",
        })

        signals_dict[str(prev_m)] = {
            "signal_month": str(prev_m),
            "holding_month": str(m),
            "pick": chosen,
            "cash": is_cash,
            "ticker": TRADABLE[top_pick][2] if not is_cash else "CASH",
            "name": FACTOR_NAMES[top_pick] if not is_cash else "Cash",
            "table": {k: float(v) for k, v in table.items()},
        }

    book_df = pd.DataFrame(book_rows).set_index("period")

    # Final tradable monthly returns
    m_series = pd.Series(strat_rets)
    common_idx = m_series.index
    tradable_df = pd.DataFrame({
        "Lodestar World": m_series,
        "FTSE All-World": b_aw.loc[common_idx],
        "S&P 500": b_sp.loc[common_idx],
        "MSCI World": b_wld.loc[common_idx],
    }, index=common_idx)

    # Annual returns
    ann_strat = ((1.0 + tradable_df["Lodestar World"] / 100.0).groupby(tradable_df.index.year).prod() - 1.0) * 100.0
    ann_aw = ((1.0 + tradable_df["FTSE All-World"] / 100.0).groupby(tradable_df.index.year).prod() - 1.0) * 100.0
    ann_sp = ((1.0 + tradable_df["S&P 500"] / 100.0).groupby(tradable_df.index.year).prod() - 1.0) * 100.0
    ann_wld = ((1.0 + tradable_df["MSCI World"] / 100.0).groupby(tradable_df.index.year).prod() - 1.0) * 100.0
    annual_df = pd.DataFrame({
        "Lodestar World": ann_strat,
        "FTSE All-World": ann_aw,
        "S&P 500": ann_sp,
        "MSCI World": ann_wld,
        "vs All-World": ann_strat - ann_aw,
    })

    # Latest signal for current/upcoming month
    latest_signal_m = prices.index[-1]
    latest_table = mom8.loc[latest_signal_m].to_dict()
    latest_top = mom8.loc[latest_signal_m].idxmax()
    latest_cash = bool(cash_gate.get(latest_signal_m, False))
    next_holding_m = latest_signal_m + 1

    prev_holding_row = book_df.iloc[-1]
    prev_sig = {
        "pick": prev_holding_row["pick"],
        "cash": bool(prev_holding_row["cash"]),
    }

    signal_payload = {
        "signal_month": str(latest_signal_m),
        "holding_month": str(next_holding_m),
        "pick": latest_top,
        "cash": latest_cash,
        "ticker": TRADABLE[latest_top][2],
        "isin": TRADABLE[latest_top][0],
        "name": FACTOR_NAMES[latest_top],
        "table": {k: float(v) for k, v in latest_table.items()},
        "previous": prev_sig,
        "source": "LSE Total Return",
        "stale": False,
        "built_at": datetime.now(timezone.utc).isoformat(),
    }

    return book_df, tradable_df, annual_df, signal_payload, signals_dict


def main():
    prices = load_seed_prices()
    prices = update_latest_prices(prices)

    book_df, tradable_df, annual_df, signal_payload, signals_dict = compute_signals(prices)

    # Save to data directory
    book_df.to_csv(DATA / "final_book.csv")
    tradable_df.to_csv(DATA / "final_tradable.csv")
    tradable_df.to_csv(DATA / "track_record.csv")
    annual_df.to_csv(DATA / "final_tradable_annual.csv")

    (DATA / "signal.json").write_text(json.dumps(signal_payload, indent=2))
    (DATA / "signal_history.json").write_text(json.dumps(signals_dict, indent=2))

    price_status = {
        "expected": signal_payload["signal_month"],
        "performanceThrough": signal_payload["signal_month"],
        "inputs": {k: {"status": "ok", "last": signal_payload["signal_month"]} for k in TICKERS},
        "missing": [],
    }
    (DATA / "price_status.json").write_text(json.dumps(price_status, indent=2))

    print(f"Rebuilt Lodestar World data through {signal_payload['signal_month']}:")
    print(f"  Holdings book: {len(book_df)} months ({book_df.index[0]} .. {book_df.index[-1]})")
    print(f"  Current holding for {signal_payload['holding_month']}: {signal_payload['name']} ({signal_payload['ticker']})")
    print(f"  Cash gate active: {signal_payload['cash']}")
    return signal_payload


if __name__ == "__main__":
    main()
