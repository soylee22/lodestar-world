#!/usr/bin/env python3
"""Contenders YTD Performance Engine for Last Year's Winner.

Scrapes live S&P 500 YTD performance from Slickcharts, identifies the top 5
contenders in the 2027 reselection race, downloads daily Close price histories
from 2026-01-01 to present using yfinance, and outputs daily normalized YTD percentage
series with company logos and peak metrics.
"""

from __future__ import annotations

import json
import urllib.request
from datetime import date, datetime
from pathlib import Path
from bs4 import BeautifulSoup
import pandas as pd
import yfinance as yf

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "data"
LOGOS_DIR = HERE / "assets" / "company-logos"

SLICKCHARTS_URL = "https://www.slickcharts.com/sp500/performance"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

# Distinctive, accessible color palette for contenders
TICKER_COLORS = {
    "MRNA": "#2563eb",  # Bright Blue (Leader)
    "SNDK": "#d97706",  # Amber/Gold (Current Active Holding)
    "DELL": "#0d9488",  # Teal (Hardware / Servers)
    "MU": "#e11d48",    # Rose / Crimson (Semiconductors)
    "MPC": "#7c3aed",   # Purple (Energy)
    "NVDA": "#16a34a",  # Green
    "VST": "#ea580c",   # Orange
    "PLTR": "#475569",  # Slate
    "SPY": "#64748b",   # Muted Slate (Benchmark)
}

COMPANY_NAMES = {
    "MRNA": "Moderna Inc.",
    "SNDK": "SanDisk Corporation",
    "DELL": "Dell Technologies Inc.",
    "MU": "Micron Technology Inc.",
    "MPC": "Marathon Petroleum Corp.",
    "NVDA": "NVIDIA Corp.",
    "VST": "Vistra Corp.",
    "PLTR": "Palantir Technologies",
    "SPY": "S&P 500 Index (SPY)",
}


def scrape_slickcharts_top(n: int = 5) -> list[dict]:
    """Scrape top N performers from Slickcharts S&P 500 performance page."""
    try:
        req = urllib.request.Request(SLICKCHARTS_URL, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=12) as resp:
            html = resp.read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table")
        if not table:
            raise ValueError("No table found on Slickcharts page")

        rows = table.find_all("tr")[1:]  # Skip header
        contenders = []
        for r in rows:
            cols = [c.get_text(strip=True) for c in r.find_all("td")]
            if len(cols) >= 4:
                try:
                    rank = int(cols[0])
                    name = cols[1]
                    ticker = cols[2].strip().upper()
                    ytd_str = cols[3].replace("%", "").replace(",", "").strip()
                    ytd = float(ytd_str)
                    contenders.append({
                        "rank": rank,
                        "ticker": ticker,
                        "name": COMPANY_NAMES.get(ticker, name),
                        "slickchartsYtd": ytd,
                    })
                except Exception:
                    continue
            if len(contenders) >= n:
                break
        if contenders:
            return contenders
    except Exception as e:
        print(f"Warning: Failed to scrape Slickcharts ({e}). Using canonical fallback.")

    # Fallback to verified top contenders
    return [
        {"rank": 1, "ticker": "MRNA", "name": "Moderna Inc.", "slickchartsYtd": 651.85},
        {"rank": 2, "ticker": "SNDK", "name": "SanDisk Corporation", "slickchartsYtd": 384.83},
        {"rank": 3, "ticker": "DELL", "name": "Dell Technologies Inc.", "slickchartsYtd": 237.07},
        {"rank": 4, "ticker": "MU", "name": "Micron Technology Inc.", "slickchartsYtd": 209.99},
        {"rank": 5, "ticker": "MPC", "name": "Marathon Petroleum Corp.", "slickchartsYtd": 173.46},
    ]


def build_contenders_chart_data(top_n: int = 5) -> dict:
    """Fetch daily price series and build normalized YTD percentage trajectory data."""
    top_items = scrape_slickcharts_top(top_n)
    tickers = [item["ticker"] for item in top_items]
    all_tickers = tickers + ["SPY"]

    print(f"Fetching daily 2026 price history for: {all_tickers}...")
    df = yf.download(all_tickers, start="2026-01-01", auto_adjust=True, progress=False)["Close"]

    # Drop any leading rows where all are NaN
    df = df.dropna(how="all")
    dates = [d.strftime("%Y-%m-%d") for d in df.index]

    base_prices = df.iloc[0]
    pct_returns = ((df / base_prices) - 1.0) * 100.0

    series_list = []
    for item in top_items:
        t = item["ticker"]
        if t in pct_returns.columns:
            s = pct_returns[t]
            cur_ret = round(float(s.iloc[-1]), 1)
            peak_val = round(float(s.max()), 1)
            peak_idx = int(s.values.argmax())
            peak_date = dates[peak_idx]

            logo_rel = f"assets/company-logos/{t}.png"
            logo_path = LOGOS_DIR / f"{t}.png"
            has_logo = logo_path.is_file()

            # Clean points array: rounded to 1 decimal place
            pts = [round(float(v), 1) if pd.notna(v) else 0.0 for v in s]

            series_list.append({
                "ticker": t,
                "name": item["name"],
                "rank": item["rank"],
                "color": TICKER_COLORS.get(t, "#2563eb"),
                "logo": logo_rel if has_logo else None,
                "currentYtd": cur_ret,
                "peakYtd": peak_val,
                "peakDate": peak_date,
                "isHolding": (t == "SNDK"),
                "isLeader": (item["rank"] == 1),
                "points": pts,
            })

    # Benchmark SPY
    if "SPY" in pct_returns.columns:
        s_spy = pct_returns["SPY"]
        pts_spy = [round(float(v), 1) if pd.notna(v) else 0.0 for v in s_spy]
        spy_cur = round(float(s_spy.iloc[-1]), 1)
        spy_peak = round(float(s_spy.max()), 1)
        peak_idx_spy = int(s_spy.values.argmax())
        series_list.append({
            "ticker": "SPY",
            "name": "S&P 500 Benchmark",
            "rank": None,
            "color": TICKER_COLORS["SPY"],
            "logo": "assets/company-logos/SPY.png" if (LOGOS_DIR / "SPY.png").is_file() else None,
            "currentYtd": spy_cur,
            "peakYtd": spy_peak,
            "peakDate": dates[peak_idx_spy],
            "isHolding": False,
            "isLeader": False,
            "points": pts_spy,
        })

    payload = {
        "asof": dates[-1] if dates else date.today().isoformat(),
        "startDate": dates[0] if dates else "2026-01-02",
        "dates": dates,
        "series": series_list,
    }

    out_file = DATA_DIR / "lyw_contenders_chart.json"
    out_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Saved {len(series_list)} contenders time series ({len(dates)} trading days) to {out_file}")
    return payload


if __name__ == "__main__":
    data = build_contenders_chart_data(5)
    print("Top series:")
    for s in data["series"]:
        print(f"  #{s['rank']} {s['ticker']}: {s['currentYtd']}% (Peak: {s['peakYtd']}%)")
