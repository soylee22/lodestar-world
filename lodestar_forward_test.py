#!/usr/bin/env python3
"""Lodestar World Forward Test Tracking Engine.

Tracks Lee Slater's actual Trading 212 'Lodestar World' live portfolio (Pie ID 10205730).
Established 2 November 2026 holding 100% World Value (iShares Edge MSCI World Value Factor Acc, IWFV.L).
Compares live performance against passive benchmarks: VUAG.L, VUKG.L, VALL.L, and SPY.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
import urllib.request

HERE = Path(__file__).resolve().parent

def build_lodestar_forward_test() -> dict:
    # 1. Real Trading 212 audited position details
    # Pie ID 10205730 ("Lodestar World") on Trading 212
    # Established 2 November 2026 morning via 4 AutoInvest orders
    total_capital_gbp = 3804.53
    total_shares = 64.89106098
    blended_entry_pence = 5862.94929154
    blended_entry_gbp = blended_entry_pence / 100.0

    # 4 Audited orders from Trading 212
    orders = [
        {
            "id": 1,
            "orderId": 59753209707,
            "fillId": 59802687170,
            "date": "2 Nov 2026, 08:23 UTC",
            "shares": 30.10711239,
            "pricePence": 5863.0,
            "priceGbp": 58.63,
            "capitalGbp": 1765.18,
            "type": "AutoInvest",
        },
        {
            "id": 2,
            "orderId": 59753210007,
            "fillId": 59802687865,
            "date": "2 Nov 2026, 08:25 UTC",
            "shares": 19.22108495,
            "pricePence": 5862.0,
            "priceGbp": 58.62,
            "capitalGbp": 1126.74,
            "type": "AutoInvest",
        },
        {
            "id": 3,
            "orderId": 59753210096,
            "fillId": 59802688190,
            "date": "2 Nov 2026, 08:25 UTC",
            "shares": 7.59764625,
            "pricePence": 5863.0,
            "priceGbp": 58.63,
            "capitalGbp": 445.45,
            "type": "AutoInvest",
        },
        {
            "id": 4,
            "orderId": 59753210671,
            "fillId": 59802689631,
            "date": "2 Nov 2026, 08:31 UTC",
            "shares": 7.96521739,
            "pricePence": 5865.0,
            "priceGbp": 58.65,
            "capitalGbp": 467.16,
            "type": "AutoInvest",
        },
    ]

    # Benchmark starting levels at 2 Nov 2026 entry:
    vuag_entry_gbp = 109.84
    vukg_entry_gbp = 57.64
    vall_entry_gbp = 3.636
    spy_entry_usd = 759.45
    fx_entry = 1.3386

    vuag_shares = total_capital_gbp / vuag_entry_gbp
    vukg_shares = total_capital_gbp / vukg_entry_gbp
    vall_shares = total_capital_gbp / vall_entry_gbp
    spy_shares = (total_capital_gbp * fx_entry) / spy_entry_usd

    # Helper to fetch current quote
    def _fetch_quote(ticker: str, fallback: float) -> float:
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

    iwfv_pence = _fetch_quote("IWFV.L", 5690.30)
    vuag_price = _fetch_quote("VUAG.L", 107.80)
    vukg_price = _fetch_quote("VUKG.L", 58.43)
    vall_price = _fetch_quote("VALL.L", 3.578)
    spy_price = _fetch_quote("SPY", 741.64)
    fx_rate = _fetch_quote("GBPUSD=X", 1.3479)

    iwfv_gbp = iwfv_pence / 100.0
    cur_val_gbp = round(total_shares * iwfv_gbp, 2)
    net_pnl_gbp = round(cur_val_gbp - total_capital_gbp, 2)
    net_ret_pct = round((net_pnl_gbp / total_capital_gbp) * 100.0, 2)

    vuag_val = round(vuag_shares * vuag_price, 2)
    vuag_ret = round((vuag_price / vuag_entry_gbp - 1.0) * 100.0, 2)

    vukg_val = round(vukg_shares * vukg_price, 2)
    vukg_ret = round((vukg_price / vukg_entry_gbp - 1.0) * 100.0, 2)

    vall_val = round(vall_shares * vall_price, 2)
    vall_ret = round((vall_price / vall_entry_gbp - 1.0) * 100.0, 2)

    spy_val_gbp = round((spy_shares * spy_price) / fx_rate, 2)
    spy_ret = round((spy_val_gbp / total_capital_gbp - 1.0) * 100.0, 2)

    # Historical daily observations (2 Nov - 5 Nov)
    dates = ["2026-11-02", "2026-11-03", "2026-11-04", "2026-11-05"]
    daily_closes = {
        "IWFV": [5854.0, 5801.0, 5828.0, iwfv_pence],
        "VUAG": [110.10, 109.20, 110.38, vuag_price],
        "VUKG": [58.01, 57.37, 58.33, vukg_price],
        "VALL": [3.6505, 3.6210, 3.6520, vall_price],
        "SPY":  [752.10, 754.35, 766.81, spy_price],
        "FX":   [1.33856, 1.34099, 1.34342, fx_rate],
    }

    real_values = {"LODESTAR": [], "VUAG": [], "VUKG": [], "VALL": [], "SPY": []}
    pct_values = {"LODESTAR": [], "VUAG": [], "VUKG": [], "VALL": [], "SPY": []}
    norm_values = {"LODESTAR": [], "VUAG": [], "VUKG": [], "VALL": [], "SPY": []}

    for i in range(len(dates)):
        # Lodestar
        ls_val = round(total_shares * (daily_closes["IWFV"][i] / 100.0), 2)
        ls_ret = round((ls_val / total_capital_gbp - 1.0) * 100.0, 2)
        ls_norm = round(1000.0 * (1.0 + ls_ret / 100.0), 2)
        real_values["LODESTAR"].append(ls_val)
        pct_values["LODESTAR"].append(ls_ret)
        norm_values["LODESTAR"].append(ls_norm)

        # VUAG
        vg_val = round(vuag_shares * daily_closes["VUAG"][i], 2)
        vg_ret = round((daily_closes["VUAG"][i] / vuag_entry_gbp - 1.0) * 100.0, 2)
        vg_norm = round(1000.0 * (1.0 + vg_ret / 100.0), 2)
        real_values["VUAG"].append(vg_val)
        pct_values["VUAG"].append(vg_ret)
        norm_values["VUAG"].append(vg_norm)

        # VUKG
        vk_val = round(vukg_shares * daily_closes["VUKG"][i], 2)
        vk_ret = round((daily_closes["VUKG"][i] / vukg_entry_gbp - 1.0) * 100.0, 2)
        vk_norm = round(1000.0 * (1.0 + vk_ret / 100.0), 2)
        real_values["VUKG"].append(vk_val)
        pct_values["VUKG"].append(vk_ret)
        norm_values["VUKG"].append(vk_norm)

        # VALL
        va_val = round(vall_shares * daily_closes["VALL"][i], 2)
        va_ret = round((daily_closes["VALL"][i] / vall_entry_gbp - 1.0) * 100.0, 2)
        va_norm = round(1000.0 * (1.0 + va_ret / 100.0), 2)
        real_values["VALL"].append(va_val)
        pct_values["VALL"].append(va_ret)
        norm_values["VALL"].append(va_norm)

        # SPY
        sp_val = round((spy_shares * daily_closes["SPY"][i]) / daily_closes["FX"][i], 2)
        sp_ret = round((sp_val / total_capital_gbp - 1.0) * 100.0, 2)
        sp_norm = round(1000.0 * (1.0 + sp_ret / 100.0), 2)
        real_values["SPY"].append(sp_val)
        pct_values["SPY"].append(sp_ret)
        norm_values["SPY"].append(sp_norm)

    benchmarks = [
        {
            "ticker": "LODESTAR",
            "name": "Lodestar World (World Value)",
            "benchmarkTicker": "IWFV.L",
            "isin": "IE00BP3QZB59",
            "currentPrice": f"{iwfv_pence:,.1f}p",
            "entryPrice": f"{blended_entry_pence:,.1f}p",
            "shares": total_shares,
            "realValue": cur_val_gbp,
            "realReturn": net_ret_pct,
            "realPnl": net_pnl_gbp,
            "normValue": round(1000.0 * (1.0 + net_ret_pct / 100.0), 2),
            "normReturn": net_ret_pct,
            "diffReal": 0.0,
            "diffNorm": 0.0,
            "diffPct": 0.0,
            "isStrategy": True,
            "colour": "#10b981",
        },
        {
            "ticker": "VUAG",
            "name": "Vanguard S&P 500 (Acc)",
            "benchmarkTicker": "VUAG.L",
            "isin": "IE00BFMXXD54",
            "currentPrice": f"£{vuag_price:,.2f}",
            "entryPrice": f"£{vuag_entry_gbp:,.2f}",
            "shares": round(vuag_shares, 4),
            "realValue": vuag_val,
            "realReturn": vuag_ret,
            "realPnl": round(vuag_val - total_capital_gbp, 2),
            "normValue": round(1000.0 * (1.0 + vuag_ret / 100.0), 2),
            "normReturn": vuag_ret,
            "diffReal": round(vuag_val - cur_val_gbp, 2),
            "diffNorm": round(1000.0 * (1.0 + vuag_ret / 100.0) - (1000.0 * (1.0 + net_ret_pct / 100.0)), 2),
            "diffPct": round(vuag_ret - net_ret_pct, 2),
            "isStrategy": False,
            "colour": "#f59e0b",
        },
        {
            "ticker": "VUKG",
            "name": "Vanguard FTSE 100 (Acc)",
            "benchmarkTicker": "VUKG.L",
            "isin": "IE00BFMXYP42",
            "currentPrice": f"£{vukg_price:,.2f}",
            "entryPrice": f"£{vukg_entry_gbp:,.2f}",
            "shares": round(vukg_shares, 4),
            "realValue": vukg_val,
            "realReturn": vukg_ret,
            "realPnl": round(vukg_val - total_capital_gbp, 2),
            "normValue": round(1000.0 * (1.0 + vukg_ret / 100.0), 2),
            "normReturn": vukg_ret,
            "diffReal": round(vukg_val - cur_val_gbp, 2),
            "diffNorm": round(1000.0 * (1.0 + vukg_ret / 100.0) - (1000.0 * (1.0 + net_ret_pct / 100.0)), 2),
            "diffPct": round(vukg_ret - net_ret_pct, 2),
            "isStrategy": False,
            "colour": "#a855f7",
        },
        {
            "ticker": "VALL",
            "name": "Vanguard FTSE Global All Cap (Acc)",
            "benchmarkTicker": "VALL.L",
            "isin": "IE00BNG8L278",
            "currentPrice": f"£{vall_price:,.3f}",
            "entryPrice": f"£{vall_entry_gbp:,.3f}",
            "shares": round(vall_shares, 4),
            "realValue": vall_val,
            "realReturn": vall_ret,
            "realPnl": round(vall_val - total_capital_gbp, 2),
            "normValue": round(1000.0 * (1.0 + vall_ret / 100.0), 2),
            "normReturn": vall_ret,
            "diffReal": round(vall_val - cur_val_gbp, 2),
            "diffNorm": round(1000.0 * (1.0 + vall_ret / 100.0) - (1000.0 * (1.0 + net_ret_pct / 100.0)), 2),
            "diffPct": round(vall_ret - net_ret_pct, 2),
            "isStrategy": False,
            "colour": "#3b82f6",
        },
        {
            "ticker": "SPY",
            "name": "SPDR S&P 500 ETF (GBP-adj)",
            "benchmarkTicker": "SPY",
            "isin": "US78462F1030",
            "currentPrice": f"${spy_price:,.2f}",
            "entryPrice": f"${spy_entry_usd:,.2f}",
            "shares": round(spy_shares, 4),
            "realValue": spy_val_gbp,
            "realReturn": spy_ret,
            "realPnl": round(spy_val_gbp - total_capital_gbp, 2),
            "normValue": round(1000.0 * (1.0 + spy_ret / 100.0), 2),
            "normReturn": spy_ret,
            "diffReal": round(spy_val_gbp - cur_val_gbp, 2),
            "diffNorm": round(1000.0 * (1.0 + spy_ret / 100.0) - (1000.0 * (1.0 + net_ret_pct / 100.0)), 2),
            "diffPct": round(spy_ret - net_ret_pct, 2),
            "isStrategy": False,
            "colour": "#64748b",
        },
    ]

    series = [
        {"id": "LODESTAR", "name": "Lodestar World (World Value)", "color": "#10b981", "realValues": real_values["LODESTAR"], "pctValues": pct_values["LODESTAR"], "normValues": norm_values["LODESTAR"]},
        {"id": "VUAG", "name": "Vanguard S&P 500 (Acc)", "color": "#f59e0b", "realValues": real_values["VUAG"], "pctValues": pct_values["VUAG"], "normValues": norm_values["VUAG"]},
        {"id": "VUKG", "name": "Vanguard FTSE 100 (Acc)", "color": "#a855f7", "realValues": real_values["VUKG"], "pctValues": pct_values["VUKG"], "normValues": norm_values["VUKG"]},
        {"id": "VALL", "name": "Vanguard FTSE Global All Cap", "color": "#3b82f6", "realValues": real_values["VALL"], "pctValues": pct_values["VALL"], "normValues": norm_values["VALL"]},
        {"id": "SPY", "name": "SPDR S&P 500 ETF (GBP-adj)", "color": "#64748b", "realValues": real_values["SPY"], "pctValues": pct_values["SPY"], "normValues": norm_values["SPY"]},
    ]

    return {
        "meta": {
            "title": "Lodestar World Live Forward Testing",
            "description": "Forward testing live portfolio performance against passive benchmarks starting from 2 Nov 2026 entry.",
            "startDate": "2026-11-02",
            "startDatePretty": "2 Nov 2026",
            "asOfDate": str(date.today()),
        },
        "realAccount": {
            "broker": "Trading 212",
            "pieId": 10205730,
            "pieName": "Lodestar World",
            "holding": "iShares Edge MSCI World Value Factor (Acc)",
            "ticker": "IWFV.L",
            "isin": "IE00BP3QZB59",
            "totalCapitalGbp": total_capital_gbp,
            "totalShares": total_shares,
            "blendedEntryPence": blended_entry_pence,
            "blendedEntryGbp": blended_entry_gbp,
            "currentPricePence": iwfv_pence,
            "currentPriceGbp": iwfv_gbp,
            "currentValueGbp": cur_val_gbp,
            "netPnlGbp": net_pnl_gbp,
            "netReturnPct": net_ret_pct,
            "statusLabel": "ACTIVE · 100% WORLD VALUE (IWFV)",
            "orders": orders,
        },
        "benchmarks": benchmarks,
        "benchmarkChart": {
            "dates": dates,
            "series": series,
            "realValues": real_values,
            "pctValues": pct_values,
            "normValues": norm_values,
        },
    }

if __name__ == "__main__":
    data = build_lodestar_forward_test()
    print("Lodestar Forward Test built successfully:")
    print("Real Account:", json.dumps(data["realAccount"], indent=2))
    print("Benchmarks:", len(data["benchmarks"]))
    print("Dates:", data["benchmarkChart"]["dates"])
