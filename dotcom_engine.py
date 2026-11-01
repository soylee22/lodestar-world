#!/usr/bin/env python3
"""Lodestar World Dot-Com Bubble Extended Backtest Engine (1998-2026).

Computes full 28-year track record using MSCI World Net Total Return GBP factor
indices (Value, Momentum, Quality, Small Cap, High Dividend Yield) and S&P 500
cash preservation gate from December 1998 through October 2026 (335 months).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "data"

LOOKBACK = 8
CASH_LOOKBACK = 19
CASH_THRESHOLD = -0.25


def build_dotcom_data() -> dict:
    msci_path = DATA_DIR / "msci_netr_gbp.csv"
    spx_path = DATA_DIR / "spx_monthly.csv"

    if not msci_path.is_file() or not spx_path.is_file():
        return {}

    msci = pd.read_csv(msci_path, index_col=0)
    msci.index = pd.PeriodIndex(msci.index, freq="M")
    spx = pd.read_csv(spx_path, index_col=0).iloc[:, 0]
    spx.index = pd.PeriodIndex(spx.index, freq="M")

    # 5 slots: MOM, VAL, QUAL, SMALL, HDY (proxy for TDGB)
    slots = ["WLD_MOM", "WLD_VAL", "WLD_QUAL", "WLD_SMALL", "WLD_HDY"]
    df = msci[slots].copy()

    mom8 = df / df.shift(LOOKBACK) - 1.0
    cash_gate = (spx / spx.shift(CASH_LOOKBACK) - 1.0) < CASH_THRESHOLD
    monthly_rets = df.pct_change(fill_method=None) * 100.0
    core_rets = msci["WLD_CORE"].pct_change(fill_method=None) * 100.0
    fallback_rets = df[["WLD_MOM", "WLD_VAL", "WLD_QUAL"]].mean(axis=1).pct_change(fill_method=None) * 100.0
    bench_rets = core_rets.combine_first(fallback_rets)

    start_p = pd.Period("1999-09", freq="M")
    end_p = df.index[-1]

    strat_rets = {}
    core_series = {}
    picks_history = []
    cash_count = 0

    for p in pd.period_range(start_p, end_p, freq="M"):
        prev = p - 1
        if prev not in mom8.index:
            continue
        top = mom8.loc[prev].idxmax()
        is_cash = bool(cash_gate.get(prev, False))
        if is_cash:
            cash_count += 1
            chosen = "CASH"
            r = 0.0
        else:
            chosen = top
            r = float(monthly_rets.loc[p, top])

        strat_rets[p] = r
        core_series[p] = float(bench_rets.loc[p]) if p in bench_rets.index else 0.0

        picks_history.append({
            "period": str(p),
            "pick": chosen,
            "cash": is_cash,
            "return": round(r, 2),
        })

    s_strat = pd.Series(strat_rets)
    s_core = pd.Series(core_series)

    # Annual returns
    ann_strat = ((1.0 + s_strat / 100.0).groupby(s_strat.index.year).prod() - 1.0) * 100.0
    ann_core = ((1.0 + s_core / 100.0).groupby(s_core.index.year).prod() - 1.0) * 100.0

    years_list = []
    for y in sorted(ann_strat.index):
        r_strat = round(float(ann_strat[y]), 2)
        r_core = round(float(ann_core.get(y, 0.0)), 2)
        years_list.append({
            "year": int(y),
            "strategy": r_strat,
            "benchmark": r_core,
            "excess": round(r_strat - r_core, 2),
            "beat": r_strat > r_core,
        })

    def calc_stats(series: pd.Series) -> dict:
        n_years = len(series) / 12.0
        growth = float((1.0 + series / 100.0).prod())
        cagr = (growth ** (1.0 / n_years) - 1.0) * 100.0
        vol = float(series.std() * np.sqrt(12))
        sharpe = cagr / vol if vol > 0 else 0.0

        cum = (1.0 + series / 100.0).cumprod()
        peak = cum.cummax()
        dd = (cum / peak - 1.0) * 100.0
        max_dd = float(dd.min())
        return {
            "months": len(series),
            "years": round(n_years, 1),
            "cagr": round(cagr, 2),
            "vol": round(vol, 2),
            "sharpe": round(sharpe, 2),
            "maxDrawdown": round(max_dd, 2),
            "growthMultiple": round(growth, 2),
        }

    stats_strat = calc_stats(s_strat)
    stats_core = calc_stats(s_core)
    stats_strat["cashMonths"] = cash_count
    stats_strat["positiveYears"] = sum(y["strategy"] > 0 for y in years_list)
    stats_strat["totalYears"] = len(years_list)

    return {
        "start": str(start_p),
        "end": str(end_p),
        "stats": stats_strat,
        "benchmarkStats": stats_core,
        "years": years_list,
        "picks": picks_history,
    }


if __name__ == "__main__":
    d = build_dotcom_data()
    print(f"Dot-Com Engine: {d['stats']['years']} years ({d['start']} to {d['end']}), CAGR: {d['stats']['cagr']}% vs Benchmark: {d['benchmarkStats']['cagr']}%, Cash months: {d['stats']['cashMonths']}")
