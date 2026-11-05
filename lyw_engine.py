#!/usr/bin/env python3
"""Last Year's Winner (LYW) data and calculation engine.

Parses 29-year historical backtest (1997-2025), tracks live 2026 holding (SNDK)
with fixed 35% entry stop-loss, and evaluates 2027 candidate race.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

import pandas as pd
try:
    import yfinance as yf
except ImportError:
    yf = None

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
    "MU": "Micron Technology Inc.",
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
    strat_wealth = 10000.0
    spy_wealth = 10000.0
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

        strat_wealth *= (1.0 + leg_ret / 100.0)
        spy_wealth *= (1.0 + spy_ret / 100.0)

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
            "wealth": round(strat_wealth),
            "benchmarkWealth": round(spy_wealth),
        })

    # Live 2026 holding: SNDK - STOPPED OUT on 5 Nov 2026 at $998.05
    entry_price_2026 = 1557.71
    exit_price_2026 = 998.05
    peak_price_2026 = 1557.71
    cur_price_2026 = exit_price_2026

    stop_price_2026 = round(entry_price_2026 * (1.0 - 0.35), 2)
    buffer_dollars = round(cur_price_2026 - stop_price_2026, 2)
    buffer_pct = round((buffer_dollars / stop_price_2026) * 100.0, 1)
    fall_to_stop_pct = 0.0
    is_stopped_2026 = True

    # Realised leg performance:
    val_gbp = 626.97
    net_pnl_gbp = -373.03
    net_return_pct = -37.30

    # Live Vanguard & Index Benchmark Comparisons (Since 12 Oct 2026 entry with £1,000 capital)
    # Entry prices on 12 Oct 2026 close:
    # VUAG.L: £114.36
    # VUKG.L: £57.39
    # VALL.L: £3.774
    # SPY: $778.10
    vuag_price = 110.38
    vukg_price = 58.90
    vall_price = 3.655
    spy_price = 766.81
    fx_rate = 1.3482

    import urllib.request
    def _fetch_px(ticker: str, fallback: float) -> float:
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=5d"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=3) as r:
                d = json.load(r)
                p = d["chart"]["result"][0]["meta"].get("regularMarketPrice")
                if p and float(p) > 0:
                    return round(float(p), 4)
        except Exception:
            pass
        return fallback

    vuag_price = _fetch_px("VUAG.L", 110.38)
    vukg_price = _fetch_px("VUKG.L", 58.90)
    vall_price = _fetch_px("VALL.L", 3.655)
    spy_price = _fetch_px("SPY", 766.81)
    fx_rate = _fetch_px("GBPUSD=X", 1.3482)

    vuag_shares = round(1000.0 / 114.36, 6)
    vukg_shares = round(1000.0 / 57.39, 6)
    vall_shares = round(1000.0 / 3.774, 6)
    spy_shares = 1.6983917

    vuag_val = round(vuag_shares * vuag_price, 2)
    vuag_ret = round((vuag_price / 114.36 - 1.0) * 100.0, 2)
    vukg_val = round(vukg_shares * vukg_price, 2)
    vukg_ret = round((vukg_price / 57.39 - 1.0) * 100.0, 2)
    vall_val = round(vall_shares * vall_price, 2)
    vall_ret = round((vall_price / 3.774 - 1.0) * 100.0, 2)
    spy_val_gbp = round(spy_shares * spy_price / fx_rate, 2)
    spy_return_pct = round((spy_val_gbp / 1000.0 - 1.0) * 100.0, 2)

    # Real Account details across both Trading 212 tranches:
    real_account = {
        "holdingYear": 2026,
        "ticker": "100% CASH",
        "name": "Trading 212 ISA (SanDisk Liquidated)",
        "broker": "Trading 212",
        "totalCapitalGbp": 1831.78,
        "netInvestedGbp": 1827.04,
        "totalShares": 1.79031071,
        "blendedCostBasisUsd": 1360.46,
        "exitPriceUsd": 998.05,
        "exitDate": "5 Nov 2026, 09:03 UTC",
        "realisedCashGbp": 1323.36,
        "realisedLossGbp": -503.68,
        "realisedReturnPct": -27.50,
        "statusLabel": "STOPPED OUT · 100% CASH IN PIE",
        "tranches": [
            {
                "id": 1,
                "label": "Tranche 1 (Initial Entry)",
                "date": "12 Oct 2026, 11:47 BST",
                "shares": 0.8481779,
                "priceUsd": 1557.71,
                "fxRate": 1.3232,
                "capitalGbp": 1000.0,
                "netInvestedGbp": 998.50,
                "feeGbp": 1.50,
            },
            {
                "id": 2,
                "label": "Tranche 2 (Top-up)",
                "date": "2 Nov 2026, 08:26 GMT",
                "orderId": 59802688463,
                "fillId": 59802688467,
                "shares": 0.94213281,
                "priceUsd": 1182.88,
                "fxRate": 1.3418,
                "capitalGbp": 831.78,
                "netInvestedGbp": 830.53,
                "feeGbp": 1.25,
            },
        ],
    }

    # Historical Daily Benchmark Chart Series (12 Oct 2026 to 5 Nov 2026)
    chart_dates = ["2026-10-12", "2026-10-13", "2026-10-14", "2026-10-15", "2026-10-16", "2026-10-19", "2026-10-20", "2026-10-21", "2026-10-22", "2026-10-23", "2026-10-26", "2026-10-27", "2026-10-28", "2026-10-29", "2026-10-30", "2026-11-02", "2026-11-03", "2026-11-04", "2026-11-05"]
    sndk_hist = [1487.33, 1482.33, 1403.34, 1394.83, 1299.30, 1371.12, 1365.38, 1378.22, 1260.93, 1238.03, 1255.58, 1304.84, 1404.77, 1330.05, 1150.89, 1075.08, 1126.52, 1037.40, 998.05]
    fx_hist = [1.3242, 1.3210, 1.3257, 1.3230, 1.3273, 1.3336, 1.3308, 1.3373, 1.3396, 1.3404, 1.3378, 1.3345, 1.3306, 1.3328, 1.3379, 1.3386, 1.3410, 1.3434, 1.3482]
    vuag_hist = [114.36, 113.76, 113.92, 112.80, 111.98, 112.28, 111.70, 111.96, 110.92, 110.82, 111.32, 112.36, 112.52, 111.74, 109.78, 110.10, 109.20, 109.80, vuag_price]
    vukg_hist = [57.39, 57.37, 57.84, 58.42, 58.64, 58.02, 57.86, 57.94, 57.82, 57.61, 58.02, 57.62, 57.66, 57.78, 57.78, 58.01, 57.37, 58.10, vukg_price]
    vall_hist = [3.774, 3.754, 3.752, 3.719, 3.699, 3.704, 3.687, 3.6985, 3.655, 3.6525, 3.6695, 3.7025, 3.708, 3.690, 3.628, 3.6505, 3.621, 3.638, vall_price]
    spy_hist = [778.10, 778.01, 769.60, 771.79, 763.25, 766.48, 769.05, 773.09, 763.96, 759.97, 765.37, 769.66, 772.31, 769.36, 755.72, 752.10, 754.35, 766.81, spy_price]

    lyw_real, lyw_pct, lyw_norm = [], [], []
    vuag_real, vuag_pct, vuag_norm = [], [], []
    vukg_real, vukg_pct, vukg_norm = [], [], []
    vall_real, vall_pct, vall_norm = [], [], []
    spy_real, spy_pct, spy_norm = [], [], []

    for idx, d in enumerate(chart_dates):
        fx = fx_hist[idx]
        sp = sndk_hist[idx]
        vp = vuag_hist[idx]
        kp = vukg_hist[idx]
        ap = vall_hist[idx]
        spp = spy_hist[idx]

        if d < "2026-11-02":
            strat_r = round((0.8481779 * sp) / fx, 2)
            strat_p = round((strat_r / 1000.0 - 1.0) * 100.0, 2)
            strat_n = strat_r
            vr = round((1000.0 / 114.36) * vp, 2)
            kr = round((1000.0 / 57.39) * kp, 2)
            ar = round((1000.0 / 3.774) * ap, 2)
            sr = round((1000.0 * 1.3232 / 778.10) * spp / fx, 2)
            vpct = round((vr / 1000.0 - 1.0) * 100.0, 2)
            kpct = round((kr / 1000.0 - 1.0) * 100.0, 2)
            apct = round((ar / 1000.0 - 1.0) * 100.0, 2)
            spct = round((sr / 1000.0 - 1.0) * 100.0, 2)
            vn, kn, an, sn = vr, kr, ar, sr
        elif d < "2026-11-05":
            strat_r = round((1.79031071 * sp) / fx, 2)
            strat_p = round((strat_r / 1831.78 - 1.0) * 100.0, 2)
            strat_n = round((0.8481779 * sp) / fx, 2)
            vr = round(((1000.0 / 114.36) + (831.78 / 110.10)) * vp, 2)
            kr = round(((1000.0 / 57.39) + (831.78 / 58.01)) * kp, 2)
            ar = round(((1000.0 / 3.774) + (831.78 / 3.6505)) * ap, 2)
            sr = round(((1000.0 * 1.3232 / 778.10) + (831.78 * 1.3418 / 752.10)) * spp / fx, 2)
            vpct = round((vr / 1831.78 - 1.0) * 100.0, 2)
            kpct = round((kr / 1831.78 - 1.0) * 100.0, 2)
            apct = round((ar / 1831.78 - 1.0) * 100.0, 2)
            spct = round((sr / 1831.78 - 1.0) * 100.0, 2)
            vn = round((1000.0 / 114.36) * vp, 2)
            kn = round((1000.0 / 57.39) * kp, 2)
            an = round((1000.0 / 3.774) * ap, 2)
            sn = round((1000.0 * 1.3232 / 778.10) * spp / fx, 2)
        else:
            strat_r = 1323.36
            strat_p = -27.50
            strat_n = 626.97
            vr = round(((1000.0 / 114.36) + (831.78 / 110.10)) * vp, 2)
            kr = round(((1000.0 / 57.39) + (831.78 / 58.01)) * kp, 2)
            ar = round(((1000.0 / 3.774) + (831.78 / 3.6505)) * ap, 2)
            sr = round(((1000.0 * 1.3232 / 778.10) + (831.78 * 1.3418 / 752.10)) * spp / fx, 2)
            vpct = round((vr / 1831.78 - 1.0) * 100.0, 2)
            kpct = round((kr / 1831.78 - 1.0) * 100.0, 2)
            apct = round((ar / 1831.78 - 1.0) * 100.0, 2)
            spct = round((sr / 1831.78 - 1.0) * 100.0, 2)
            vn = round((1000.0 / 114.36) * vp, 2)
            kn = round((1000.0 / 57.39) * kp, 2)
            an = round((1000.0 / 3.774) * ap, 2)
            sn = round((1000.0 * 1.3232 / 778.10) * spp / fx, 2)

        lyw_real.append(strat_r); lyw_pct.append(strat_p); lyw_norm.append(strat_n)
        vuag_real.append(vr); vuag_pct.append(vpct); vuag_norm.append(vn)
        vukg_real.append(kr); vukg_pct.append(kpct); vukg_norm.append(kn)
        vall_real.append(ar); vall_pct.append(apct); vall_norm.append(an)
        spy_real.append(sr); spy_pct.append(spct); spy_norm.append(sn)

    benchmark_chart = {
        "dates": chart_dates,
        "series": [
            {
                "id": "LYW",
                "ticker": "LYW (SNDK → Cash)",
                "name": "Last Year's Winner",
                "color": "#9f4735",
                "realValues": lyw_real,
                "pctValues": lyw_pct,
                "normValues": lyw_norm,
            },
            {
                "id": "VUAG",
                "ticker": "VUAG.L",
                "name": "Vanguard S&P 500 (VUAG)",
                "color": "#265944",
                "realValues": vuag_real,
                "pctValues": vuag_pct,
                "normValues": vuag_norm,
            },
            {
                "id": "VUKG",
                "ticker": "VUKG.L",
                "name": "Vanguard FTSE 100 (VUKG)",
                "color": "#4f772d",
                "realValues": vukg_real,
                "pctValues": vukg_pct,
                "normValues": vukg_norm,
            },
            {
                "id": "VALL",
                "ticker": "VALL.L",
                "name": "Vanguard FTSE Global All-Cap (VALL)",
                "color": "#1d3557",
                "realValues": vall_real,
                "pctValues": vall_pct,
                "normValues": vall_norm,
            },
            {
                "id": "SPY",
                "ticker": "SPY",
                "name": "SPDR S&P 500 ETF (USD)",
                "color": "#838880",
                "realValues": spy_real,
                "pctValues": spy_pct,
                "normValues": spy_norm,
            },
        ],
    }

    benchmarks = [
        {
            "id": "VUAG",
            "ticker": "VUAG.L",
            "name": "Vanguard S&P 500 (Acc)",
            "assetClass": "US Large-Cap Equity",
            "currency": "GBP",
            "entryDate": "12 Oct 2026",
            "entryPrice": 114.36,
            "currentPrice": vuag_price,
            "shares": vuag_shares,
            "capitalGbp": 1000.0,
            "valuationGbp": vuag_val,
            "netReturnPct": vuag_ret,
            "diffVsStrategyGbp": round(val_gbp - vuag_val, 2),
            "realInvestedGbp": 1831.78,
            "realValuationGbp": vuag_real[-1],
            "realReturnPct": vuag_pct[-1],
            "realDiffVsStrategyGbp": round(vuag_real[-1] - 1323.36, 2),
        },
        {
            "id": "VUKG",
            "ticker": "VUKG.L",
            "name": "Vanguard FTSE 100 (Acc)",
            "assetClass": "UK Large-Cap Equity",
            "currency": "GBP",
            "entryDate": "12 Oct 2026",
            "entryPrice": 57.39,
            "currentPrice": vukg_price,
            "shares": vukg_shares,
            "capitalGbp": 1000.0,
            "valuationGbp": vukg_val,
            "netReturnPct": vukg_ret,
            "diffVsStrategyGbp": round(val_gbp - vukg_val, 2),
            "realInvestedGbp": 1831.78,
            "realValuationGbp": vukg_real[-1],
            "realReturnPct": vukg_pct[-1],
            "realDiffVsStrategyGbp": round(vukg_real[-1] - 1323.36, 2),
        },
        {
            "id": "VALL",
            "ticker": "VALL.L",
            "name": "Vanguard FTSE Global All-Cap (Acc)",
            "assetClass": "Global All-Cap Equity",
            "currency": "GBP",
            "entryDate": "12 Oct 2026",
            "entryPrice": 3.774,
            "currentPrice": vall_price,
            "shares": vall_shares,
            "capitalGbp": 1000.0,
            "valuationGbp": vall_val,
            "netReturnPct": vall_ret,
            "diffVsStrategyGbp": round(val_gbp - vall_val, 2),
            "realInvestedGbp": 1831.78,
            "realValuationGbp": vall_real[-1],
            "realReturnPct": vall_pct[-1],
            "realDiffVsStrategyGbp": round(vall_real[-1] - 1323.36, 2),
        },
        {
            "id": "SPY",
            "ticker": "SPY",
            "name": "SPDR S&P 500 ETF (USD)",
            "assetClass": "US S&P 500 (USD Model)",
            "currency": "USD",
            "entryDate": "12 Oct 2026",
            "entryPrice": 778.10,
            "currentPrice": spy_price,
            "shares": spy_shares,
            "capitalGbp": 1000.0,
            "valuationGbp": spy_val_gbp,
            "netReturnPct": spy_return_pct,
            "diffVsStrategyGbp": round(val_gbp - spy_val_gbp, 2),
            "realInvestedGbp": 1831.78,
            "realValuationGbp": spy_real[-1],
            "realReturnPct": spy_pct[-1],
            "realDiffVsStrategyGbp": round(spy_real[-1] - 1323.36, 2),
        },
    ]

    drawdown_from_entry = round((exit_price_2026 / entry_price_2026 - 1.0) * 100.0, 2)
    drawdown_from_peak = round((exit_price_2026 / peak_price_2026 - 1.0) * 100.0, 2)

    live_position = {
        "holdingYear": 2026,
        "ticker": "CASH",
        "name": "100% Cash (SNDK Stopped Out)",
        "broker": "Trading 212",
        "investedGbp": 998.50,
        "investedUsd": 1557.71,
        "shares": 0.0,
        "entryDate": "12 Oct 2026, 11:47 BST",
        "exitDate": "5 Nov 2026, 09:03 UTC",
        "entryPrice": entry_price_2026,
        "exitPrice": exit_price_2026,
        "currentPrice": exit_price_2026,
        "peakPrice": peak_price_2026,
        "stopLossPercent": 35.0,
        "stopLossPrice": stop_price_2026,
        "bufferPercent": buffer_pct,
        "bufferDollars": buffer_dollars,
        "fallToStopPct": fall_to_stop_pct,
        "drawdownFromEntry": drawdown_from_entry,
        "drawdownFromPeak": drawdown_from_peak,
        "fxRate": round(fx_rate, 4),
        "valuationGbp": val_gbp,
        "netPnlGbp": net_pnl_gbp,
        "netReturnPct": net_return_pct,
        "totalPieCashRealisedGbp": 1323.36,
        "spyPrice": round(spy_price, 2),
        "spyValuationGbp": spy_val_gbp,
        "spyReturnPct": spy_return_pct,
        "diffVsSpyGbp": round(val_gbp - spy_val_gbp, 2),
        "isStopped": is_stopped_2026,
        "statusLabel": "STOPPED OUT · 100% CASH",
        "statusClass": "red",
        "reselectionDate": "31 Dec 2026 close",
        "benchmarks": benchmarks,
    }

    # Load 2027 contenders chart data if present
    chart_path = DATA_DIR / "lyw_contenders_chart.json"
    chart_data = None
    if chart_path.is_file():
        try:
            chart_data = json.loads(chart_path.read_text(encoding="utf-8"))
        except Exception:
            chart_data = None

    # Descriptions for known contenders
    CONTENDER_DESCS = {
        "MRNA": "Leading the 2026 S&P 500 performance race. If MRNA maintains first place through 31 December, all portfolio capital rotates 100% into MRNA on 2 January 2027.",
        "SNDK": "Holding the second position in 2026. If SanDisk surges and overtakes Moderna by 31 December, the strategy continues holding SanDisk for a second consecutive year.",
        "DELL": "Enterprise AI servers and storage growth. Surged strongly in mid-year and remains firmly in the top tier of 2026 momentum performers.",
        "MU": "High-bandwidth memory and semiconductor surge. Memory cycle demand driving substantial index outperformance across 2026.",
        "MPC": "Downstream refining margins and heavy capital returns driving energy sector outperformance into the 2027 race.",
        "NVDA": "Dominant GPU leader following consecutive record years in 2023 and 2024.",
        "VST": "2024 winner (+236.8%) continuing strong nuclear and power infrastructure expansion.",
        "PLTR": "Enterprise AI platform adoption driving steady index outperformance.",
        "APP": "Ad-tech monetization platform surging on software momentum.",
    }

    # Build 2027 contenders list from chart_data if available
    contenders = []
    if chart_data and "series" in chart_data:
        non_spy = [s for s in chart_data["series"] if s.get("ticker") != "SPY"]
        # Sort by current YTD descending
        non_spy.sort(key=lambda x: x.get("currentYtd", 0), reverse=True)
        leader_ytd = non_spy[0]["currentYtd"] if non_spy else 0.0

        for idx, s in enumerate(non_spy, start=1):
            t = s["ticker"]
            cur_ytd = s["currentYtd"]
            gap = round(cur_ytd - leader_ytd, 1) if idx > 1 else 0.0
            is_hold = (t == "SNDK")

            if idx == 1:
                status = "Rank 1 · 2027 Target"
                action = "Buy at Jan 2027 Open"
            elif is_hold:
                status = f"Rank {idx} · Liquidated (35% Stop)"
                action = "Stopped Out ($998.05)"
            else:
                status = f"Rank {idx} · Contender"
                action = f"{gap}% Gap"

            contenders.append({
                "rank": idx,
                "ticker": t,
                "name": s["name"],
                "ytd": cur_ytd,
                "gap": gap,
                "peak": s.get("peakYtd", cur_ytd),
                "peakDate": s.get("peakDate"),
                "status": status,
                "action": action,
                "desc": CONTENDER_DESCS.get(t, f"Surging momentum performer in the 2026 S&P 500 reselection race with {cur_ytd}% YTD return."),
                "logo": s.get("logo"),
                "color": s.get("color"),
            })

    # Fallback or fill remaining trailing contenders
    if len(contenders) < 5:
        contenders = [
            {
                "rank": 1,
                "ticker": "MRNA",
                "name": "Moderna Inc.",
                "ytd": 618.5,
                "gap": 0.0,
                "status": "Rank 1 · 2027 Target",
                "action": "Buy at Jan 2027 Open",
                "desc": CONTENDER_DESCS["MRNA"],
            },
            {
                "rank": 2,
                "ticker": "SNDK",
                "name": "SanDisk Corporation",
                "ytd": 318.1,
                "gap": -300.4,
                "status": "Rank 2 · Active Holding",
                "action": "Active Hold (35% Stop)",
                "desc": CONTENDER_DESCS["SNDK"],
            },
            {
                "rank": 3,
                "ticker": "DELL",
                "name": "Dell Technologies Inc.",
                "ytd": 235.5,
                "gap": -383.0,
                "status": "Rank 3 · Contender",
                "action": "-383.0% Gap",
                "desc": CONTENDER_DESCS["DELL"],
            },
            {
                "rank": 4,
                "ticker": "MU",
                "name": "Micron Technology Inc.",
                "ytd": 180.7,
                "gap": -437.8,
                "status": "Rank 4 · Contender",
                "action": "-437.8% Gap",
                "desc": CONTENDER_DESCS["MU"],
            },
            {
                "rank": 5,
                "ticker": "MPC",
                "name": "Marathon Petroleum Corp.",
                "ytd": 172.4,
                "gap": -446.1,
                "status": "Rank 5 · Contender",
                "action": "-446.1% Gap",
                "desc": CONTENDER_DESCS["MPC"],
            },
        ]

    # Append trailing contenders for context
    existing_tickers = {c["ticker"] for c in contenders}
    trailing = [
        ("NVDA", "NVIDIA Corp.", 138.2, CONTENDER_DESCS["NVDA"]),
        ("VST", "Vistra Corp.", 114.2, CONTENDER_DESCS["VST"]),
        ("PLTR", "Palantir Technologies", 98.5, CONTENDER_DESCS["PLTR"]),
        ("APP", "AppLovin Corp.", 84.2, CONTENDER_DESCS["APP"]),
    ]
    leader_ret = contenders[0]["ytd"]
    for t_sym, t_nm, t_ret, t_desc in trailing:
        if t_sym not in existing_tickers:
            contenders.append({
                "rank": len(contenders) + 1,
                "ticker": t_sym,
                "name": t_nm,
                "ytd": t_ret,
                "gap": round(t_ret - leader_ret, 1),
                "status": "Contender",
                "action": "Trailing Contender",
                "desc": t_desc,
            })

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
            "strapline": "S&P 500 #1 Momentum Rotation with Fixed 35% Entry Stop-Loss",
            "holdingYear": 2026,
            "asof": date.today().isoformat(),
        },
        "livePosition": live_position,
        "realAccount": real_account,
        "benchmarks": benchmarks,
        "benchmarkChart": benchmark_chart,
        "race2027": contenders,
        "contendersChart": chart_data,
        "stats": stats,
        "archive": archive,
    }


if __name__ == "__main__":
    d = build_lyw_data()
    print(f"LYW Data built successfully: {len(d['archive'])} years, CAGR: {d['stats']['cagr']}%, live: {d['livePosition']['ticker']}")
