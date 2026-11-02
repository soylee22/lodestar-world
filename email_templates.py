"""HTML and plain text email templates for Lodestar World and Last Year's Winner.
Designed for clean Apple Mail, Gmail, and mobile rendering.
"""
from __future__ import annotations

from datetime import date
from typing import Any, Dict, List


def format_pct(val: float | None) -> str:
    if val is None:
        return "N/A"
    return f"{val:+.1f}%"


def build_lodestar_world_email(
    today: date,
    days_left: int,
    signal_date: date,
    holding_name: str,
    holding_ticker: str,
    holding_month: str,
    projected_name: str,
    projected_ticker: str,
    is_change: bool,
    is_cash: bool,
    ranks: List[Dict[str, Any]],
    spx_chg: float,
    spx_threshold: float,
    lookback_base: str,
    cash_base: str,
) -> tuple[str, str, str]:
    """Build (subject, plain_text, html) for Lodestar World email."""
    lead_gap = 0.0
    if len(ranks) >= 2:
        lead_gap = round(ranks[0]["momentum"] - ranks[1]["momentum"], 1)

    if is_cash:
        subject = f"Lodestar World: CASH RULE FIRES · 100% cash, {days_left}d to rebalance"
        status_label = "DEFENSIVE CASH FILTER TRIGGERED · 100% CASH"
        badge_bg = "#fef2f2"
        badge_color = "#b91c1c"
        badge_border = "#fecaca"
        action_title = "Move 100% to Cash at Month-End"
        action_desc = f"Broad market fell below {spx_threshold:.0f}% threshold. Capital moves 100% to cash to protect capital."
    elif not is_change:
        subject = f"Lodestar World: {holding_name} ({holding_ticker}) · {days_left}d to rebalance"
        status_label = f"HOLD {holding_name.upper()} · ZERO TURNOVER"
        badge_bg = "#ecfdf5"
        badge_color = "#047857"
        badge_border = "#a7f3d0"
        action_title = f"Maintain 100% in {holding_name} ({holding_ticker})"
        action_desc = f"{holding_name} leads {ranks[1]['name']} by +{lead_gap:.1f} percentage points. Projected allocation remains 100% with zero dealing transactions."
    else:
        subject = f"Lodestar World: Rotate to {projected_name} ({projected_ticker}) · {days_left}d to rebalance"
        status_label = f"REBALANCE: WOULD ROTATE TO {projected_name.upper()}"
        badge_bg = "#eff6ff"
        badge_color = "#1d4ed8"
        badge_border = "#bfdbfe"
        action_title = f"Rotate 100% to {projected_name} ({projected_ticker})"
        action_desc = f"{projected_name} overtook {holding_name} and leads by +{lead_gap:.1f} percentage points. Rotation pending at month-end close."

    margin_text = f"{ranks[0]['name']} holds the slot unless it gives back {lead_gap}% against {ranks[1]['name']} this month." if (len(ranks) >= 2 and not is_cash) else ""

    # Plain text version
    plain_lines = [
        "LODESTAR WORLD · FACTOR & DIVIDEND SLEEVE",
        f"Positioning & 8-Month Momentum Standings",
        f"{days_left}d to Rebalance",
        "",
        f"Status: {status_label}",
        "",
        f"CURRENT TARGET ALLOCATION (100%)",
        f"{holding_name} ({holding_ticker}) · Signal of {holding_month}",
        f"Projected Action: {action_title}",
        f"Next signal at {today.strftime('%Y-%m')} close, acting {signal_date.strftime('%-d %b %Y')} ({days_left} days out).",
        "",
        "TRAILING 8-MONTH RELATIVE MOMENTUM:",
    ]
    for r in ranks:
        mark = " ★ (PROJECTED LEADER)" if r.get("is_leader") else ""
        gap = f"-{round(ranks[0]['momentum'] - r['momentum'], 1):.1f}pp" if not r.get("is_leader") else "Leader"
        plain_lines.append(f"  #{r['rank']} {r['name']:<22} ({r['ticker']:<8}) {r['momentum']:>+6.1f}%  [{gap}]{mark}")

    if margin_text:
        plain_lines += ["", margin_text]

    plain_lines += [
        "",
        f"DEFENSIVE CASH FILTER (S&P 500):",
        f"S&P 500 is {spx_chg:+.1f}% vs {cash_base} close (Threshold: {spx_threshold:.0f}%). {'CASH FILTER ACTIVE' if is_cash else 'INVESTED (REGIME NORMAL)'}.",
        "",
        "STRATEGY BENCHMARK STATS (2017-2026):",
        "CAGR: +16.3% vs All-World +11.3% · Max Drawdown: -13.4% vs -15.5% · Sharpe: 1.10 vs 0.80",
        "",
        f"Prices to {today.strftime('%-d %b %Y')}. Provisional. The signal that counts is computed at the month-end close.",
        "https://soylee22.github.io/lodestar-world/",
    ]
    plain = "\n".join(plain_lines)

    # HTML Table rows
    table_rows = []
    for r in ranks:
        is_lead = r.get("is_leader")
        row_bg = "#f0fdf4" if is_lead else "#ffffff"
        star = '<span style="color:#059669;font-weight:700;margin-left:6px;">★ Leader</span>' if is_lead else ""
        gap_str = "Leader" if is_lead else f"-{round(ranks[0]['momentum'] - r['momentum'], 1):.1f}%"
        table_rows.append(f"""
          <tr style="background-color:{row_bg};border-bottom:1px solid #e2e8f0;">
            <td style="padding:10px 12px;font-size:13px;font-weight:700;color:#64748b;">#{r['rank']}</td>
            <td style="padding:10px 12px;font-size:13px;font-weight:{'700' if is_lead else '600'};color:#0f172a;">{r['name']} {star}</td>
            <td style="padding:10px 12px;font-size:12px;font-family:monospace;color:#475569;">{r['ticker']}</td>
            <td style="padding:10px 12px;font-size:13px;font-weight:700;text-align:right;color:{'#059669' if r['momentum'] >= 0 else '#dc2626'};">{r['momentum']:+.1f}%</td>
            <td style="padding:10px 12px;font-size:12px;color:#64748b;text-align:right;">{gap_str}</td>
          </tr>
        """)
    table_html = "".join(table_rows)

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{subject}</title>
</head>
<body style="margin:0;padding:24px 12px;background-color:#f1f5f9;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased;color:#0f172a;">
  <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color:#f1f5f9;">
    <tr>
      <td align="center">
        <table width="100%" border="0" cellspacing="0" cellpadding="0" style="max-width:600px;text-align:left;">
          
          <!-- Brand Header -->
          <tr>
            <td style="padding:12px 6px 20px 6px;">
              <table width="100%" border="0" cellspacing="0" cellpadding="0">
                <tr>
                  <td>
                    <div style="font-size:11px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:#64748b;margin-bottom:4px;">Lodestar World · Factor &amp; Dividend Sleeve</div>
                    <div style="font-size:24px;font-weight:800;letter-spacing:-0.02em;color:#0f172a;line-height:1.2;">Positioning &amp; 8-Mo Standings</div>
                  </td>
                  <td align="right" valign="top">
                    <span style="display:inline-block;padding:5px 12px;border-radius:9999px;background-color:#e2e8f0;color:#334155;font-size:12px;font-weight:600;">
                      {days_left}d to Rebalance
                    </span>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Main White Container -->
          <tr>
            <td style="background-color:#ffffff;border-radius:16px;border:1px solid #e2e8f0;padding:24px 22px;box-shadow:0 4px 16px rgba(0,0,0,0.04);">
              
              <!-- Status Pill Banner -->
              <div style="background-color:{badge_bg};border:1px solid {badge_border};border-radius:10px;padding:12px 16px;margin-bottom:20px;text-align:center;">
                <div style="font-size:13px;font-weight:800;letter-spacing:0.04em;color:{badge_color};">
                  {status_label}
                </div>
              </div>

              <!-- Active Allocation Card -->
              <div style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;color:#475569;margin-bottom:8px;">
                Active Target Allocation (100%)
              </div>
              <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color:#f8fafc;border-radius:12px;border:1px solid #e2e8f0;padding:16px;margin-bottom:20px;">
                <tr>
                  <td width="60%" valign="top" style="padding:4px 8px;border-right:1px solid #e2e8f0;">
                    <div style="font-size:18px;font-weight:800;color:#0f172a;">{holding_name} ({holding_ticker})</div>
                    <div style="font-size:12px;color:#64748b;margin-top:3px;">iShares Edge MSCI World Value Factor UCITS ETF</div>
                    <div style="font-size:11px;font-family:monospace;color:#64748b;margin-top:2px;">ISIN: IE00BP3QZB59 · London Stock Exchange</div>
                  </td>
                  <td width="40%" valign="top" style="padding:4px 8px 4px 16px;">
                    <div style="font-size:11px;font-weight:700;text-transform:uppercase;color:#64748b;">Target Share</div>
                    <div style="font-size:22px;font-weight:800;color:#059669;">100%</div>
                    <div style="font-size:12px;font-weight:600;color:#334155;margin-top:2px;">
                      Signal: {holding_month}
                    </div>
                  </td>
                </tr>
              </table>

              <!-- Projection & Margin Grid -->
              <table width="100%" border="0" cellspacing="0" cellpadding="0" style="margin-bottom:20px;">
                <tr>
                  <td width="48%" valign="top" style="background-color:#f8fafc;border-radius:10px;border:1px solid #e2e8f0;padding:12px 14px;">
                    <div style="font-size:11px;font-weight:700;text-transform:uppercase;color:#64748b;margin-bottom:4px;">Next Rebalance</div>
                    <div style="font-size:14px;font-weight:800;color:#0f172a;">{action_title}</div>
                    <div style="font-size:12px;color:#64748b;margin-top:4px;">Acts: <b>{signal_date.strftime('%-d %b %Y')}</b> ({days_left}d out)</div>
                  </td>
                  <td width="4%"></td>
                  <td width="48%" valign="top" style="background-color:#f8fafc;border-radius:10px;border:1px solid #e2e8f0;padding:12px 14px;">
                    <div style="font-size:11px;font-weight:700;text-transform:uppercase;color:#64748b;margin-bottom:4px;">Lead Margin</div>
                    <div style="font-size:14px;font-weight:800;color:#059669;">+{lead_gap:.1f} percentage points</div>
                    <div style="font-size:12px;color:#64748b;margin-top:4px;">over #2 {ranks[1]['name']}</div>
                  </td>
                </tr>
              </table>

              <!-- Standings Table -->
              <div style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;color:#475569;margin-bottom:10px;">
                Global Factor &amp; Dividend Leaderboard (8-Mo Momentum)
              </div>
              <table width="100%" border="0" cellspacing="0" cellpadding="0" style="border-collapse:collapse;border:1px solid #e2e8f0;border-radius:10px;overflow:hidden;margin-bottom:16px;">
                <thead>
                  <tr style="background-color:#f8fafc;border-bottom:1px solid #e2e8f0;">
                    <th align="left" style="padding:10px 12px;font-size:11px;font-weight:700;color:#64748b;text-transform:uppercase;">#</th>
                    <th align="left" style="padding:10px 12px;font-size:11px;font-weight:700;color:#64748b;text-transform:uppercase;">ETF / Factor</th>
                    <th align="left" style="padding:10px 12px;font-size:11px;font-weight:700;color:#64748b;text-transform:uppercase;">Ticker</th>
                    <th align="right" style="padding:10px 12px;font-size:11px;font-weight:700;color:#64748b;text-transform:uppercase;">8-Mo Return</th>
                    <th align="right" style="padding:10px 12px;font-size:11px;font-weight:700;color:#64748b;text-transform:uppercase;">Gap</th>
                  </tr>
                </thead>
                <tbody>
                  {table_html}
                </tbody>
              </table>

              <!-- Lead Margin Note -->
              {f'<div style="background-color:#f8fafc;border-left:3px solid #059669;padding:10px 14px;border-radius:4px;font-size:12px;color:#334155;margin-bottom:20px;line-height:1.4;">{margin_text}</div>' if margin_text else ''}

              <!-- Cash Protection Gate -->
              <div style="background-color:#f8fafc;border-radius:10px;border:1px solid #e2e8f0;padding:14px 16px;margin-bottom:22px;">
                <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;color:#64748b;margin-bottom:4px;">Defensive Regime Filter (S&amp;P 500)</div>
                <table width="100%" border="0" cellspacing="0" cellpadding="0">
                  <tr>
                    <td style="font-size:13px;color:#0f172a;">
                      S&amp;P 500 is <b>{spx_chg:+.1f}%</b> vs {cash_base} close (Threshold: {spx_threshold:.0f}%)
                    </td>
                    <td align="right">
                      <span style="display:inline-block;padding:3px 10px;border-radius:9999px;font-size:11px;font-weight:700;background-color:{'#fef2f2' if is_cash else '#ecfdf5'};color:{'#b91c1c' if is_cash else '#047857'};">
                        {'CASH FILTER ACTIVE' if is_cash else 'INVESTED (NORMAL)'}
                      </span>
                    </td>
                  </tr>
                </table>
              </div>

              <!-- Track Record Highlights -->
              <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color:#f8fafc;border-radius:10px;border:1px solid #e2e8f0;padding:12px 14px;margin-bottom:22px;text-align:center;">
                <tr>
                  <td width="33%" style="border-right:1px solid #e2e8f0;">
                    <div style="font-size:10px;font-weight:700;text-transform:uppercase;color:#64748b;">10-Yr CAGR</div>
                    <div style="font-size:16px;font-weight:800;color:#0f172a;margin-top:2px;">16.3%</div>
                    <div style="font-size:10px;color:#059669;">+5.0pp vs All-World</div>
                  </td>
                  <td width="33%" style="border-right:1px solid #e2e8f0;">
                    <div style="font-size:10px;font-weight:700;text-transform:uppercase;color:#64748b;">Max Drawdown</div>
                    <div style="font-size:16px;font-weight:800;color:#0f172a;margin-top:2px;">-13.4%</div>
                    <div style="font-size:10px;color:#059669;">vs -15.5% Benchmark</div>
                  </td>
                  <td width="33%">
                    <div style="font-size:10px;font-weight:700;text-transform:uppercase;color:#64748b;">Sharpe Ratio</div>
                    <div style="font-size:16px;font-weight:800;color:#0f172a;margin-top:2px;">1.10</div>
                    <div style="font-size:10px;color:#059669;">Sortino 1.97</div>
                  </td>
                </tr>
              </table>

              <!-- CTA Button -->
              <div style="text-align:center;margin:24px 0 10px 0;">
                <a href="https://soylee22.github.io/lodestar-world/" style="display:inline-block;padding:12px 28px;background-color:#0f172a;color:#ffffff;text-decoration:none;font-size:13px;font-weight:700;border-radius:10px;letter-spacing:0.02em;">
                  Open Live Lodestar World Dashboard →
                </a>
              </div>

            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding:18px 8px;text-align:center;font-size:11px;color:#94a3b8;line-height:1.5;">
              Provisional reading as of {today.strftime('%d %b %Y')}. Official signal computes at month-end close.<br>
              Lodestar World · <a href="https://soylee22.github.io/lodestar-world/" style="color:#64748b;text-decoration:underline;">soylee22.github.io/lodestar-world</a>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""
    return subject, plain, html
    return subject, plain, html


def build_lyw_email(
    today: date,
    days_to_year_end: int,
    live_pos: Dict[str, Any],
    contenders: List[Dict[str, Any]],
) -> tuple[str, str, str]:
    """Build (subject, plain_text, html) for Last Year's Winner email."""
    ticker = live_pos.get("ticker", "SNDK")
    name = live_pos.get("name", "SanDisk Corp.")
    cur_price = live_pos.get("currentPrice", 0.0)
    entry_price = live_pos.get("entryPrice", 1557.71)
    shares = live_pos.get("shares", 0.8481779)
    val_gbp = live_pos.get("valuationGbp", 0.0)
    net_pnl = live_pos.get("netPnlGbp", 0.0)
    net_ret = live_pos.get("netReturnPct", 0.0)
    stop_price = live_pos.get("stopLossPrice", 1012.51)
    buffer_pct = live_pos.get("bufferPercent", 0.0)
    buffer_dlr = live_pos.get("bufferDollars", 0.0)
    fall_to_stop = live_pos.get("fallToStopPct", 0.0)
    is_stopped = live_pos.get("isStopped", False)
    spy_val = live_pos.get("spyValuationGbp", 0.0)
    spy_ret = live_pos.get("spyReturnPct", 0.0)
    diff_spy = live_pos.get("diffVsSpyGbp", 0.0)
    drawdown_entry = live_pos.get("drawdownFromEntry", 0.0)
    drawdown_peak = live_pos.get("drawdownFromPeak", 0.0)

    if is_stopped:
        subject = f"LYW: STOP BREACHED · SNDK in cash, {days_to_year_end}d to year-end"
        status_label = "MODEL STOP BREACHED · IN CASH"
        badge_bg = "#fef2f2"
        badge_color = "#b91c1c"
        badge_border = "#fecaca"
    else:
        subject = f"LYW: hold {ticker} (+{fall_to_stop:.1f}% to stop), {days_to_year_end}d to year-end"
        status_label = f"HOLD {ticker} · 35% ENTRY STOP UNTOUCHED"
        badge_bg = "#ecfdf5"
        badge_color = "#047857"
        badge_border = "#a7f3d0"

    leader = contenders[0] if contenders else {}
    cushion_text = ""
    if len(contenders) >= 2:
        c1 = contenders[0]["ytd"]
        c2 = contenders[1]["ytd"]
        cushion = round((1.0 - (100.0 + c2) / (100.0 + c1)) * 100.0, 1) if (100.0 + c1) > 0 else 0.0
        cushion_text = f"With {contenders[1]['ticker']} unchanged, {contenders[0]['ticker']} could fall {cushion:.1f}% before they tie."

    # Plain text version
    plain_lines = [
        f"Last Year's Winner · Daily Monitor",
        f"Personal rule: {status_label}",
        "",
        f"Holding now: {name} ({ticker}), {shares:.7f} shares.",
        f"Bought 12 Oct 2026, 11:47 BST at ${entry_price:,.2f}.",
        f"£1,000.00 paid, including £1.50 FX fee.",
        "",
        "Since your purchase:",
        f"Your holding: £{val_gbp:,.2f} · £{net_pnl:+,.2f} ({net_ret:+.2f}%), including the entry fee.",
        f"Hypothetical S&P 500 (SPY): £{spy_val:,.2f} · {spy_ret:+.2f}% from £1,000.",
        f"Difference: £{diff_spy:+,.2f} versus SPY.",
        "",
        "Fixed entry stop:",
        f"35% below your purchase: ${stop_price:,.2f}. This threshold does not trail the high.",
        f"Observed price: ${cur_price:,.2f} · {drawdown_entry:+.2f}% versus entry.",
        f"Drawdown from the observed post-entry high: {drawdown_peak:+.2f}%.",
        f"Price can fall a further {fall_to_stop:.1f}% (${buffer_dlr:,.2f}) to the stop.",
        f"Status: {'BREACH OBSERVED' if is_stopped else 'No breach found in available observations. A stop sale would leave cash until January.'}",
        "",
        f"2027 Strategy Countdown:",
        f"{days_to_year_end} calendar days until the {today.year} year-end close.",
        "The December signal selects the stock for the first trading session of January.",
        "",
        "Next-year candidates · YTD total return through today:",
    ]
    for i, c in enumerate(contenders[:5], 1):
        plain_lines.append(f"  {i}. {c['name']} ({c['ticker']}) · {c['ytd']:+.2f}%")

    if leader:
        plain_lines += [
            f"If the year ended at that close: {leader['name']} ({leader['ticker']}). Provisional, not a trade today.",
        ]
    if cushion_text:
        plain_lines.append(cushion_text)

    plain_lines += [
        "",
        f"Prices to {today.strftime('%-d %b %Y')}. Stop observations are indicative.",
        "https://soylee22.github.io/lodestar-world/#lyw",
    ]
    plain = "\n".join(plain_lines)

    # HTML Contenders table
    contender_rows = []
    for c in contenders[:5]:
        is_lead = (c.get("rank") == 1)
        is_active = (c.get("ticker") == ticker)
        row_bg = "#eff6ff" if is_lead else ("#f0fdf4" if is_active else "#ffffff")
        tag = '<span style="color:#2563eb;font-weight:700;margin-left:6px;">★ 2027 Leader</span>' if is_lead else (
            '<span style="color:#059669;font-weight:700;margin-left:6px;">(Active Hold)</span>' if is_active else ""
        )
        contender_rows.append(f"""
          <tr style="background-color:{row_bg};border-bottom:1px solid #e2e8f0;">
            <td style="padding:10px 12px;font-size:13px;font-weight:700;color:#64748b;">#{c['rank']}</td>
            <td style="padding:10px 12px;font-size:13px;font-weight:600;color:#0f172a;">{c['name']} {tag}</td>
            <td style="padding:10px 12px;font-size:12px;font-family:monospace;color:#475569;">{c['ticker']}</td>
            <td style="padding:10px 12px;font-size:13px;font-weight:700;text-align:right;color:#059669;">{c['ytd']:+.1f}%</td>
          </tr>
        """)
    contenders_table_html = "".join(contender_rows)

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{subject}</title>
</head>
<body style="margin:0;padding:24px 12px;background-color:#f1f5f9;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased;color:#0f172a;">
  <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color:#f1f5f9;">
    <tr>
      <td align="center">
        <table width="100%" border="0" cellspacing="0" cellpadding="0" style="max-width:600px;text-align:left;">
          
          <!-- Brand Header -->
          <tr>
            <td style="padding:12px 6px 20px 6px;">
              <table width="100%" border="0" cellspacing="0" cellpadding="0">
                <tr>
                  <td>
                    <div style="font-size:11px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:#64748b;margin-bottom:4px;">Last Year's Winner · Momentum Sleeve</div>
                    <div style="font-size:24px;font-weight:800;letter-spacing:-0.02em;color:#0f172a;line-height:1.2;">2026 Position &amp; 2027 Contenders</div>
                  </td>
                  <td align="right" valign="top">
                    <span style="display:inline-block;padding:5px 12px;border-radius:9999px;background-color:#e2e8f0;color:#334155;font-size:12px;font-weight:600;">
                      {days_to_year_end}d to Year-End
                    </span>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Main White Container -->
          <tr>
            <td style="background-color:#ffffff;border-radius:16px;border:1px solid #e2e8f0;padding:24px 22px;box-shadow:0 4px 16px rgba(0,0,0,0.04);">
              
              <!-- Status Pill Banner -->
              <div style="background-color:{badge_bg};border:1px solid {badge_border};border-radius:10px;padding:12px 16px;margin-bottom:20px;text-align:center;">
                <div style="font-size:13px;font-weight:800;letter-spacing:0.04em;color:{badge_color};">
                  {status_label}
                </div>
              </div>

              <!-- Position & Valuation Grid -->
              <div style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;color:#475569;margin-bottom:8px;">
                Active Holding (2026 Winner)
              </div>
              <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color:#f8fafc;border-radius:12px;border:1px solid #e2e8f0;padding:16px;margin-bottom:20px;">
                <tr>
                  <td width="55%" valign="top" style="padding:4px 8px;border-right:1px solid #e2e8f0;">
                    <div style="font-size:18px;font-weight:800;color:#0f172a;">{name} ({ticker})</div>
                    <div style="font-size:12px;color:#64748b;margin-top:2px;">{shares:.7f} shares · Fill: ${entry_price:,.2f}</div>
                    <div style="font-size:12px;color:#64748b;">Bought 12 Oct 2026 · £1,000 paid</div>
                  </td>
                  <td width="45%" valign="top" style="padding:4px 8px 4px 16px;">
                    <div style="font-size:11px;font-weight:700;text-transform:uppercase;color:#64748b;">Current Valuation</div>
                    <div style="font-size:20px;font-weight:800;color:#0f172a;">£{val_gbp:,.2f}</div>
                    <div style="font-size:12px;font-weight:700;color:{'#059669' if net_pnl >= 0 else '#dc2626'};margin-top:2px;">
                      £{net_pnl:+,.2f} ({net_ret:+.2f}%)
                    </div>
                  </td>
                </tr>
              </table>

              <!-- Benchmark Comparison & Stop Loss Panels -->
              <table width="100%" border="0" cellspacing="0" cellpadding="0" style="margin-bottom:20px;">
                <tr>
                  <td width="48%" valign="top" style="background-color:#f8fafc;border-radius:10px;border:1px solid #e2e8f0;padding:12px 14px;">
                    <div style="font-size:11px;font-weight:700;text-transform:uppercase;color:#64748b;margin-bottom:4px;">vs S&amp;P 500 (SPY)</div>
                    <div style="font-size:14px;font-weight:800;color:#0f172a;">£{spy_val:,.2f} <span style="font-size:12px;font-weight:600;color:{'#059669' if spy_ret >= 0 else '#dc2626'};">({spy_ret:+.2f}%)</span></div>
                    <div style="font-size:12px;color:#64748b;margin-top:4px;">Diff: <b style="color:{'#059669' if diff_spy >= 0 else '#dc2626'};">£{diff_spy:+,.2f}</b></div>
                  </td>
                  <td width="4%"></td>
                  <td width="48%" valign="top" style="background-color:#f8fafc;border-radius:10px;border:1px solid #e2e8f0;padding:12px 14px;">
                    <div style="font-size:11px;font-weight:700;text-transform:uppercase;color:#64748b;margin-bottom:4px;">Fixed 35% Entry Stop</div>
                    <div style="font-size:14px;font-weight:800;color:#0f172a;">${stop_price:,.2f}</div>
                    <div style="font-size:12px;color:#059669;margin-top:4px;"><b>+{fall_to_stop:.1f}% room</b> (${buffer_dlr:,.2f})</div>
                  </td>
                </tr>
              </table>

              <!-- 2027 Contenders Race -->
              <div style="font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;color:#475569;margin-bottom:10px;">
                2027 Contender Race · Top S&amp;P 500 YTD
              </div>
              <table width="100%" border="0" cellspacing="0" cellpadding="0" style="border-collapse:collapse;border:1px solid #e2e8f0;border-radius:10px;overflow:hidden;margin-bottom:16px;">
                <thead>
                  <tr style="background-color:#f8fafc;border-bottom:1px solid #e2e8f0;">
                    <th align="left" style="padding:10px 12px;font-size:11px;font-weight:700;color:#64748b;text-transform:uppercase;">#</th>
                    <th align="left" style="padding:10px 12px;font-size:11px;font-weight:700;color:#64748b;text-transform:uppercase;">Stock</th>
                    <th align="left" style="padding:10px 12px;font-size:11px;font-weight:700;color:#64748b;text-transform:uppercase;">Ticker</th>
                    <th align="right" style="padding:10px 12px;font-size:11px;font-weight:700;color:#64748b;text-transform:uppercase;">YTD Return</th>
                  </tr>
                </thead>
                <tbody>
                  {contenders_table_html}
                </tbody>
              </table>

              <!-- Lead Cushion Note -->
              {f'<div style="background-color:#f8fafc;border-left:3px solid #2563eb;padding:10px 14px;border-radius:4px;font-size:12px;color:#334155;margin-bottom:20px;line-height:1.4;">{cushion_text}</div>' if cushion_text else ''}

              <!-- CTA Button -->
              <div style="text-align:center;margin:24px 0 10px 0;">
                <a href="https://soylee22.github.io/lodestar-world/#lyw" style="display:inline-block;padding:12px 28px;background-color:#0f172a;color:#ffffff;text-decoration:none;font-size:13px;font-weight:700;border-radius:10px;letter-spacing:0.02em;">
                  Open LYW Tracker Dashboard →
                </a>
              </div>

            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding:18px 8px;text-align:center;font-size:11px;color:#94a3b8;line-height:1.5;">
              Indicative quote: ${cur_price:,.2f} ({drawdown_entry:+.2f}% vs entry). Stop observations are indicative and do not execute orders.<br>
              Last Year's Winner · <a href="https://soylee22.github.io/lodestar-world/#lyw" style="color:#64748b;text-decoration:underline;">soylee22.github.io/lodestar-world</a>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""
    return subject, plain, html
