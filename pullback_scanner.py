#!/usr/bin/env python3
"""
Weekly (1W) Simple Pullback & Pullback XL Scanner + 10-Year Backtest Engine.

Published at: https://soylee22.github.io/lodestar-world/pullback.html
Refreshed automatically via GitHub Actions (.github/workflows/pullback-scanner.yml and daily.yml).
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yfinance as yf

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "data"
OUT_JSON = DATA_DIR / "pullback_scan.json"
OUT_HTML = HERE / "pullback.html"

ETF_UNIVERSE: list[tuple[str, str, str, str, str]] = [
    ("VUAG", "VUAG.L", "LSE:VUAG", "Vanguard S&P 500 Acc (GBP)", "Core Index"),
    ("CNX1", "CNX1.L", "LSE:CNX1", "iShares Nasdaq 100 Acc (GBP)", "Tech / Nasdaq"),
    ("LQQ.PA", "LQQ.PA", "EURONEXT:LQQ", "Amundi Nasdaq-100 2x Leveraged (EUR)", "Leveraged"),
    ("SMGB", "SMGB.L", "LSE:SMGB", "VanEck Semiconductor Acc (GBP)", "Semiconductors"),
    ("IUMO", "IUMO.L", "LSE:IUMO", "iShares Edge MSCI USA Momentum (GBP)", "Factor"),
    ("SWDA", "SWDA.L", "LSE:SWDA", "iShares Core MSCI World Acc (GBP)", "Core Index"),
    ("SSLN", "SSLN.L", "LSE:SSLN", "iShares Physical Silver ETC (GBP)", "Precious Metals"),
    ("SGLN", "SGLN.L", "LSE:SGLN", "iShares Physical Gold ETC (GBP)", "Precious Metals"),
    ("LQQ3", "LQQ3.L", "LSE:LQQ3", "WisdomTree Nasdaq 100 3x Daily (GBP)", "Leveraged"),
    ("VUKG", "VUKG.L", "LSE:VUKG", "Vanguard FTSE 100 Acc (GBP)", "Core Index"),
    ("VFEG", "VFEG.L", "LSE:VFEG", "Vanguard FTSE Emerging Markets Acc (GBP)", "Regional"),
    ("VDPG", "VDPG.L", "LSE:VDPG", "Vanguard FTSE Dev Asia Pac ex-Japan Acc (GBP)", "Regional"),
    ("VEUA", "VEUA.L", "LSE:VEUA", "Vanguard FTSE Developed Europe Acc (GBP)", "Regional"),
    ("VJPB", "VJPB.L", "LSE:VJPB", "Vanguard FTSE Japan Acc (GBP)", "Regional"),
    ("VAGS", "VAGS.L", "LSE:VAGS", "Vanguard Global Aggregate Bond Hedged Acc (GBP)", "Bonds"),
    ("VNRG", "VNRG.L", "LSE:VNRG", "Vanguard FTSE North America Acc (GBP)", "Core Index"),
    ("VHYL", "VHYL.L", "LSE:VHYL", "Vanguard FTSE All-World High Dividend Yield (GBP)", "Dividend"),
    ("TDGB", "TDGB.L", "LSE:TDGB", "VanEck Morningstar Dev Markets Dividend Leaders (GBP)", "Dividend"),
    ("IITU", "IITU.L", "LSE:IITU", "iShares S&P 500 IT Sector (GBP)", "Tech / Nasdaq"),
    ("INRG", "INRG.L", "LSE:INRG", "iShares Global Clean Energy (GBP)", "Thematic"),
    ("SEMI", "SEMI.L", "LSE:SEMI", "iShares MSCI Global Semiconductors (GBP)", "Semiconductors"),
    ("QWTM", "QWTM.L", "LSE:QWTM", "Xtrackers MSCI World Momentum (GBP)", "Factor"),
    ("IUKD", "IUKD.L", "LSE:IUKD", "iShares UK Dividend (GBP)", "Dividend"),
    ("DGRG", "DGRG.L", "LSE:DGRG", "WisdomTree Global Quality Dividend Growth (GBP)", "Dividend"),
    ("XDAX", "XDAX.L", "LSE:XDAX", "Xtrackers DAX UCITS ETF (GBP)", "Regional"),
    ("MWEP", "MWEP.L", "LSE:MWEP", "Xtrackers MSCI World Equal Weight (GBP)", "Factor"),
    ("XWHS", "XWHS.L", "LSE:XWHS", "Xtrackers MSCI World Health Care (GBP)", "Sector"),
    ("HPRO", "HPRO.L", "LSE:HPRO", "HSBC FTSE EPRA NAREIT Developed Property (GBP)", "Sector"),
    ("XWES", "XWES.L", "LSE:XWES", "Xtrackers MSCI World Energy (GBP)", "Sector"),
    ("XWFS", "XWFS.L", "LSE:XWFS", "Xtrackers MSCI World Financials (GBP)", "Sector"),
    ("XWCS", "XWCS.L", "LSE:XWCS", "Xtrackers MSCI World Consumer Staples (GBP)", "Sector"),
]

STOCK_UNIVERSE: list[tuple[str, str, str, str, str]] = [
    ("NVDA", "NVDA", "NASDAQ:NVDA", "Nvidia", "US Mag 7"),
    ("AAPL", "AAPL", "NASDAQ:AAPL", "Apple", "US Mag 7"),
    ("MSFT", "MSFT", "NASDAQ:MSFT", "Microsoft", "US Mag 7"),
    ("GOOGL", "GOOGL", "NASDAQ:GOOGL", "Alphabet", "US Mag 7"),
    ("AMZN", "AMZN", "NASDAQ:AMZN", "Amazon", "US Mag 7"),
    ("META", "META", "NASDAQ:META", "Meta Platforms", "US Mag 7"),
    ("TSLA", "TSLA", "NASDAQ:TSLA", "Tesla", "US Mag 7"),
    ("JPM", "JPM", "NYSE:JPM", "JPMorgan Chase", "US Compounder"),
    ("COST", "COST", "NASDAQ:COST", "Costco Wholesale", "US Compounder"),
    ("WMT", "WMT", "NYSE:WMT", "Walmart", "US Compounder"),
    ("BRK-B", "BRK-B", "NYSE:BRK.B", "Berkshire Hathaway", "US Compounder"),
    ("MA", "MA", "NYSE:MA", "Mastercard", "US Compounder"),
    ("V", "V", "NYSE:V", "Visa", "US Compounder"),
    ("LLY", "LLY", "NYSE:LLY", "Eli Lilly", "US Compounder"),
    ("ASML", "ASML.AS", "EURONEXT:ASML", "ASML Holding (EUR)", "Europe Semiconductor"),
    ("RR.L", "RR.L", "LSE:RR.", "Rolls-Royce Holdings", "UK Blue Chip"),
    ("AZN.L", "AZN.L", "LSE:AZN", "AstraZeneca", "UK Blue Chip"),
    ("BATS.L", "BATS.L", "LSE:BATS", "British American Tobacco", "UK Blue Chip"),
    ("BA.L", "BA.L", "LSE:BA.", "BAE Systems", "UK Blue Chip"),
    ("BP.L", "BP.L", "LSE:BP.", "BP", "UK Blue Chip"),
    ("LGEN.L", "LGEN.L", "LSE:LGEN", "Legal & General", "UK Blue Chip"),
    ("AV.L", "AV.L", "LSE:AV.", "Aviva", "UK Blue Chip"),
    ("RIO.L", "RIO.L", "LSE:RIO", "Rio Tinto", "UK Blue Chip"),
]


def evaluate_bar(
    close: pd.Series,
    sma14: pd.Series,
    sma20: pd.Series,
    sma50: pd.Series,
    sma200: pd.Series,
    z20: pd.Series,
    roc14: pd.Series,
    idx: int,
    require_200: bool = False,
) -> dict[str, Any]:
    c = float(close.iloc[idx])
    c_prev = float(close.iloc[idx - 1])
    s14_prev = float(sma14.iloc[idx - 1])
    s20 = float(sma20.iloc[idx])
    s50 = float(sma50.iloc[idx])
    s200 = float(sma200.iloc[idx]) if not np.isnan(sma200.iloc[idx]) else np.nan
    z = float(z20.iloc[idx])
    r14 = float(roc14.iloc[idx])
    r14_prev = float(roc14.iloc[idx - 1])

    below_mas = (c < s20) and (c < s50) and (c_prev < s14_prev)
    neg_roc = (r14 < 0.0) or (r14_prev < 0.0)
    has_200 = len(close) >= 200
    if require_200 and has_200:
        trend_pass = (not np.isnan(s200)) and (c > s200)
    else:
        trend_pass = True

    if below_mas and neg_roc and trend_pass:
        if z <= -2.40:
            state = "PULLBACK XL"
        elif z <= -1.35:
            state = "PULLBACK"
        elif z <= -0.95:
            state = "NEAR (-0.95 to -1.35 SD)"
        else:
            state = "BELOW 50 SMA"
    elif z <= -1.35 and neg_roc and (c >= s50) and trend_pass:
        state = "ABOVE 50 SMA"
    elif z <= -1.35 and neg_roc and not trend_pass:
        state = "BELOW 200 SMA"
    else:
        state = "NONE"

    return {
        "date": close.index[idx].strftime("%Y-%m-%d"),
        "price": c,
        "z20": z,
        "roc14": r14,
        "vs_sma50": (c / s50 - 1.0) * 100.0 if not np.isnan(s50) else np.nan,
        "vs_sma200": (c / s200 - 1.0) * 100.0 if not np.isnan(s200) else np.nan,
        "state": state,
    }


def analyze_series(
    label: str,
    yf_sym: str,
    tv_sym: str,
    name: str,
    category: str,
    group_kind: str,
    close: pd.Series,
) -> dict[str, Any]:
    close = close.dropna()
    sma14 = close.rolling(14).mean()
    sma20 = close.rolling(20).mean()
    sd20 = close.rolling(20).std(ddof=0)
    z20 = (close - sma20) / sd20
    sma50 = close.rolling(50).mean()
    sma200 = close.rolling(200).mean()
    roc14 = 100.0 * (close / close.shift(14) - 1.0)

    start_idx = max(50, len(close) - 522)

    ep_pb = False
    ep_xl = False
    signals_pb: list[dict[str, Any]] = []
    signals_xl: list[dict[str, Any]] = []
    recent_episode_signal = "NONE"
    recent_episode_date = "-"
    recent_episode_weeks_ago = 999

    for i in range(start_idx, len(close)):
        z = float(z20.iloc[i])
        if np.isnan(z):
            continue
        if z >= 0.25:
            ep_pb = False
            ep_xl = False

        bar = evaluate_bar(close, sma14, sma20, sma50, sma200, z20, roc14, i, require_200=False)
        is_xl = bar["state"] == "PULLBACK XL"
        is_pb = bar["state"] in ("PULLBACK", "PULLBACK XL")

        c = bar["price"]
        fwd_6m = (float(close.iloc[i + 26]) / c - 1.0) * 100.0 if i + 26 < len(close) else np.nan
        fwd_1y = (float(close.iloc[i + 52]) / c - 1.0) * 100.0 if i + 52 < len(close) else np.nan
        fwd_2y = (float(close.iloc[i + 104]) / c - 1.0) * 100.0 if i + 104 < len(close) else np.nan
        win_3m = close.iloc[i : min(i + 14, len(close))]
        dd_3m = (float(win_3m.min()) / c - 1.0) * 100.0

        weeks_ago = (len(close) - 1) - i
        sig_entry = {
            "date": bar["date"],
            "price": c,
            "z20": z,
            "ret_6m": fwd_6m,
            "ret_1y": fwd_1y,
            "ret_2y": fwd_2y,
            "dd_3m": dd_3m,
            "weeks_ago": weeks_ago,
        }

        if is_pb and not ep_pb:
            ep_pb = True
            signals_pb.append(sig_entry)
            if weeks_ago <= 4 and recent_episode_signal != "PULLBACK XL":
                recent_episode_signal = "PULLBACK"
                recent_episode_date = bar["date"]
                recent_episode_weeks_ago = weeks_ago

        if is_xl and not ep_xl:
            ep_xl = True
            signals_xl.append(sig_entry)
            if weeks_ago <= 4:
                recent_episode_signal = "PULLBACK XL"
                recent_episode_date = bar["date"]
                recent_episode_weeks_ago = weeks_ago

    def summarize(sig_list: list[dict[str, Any]]) -> dict[str, Any]:
        if not sig_list:
            return {
                "count": 0,
                "count_1y": 0,
                "med_6m": None,
                "med_1y": None,
                "med_2y": None,
                "win_1y": None,
                "med_dd_3m": None,
            }
        df_s = pd.DataFrame(sig_list)
        s1y = df_s["ret_1y"].dropna()
        s6m = df_s["ret_6m"].dropna()
        s2y = df_s["ret_2y"].dropna()
        sdd = df_s["dd_3m"].dropna()
        return {
            "count": int(len(df_s)),
            "count_1y": int(len(s1y)),
            "med_6m": float(s6m.median()) if len(s6m) else None,
            "med_1y": float(s1y.median()) if len(s1y) else None,
            "med_2y": float(s2y.median()) if len(s2y) else None,
            "win_1y": float((s1y > 0).mean() * 100.0) if len(s1y) else None,
            "med_dd_3m": float(sdd.median()) if len(sdd) else None,
        }

    pb_stats = summarize(signals_pb)
    xl_stats = summarize(signals_xl)

    closed_bar = evaluate_bar(close, sma14, sma20, sma50, sma200, z20, roc14, -2, require_200=False)
    live_bar = evaluate_bar(close, sma14, sma20, sma50, sma200, z20, roc14, -1, require_200=False)

    win_all = pb_stats["win_1y"]
    med_all = pb_stats["med_1y"]
    win_xl = xl_stats["win_1y"]
    med_xl = xl_stats["med_1y"]

    if win_all is not None and win_all >= 80.0 and (med_all or 0) >= 12.0:
        tier = "Tier 1: Buy All Pullbacks & XL"
        tier_code = 1
    elif win_xl is not None and win_xl >= 80.0 and (med_xl or 0) >= 15.0:
        tier = "Tier 2: Buy XL Only"
        tier_code = 2
    elif win_all is not None and win_all >= 70.0 and (med_all or 0) >= 9.0:
        tier = "Tier 3: Selective / Moderate"
        tier_code = 3
    elif pb_stats["count_1y"] < 2:
        tier = "Short History (<2 completed 1Y signals)"
        tier_code = 3
    else:
        tier = "Tier 4: Avoid (Low Win Rate / Value Trap)"
        tier_code = 4

    return {
        "label": label,
        "yf_sym": yf_sym,
        "tv_sym": tv_sym,
        "name": name,
        "category": category,
        "group_kind": group_kind,
        "weeks": int(len(close)),
        "closed_date": closed_bar["date"],
        "closed_state": closed_bar["state"],
        "closed_z20": closed_bar["z20"],
        "closed_roc14": closed_bar["roc14"],
        "live_date": live_bar["date"],
        "live_price": live_bar["price"],
        "live_state": live_bar["state"],
        "live_z20": live_bar["z20"],
        "live_roc14": live_bar["roc14"],
        "vs_sma50": live_bar["vs_sma50"],
        "vs_sma200": live_bar["vs_sma200"],
        "recent_episode_signal": recent_episode_signal,
        "recent_episode_date": recent_episode_date,
        "recent_episode_weeks_ago": recent_episode_weeks_ago,
        "pb_stats": pb_stats,
        "xl_stats": xl_stats,
        "tier": tier,
        "tier_code": tier_code,
    }


def render_html(records: list[dict[str, Any]], out_path: Path) -> None:
    now_str = dt.datetime.now(dt.timezone.utc).strftime("%d %b %Y · %H:%M UTC")
    data_json = json.dumps(records)

    active_xl = sum(
        1
        for r in records
        if (r["closed_state"] == "PULLBACK XL" or r["live_state"] == "PULLBACK XL" or r["recent_episode_signal"] == "PULLBACK XL")
        and r["tier_code"] in (1, 2)
    )
    active_pb = sum(
        1
        for r in records
        if (r["closed_state"].startswith("PULLBACK") or r["live_state"].startswith("PULLBACK") or r["recent_episode_signal"] != "NONE")
        and r["tier_code"] in (1, 2)
    )
    tier1_count = sum(1 for r in records if r["tier_code"] == 1)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Simple Pullback 1W Scanner | Lodestar Institutional Telemetry</title>
<style>
  :root {{
    --bg: #0b121c;
    --surface: #111b29;
    --surface-2: #162234;
    --surface-hover: #1b2a40;
    --ink: #e8eef7;
    --muted: #8b9bb4;
    --border: #213249;
    --teal: #2dd4bf;
    --gold: #e8c070;
    --coral: #ff687b;
    --blue: #4f9cf9;
    --mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    --sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Inter, Roboto, sans-serif;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    font-family: var(--sans);
    background: var(--bg);
    color: var(--ink);
    margin: 0;
    padding: 0;
  }}
  .topbar {{
    background: #080e16;
    border-bottom: 1px solid var(--border);
    padding: 12px 28px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 14px;
    position: sticky;
    top: 0;
    z-index: 50;
  }}
  .brand {{
    display: flex;
    align-items: center;
    gap: 12px;
    font-weight: 700;
    font-size: 15px;
    letter-spacing: -0.01em;
  }}
  .brand-pill {{
    background: rgba(232,192,112,0.16);
    color: var(--gold);
    border: 1px solid rgba(232,192,112,0.45);
    padding: 3px 9px;
    border-radius: 999px;
    font-family: var(--mono);
    font-size: 11px;
  }}
  .nav-links {{
    display: flex;
    gap: 10px;
    align-items: center;
    flex-wrap: wrap;
  }}
  .nav-link {{
    color: var(--muted);
    text-decoration: none;
    font-size: 13px;
    padding: 6px 12px;
    border-radius: 6px;
    border: 1px solid transparent;
    transition: all 0.15s;
  }}
  .nav-link:hover {{
    color: var(--ink);
    background: var(--surface);
  }}
  .nav-link.active {{
    color: var(--gold);
    background: rgba(232,192,112,0.1);
    border-color: rgba(232,192,112,0.35);
    font-weight: 600;
  }}
  .wrap {{
    max-width: 1440px;
    margin: 0 auto;
    padding: 28px;
  }}
  .hero {{
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    flex-wrap: wrap;
    gap: 20px;
    margin-bottom: 22px;
  }}
  h1 {{
    margin: 0 0 6px 0;
    font-size: 26px;
    letter-spacing: -0.02em;
  }}
  .sub {{
    color: var(--muted);
    font-size: 13.5px;
    margin: 0;
  }}
  .kpis {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
    gap: 14px;
    margin-bottom: 22px;
  }}
  .kpi {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 15px 18px;
  }}
  .kpi .k {{
    font-family: var(--mono);
    font-size: 11px;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }}
  .kpi .v {{
    font-size: 24px;
    font-weight: 700;
    margin-top: 5px;
    font-variant-numeric: tabular-nums;
  }}
  .kpi .s {{
    font-size: 12px;
    color: var(--muted);
    margin-top: 3px;
  }}
  .controls {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
    margin-bottom: 16px;
  }}
  .btn-group {{
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }}
  button.flt {{
    background: var(--surface);
    color: var(--ink);
    border: 1px solid var(--border);
    padding: 8px 14px;
    border-radius: 7px;
    cursor: pointer;
    font-size: 13px;
    transition: all 0.15s;
  }}
  button.flt:hover {{
    background: var(--surface-2);
  }}
  button.flt.active {{
    background: rgba(45,212,191,0.14);
    border-color: var(--teal);
    color: var(--teal);
    font-weight: 600;
  }}
  input.search {{
    background: var(--surface);
    color: var(--ink);
    border: 1px solid var(--border);
    padding: 8px 14px;
    border-radius: 7px;
    font-size: 13px;
    min-width: 240px;
  }}
  .table-wrap {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    overflow-x: auto;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
  }}
  th, td {{
    padding: 10px 12px;
    text-align: left;
    border-bottom: 1px solid var(--border);
    white-space: nowrap;
  }}
  th {{
    background: #0d1520;
    color: var(--muted);
    font-family: var(--mono);
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    cursor: pointer;
    user-select: none;
  }}
  th:hover {{ color: var(--ink); }}
  tr:hover {{ background: var(--surface-hover); }}
  .badge {{
    display: inline-block;
    padding: 3px 8px;
    border-radius: 4px;
    font-family: var(--mono);
    font-weight: 700;
    font-size: 11px;
  }}
  .xl {{ background: rgba(232,192,112,0.18); color: var(--gold); border: 1px solid var(--gold); }}
  .pb {{ background: rgba(45,212,191,0.16); color: var(--teal); border: 1px solid var(--teal); }}
  .near {{ background: rgba(255,104,123,0.14); color: var(--coral); border: 1px solid rgba(255,104,123,0.35); }}
  .none {{ color: var(--muted); font-family: var(--mono); font-size: 11.5px; }}
  .t1 {{ color: var(--teal); font-weight: 600; }}
  .t2 {{ color: var(--gold); font-weight: 600; }}
  .t3 {{ color: var(--blue); }}
  .t4 {{ color: var(--coral); }}
  .mono {{ font-family: var(--mono); font-variant-numeric: tabular-nums; }}
  a.tv-link {{
    color: var(--ink);
    text-decoration: none;
    font-weight: 700;
    font-family: var(--mono);
  }}
  a.tv-link:hover {{ color: var(--teal); text-decoration: underline; }}
</style>
</head>
<body>
<header class="topbar">
  <div class="brand">
    <span>🎯 Simple Pullback 1W Scanner</span>
    <span class="brand-pill">SMR 14 / 20 · 1W SNIPE MODE</span>
  </div>
  <nav class="nav-links">
    <a class="nav-link" href="./index.html">← Back to Lodestar World &amp; LYW</a>
    <a class="nav-link active" href="./pullback.html">Simple Pullback 1W Scanner</a>
    <a class="nav-link" href="https://github.com/soylee22/lodestar-world/actions" target="_blank" rel="noopener">GitHub Actions ↗</a>
  </nav>
</header>

<div class="wrap">
  <div class="hero">
    <div>
      <h1>Weekly (1W) Simple Pullback &amp; XL Scanner</h1>
      <p class="sub">31 UK/European ETFs &amp; 23 Global Compounder Equities · 20W Z-Score (&le; -1.35 SD / -2.40 SD) + 14W ROC below 20W &amp; 50W SMAs</p>
    </div>
    <div class="mono" style="font-size:12px;color:var(--muted)">Last refreshed: <strong style="color:var(--ink)">{now_str}</strong></div>
  </div>

  <div class="kpis">
    <div class="kpi">
      <div class="k">Active Tier 1/2 Pullback XL</div>
      <div class="v" style="color:var(--gold)">{active_xl}</div>
      <div class="s">Confirmed or live &le; -2.40 SD flushes</div>
    </div>
    <div class="kpi">
      <div class="k">Total Active Tier 1/2 Signals</div>
      <div class="v" style="color:var(--teal)">{active_pb}</div>
      <div class="s">High-win-rate Pullback + XL setups</div>
    </div>
    <div class="kpi">
      <div class="k">Tier 1 Approved Universe</div>
      <div class="v">{tier1_count} / {len(records)}</div>
      <div class="s">&ge; 80% 1Y win rate &amp; &ge; +12% 1Y median</div>
    </div>
    <div class="kpi">
      <div class="k">Top Live Conviction</div>
      <div class="v" style="color:var(--gold);font-size:18px">SMGB.L · SEMI.L · IUMO.L</div>
      <div class="s">+ CNX1.L · LQQ.PA · SSLN.L · ASML · NVDA</div>
    </div>
  </div>

  <div class="controls">
    <div class="btn-group">
      <button class="flt active" onclick="setFilter('BUY_NOW', this)">🔥 Actionable Buys Now (Tier 1 &amp; 2)</button>
      <button class="flt" onclick="setFilter('ACTIVE_ALL', this)">All Active Signals</button>
      <button class="flt" onclick="setFilter('TIER12', this)">Approved Watchlist (Tier 1 &amp; 2)</button>
      <button class="flt" onclick="setFilter('ETF', this)">All 31 ETFs</button>
      <button class="flt" onclick="setFilter('STOCK', this)">All 23 Stocks</button>
      <button class="flt" onclick="setFilter('ALL', this)">All 54 Instruments</button>
    </div>
    <input type="search" id="searchBox" class="search" placeholder="Filter by ticker, name, or sector..." oninput="render()">
  </div>

  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th onclick="sortBy('group_kind')">Type</th>
          <th onclick="sortBy('yf_sym')">Ticker ↕</th>
          <th onclick="sortBy('name')">Name ↕</th>
          <th onclick="sortBy('closed_z20')">Last Closed (1W) ↕</th>
          <th onclick="sortBy('live_z20')">Live Bar (1W) ↕</th>
          <th onclick="sortBy('live_z20')">20W Z-Score ↕</th>
          <th onclick="sortBy('live_roc14')">14W ROC ↕</th>
          <th onclick="sortBy('vs_sma50')">vs 50W SMA ↕</th>
          <th onclick="sortBy('vs_sma200')">vs 200W SMA ↕</th>
          <th onclick="sortBy('pb_1y')">10Y All PB 1Y (Win%) ↕</th>
          <th onclick="sortBy('xl_1y')">10Y XL 1Y (Win%) ↕</th>
          <th onclick="sortBy('dd_3m')">3M Wiggle ↕</th>
          <th onclick="sortBy('tier_code')">10Y Strategy Tier ↕</th>
        </tr>
      </thead>
      <tbody id="rows"></tbody>
    </table>
  </div>
</div>

<script>
const DATA = {data_json};
let currentFilter = 'BUY_NOW';
let sortKey = 'live_z20';
let sortAsc = true;

function badge(state) {{
  if (state === 'PULLBACK XL') return '<span class="badge xl">PULLBACK XL</span>';
  if (state === 'PULLBACK') return '<span class="badge pb">PULLBACK</span>';
  if (state === 'ABOVE 50 SMA' || state.startsWith('NEAR')) return '<span class="badge near">' + state + '</span>';
  return '<span class="none">' + state + '</span>';
}}

function fmtStat(s) {{
  if (!s || s.med_1y === null || s.med_1y === undefined) return '<span class="none">n=' + (s ? s.count : 0) + '</span>';
  const sign = s.med_1y >= 0 ? '+' : '';
  const col = s.med_1y >= 15 && s.win_1y >= 80 ? 'color:var(--teal)' : s.med_1y < 0 ? 'color:var(--coral)' : '';
  return `<span class="mono" style="${{col}}"><b>${{sign}}${{s.med_1y.toFixed(1)}}%</b> (${{s.win_1y.toFixed(0)}}%, n=${{s.count}})</span>`;
}}

function getVal(r, k) {{
  if (k === 'pb_1y') return r.pb_stats && r.pb_stats.med_1y !== null ? r.pb_stats.med_1y : -999;
  if (k === 'xl_1y') return r.xl_stats && r.xl_stats.med_1y !== null ? r.xl_stats.med_1y : -999;
  if (k === 'dd_3m') return r.pb_stats && r.pb_stats.med_dd_3m !== null ? r.pb_stats.med_dd_3m : -999;
  return r[k] !== null && r[k] !== undefined ? r[k] : '';
}}

function sortBy(k) {{
  if (sortKey === k) {{
    sortAsc = !sortAsc;
  }} else {{
    sortKey = k;
    sortAsc = (k === 'live_z20' || k === 'closed_z20' || k === 'tier_code' || k === 'yf_sym' || k === 'name');
  }}
  render();
}}

function setFilter(mode, btn) {{
  currentFilter = mode;
  document.querySelectorAll('.btn-group button').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  render();
}}

function render() {{
  const q = (document.getElementById('searchBox').value || '').toLowerCase().trim();
  const tbody = document.getElementById('rows');
  tbody.innerHTML = '';

  const filtered = DATA.filter(r => {{
    if (q) {{
      const hay = (r.label + ' ' + r.yf_sym + ' ' + r.name + ' ' + r.category + ' ' + r.tier).toLowerCase();
      if (!hay.includes(q)) return false;
    }}
    const isAct = r.closed_state.startsWith('PULLBACK') || r.live_state.startsWith('PULLBACK') || r.recent_episode_signal !== 'NONE' || r.live_state === 'ABOVE 50 SMA';
    if (currentFilter === 'BUY_NOW') return isAct && (r.tier_code === 1 || r.tier_code === 2 || r.pb_stats.count_1y < 2);
    if (currentFilter === 'ACTIVE_ALL') return isAct;
    if (currentFilter === 'TIER12') return r.tier_code === 1 || r.tier_code === 2;
    if (currentFilter === 'ETF') return r.group_kind === 'ETF';
    if (currentFilter === 'STOCK') return r.group_kind === 'STOCK';
    return true;
  }});

  filtered.sort((a, b) => {{
    const va = getVal(a, sortKey);
    const vb = getVal(b, sortKey);
    if (va < vb) return sortAsc ? -1 : 1;
    if (va > vb) return sortAsc ? 1 : -1;
    return 0;
  }});

  filtered.forEach(r => {{
    const tr = document.createElement('tr');
    const tClass = r.tier_code === 1 ? 't1' : r.tier_code === 2 ? 't2' : r.tier_code === 3 ? 't3' : 't4';
    const dd = r.pb_stats.med_dd_3m !== null ? r.pb_stats.med_dd_3m.toFixed(1) + '%' : '-';
    const s200 = r.vs_sma200 !== null && !isNaN(r.vs_sma200) ? (r.vs_sma200 >= 0 ? '+' : '') + r.vs_sma200.toFixed(1) + '%' : '-';
    const tvUrl = 'https://www.tradingview.com/chart/?symbol=' + encodeURIComponent(r.tv_sym) + '&interval=1W';
    tr.innerHTML = `
      <td class="mono" style="color:var(--muted)">${{r.group_kind}}</td>
      <td><a class="tv-link" href="${{tvUrl}}" target="_blank" rel="noopener" title="Open 1W chart on TradingView">${{r.yf_sym}} ↗</a></td>
      <td>${{r.name}} <span class="none">(${{r.category}})</span></td>
      <td>${{badge(r.closed_state)}} <span class="none">(${{r.closed_z20.toFixed(2)}})</span></td>
      <td>${{badge(r.live_state)}}</td>
      <td class="mono"><b>${{r.live_z20.toFixed(2)}} SD</b></td>
      <td class="mono" style="color:${{r.live_roc14 < 0 ? 'var(--coral)' : 'var(--teal)'}}">${{r.live_roc14.toFixed(1)}}%</td>
      <td class="mono">${{(r.vs_sma50 >= 0 ? '+' : '') + r.vs_sma50.toFixed(1)}}%</td>
      <td class="mono">${{s200}}</td>
      <td>${{fmtStat(r.pb_stats)}}</td>
      <td>${{fmtStat(r.xl_stats)}}</td>
      <td class="mono" style="color:var(--muted)">${{dd}}</td>
      <td class="${{tClass}}">${{r.tier}}</td>
    `;
    tbody.appendChild(tr);
  }});
}}

render();
</script>
</body>
</html>"""
    out_path.write_text(html, encoding="utf-8")


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    all_items = [(a, b, c, d, e, "ETF") for a, b, c, d, e in ETF_UNIVERSE] + [
        (a, b, c, d, e, "STOCK") for a, b, c, d, e in STOCK_UNIVERSE
    ]
    tickers = [item[1] for item in all_items]
    print(f"Downloading 15-year weekly adjusted data for {len(tickers)} instruments...")
    raw = yf.download(tickers, period="15y", interval="1wk", progress=False, auto_adjust=True)

    records: list[dict[str, Any]] = []
    for label, yf_sym, tv_sym, name, category, group_kind in all_items:
        s = raw["Close"][yf_sym].dropna()
        rec = analyze_series(label, yf_sym, tv_sym, name, category, group_kind, s)
        records.append(rec)

    OUT_JSON.write_text(json.dumps(records, indent=2), encoding="utf-8")
    render_html(records, OUT_HTML)
    print(f"Saved {OUT_JSON} and {OUT_HTML} ({len(records)} instruments).")


if __name__ == "__main__":
    main()
