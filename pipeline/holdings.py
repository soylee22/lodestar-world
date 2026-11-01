"""Top holdings and fundamentals for whichever ETF is currently held.

Refreshed with the monthly job. Driven by data/signal.json.
Everything is written into data/holdings.json and baked into data.js.
"""

from __future__ import annotations

import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path

import yfinance as yf

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DATA = ROOT / "data"

FIELDS = [
    "shortName", "longName", "sector", "industry", "marketCap", "trailingPE",
    "forwardPE", "revenueGrowth", "earningsGrowth", "profitMargins",
    "dividendYield", "dividendRate", "currentPrice", "regularMarketPrice", "country", "website"
]


def _retry(fn, n=3, wait=2):
    for i in range(n):
        try:
            out = fn()
            if out is not None:
                return out
        except Exception:
            pass
        time.sleep(wait)
    return None


def fund_holdings(ticker: str, top: int = 10) -> dict | None:
    def go():
        fd = yf.Ticker(ticker).funds_data
        th = fd.top_holdings
        if th is None or th.empty:
            return None
        rows = []
        for sym, r in th.head(top).iterrows():
            weight = float(r.get("Holding Percent", 0.0))
            rows.append({
                "symbol": str(sym),
                "name": str(r.get("Name") or sym),
                "weight": weight,
            })
        return {
            "holdings": rows,
            "sector_weights": {k: float(v) for k, v in (fd.sector_weightings or {}).items() if v},
        }
    return _retry(go)


def fundamentals(symbol: str) -> dict:
    def go():
        info = yf.Ticker(symbol).info
        if not info:
            return None
        out = {k: info.get(k) for k in FIELDS}
        if out.get("marketCap") is not None:
            out["marketCap"] = float(out["marketCap"])
        return out
    return _retry(go) or {}


def dividend_yield_percent(info: dict) -> float | None:
    try:
        rate = float(info.get("dividendRate", 0.0))
        price = float(info.get("currentPrice") or info.get("regularMarketPrice") or 0.0)
    except (KeyError, TypeError, ValueError):
        return None
    if not math.isfinite(rate) or not math.isfinite(price) or rate < 0 or price <= 0:
        return None
    return rate / price * 100.0


def build(signal=None):
    if signal is None:
        signal_file = DATA / "signal.json"
        if not signal_file.is_file():
            print("  !! signal.json missing; cannot build holdings")
            return None
        signal = json.loads(signal_file.read_text())

    is_cash = signal.get("cash", False)
    if is_cash:
        out = {
            "as_at": signal["signal_month"],
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "snapshot_date": signal["signal_month"],
            "source": "Cash reserve",
            "legs": {},
        }
        (DATA / "holdings.json").write_text(json.dumps(out, indent=2))
        return out

    ticker = signal["ticker"]
    slot = signal["pick"]
    print(f"  Fetching holdings for {slot} ({ticker})...")

    h = fund_holdings(ticker)
    if not h:
        print(f"  !! fund holdings unavailable for {ticker}")
        return None

    enriched = []
    for row in h["holdings"]:
        f = fundamentals(row["symbol"])
        enriched.append({
            **row,
            "company": f.get("longName") or f.get("shortName") or row["name"],
            "sector": row.get("sector") or f.get("sector"),
            "website": f.get("website"),
            "industry": f.get("industry"),
            "market_cap": f.get("marketCap"),
            "pe": f.get("trailingPE"),
            "forward_pe": f.get("forwardPE"),
            "revenue_growth": f.get("revenueGrowth"),
            "earnings_growth": f.get("earningsGrowth"),
            "profit_margin": f.get("profitMargins"),
            "dividend_yield": dividend_yield_percent(f),
        })

    top10_w = sum(r["weight"] for r in enriched)
    out = {
        "as_at": signal["signal_month"],
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "snapshot_date": signal["signal_month"],
        "source": "Yahoo Finance fund holdings disclosure",
        "legs": {
            "factor": {
                "slot": slot,
                "ticker": ticker,
                "holdings": enriched,
                "sector_weights": h["sector_weights"],
                "top10_weight": top10_w,
                "source": "Yahoo Finance top-ten holdings",
                "fundamentals_source": "Yahoo Finance",
                "snapshot_date": signal["signal_month"],
            }
        }
    }

    (DATA / "holdings.json").write_text(json.dumps(out, indent=2))
    print(f"  Wrote {DATA / 'holdings.json'} with {len(enriched)} holdings")
    return out


if __name__ == "__main__":
    build()
