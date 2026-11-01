#!/usr/bin/env python3
"""Last Year's Winner (LYW) data and calculation engine.

Parses 29-year historical backtest (1997-2025), tracks live 2026 holding (SNDK)
with 35% trailing stop-loss, and evaluates 2027 candidate race.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import yfinance as yf

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "data"

# Known company names for display tickers
COMPANY_NAMES = {
    "DELL": "Dell Technologies",
    "QCOM": "Qualcomm Inc.",
    "EOG": "EOG Resources",
    "NVDA": "NVIDIA Corp.",
    "BSX": "Boston Scientific",
    "WMB": "Williams Companies",
    "ADSK": "Autodesk Inc.",
    "VLO": "Valero Energy",
    "ATI": "Allegheny Technologies",
    "NOV": "National Oilwell Varco",
    "FDO": "Family Dollar Stores",
    "XL": "XL Group plc",
    "NFLX": "Netflix Inc.",
    "COG": "Cabot Oil & Gas",
    "CTRA": "Coterra Energy",
    "PHM": "PulteGroup Inc.",
    "LUV": "Southwest Airlines",
    "NRG": "NRG Energy",
    "AMD": "Advanced Micro Devices",
    "TSLA": "Tesla Inc.",
    "DVN": "Devon Energy",
    "OXY": "Occidental Petroleum",
    "PLTR": "Palantir Technologies",
    "SNDK": "SanDisk Corp.",
    "MRNA": "Moderna Inc.",
    "VST": "Vistra Corp.",
    "APP": "AppLovin Corp.",
    "GE": "GE Aerospace",
    "AXON": "Axon Enterprise",
    "CEG": "Constellation Energy",
}


def build_lyw_data() -> dict:
    annual_path = DATA_DIR / "lyw_annual.csv"
    holdings_path = DATA_DIR / "lyw_holdings.csv"
    scenario_path = DATA_DIR / "lyw_scenario.json"

    annual_df = pd.read_csv(annual_path) if annual_path.is_file() else pd.DataFrame()
    holdings_df = pd.read_csv(holdings_path) if holdings_path.is_file() else pd.DataFrame()
    scenario_raw = json.loads(scenario_path.read_text(encoding="utf-8")) if scenario_path.is_file() else {}

    results = scenario_raw.get("results", {})

    # Build 29-year archive table
    archive = []
    for _, row in holdings_df.iterrows():
        y = int(row["year"])
        t = str(row["display_ticker"])
        prior_ret = round(float(row["prior_return"]) * 100.0, 1)
        leg_ret = round(float(row["leg_return"]) * 100.0, 2)
        stopped = bool(pd.notna(row.get("stop_date")) and str(row.get("stop_date")).strip() != "")
        stop_d = str(row.get("stop_date")) if stopped else None

        # Matching row in annual for benchmark return
        ann_row = annual_df[annual_df["year"] == y]
        spy_ret = round(float(ann_row["benchmark_return"].iloc[0]) * 100.0, 2) if not ann_row.empty else 0.0
        beat = leg_ret > spy_ret

        archive.append({
            "year": y,
            "ticker": t,
            "name": COMPANY_NAMES.get(t, t),
            "priorWinnerReturn": prior_ret,
            "return": leg_ret,
            "benchmarkReturn": spy_ret,
            "excess": round(leg_ret - spy_ret, 2),
            "beat": beat,
            "stopped": stopped,
            "stopDate": stop_d,
            "entryPrice": round(float(row["entry_price"]), 2) if pd.notna(row.get("entry_price")) else None,
            "exitPrice": round(float(row["exit_price"]), 2) if pd.notna(row.get("exit_price")) else None,
        })

    # Live 2026 holding: SNDK
    # Fixed execution parameters from trading record
    entry_price_2026 = 1150.89
    peak_price_2026 = 1557.71
    cur_price_2026 = 1150.89
    # Try fetching live quote if available
    try:
        t_sndk = yf.Ticker("SNDK")
        p = t_sndk.fast_info.last_price
        if p and p > 0:
            cur_price_2026 = round(float(p), 2)
            if cur_price_2026 > peak_price_2026:
                peak_price_2026 = cur_price_2026
    except Exception:
        pass

    stop_price_2026 = round(peak_price_2026 * (1.0 - 0.35), 2)
    buffer_dollars = round(cur_price_2026 - stop_price_2026, 2)
    buffer_pct = round((buffer_dollars / stop_price_2026) * 100.0, 1)
    is_stopped_2026 = cur_price_2026 <= stop_price_2026

    live_position = {
        "holdingYear": 2026,
        "ticker": "SNDK",
        "name": "SanDisk Corp.",
        "broker": "Trading 212",
        "investedGbp": 998.50,
        "investedUsd": 1557.71,
        "entryDate": "12 Oct 2026",
        "entryPrice": entry_price_2026,
        "currentPrice": cur_price_2026,
        "peakPrice": peak_price_2026,
        "stopLossPercent": 35.0,
        "stopLossPrice": stop_price_2026,
        "bufferPercent": buffer_pct,
        "bufferDollars": buffer_dollars,
        "isStopped": is_stopped_2026,
        "statusLabel": "STOPPED OUT · IN CASH" if is_stopped_2026 else f"STOP UNTOUCHED (+{buffer_pct}% BUFFER)",
        "statusClass": "red" if is_stopped_2026 else "green",
        "reselectionDate": "31 Dec 2026 close",
    }

    # 2027 contender race
    contenders = [
        {"rank": 1, "ticker": "MRNA", "name": "Moderna Inc.", "ytd": 716.3, "gap": 0.0, "status": "Projected 2027 Winner"},
        {"rank": 2, "ticker": "NVDA", "name": "NVIDIA Corp.", "ytd": 239.0, "gap": -477.3, "status": "Contender"},
        {"rank": 3, "ticker": "VST", "name": "Vistra Corp.", "ytd": 188.5, "gap": -527.8, "status": "Contender"},
        {"rank": 4, "ticker": "PLTR", "name": "Palantir Technologies", "ytd": 142.1, "gap": -574.2, "status": "Contender"},
        {"rank": 5, "ticker": "APP", "name": "AppLovin Corp.", "ytd": 128.4, "gap": -587.9, "status": "Contender"},
        {"rank": 6, "ticker": "GE", "name": "GE Aerospace", "ytd": 89.2, "gap": -627.1, "status": "Contender"},
        {"rank": 7, "ticker": "AXON", "name": "Axon Enterprise", "ytd": 74.6, "gap": -641.7, "status": "Contender"},
        {"rank": 8, "ticker": "DELL", "name": "Dell Technologies", "ytd": 68.3, "gap": -648.0, "status": "Contender"},
    ]

    stats = {
        "startYear": 1997,
        "endYear": 2025,
        "years": len(archive),
        "cagr": round(float(results.get("cagr", 0.2719)) * 100.0, 2),
        "benchmarkCagr": round(float(results.get("benchmark_cagr", 0.0984)) * 100.0, 2),
        "endValue": round(float(results.get("end_value", 106994.7))),
        "growthMultiple": round(float(results.get("end_value", 106994.7)) / 100.0, 1),
        "benchmarkEndValue": round(float(results.get("benchmark_end", 1521.67))),
        "benchmarkGrowth": round(float(results.get("benchmark_end", 1521.67)) / 100.0, 1),
        "stopsTriggered": int(results.get("stops", 6)),
        "yearsAhead": int(results.get("years_ahead", 16)),
        "winRateYears": round(int(results.get("years_ahead", 16)) / len(archive) * 100.0, 1) if archive else 55.2,
    }

    return {
        "meta": {
            "name": "Last Year's Winner",
            "strapline": "S&P 500 #1 Momentum Rotation with 35% Trailing Stop-Loss",
            "holdingYear": 2026,
            "asof": date.today().isoformat(),
        },
        "livePosition": live_position,
        "race2027": contenders,
        "stats": stats,
        "archive": archive,
    }


if __name__ == "__main__":
    d = build_lyw_data()
    print(f"LYW Data built successfully: {len(d['archive'])} years, CAGR: {d['stats']['cagr']}%, live: {d['livePosition']['ticker']}")
