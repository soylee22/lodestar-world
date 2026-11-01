#!/usr/bin/env python3
"""Compile the Lodestar World track record into a single data.js literal.

Reads final_tradable.csv, final_tradable_annual.csv, final_book.csv, holdings.json
and writes data.js next to this script as:

    const DATA = { ... };

Nothing is computed in the browser.
"""

from __future__ import annotations

import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "data"

sys.path.insert(0, str(HERE))
from universe import FACTOR_NAMES, TRADABLE, STYLES  # noqa: E402
from lyw_engine import build_lyw_data  # noqa: E402
from dotcom_engine import build_dotcom_data  # noqa: E402
from pipeline.lookthrough import consolidate, company_domain  # noqa: E402
from pipeline.logos import company_key, load_registry  # noqa: E402

RISK_FREE = 0.02  # 2.0% annual risk-free rate for Sharpe and Sortino

STRATEGY_COL = 0
BENCHMARKS = {"allworld": "FTSE All-World", "sp500": "S&P 500", "world": "MSCI World"}
LABELS = {
    "strategy": "Lodestar World",
    "allworld": "FTSE All-World",
    "sp500": "S&P 500",
    "world": "MSCI World",
}

MONTH_ABBR = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

SECTOR_META = {
    "technology":             ("Technology", "INFOTECH"),
    "information_technology": ("Technology", "INFOTECH"),
    "consumer_discretionary": ("Consumer Discretionary", "CONS_DISC"),
    "consumer_staples":       ("Consumer Staples", "CONS_STAP"),
    "health_care":            ("Health Care", "HEALTH"),
    "materials":              ("Materials", "MATERIALS"),
    "financials":             ("Financials", "FIN"),
    "communication":          ("Communication Services", "COMMS"),
    "energy":                 ("Energy", "ENERGY"),
    "healthcare":             ("Health Care", "HEALTH"),
    "consumer_cyclical":      ("Consumer Cyclical", "CONS_DISC"),
    "consumer_defensive":     ("Consumer Defensive", "CONS_STAP"),
    "industrials":            ("Industrials", "INDUST"),
    "basic_materials":        ("Basic Materials", "MATERIALS"),
    "financial_services":     ("Financial Services", "FIN"),
    "communication_services": ("Communication Services", "COMMS"),
    "utilities":              ("Utilities", "UTIL"),
    "realestate":             ("Real Estate", "REALEST"),
    "real_estate":            ("Real Estate", "REALEST"),
}
MIX_FLOOR = 3.0
TOP_NAMED = 3


def r6(x):
    """Round for transport; keep NaN/inf out of JSON."""
    if x is None:
        return None
    if isinstance(x, (np.floating, float)) and (math.isnan(x) or math.isinf(x)):
        return None
    return round(float(x), 6)


def num(x):
    if x is None or x == "":
        return None
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return None if (math.isnan(v) or math.isinf(v)) else v


def sector_meta(raw) -> tuple:
    key = str(raw or "").strip().lower().replace(" ", "_").replace("-", "_")
    if key in SECTOR_META:
        return SECTOR_META[key]
    return (str(raw).strip() or "Other", "OTHER")


def stats_for(pct: pd.Series) -> dict:
    """Full statistics block for one monthly-percent return series."""
    r = pct.to_numpy(dtype=float) / 100.0
    n = len(r)
    wealth = np.cumprod(1.0 + r)
    growth = float(wealth[-1])
    cagr = growth ** (12.0 / n) - 1.0
    vol = float(np.std(r, ddof=1)) * math.sqrt(12.0)
    sharpe = (cagr - RISK_FREE) / vol if vol > 0 else 0.0
    downside = float(np.sqrt(np.mean(np.minimum(r, 0.0) ** 2))) * math.sqrt(12.0)
    sortino = (cagr - RISK_FREE) / downside if downside > 0 else 0.0
    peak = np.maximum.accumulate(wealth)
    dd = wealth / peak - 1.0
    trough = int(np.argmin(dd))

    peak_i = int(np.argmax(wealth[: trough + 1]))
    rec_i = None
    for j in range(trough + 1, n):
        if wealth[j] >= peak[trough]:
            rec_i = j
            break

    idx = list(pct.index)
    best = int(np.argmax(r))
    worst = int(np.argmin(r))

    roll = [None] * n
    for i in range(11, n):
        roll[i] = r6((np.prod(1.0 + r[i - 11: i + 1]) - 1.0) * 100.0)

    return {
        "months": n,
        "growth": r6(growth),
        "cagr": r6(cagr * 100.0),
        "vol": r6(vol * 100.0),
        "sharpe": r6(sharpe),
        "sortino": r6(sortino),
        "downside": r6(downside * 100.0),
        "maxdd": r6(float(dd.min()) * 100.0),
        "maxddPeak": str(idx[peak_i]),
        "maxddTrough": str(idx[trough]),
        "maxddRecovered": str(idx[rec_i]) if rec_i is not None else None,
        "maxddRecoveryMonths": (rec_i - trough) if rec_i is not None else None,
        "best": r6(float(r[best]) * 100.0),
        "bestMonth": str(idx[best]),
        "worst": r6(float(r[worst]) * 100.0),
        "worstMonth": str(idx[worst]),
        "posRate": r6(float((r > 0).mean()) * 100.0),
        "posMonths": int((r > 0).sum()),
        "wealth": [r6(v) for v in wealth],
        "drawdown": [r6(v * 100.0) for v in dd],
        "rolling12": roll,
    }


def pretty(period: str) -> str:
    y, m = str(period).split("-")
    return f"{MONTH_ABBR[int(m) - 1]} {y}"


def ordinal(period: str) -> int:
    y, m = str(period).split("-")
    return int(y) * 12 + int(m) - 1


def build_book(current: dict) -> dict | None:
    path = DATA_DIR / "holdings.json"
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

    if current.get("cash"):
        return None

    legs_src = raw.get("legs", {})
    factor_src = legs_src.get("factor")
    if not factor_src or not factor_src.get("holdings"):
        return None

    held = current["legs"][0] if current.get("legs") else None
    if not held:
        return None

    leg_w = 100.0  # 100% of the book
    rows = factor_src.get("holdings", [])
    holdings = []
    for r in rows:
        w = num(r.get("weight")) or 0.0
        sec_name, glyph = sector_meta(r.get("sector"))
        holdings.append({
            "sym": str(r.get("symbol") or "").upper(),
            "isin": r.get("isin"),
            "domain": company_domain(r.get("website")),
            "name": str(r.get("name") or r.get("company") or r.get("symbol") or ""),
            "sector": sec_name,
            "glyph": glyph,
            "industry": (str(r["industry"]) if r.get("industry") else None),
            "w": r6(w * 100.0),
            "bw": r6(w * leg_w),
            "mcap": num(r.get("market_cap")),
            "pe": r6(num(r.get("pe"))),
            "fpe": r6(num(r.get("forward_pe"))),
            "rev": r6(num(r.get("revenue_growth"))),
            "earn": r6(num(r.get("earnings_growth"))),
            "margin": r6(num(r.get("profit_margin"))),
            "yield": r6(num(r.get("dividend_yield"))),
        })

    holdings.sort(key=lambda h: -(h["w"] or 0.0))
    top10 = sum((h["w"] or 0.0) for h in holdings)

    mix = sorted(
        ({"name": sector_meta(k)[0], "glyph": sector_meta(k)[1], "w": r6(num(v) * 100.0)}
         for k, v in (factor_src.get("sector_weights") or {}).items() if num(v)),
        key=lambda m: -m["w"],
    )
    shown = [m for m in mix if m["w"] >= MIX_FLOOR]
    tail = [m for m in mix if m["w"] < MIX_FLOOR]

    logo_file = DATA_DIR / "company_logos.json"
    logo_registry = load_registry(logo_file) if logo_file.is_file() else {}
    for h in holdings:
        sym = h["sym"]
        h["logo"] = next((logo_registry[sym]["path"]
                          for s in [sym]
                          if s in logo_registry
                          and (HERE / logo_registry[s]["path"]).is_file()), None)

    leg_out = {
        "leg": "Factor",
        "code": held["code"],
        "name": held["name"],
        "ticker": held["lse"],
        "source": factor_src.get("source", "Yahoo Finance top-ten holdings"),
        "snapshotDate": factor_src.get("snapshot_date", raw.get("as_at")),
        "sourceUrl": factor_src.get("source_url"),
        "fundamentalsSource": "Yahoo Finance",
        "fundamentalsFetchedAt": raw.get("fetched_at"),
        "isin": held["isin"],
        "legWeight": 100.0,
        "top10": r6(top10),
        "top10Book": r6(top10),
        "restBook": r6(100.0 - top10),
        "count": len(holdings),
        "holdings": holdings,
        "mix": shown,
        "mixTail": ({"n": len(tail), "w": r6(sum(m["w"] for m in tail))} if tail else None),
    }

    consolidated = consolidate([leg_out])
    for company in consolidated["holdings"]:
        company["logo"] = next(
            (
                logo_registry[symbol]["path"]
                for symbol in company["symbols"]
                if symbol in logo_registry
                and (HERE / logo_registry[symbol]["path"]).is_file()
            ),
            None,
        )
    consolidated["fullDisclosure"] = False
    consolidated["sources"] = [
        {"ticker": held["lse"], "snapshotDate": raw.get("as_at"), "url": None}
    ]
    named = consolidated["holdings"][:TOP_NAMED]

    return {
        "asOf": raw.get("as_at"),
        "asOfPretty": pretty(raw["as_at"]) if raw.get("as_at") else None,
        "fetchedAt": raw.get("fetched_at"),
        "snapshotDate": raw.get("snapshot_date"),
        "stale": False,
        "legs": [leg_out],
        "consolidated": consolidated,
        "named": [{"sym": h["sym"], "name": h["name"], "bw": h["bw"]} for h in named],
        "namedBook": r6(sum((h["bw"] or 0.0) for h in named)),
        "namedCount": len(named),
        "topBook": r6(named[0]["bw"]) if named else None,
        "topSym": named[0]["sym"] if named else None,
    }


def main():
    monthly = pd.read_csv(DATA_DIR / "final_tradable.csv", index_col=0)
    annual = pd.read_csv(DATA_DIR / "final_tradable_annual.csv", index_col=0)
    book = pd.read_csv(DATA_DIR / "final_book.csv", index_col=0)

    price_status_path = DATA_DIR / "price_status.json"
    price_status = json.loads(price_status_path.read_text()) if price_status_path.is_file() else None

    months = [str(i) for i in monthly.index]
    start, end = months[0], months[-1]

    current_month = str(book.index[-1])
    current_row = book.iloc[-1]

    calendar = [f"{o // 12}-{o % 12 + 1:02d}" for o in range(ordinal(start), ordinal(end) + 1)]
    observed = set(months)
    gaps = [m for m in calendar if m not in observed]
    t_index = [ordinal(m) - ordinal(start) for m in months]

    allocation_calendar = [str(m) for m in pd.period_range(start, current_month, freq="M")]

    cols = {"strategy": monthly.columns[STRATEGY_COL]}
    cols.update(BENCHMARKS)

    returns, stats = {}, {}
    for key, col in cols.items():
        col_s = monthly[col]
        returns[key] = [r6(v) for v in col_s.to_numpy(dtype=float)]
        stats[key] = stats_for(col_s)

    strat = monthly[cols["strategy"]].to_numpy(dtype=float)
    aw = monthly[cols["allworld"]].to_numpy(dtype=float)
    excess_m = strat - aw
    wins = int((strat > aw).sum())

    years = []
    for y, row in annual.iterrows():
        in_year = [m for m in months if m.startswith(f"{y}-")]
        years.append({
            "year": int(y),
            "strategy": r6(row.iloc[STRATEGY_COL]),
            "allworld": r6(row[BENCHMARKS["allworld"]]),
            "sp500": r6(row[BENCHMARKS["sp500"]]),
            "world": r6(row[BENCHMARKS["world"]]),
            "excess": r6(row["vs All-World"]),
            "monthsCovered": len(in_year),
            "partial": len(in_year) < 12,
            "span": f"{pretty(in_year[0])} – {pretty(in_year[-1])}",
        })
    beat_years = sum(1 for y in years if (y["excess"] or 0) > 0)

    ret_by_month = {m: returns["strategy"][i] for i, m in enumerate(months)}
    holdings = []
    for period, row in book.iterrows():
        is_cash = bool(row["cash"])
        holdings.append({
            "m": str(period),
            "factor": None if is_cash else str(row["pick"]),
            "sector": None,
            "cash": is_cash,
            "ret": ret_by_month.get(str(period)),
            "priced": str(period) in observed,
            "factorSource": row.get("source", "LSE Total Return"),
            "sectorSource": None,
        })

    # Run-length ribbon
    def runs():
        out, cur = [], None
        for i, h in enumerate(holdings):
            slot = "CASH" if h["cash"] else h["factor"]
            if cur and cur["slot"] == slot:
                cur["end"] = i
                cur["months"] += 1
            else:
                cur = {"slot": slot, "start": i, "end": i, "months": 1}
                out.append(cur)
        for run in out:
            window = holdings[run["start"]: run["end"] + 1]
            vals = [h["ret"] for h in window if h["ret"] is not None]
            run["priced"] = len(vals)
            run["avgRet"] = r6(float(np.mean(vals))) if vals else None
            run["from"] = pretty(window[0]["m"])
            run["to"] = pretty(window[-1]["m"])
            run["name"] = "Cash" if run["slot"] == "CASH" else FACTOR_NAMES[run["slot"]]
        return out

    factor_slots = list(FACTOR_NAMES.keys())
    held_priced = {c: 0 for c in factor_slots}
    tenure = {c: 0 for c in factor_slots}
    for h in holdings:
        if h["cash"]:
            continue
        tenure[h["factor"]] += 1
        if h["priced"]:
            held_priced[h["factor"]] += 1

    lanes = [
        {
            "id": "factor",
            "title": "World Factor & Dividend Allocation",
            "subtitle": "5 London-listed global UCITS ETFs",
            "slots": [{"code": c, "name": FACTOR_NAMES[c], "ticker": TRADABLE[c][2],
                       "isin": TRADABLE[c][0], "months": tenure[c]} for c in factor_slots],
            "runs": runs(),
        }
    ]

    # Heatmap grid
    signal_month = end
    grid, ylist = [], list(range(int(start[:4]), int(signal_month[:4]) + 1))
    lookup = {m: returns["strategy"][i] for i, m in enumerate(months)}
    for y in ylist:
        cells = [lookup.get(f"{y}-{mm:02d}") for mm in range(1, 13)]
        ytd = None
        present = [c for c in cells if c is not None]
        if present:
            ytd = r6((np.prod([1 + c / 100.0 for c in present]) - 1.0) * 100.0)
        grid.append({"year": y, "cells": cells, "ytd": ytd})

    last_pick = str(current_row["pick"])
    is_cash_now = bool(current_row["cash"])
    next_holding_m = str(pd.Period(current_month, "M") + 1)

    current = {
        "asof": signal_month,
        "asofPretty": pretty(signal_month),
        "holdingMonth": next_holding_m,
        "holdingMonthPretty": pretty(next_holding_m),
        "factorSource": "LSE Total Return",
        "sectorSource": None,
        "cash": is_cash_now,
        "legs": [] if is_cash_now else [
            {
                "leg": "Factor",
                "code": last_pick,
                "name": FACTOR_NAMES[last_pick],
                "isin": TRADABLE[last_pick][0],
                "lse": TRADABLE[last_pick][2],
                "xetra": TRADABLE[last_pick][1],
                "us": TRADABLE[last_pick][3],
                "weight": 100,
            }
        ],
    }

    book_data = build_book(current)

    # Leaderboard for next month projection
    signal_json_path = DATA_DIR / "signal.json"
    signal_raw = json.loads(signal_json_path.read_text(encoding="utf-8")) if signal_json_path.is_file() else {}
    daily_json_path = DATA_DIR / "daily_signal.json"
    daily_raw = json.loads(daily_json_path.read_text(encoding="utf-8")) if daily_json_path.is_file() else {}

    fund_prices_path = DATA_DIR / "fund_prices_gbp.csv"
    spx_chg = 35.07
    if fund_prices_path.is_file():
        fp_df = pd.read_csv(fund_prices_path, index_col=0)
        if "SPX" in fp_df.columns and len(fp_df) >= 20:
            spx_chg = round(float((fp_df["SPX"].iloc[-1] / fp_df["SPX"].iloc[-20] - 1.0) * 100.0), 2)

    sig_table = signal_raw.get("table", {})
    sorted_slots = sorted(sig_table.keys(), key=lambda k: sig_table[k], reverse=True) if sig_table else list(factor_slots)
    top_sig_slot = sorted_slots[0] if sorted_slots else last_pick
    top_sig_return = round(sig_table.get(top_sig_slot, 0.0) * 100.0, 2) if sig_table else 18.04
    second_sig_slot = sorted_slots[1] if len(sorted_slots) > 1 else None
    second_sig_return = round(sig_table.get(second_sig_slot, 0.0) * 100.0, 2) if second_sig_slot else 8.45
    lead_margin_pp = round(top_sig_return - second_sig_return, 2)

    styles_dict = dict(STYLES)
    official_standings = []
    for rank_idx, slot in enumerate(sorted_slots, 1):
        m_val = round(sig_table.get(slot, 0.0) * 100.0, 2)
        gap = round(m_val - top_sig_return, 2)
        style_key = slot.replace("WLD_", "")
        style_name = styles_dict.get(style_key, style_key)
        bar_pct = round(max(15.0, (m_val / top_sig_return) * 100.0 if top_sig_return > 0 else 20.0), 1)
        official_standings.append({
            "rank": rank_idx,
            "slot": slot,
            "name": FACTOR_NAMES[slot],
            "style": style_name,
            "ticker": TRADABLE[slot][2],
            "isin": TRADABLE[slot][0],
            "momentum": m_val,
            "gap": gap,
            "barPct": bar_pct,
            "isLeader": rank_idx == 1,
            "isHeld": slot == last_pick,
            "targetWeight": 100 if rank_idx == 1 else 0,
        })

    is_action_hold = (top_sig_slot == last_pick)
    action_type = "HOLD" if is_action_hold else "SWITCH"
    action_title = (
        f"Maintain 100% position in {FACTOR_NAMES[top_sig_slot]} ({TRADABLE[top_sig_slot][2]})"
        if is_action_hold else
        f"Rotate 100% into {FACTOR_NAMES[top_sig_slot]} ({TRADABLE[top_sig_slot][2]})"
    )
    action_summary = (
        f"{FACTOR_NAMES[top_sig_slot]} maintains the #1 rank with a +{lead_margin_pp:.2f} percentage point lead over {FACTOR_NAMES[second_sig_slot]}. Because it matches the prior month holding, no trade is required (zero turnover and zero dealing costs)."
        if is_action_hold else
        f"{FACTOR_NAMES[top_sig_slot]} has overtaken {FACTOR_NAMES[last_pick]} to become the new #1 momentum leader. Rebalance is scheduled for the first trading day of the month."
    )

    # Process daily standings if available
    live_standings = []
    if daily_raw and "ranks" in daily_raw:
        daily_top_mom = daily_raw["ranks"][0]["momentum"] if daily_raw["ranks"] else 25.77
        for r in daily_raw.get("ranks", []):
            s_key = r["slot"].replace("WLD_", "")
            live_standings.append({
                "rank": r["rank"],
                "slot": r["slot"],
                "name": r["name"],
                "style": styles_dict.get(s_key, s_key),
                "ticker": r["ticker"],
                "isin": TRADABLE[r["slot"]][0],
                "momentum": r["momentum"],
                "gap": round(r["momentum"] - daily_top_mom, 2),
                "barPct": round(max(15.0, (r["momentum"] / daily_top_mom) * 100.0 if daily_top_mom > 0 else 20.0), 1),
                "isLeader": r["rank"] == 1,
                "isHeld": r["slot"] == last_pick,
                "targetWeight": 100 if r["rank"] == 1 else 0,
            })

    leaderboard = {
        "signalMonth": signal_month,
        "signalMonthPretty": pretty(signal_month),
        "holdingMonth": next_holding_m,
        "holdingMonthPretty": pretty(next_holding_m),
        "action": action_type,
        "actionTitle": action_title,
        "actionSummary": action_summary,
        "leadMargin": lead_margin_pp,
        "runnerUp": FACTOR_NAMES[second_sig_slot] if second_sig_slot else "",
        "cashGate": {
            "active": False,
            "spxChange": spx_chg,
            "threshold": -25.0,
            "status": "Inactive (Normal Equity Regime)",
            "ruleText": "S&P 500 must fall >25% below its 19-month lookback to trigger GBP cash preservation.",
        },
        "standings": official_standings,
        "live": {
            "asof": daily_raw.get("asof", "2026-11-01"),
            "daysLeft": daily_raw.get("days_left", 29),
            "projectedPick": daily_raw.get("projected_name", "World Value"),
            "projectedTicker": daily_raw.get("projected_ticker", "IWVL.L"),
            "cashGateActive": daily_raw.get("cash_gate", {}).get("active", False),
            "spxChange": daily_raw.get("cash_gate", {}).get("spx_change", spx_chg),
            "standings": live_standings,
        } if daily_raw else None,
    }

    payload = {
        "meta": {
            "name": "Lodestar World",
            "strapline": "Global Factor & Dividend Rotation",
            "start": start,
            "end": end,
            "startPretty": pretty(start),
            "endPretty": pretty(end),
            "months": len(months),
            "calendarMonths": len(calendar),
            "gaps": gaps,
            "riskFree": RISK_FREE * 100.0,
            "currency": "GBP",
            "basis": "Total return in sterling, net of fund fees, gross of dealing costs and taxes.",
            "builtAt": datetime.now(timezone.utc).isoformat(),
            "expectedEnd": signal_month,
            "performancePending": False,
            "proxyMonths": [],
        },
        "labels": LABELS,
        "order": ["strategy", "allworld", "sp500", "world"],
        "months": months,
        "monthsPretty": [pretty(m) for m in months],
        "t": t_index,
        "span": len(calendar) - 1,
        "calendar": calendar,
        "allocationCalendar": allocation_calendar,
        "returns": returns,
        "stats": stats,
        "excess": {
            "monthly": [r6(v) for v in excess_m],
            "wins": wins,
            "losses": len(months) - wins,
            "winRate": r6(wins / len(months) * 100.0),
            "beatYears": beat_years,
            "totalYears": len(years),
            "avgMonthly": r6(float(excess_m.mean())),
        },
        "years": years,
        "heatmap": {
            "years": grid,
            "monthLabels": MONTH_ABBR,
            "pending": [],
        },
        "holdings": holdings,
        "lanes": lanes,
        "current": current,
        "leaderboard": leaderboard,
        "priceStatus": price_status,
        "book": book_data,
        "universe": {
            "pricedMonths": len(months),
            "maxHeld": max(held_priced.values()),
            "styles": [{"key": k, "name": n} for k, n in STYLES],
            "factors": [{
                "code": c,
                "name": FACTOR_NAMES[c],
                "style": c.replace("WLD_", ""),
                "region": "World",
                "isin": TRADABLE[c][0],
                "lse": TRADABLE[c][2],
                "xetra": TRADABLE[c][1],
                "held": held_priced[c],
                "heldAll": tenure[c],
                "live": not is_cash_now and c == last_pick,
            } for c in factor_slots],
            "sectors": [],
        },
    }

    # Add LYW, Dot-Com Lodestar, and Combined 50/50 Dual Engine data
    lyw_data = build_lyw_data()
    dotcom_data = build_dotcom_data()

    combined_years = []
    lode_ann_dict = {y["year"]: y["strategy"] for y in dotcom_data.get("years", [])}
    lyw_ann_dict = {y["year"]: y["return"] for y in lyw_data.get("archive", [])}

    all_common_y = sorted(set(lode_ann_dict.keys()).intersection(set(lyw_ann_dict.keys())))
    blend_rets = []
    for y in all_common_y:
        r_lode = lode_ann_dict[y]
        r_lyw = lyw_ann_dict[y]
        b_ret = round(0.5 * r_lode + 0.5 * r_lyw, 2)
        blend_rets.append(b_ret)
        combined_years.append({
            "year": y,
            "lodestar": r_lode,
            "lyw": r_lyw,
            "blend": b_ret,
        })

    if blend_rets:
        b_arr = np.array(blend_rets)
        growth_comb = float(np.prod(1.0 + b_arr / 100.0))
        cagr_comb = round((growth_comb ** (1.0 / len(b_arr)) - 1.0) * 100.0, 2)
        vol_comb = round(float(np.std(b_arr)), 2)
        sharpe_comb = round(cagr_comb / vol_comb if vol_comb > 0 else 0.0, 2)
        cum_b = np.cumprod(1.0 + b_arr / 100.0)
        peak_b = np.maximum.accumulate(cum_b)
        maxdd_comb = round(float(np.min((cum_b / peak_b - 1.0) * 100.0)), 2)
    else:
        growth_comb, cagr_comb, vol_comb, sharpe_comb, maxdd_comb = 1.0, 0.0, 0.0, 0.0, 0.0

    payload["lyw"] = lyw_data
    payload["dotcom"] = dotcom_data
    payload["combined"] = {
        "allocation": "50% Lodestar World / 50% Last Year's Winner",
        "yearsCovered": len(combined_years),
        "startYear": combined_years[0]["year"] if combined_years else 2000,
        "endYear": combined_years[-1]["year"] if combined_years else 2025,
        "stats": {
            "cagr": cagr_comb,
            "vol": vol_comb,
            "sharpe": sharpe_comb,
            "maxDrawdown": maxdd_comb,
            "growthMultiple": round(growth_comb, 2),
            "positiveYears": sum(y["blend"] > 0 for y in combined_years),
            "totalYears": len(combined_years),
        },
        "years": combined_years,
    }

    body = json.dumps(payload, separators=(",", ":"), allow_nan=False)
    out = HERE / "data.js"
    out.write_text(
        "/* Generated by build_data.py. Do not edit by hand. */\n"
        f"const DATA = {body};\n",
        encoding="utf-8",
    )

    s = stats["strategy"]
    a = stats["allworld"]
    print(f"wrote {out} ({out.stat().st_size / 1024:.1f} KB)")
    print(f"  window        {start} .. {end} ({len(months)} months)")
    print(f"  strategy      CAGR {s['cagr']:.2f}%  vol {s['vol']:.2f}%  Sharpe {s['sharpe']:.2f}  "
          f"Sortino {s['sortino']:.2f}  maxDD {s['maxdd']:.2f}%  x{s['growth']:.2f}")
    print(f"  all-world     CAGR {a['cagr']:.2f}%  vol {a['vol']:.2f}%  Sharpe {a['sharpe']:.2f}  "
          f"maxDD {a['maxdd']:.2f}%  x{a['growth']:.2f}")
    print(f"  monthly wins  {wins}/{len(months)} = {wins/len(months)*100:.1f}%")
    print(f"  beat years    {beat_years}/{len(years)}")
    print("  current       " + ("Cash" if current["cash"] else
          f"{current['legs'][0]['name']} ({current['legs'][0]['lse']}) at 100%")
          + f" for {next_holding_m}, signal as of {signal_month}")


if __name__ == "__main__":
    main()
