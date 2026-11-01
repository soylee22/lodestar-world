#!/usr/bin/env python3
"""Build and update index.html with the 3 consolidated strategies:
1. Lodestar World (with Era toggle: Modern UCITS vs 28-Year Dot-Com backtest)
2. Last Year's Winner (with Live 2026 SNDK stop-loss monitor, 2027 contenders, 29-Year dot-com archive)
3. Combined 50/50 Dual Engine (with 27-year blended compounding track record)
"""

from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
SRC_HTML = HERE / "index.html.bak"
OUT_HTML = HERE / "index.html"

raw_html = SRC_HTML.read_text(encoding="utf-8")

# 1. New CSS to inject before </style>
EXTRA_CSS = """
/* ── Strategy Switcher Bar ───────────────────────────────────────────── */
.strat-bar {
  background: var(--surface);
  border-bottom: 1px solid var(--rule);
  position: sticky;
  top: 48px;
  z-index: 85;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.strat-tabs {
  display: flex;
  gap: 8px;
  padding: 8px 0;
  overflow-x: auto;
  scrollbar-width: none;
}
.strat-tabs::-webkit-scrollbar { display: none; }
.strat-tab {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  padding: 8px 18px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 8px;
  color: var(--ink-2);
  cursor: pointer;
  font-family: var(--sans);
  text-align: left;
  transition: all .15s ease;
  white-space: nowrap;
}
.strat-tab:hover {
  background: var(--paper-2);
  color: var(--ink);
}
.strat-tab.active {
  background: var(--surface-sunk);
  color: var(--ink);
  border-color: var(--rule-2);
  box-shadow: var(--shadow);
}
.strat-tab .strat-icon {
  font-size: 20px;
  line-height: 1;
}
.strat-tab .strat-title {
  display: block;
  font-size: 13.5px;
  font-weight: 600;
  letter-spacing: -.01em;
}
.strat-tab .strat-sub {
  display: block;
  font-size: 11px;
  color: var(--muted);
  font-weight: 400;
  margin-top: 1px;
}
.strat-tab.active .strat-title {
  color: var(--s1);
}

/* ── Strategy Views ─────────────────────────────────────────────────── */
.strat-view[hidden] { display: none !important; }

/* ── Era Switcher in Lodestar ───────────────────────────────────────── */
.era-selector-wrap {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 24px;
  padding: 12px 18px;
  background: var(--surface-sunk);
  border: 1px solid var(--rule);
  border-radius: 9px;
}
.era-selector-label {
  font-size: 13.5px;
  font-weight: 600;
  color: var(--ink);
}
.btn-era {
  padding: 6px 14px;
  font-size: 12px;
  font-family: var(--sans);
  border-radius: 6px;
  border: 1px solid transparent;
  cursor: pointer;
  background: transparent;
  color: var(--ink-2);
  transition: all .12s;
}
.btn-era.active {
  background: var(--surface);
  color: var(--ink);
  font-weight: 600;
  border-color: var(--rule-2);
  box-shadow: 0 1px 2px rgba(0,0,0,0.06);
}

/* ── Dot-Com Extended Panel ─────────────────────────────────────────── */
.dotcom-panel {
  background: var(--surface);
  border: 1px solid var(--rule);
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 28px;
  box-shadow: var(--shadow);
}
.dotcom-kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--rule);
}
.dotcom-kpi .k {
  font-family: var(--mono);
  font-size: 10px;
  color: var(--muted);
  letter-spacing: .08em;
  text-transform: uppercase;
}
.dotcom-kpi .v {
  font-size: 24px;
  font-weight: 700;
  color: var(--ink);
  font-variant-numeric: tabular-nums;
  margin-top: 4px;
}
.dotcom-kpi .sub {
  font-size: 11.5px;
  color: var(--muted);
  margin-top: 2px;
}

/* ── LYW Styles ─────────────────────────────────────────────────────── */
.lyw-hero {
  background: var(--band);
  color: var(--band-ink);
  padding: clamp(28px, 4.5vw, 44px);
  border-radius: 14px;
  margin-bottom: 32px;
  border: 1px solid var(--band-rule);
}
.lyw-hero-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
  gap: 20px;
  margin-top: 28px;
  padding-top: 24px;
  border-top: 1px solid var(--band-rule);
}
.lyw-kpi .k {
  font-family: var(--mono);
  font-size: 10px;
  color: var(--band-ink-2);
  letter-spacing: .08em;
  text-transform: uppercase;
}
.lyw-kpi .v {
  font-size: 26px;
  font-weight: 700;
  letter-spacing: -.02em;
  margin-top: 4px;
  font-variant-numeric: tabular-nums;
  color: var(--band-ink);
}
.lyw-kpi .sub {
  font-size: 12px;
  color: var(--band-ink-2);
  margin-top: 2px;
}

.lyw-live-card {
  background: var(--surface);
  border: 1px solid var(--rule);
  border-radius: 14px;
  padding: clamp(22px, 3.5vw, 32px);
  margin-bottom: 32px;
  box-shadow: var(--shadow);
}
.lyw-live-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(0, 1.85fr);
  gap: clamp(24px, 4vw, 48px);
  align-items: center;
}
@media(max-width: 860px){
  .lyw-live-grid { grid-template-columns: 1fr; }
}
.lyw-status-badge {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 4px 12px;
  border-radius: 999px;
  font-family: var(--mono);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: .05em;
  text-transform: uppercase;
}
.lyw-status-badge.green {
  background: rgba(27, 175, 122, 0.14);
  color: var(--s3);
  border: 1px solid rgba(27, 175, 122, 0.35);
}
.lyw-status-badge.red {
  background: rgba(165, 42, 34, 0.14);
  color: var(--neg-ink);
  border: 1px solid rgba(165, 42, 34, 0.35);
}
.lyw-stock-hero {
  font-size: clamp(38px, 5.5vw, 54px);
  font-weight: 800;
  letter-spacing: -.03em;
  line-height: 1.05;
  margin: 10px 0 4px;
  color: var(--ink);
}
.lyw-stock-sub {
  font-size: 15px;
  color: var(--muted);
}
.lyw-gauge-box {
  background: var(--surface-sunk);
  border: 1px solid var(--rule);
  border-radius: 9px;
  padding: 16px;
  margin-top: 18px;
}
.lyw-gauge-track {
  height: 11px;
  background: var(--paper-2);
  border-radius: 6px;
  position: relative;
  overflow: hidden;
  margin: 10px 0 6px;
}
.lyw-gauge-fill {
  height: 100%;
  background: linear-gradient(90deg, #e87f7c 0%, #fab219 40%, #1baf7a 100%);
  border-radius: 6px;
  transition: width .5s ease;
}
.lyw-gauge-labels {
  display: flex;
  justify-content: space-between;
  font-family: var(--mono);
  font-size: 11px;
  color: var(--muted);
}
.lyw-facts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
  gap: 14px;
}
.lyw-fact .k {
  font-family: var(--mono);
  font-size: 10px;
  color: var(--muted);
  letter-spacing: .08em;
  text-transform: uppercase;
}
.lyw-fact .v {
  font-size: 17px;
  font-weight: 600;
  color: var(--ink);
  font-variant-numeric: tabular-nums;
  margin-top: 3px;
}
.lyw-fact .v.highlight {
  color: var(--s3);
}

/* ── Combined 50/50 Dual Engine Styles ───────────────────────────────── */
.combined-hero {
  background: var(--band);
  color: var(--band-ink);
  padding: clamp(28px, 4.5vw, 44px);
  border-radius: 14px;
  margin-bottom: 32px;
  border: 1px solid var(--band-rule);
}
.dual-engine-split {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-block: 28px;
}
@media(max-width: 720px){
  .dual-engine-split { grid-template-columns: 1fr; }
}
.engine-card {
  background: var(--surface);
  border: 1px solid var(--rule);
  border-radius: 12px;
  padding: 24px;
  box-shadow: var(--shadow);
}
.engine-hd {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}
.engine-weight {
  background: var(--surface-sunk);
  border: 1px solid var(--rule-2);
  padding: 4px 10px;
  border-radius: 6px;
  font-family: var(--mono);
  font-size: 12px;
  font-weight: 700;
  color: var(--ink);
}
.badge-tag {
  display: inline-block;
  padding: 2px 7px;
  border-radius: 4px;
  font-family: var(--mono);
  font-size: 10.5px;
  font-weight: 600;
  letter-spacing: .03em;
}
.badge-tag.runner {
  background: rgba(27, 175, 122, 0.12);
  color: var(--pos-ink);
}
.badge-tag.stop {
  background: rgba(165, 42, 34, 0.12);
  color: var(--neg-ink);
}
.badge-tag.proj {
  background: rgba(42, 120, 214, 0.12);
  color: var(--s1);
}

/* ── Contenders YTD Surge Multi-Line Chart ─────────────────────────── */
.contenders-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}
.contenders-pill {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 5px 12px;
  border-radius: 999px;
  border: 1px solid var(--rule);
  background: var(--surface);
  color: var(--ink-2);
  font-size: 11.5px;
  font-family: var(--sans);
  cursor: pointer;
  transition: all .15s ease;
  user-select: none;
}
.contenders-pill:hover {
  background: var(--surface-sunk);
  color: var(--ink);
  border-color: var(--rule-2);
}
.contenders-pill.active {
  background: var(--paper-2);
  border-color: var(--ink);
  color: var(--ink);
  font-weight: 600;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}
.contenders-pill-logo {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  object-fit: cover;
  background: #fff;
  border: 1px solid rgba(0,0,0,0.1);
}
.contenders-tooltip {
  background: var(--surface);
  border: 1px solid var(--rule-2);
  border-radius: 8px;
  box-shadow: 0 10px 28px rgba(0,0,0,0.14);
  padding: 12px 16px;
  font-family: var(--sans);
  min-width: 250px;
  transition: opacity .1s ease;
}
.contenders-tooltip-hd {
  font-family: var(--mono);
  font-size: 11px;
  color: var(--muted);
  border-bottom: 1px solid var(--rule);
  padding-bottom: 6px;
  margin-bottom: 8px;
  display: flex;
  justify-content: space-between;
}
.contenders-tooltip-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  font-size: 12px;
  padding-block: 3px;
}
.contenders-tooltip-name {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--ink);
  font-weight: 500;
}
.contenders-tooltip-val {
  font-family: var(--mono);
  font-weight: 700;
}
"""

# Inject CSS
html = raw_html.replace("</style>", EXTRA_CSS + "\n</style>")

# 2. Strategy Switcher Bar HTML
STRAT_BAR_HTML = """
<!-- ── TOP-LEVEL STRATEGY SWITCHER ───────────────────────────────────── -->
<div class="strat-bar" role="navigation" aria-label="Strategy Navigation">
  <div class="wrap">
    <div class="strat-tabs" role="tablist">
      <button class="strat-tab active" id="tabLodestar" role="tab" aria-selected="true" data-target="viewLodestar">
        <span class="strat-icon">⭐</span>
        <span class="strat-meta">
          <span class="strat-title">Lodestar World</span>
          <span class="strat-sub">Global Factor &amp; Div Rotation</span>
        </span>
      </button>
      <button class="strat-tab" id="tabLyw" role="tab" aria-selected="false" data-target="viewLyw">
        <span class="strat-icon">🏆</span>
        <span class="strat-meta">
          <span class="strat-title">Last Year's Winner</span>
          <span class="strat-sub">S&amp;P 500 #1 + 35% Trailing Stop</span>
        </span>
      </button>
      <button class="strat-tab" id="tabCombined" role="tab" aria-selected="false" data-target="viewCombined">
        <span class="strat-icon">⚡</span>
        <span class="strat-meta">
          <span class="strat-title">50 / 50 Dual Engine</span>
          <span class="strat-sub">Blended Compounding Engine</span>
        </span>
      </button>
    </div>
  </div>
</div>
"""

# Insert strat-bar right after <header class="rail">...</header>
html = html.replace("</header>\n\n<main>", "</header>\n" + STRAT_BAR_HTML + "\n<main>")

# 3. Wrap Lodestar in <div id="viewLodestar" class="strat-view active">
html = html.replace(
    "<main>\n\n<!-- ── HERO ──────────────────────────────────────────────────────────── -->",
    "<main>\n\n<div id=\"viewLodestar\" class=\"strat-view active\">\n<!-- ── HERO ──────────────────────────────────────────────────────────── -->"
)

# 4. Insert Era Switcher inside Lodestar (above #years)
ERA_SWITCHER_HTML = """
<!-- ── ERA SELECTOR: MODERN UCITS VS DOT-COM EXTENDED ────────────────── -->
<div class="wrap" style="padding-top:20px">
  <div class="era-selector-wrap">
    <div>
      <div class="era-selector-label">Backtest Era &amp; History</div>
      <div style="font-size:12px;color:var(--muted)">Toggle between the live London UCITS record and the extended 28-year MSCI dot-com backtest.</div>
    </div>
    <div class="seg" role="group" aria-label="Era Selector">
      <button type="button" id="btnEraModern" class="btn-era active" aria-pressed="true">Modern UCITS (2017–2026)</button>
      <button type="button" id="btnEraDotcom" class="btn-era" aria-pressed="false">Dot-Com Extended (1999–2026, 28y)</button>
    </div>
  </div>

  <div id="panelDotcom" class="dotcom-panel" hidden>
    <div style="display:flex;align-items:baseline;justify-content:space-between;margin-bottom:16px;flex-wrap:wrap;gap:10px">
      <div>
        <h3 style="font-size:18px;font-weight:700;margin:0 0 4px">Lodestar World — 28-Year Dot-Com Backtest</h3>
        <p style="font-size:13px;color:var(--muted);margin:0">MSCI World Net Total Return factors in GBP with S&amp;P 500 nineteen-month cash gate (-25% threshold).</p>
      </div>
      <span class="badge-tag runner">28 YEARS · 326 MONTHS</span>
    </div>

    <div class="dotcom-kpi-grid">
      <div class="dotcom-kpi">
        <span class="k">Compound Return (CAGR)</span>
        <span class="v" id="dcCagr">11.30%</span>
        <span class="sub">vs 7.46% MSCI World Core</span>
      </div>
      <div class="dotcom-kpi">
        <span class="k">Max Drawdown</span>
        <span class="v" id="dcMaxDD">-26.04%</span>
        <span class="sub">vs -43.66% Core (Halved Crash)</span>
      </div>
      <div class="dotcom-kpi">
        <span class="k">Sharpe Ratio</span>
        <span class="v" id="dcSharpe">0.82</span>
        <span class="sub">vs 0.44 MSCI World Core</span>
      </div>
      <div class="dotcom-kpi">
        <span class="k">Cash Shield</span>
        <span class="v" id="dcCash">22 Months</span>
        <span class="sub">Protected in 2001-02 &amp; 2008</span>
      </div>
      <div class="dotcom-kpi">
        <span class="k">Growth of £100</span>
        <span class="v" id="dcGrowth">£1,833</span>
        <span class="sub">18.3x vs 7.1x Benchmark</span>
      </div>
    </div>

    <div class="tblwrap">
      <table class="data" id="tblDotcom"></table>
    </div>
  </div>
</div>
"""
html = html.replace(
    "<!-- ── 05 CALENDAR YEARS ─────────────────────────────────────────────── -->",
    ERA_SWITCHER_HTML + "\n<!-- ── 05 CALENDAR YEARS ─────────────────────────────────────────────── -->"
)

LYW_VIEW_HTML = """
<!-- ══════════════════════════════════════════════════════════════════════
     LAST YEAR'S WINNER (LYW) VIEW
     ══════════════════════════════════════════════════════════════════════ -->
<div id="viewLyw" class="strat-view" hidden>

  <!-- ── LYW HERO ──────────────────────────────────────────────────────── -->
  <section class="sec wrap" style="padding-top:clamp(20px, 3.5vw, 40px)">
    <div class="lyw-hero rise">
      <div class="eyebrow" style="color:var(--band-ink-2)">S&amp;P 500 #1 Momentum Rotation · 35% Trailing Stop-Loss</div>
      <div class="wordmark">
        <h1 class="title" style="color:var(--band-ink)"><span style="color:#fab219">Last Year's</span> Winner</h1>
        <div class="strap"><i style="background:#fab219"></i><span style="color:var(--band-ink-2)">Full 29-year historical compounding through dot-com bubble, GFC, and tech regimes</span></div>
      </div>
      <p class="deck" style="color:var(--band-ink);max-width:760px;margin-top:14px;line-height:1.55">
        Hold the single top-performing stock in the S&amp;P 500 from the prior calendar year, protected by an automatic 35% trailing stop-loss from highest intra-year close. If stopped out, hold cash until January.
      </p>

      <div class="lyw-hero-grid">
        <div class="lyw-kpi">
          <span class="k">29-Year CAGR (1997–2025)</span>
          <span class="v" style="color:#2ed573">27.19%</span>
          <span class="sub">vs SPY 9.84% Benchmark</span>
        </div>
        <div class="lyw-kpi">
          <span class="k">Growth of £100</span>
          <span class="v" style="color:#2ed573">£106,995</span>
          <span class="sub">1,070× Multiple vs SPY £1,522</span>
        </div>
        <div class="lyw-kpi">
          <span class="k">Trailing Stops Triggered</span>
          <span class="v">6 in 29 Years</span>
          <span class="sub">Shielded in 2000, 2001, 2002, 2008, 2011</span>
        </div>
        <div class="lyw-kpi">
          <span class="k">Win Rate vs S&amp;P 500</span>
          <span class="v">16 of 29 Years Ahead</span>
          <span class="sub">55.2% Win Rate with Explosive Right Tail</span>
        </div>
      </div>
    </div>
  </section>

  <!-- ── LIVE 2026 POSITION MONITOR ────────────────────────────────────── -->
  <section class="sec wrap" style="padding-top:0">
    <div class="sechd">
      <div>
        <div class="eyebrow">Active 2026 Position · Trading 212 Execution</div>
        <h2>Live Stop-Loss Monitor</h2>
      </div>
      <p class="lede">Real-time surveillance of the 2026 held stock, highest intra-year peak price, 35% trailing stop threshold, and current dollar/percentage safety buffer.</p>
    </div>

    <div class="lyw-live-card rise">
      <div class="lyw-live-grid">
        <div>
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">
            <span class="badge-tag runner">2026 WINNER</span>
            <span class="lyw-status-badge green" id="lywLiveStatusBadge">● STOP UNTOUCHED (+13.7% BUFFER)</span>
          </div>
          <div class="lyw-stock-hero" id="lywLiveTicker">SNDK</div>
          <div class="lyw-stock-sub" id="lywLiveName">SanDisk Corp. · Trading 212 ISA</div>

          <div class="lyw-gauge-box">
            <div style="display:flex;justify-content:space-between;align-items:baseline">
              <span style="font-size:12px;font-weight:600;color:var(--ink)">Trailing Stop Buffer</span>
              <span style="font-family:var(--mono);font-size:13px;font-weight:700;color:var(--s3)" id="lywBufferText">+$138.38 (+13.7%)</span>
            </div>
            <div class="lyw-gauge-track">
              <div class="lyw-gauge-fill" id="lywGaugeFill" style="width: 72%;"></div>
            </div>
            <div class="lyw-gauge-labels">
              <span id="lywStopPriceLbl">Stop: $1,012.51 (-35%)</span>
              <span id="lywPeakPriceLbl">Peak: $1,557.71</span>
            </div>
          </div>
        </div>

        <div>
          <div class="lyw-facts-grid">
            <div class="lyw-fact">
              <span class="k">Live Price</span>
              <span class="v highlight" id="lywLivePrice">$1,150.89</span>
            </div>
            <div class="lyw-fact">
              <span class="k">Highest Peak</span>
              <span class="v" id="lywLivePeak">$1,557.71</span>
            </div>
            <div class="lyw-fact">
              <span class="k">35% Stop Level</span>
              <span class="v" id="lywLiveStop">$1,012.51</span>
            </div>
            <div class="lyw-fact">
              <span class="k">Entry Price</span>
              <span class="v" id="lywLiveEntry">$1,557.71</span>
            </div>
            <div class="lyw-fact">
              <span class="k">Broker</span>
              <span class="v" id="lywLiveBroker">Trading 212</span>
            </div>
            <div class="lyw-fact">
              <span class="k">Reselection</span>
              <span class="v">31 Dec 2026</span>
            </div>
          </div>

          <div style="margin-top:20px;padding-top:16px;border-top:1px solid var(--rule);font-size:12.5px;color:var(--muted);line-height:1.5">
            <b>Execution rule:</b> If SNDK closes at or below <b>$1,012.51</b> on any trading day, sell 100% of the position on the next market open and hold cash until 31 December 2026. If SNDK rallies above <b>$1,557.71</b>, the 35% trailing stop ratchets upward automatically.
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- ── 2027 S&P 500 CONTENDER RACE ────────────────────────────────────── -->
  <section class="sec wrap" style="padding-top:0">
    <div class="sechd">
      <div>
        <div class="eyebrow" style="color:var(--s1)">In-Flight Rebalance Monitor · As of 30 October 2026 market close</div>
        <h2>2027 Reselection Leaderboard</h2>
      </div>
      <p class="lede">Real-time S&amp;P 500 YTD performance. The #1 stock on 31 December 2026 close becomes the sole portfolio holding for 2027.</p>
    </div>

    <!-- 2027 Leaderboard 4 Featured Cards (matching winner.html) -->
    <div class="grid-4col rise" id="cardsLeaderboard2027" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px;margin-bottom:24px">
      <!-- Card 1: Moderna -->
      <div class="engine-card" style="border:2px solid var(--s1);background:var(--surface-sunk);display:flex;flex-direction:column;justify-content:space-between">
        <div>
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
            <span class="badge-tag proj" style="background:var(--s1);color:#fff">Rank 1 · 2027 Target</span>
            <span style="font-family:var(--mono);font-size:12px;font-weight:700;color:var(--s1)">+716.3% YTD</span>
          </div>
          <div style="font-size:26px;font-weight:800;color:var(--ink);letter-spacing:-.02em">MRNA</div>
          <div style="font-size:12px;color:var(--muted);font-weight:500">Moderna Inc.</div>
          <p style="font-size:12px;color:var(--ink-2);line-height:1.52;margin-top:10px">
            Leading the 2026 S&amp;P 500 performance race. If MRNA maintains first place through 31 December, all portfolio capital rotates 100% into MRNA on 2 January 2027.
          </p>
        </div>
        <div style="margin-top:14px;padding-top:10px;border-top:1px solid var(--rule);display:flex;justify-content:space-between;align-items:center;font-size:11.5px">
          <span style="color:var(--muted)">Rotation Action:</span>
          <strong style="color:var(--s1)">Buy at Jan 2027 Open</strong>
        </div>
      </div>

      <!-- Card 2: SanDisk (Current Active Holding) -->
      <div class="engine-card" style="display:flex;flex-direction:column;justify-content:space-between">
        <div>
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
            <span class="badge-tag" style="background:rgba(42,120,214,0.12);color:var(--s1)">Rank 2 · Active Holding</span>
            <span style="font-family:var(--mono);font-size:12px;font-weight:700;color:var(--pos-ink)">+477.4% YTD</span>
          </div>
          <div style="font-size:26px;font-weight:800;color:var(--ink);letter-spacing:-.02em">SNDK</div>
          <div style="font-size:12px;color:var(--muted);font-weight:500">SanDisk Corporation</div>
          <p style="font-size:12px;color:var(--ink-2);line-height:1.52;margin-top:10px">
            Holding the second position in 2026. If SanDisk surges and overtakes Moderna by 31 December, the strategy continues holding SanDisk for a second consecutive year.
          </p>
        </div>
        <div style="margin-top:14px;padding-top:10px;border-top:1px solid var(--rule);display:flex;justify-content:space-between;align-items:center;font-size:11.5px">
          <span style="color:var(--muted)">Current Status:</span>
          <strong style="color:var(--pos-ink)">Active Hold (35% Stop)</strong>
        </div>
      </div>

      <!-- Card 3: Micron -->
      <div class="engine-card" style="display:flex;flex-direction:column;justify-content:space-between">
        <div>
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
            <span class="badge-tag" style="background:var(--surface-sunk);color:var(--muted)">Rank 3 · Contender</span>
            <span style="font-family:var(--mono);font-size:12px;font-weight:700;color:var(--pos-ink)">+295.8% YTD</span>
          </div>
          <div style="font-size:26px;font-weight:800;color:var(--ink);letter-spacing:-.02em">MU</div>
          <div style="font-size:12px;color:var(--muted);font-weight:500">Micron Technology Inc.</div>
          <p style="font-size:12px;color:var(--ink-2);line-height:1.52;margin-top:10px">
            Memory and semiconductor surge. Needs a +106% rally relative to Moderna over the next 45 trading sessions to claim the 2027 holding seat.
          </p>
        </div>
        <div style="margin-top:14px;padding-top:10px;border-top:1px solid var(--rule);display:flex;justify-content:space-between;align-items:center;font-size:11.5px">
          <span style="color:var(--muted)">Distance to #1:</span>
          <strong style="font-family:var(--mono);color:var(--muted)">-420.5% Gap</strong>
        </div>
      </div>

      <!-- Card 4: Dell -->
      <div class="engine-card" style="display:flex;flex-direction:column;justify-content:space-between">
        <div>
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
            <span class="badge-tag" style="background:var(--surface-sunk);color:var(--muted)">Rank 4 · Contender</span>
            <span style="font-family:var(--mono);font-size:12px;font-weight:700;color:var(--pos-ink)">+164.7% YTD</span>
          </div>
          <div style="font-size:26px;font-weight:800;color:var(--ink);letter-spacing:-.02em">DELL</div>
          <div style="font-size:12px;color:var(--muted);font-weight:500">Dell Technologies Inc.</div>
          <p style="font-size:12px;color:var(--ink-2);line-height:1.52;margin-top:10px">
            AI server enterprise growth. Consistent momentum performer, but distant from the current runaway leader Moderna with 62 calendar days remaining.
          </p>
        </div>
        <div style="margin-top:14px;padding-top:10px;border-top:1px solid var(--rule);display:flex;justify-content:space-between;align-items:center;font-size:11.5px">
          <span style="color:var(--muted)">Distance to #1:</span>
          <strong style="font-family:var(--mono);color:var(--muted)">-551.6% Gap</strong>
        </div>
      </div>
    </div>

    <!-- 2026 Contenders Performance Surge Multi-Line Chart -->
    <div class="card rise" style="margin-bottom:24px">
      <div class="card-hd" style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:14px">
        <div>
          <div class="ttl">The 2026 Performance Surge · Race for Next Year's Winner</div>
          <div class="sub">Daily normalized percentage return from 2 January 2026 base. Top 5 contenders with live logo badges vs S&amp;P 500 benchmark.</div>
        </div>
        <div id="chartContendersLegend" class="contenders-legend"></div>
      </div>
      <div class="card-bd" style="padding-inline:14px;padding-block:16px;position:relative">
        <div id="contendersChartContainer" style="width:100%;min-height:460px;position:relative"></div>
        <div id="contendersTooltip" class="contenders-tooltip" style="display:none;position:absolute;pointer-events:none;z-index:50"></div>
      </div>
    </div>

    <div class="card rise">
      <div class="card-hd">
        <div class="ttl">Full S&amp;P 500 Performance Ranking (2026 Year-to-Date)</div>
        <div class="sub" style="margin-left:auto">Winner takes all on first trading day of January 2027</div>
      </div>
      <div class="card-bd">
        <div class="tblwrap">
          <table class="data" id="tblContenders"></table>
        </div>
      </div>
    </div>
  </section>

  <!-- ── 29-YEAR DOT-COM BACKTEST ARCHIVE ──────────────────────────────── -->
  <section class="sec wrap" style="padding-top:0">
    <div class="sechd">
      <div>
        <div class="eyebrow">Complete 29-Year Record (1997–2025)</div>
        <h2>The Dot-Com &amp; Tech Regime Archive</h2>
      </div>
      <p class="lede">Every holding, qualifying prior-year winner return, full-year strategy performance, S&amp;P 500 benchmark return, and trailing stop-loss execution across 29 years.</p>
    </div>

    <div class="card rise">
      <div class="card-hd">
        <div class="ttl">Annual Holdings &amp; Stop-Loss Execution History</div>
        <div class="sub" style="margin-left:auto">35% trailing stop triggered only 6 times in 29 years</div>
      </div>
      <div class="card-bd">
        <div class="tblwrap">
          <table class="data" id="tblLywArchive"></table>
        </div>
      </div>
    </div>
  </section>

  <!-- ── LYW RULES & METHOD ────────────────────────────────────────────── -->
  <section class="sec wrap" style="padding-top:0">
    <div class="sechd">
      <div>
        <div class="eyebrow">Method &amp; Execution Discipline</div>
        <h2>Four Rules, Zero Discretion</h2>
      </div>
      <p class="lede">A systematic mechanical framework designed to capture extraordinary right-tail winners while eliminating catastrophic drawdowns.</p>
    </div>

    <div class="method rise">
      <ol class="steps">
        <li><b>Identify the #1 S&amp;P 500 Winner.</b> At the final market close of December, score every S&amp;P 500 constituent by full calendar-year total return. Select the single top performer.</li>
        <li><b>Hold 100% on the First Trading Day of January.</b> Allocate 100% of the strategy capital into that single stock. Do not diversify; ride the proven institutional momentum current.</li>
        <li><b>Strict 35% Trailing Stop-Loss.</b> Establish a mechanical stop-loss exactly 35% below the highest daily closing price achieved during the holding year. Ratchet upward whenever a new high is formed; never lower the stop.</li>
        <li><b>Exit to Cash on Stop Trigger.</b> If the stock closes at or below the 35% trailing stop level, exit 100% to cash on the next market session. Remain in cash for the remainder of the calendar year.</li>
      </ol>
      <div class="prose">
        <p><b>Why single-stock momentum works.</b> Extreme market winners exhibit intense price persistence driven by structural institutional inflows, index-weight expansion, and earnings acceleration. In 1997–1998, holding Dell produced back-to-back gains of +219% and +253%. In 2019, AMD delivered +160%. In 2020, Tesla delivered +96%.</p>
        <p><b>Why the 35% trailing stop is critical.</b> Momentum winners eventually crash violently. Without a stop-loss, holding Qualcomm through 2000 would have inflicted an -80% wipeout. With the 35% trailing stop, capital was extracted at -35%, preserving cash through the rest of the dot-com bust.</p>
        <p><b>Low trading friction.</b> Exactly one trade per year in normal runner years, and at most two trades in stopped years. Dealing commissions, bid-ask drag, and tax friction are virtually negligible.</p>
      </div>
    </div>
  </section>

</div><!-- /#viewLyw -->
"""

# 6. Combined 50/50 Dual Engine View HTML
COMBINED_VIEW_HTML = """
<!-- ══════════════════════════════════════════════════════════════════════
     COMBINED 50/50 DUAL ENGINE VIEW
     ══════════════════════════════════════════════════════════════════════ -->
<div id="viewCombined" class="strat-view" hidden>

  <!-- ── COMBINED HERO ─────────────────────────────────────────────────── -->
  <section class="sec wrap" style="padding-top:clamp(20px, 3.5vw, 40px)">
    <div class="combined-hero rise">
      <div class="eyebrow" style="color:var(--band-ink-2)">Systematic Compounding Portfolio · 27-Year Track Record</div>
      <div class="wordmark">
        <h1 class="title" style="color:var(--band-ink)"><span style="color:var(--s1)">50 / 50</span> Dual Engine</h1>
        <div class="strap"><i style="background:var(--s1)"></i><span style="color:var(--band-ink-2)">Half Lodestar World · Half Last Year's Winner</span></div>
      </div>
      <p class="deck" style="color:var(--band-ink);max-width:760px;margin-top:14px;line-height:1.55">
        Combines broad macroeconomic factor leadership and systematic cash gate protection with the high-octane right-tail convexity of the #1 S&amp;P 500 momentum runner.
      </p>

      <div class="lyw-hero-grid">
        <div class="lyw-kpi">
          <span class="k">27-Year Blended CAGR (1999–2025)</span>
          <span class="v" style="color:#2ed573">17.55%</span>
          <span class="sub">vs 7.46% MSCI World Core</span>
        </div>
        <div class="lyw-kpi">
          <span class="k">Growth of £100</span>
          <span class="v" style="color:#2ed573">£7,874</span>
          <span class="sub">78.7× Multiple vs £712 Core</span>
        </div>
        <div class="lyw-kpi">
          <span class="k">Win Rate</span>
          <span class="v">22 of 27 Positive Years</span>
          <span class="sub">81.5% Positive Year Probability</span>
        </div>
        <div class="lyw-kpi">
          <span class="k">Max Drawdown</span>
          <span class="v">-50.92%</span>
          <span class="sub">Drawdown Halved vs Single-Stock Pure Crash</span>
        </div>
      </div>
    </div>
  </section>

  <!-- ── ALLOCATION ARCHITECTURE ───────────────────────────────────────── -->
  <section class="sec wrap" style="padding-top:0">
    <div class="sechd">
      <div>
        <div class="eyebrow">Portfolio Blueprint</div>
        <h2>Two Complementary Compounding Engines</h2>
      </div>
      <p class="lede">How the two strategies balance and reinforce each other across market cycles.</p>
    </div>

    <div class="dual-engine-split rise">
      <div class="engine-card">
        <div class="engine-hd">
          <span class="engine-weight">50% ALLOCATION</span>
          <h3 style="margin:0;font-size:17px;font-weight:700;color:var(--s1)">Lodestar World</h3>
        </div>
        <p style="font-size:13.5px;color:var(--ink-2);line-height:1.52;margin-bottom:14px">
          Systematic monthly rotation across five London-listed UCITS ETFs (Value, Momentum, Quality, Small Cap, and Dividend Leaders) with a broad market -25% nineteen-month cash gate.
        </p>
        <ul style="font-size:12.5px;color:var(--muted);line-height:1.6;padding-left:18px;margin:0">
          <li><b>Current Position:</b> 100% IWVL.L (iShares MSCI World Value Factor)</li>
          <li><b>Role:</b> Cushions portfolio drawdowns and rotates into defensive dividend pillars during bear markets.</li>
          <li><b>Execution:</b> Monthly rebalance on first trading day. Stamp duty exempt.</li>
        </ul>
      </div>

      <div class="engine-card">
        <div class="engine-hd">
          <span class="engine-weight">50% ALLOCATION</span>
          <h3 style="margin:0;font-size:17px;font-weight:700;color:#fab219">Last Year's Winner</h3>
        </div>
        <p style="font-size:13.5px;color:var(--ink-2);line-height:1.52;margin-bottom:14px">
          Concentrated single-stock momentum in the #1 top-performing S&amp;P 500 company from the prior calendar year, protected by an automatic 35% trailing stop-loss.
        </p>
        <ul style="font-size:12.5px;color:var(--muted);line-height:1.6;padding-left:18px;margin:0">
          <li><b>Current Position:</b> SanDisk Corp. (SNDK) on Trading 212</li>
          <li><b>Role:</b> Injects extraordinary right-tail compound gains during bull market extensions.</li>
          <li><b>Execution:</b> Annual rebalance in January. 35% trailing stop to cash.</li>
        </ul>
      </div>
    </div>
  </section>

  <!-- ── 27-YEAR BLENDED HISTORY TABLE ─────────────────────────────────── -->
  <section class="sec wrap" style="padding-top:0">
    <div class="sechd">
      <div>
        <div class="eyebrow">Annual Historical Performance (1999–2025)</div>
        <h2>27-Year Blended Compounding Record</h2>
      </div>
      <p class="lede">Year-by-year returns for Lodestar World, Last Year's Winner, and the 50/50 dual engine portfolio.</p>
    </div>

    <div class="card rise">
      <div class="card-hd">
        <div class="ttl">50/50 Dual Engine vs Underlying Components</div>
        <div class="sub" style="margin-left:auto">Rebalanced annually to 50/50 on 1st January</div>
      </div>
      <div class="card-bd">
        <div class="tblwrap">
          <table class="data" id="tblCombined"></table>
        </div>
      </div>
    </div>
  </section>

</div><!-- /#viewCombined -->
"""

# Close #viewLodestar at the end of section appendix and insert LYW and Combined views inside </main>
LODESTAR_END = "</section>\n</div><!-- /#viewLodestar -->\n\n"
html = html.replace(
    "</section>\n\n</main>",
    LODESTAR_END + LYW_VIEW_HTML + "\n" + COMBINED_VIEW_HTML + "\n</main>"
)

# 7. Add JavaScript for Tab Switching, LYW rendering, Dotcom rendering, Combined rendering
EXTRA_JS = """
/* ══════════════════════════════════════════════════════════════════════
   STRATEGY SWITCHER & MULTI-STRATEGY ENGINES
   ══════════════════════════════════════════════════════════════════════ */
(function multiStrategyApp(){
  var tabLodestar = $("#tabLodestar");
  var tabLyw = $("#tabLyw");
  var tabCombined = $("#tabCombined");

  var viewLodestar = $("#viewLodestar");
  var viewLyw = $("#viewLyw");
  var viewCombined = $("#viewCombined");

  var tabs = [tabLodestar, tabLyw, tabCombined];
  var views = [viewLodestar, viewLyw, viewCombined];
  var renderContendersChart = null;

  function switchStrategy(targetId){
    views.forEach(function(v){
      if (v) v.hidden = (v.id !== targetId);
    });
    tabs.forEach(function(t){
      if (t){
        var isActive = (t.getAttribute("data-target") === targetId);
        t.classList.toggle("active", isActive);
        t.setAttribute("aria-selected", isActive ? "true" : "false");
      }
    });

    if (targetId === "viewLodestar"){
      history.replaceState(null, "", "#lodestar");
      document.title = "Lodestar World — Global Factor and Dividend Rotation";
    } else if (targetId === "viewLyw"){
      history.replaceState(null, "", "#lyw");
      document.title = "Last Year's Winner — S&P 500 #1 Momentum & 35% Stop";
      if (typeof renderContendersChart === "function") setTimeout(renderContendersChart, 20);
    } else if (targetId === "viewCombined"){
      history.replaceState(null, "", "#combined");
      document.title = "50/50 Dual Engine — Lodestar World + Last Year's Winner";
    }
  }

  tabs.forEach(function(tab){
    if (tab){
      tab.addEventListener("click", function(){
        switchStrategy(tab.getAttribute("data-target"));
      });
    }
  });

  // Handle URL hash on load
  var initialHash = window.location.hash.toLowerCase();
  if (initialHash === "#lyw"){
    switchStrategy("viewLyw");
  } else if (initialHash === "#combined" || initialHash === "#dual"){
    switchStrategy("viewCombined");
  } else {
    switchStrategy("viewLodestar");
  }

  window.addEventListener("hashchange", function(){
    var h = window.location.hash.toLowerCase();
    if (h === "#lyw") switchStrategy("viewLyw");
    else if (h === "#combined" || h === "#dual") switchStrategy("viewCombined");
    else if (h === "#lodestar") switchStrategy("viewLodestar");
  });

  // ── Helper Table Builder ──
  function buildTable(t, cols, rows){
    if (!t) return;
    t.innerHTML = "";
    var thead = el("thead"), tr = el("tr");
    cols.forEach(function(c){ tr.appendChild(el("th", {scope:"col"}, c)); });
    thead.appendChild(tr); t.appendChild(thead);
    var tb = el("tbody");
    rows.forEach(function(r){
      var x = el("tr");
      r.forEach(function(c, i){
        var cls = c && c.cls ? c.cls : (i === 1 ? "k" : "");
        var td = el("td", {class: cls});
        if (c && c.html !== undefined){
          td.innerHTML = c.html;
        } else if (c && c.v !== undefined){
          td.textContent = c.v;
        } else {
          td.textContent = (c != null ? c : "");
        }
        x.appendChild(td);
      });
      tb.appendChild(x);
    });
    t.appendChild(tb);
  }

  // ── 1. Era Switcher in Lodestar ──
  var btnModern = $("#btnEraModern");
  var btnDotcom = $("#btnEraDotcom");
  var panelDotcom = $("#panelDotcom");

  if (btnModern && btnDotcom && panelDotcom){
    btnModern.addEventListener("click", function(){
      btnModern.classList.add("active");
      btnModern.setAttribute("aria-pressed", "true");
      btnDotcom.classList.remove("active");
      btnDotcom.setAttribute("aria-pressed", "false");
      panelDotcom.hidden = true;
    });

    btnDotcom.addEventListener("click", function(){
      btnDotcom.classList.add("active");
      btnDotcom.setAttribute("aria-pressed", "true");
      btnModern.classList.remove("active");
      btnModern.setAttribute("aria-pressed", "false");
      panelDotcom.hidden = false;
    });
  }

  // Render Dotcom Table
  if (DATA.dotcom && DATA.dotcom.years){
    var dcRows = DATA.dotcom.years.map(function(y){
      return [
        String(y.year),
        {v: sgn(y.strategy), cls: "k"},
        sgn(y.benchmark),
        {v: sgnpp(y.excess), cls: y.excess >= 0 ? "pos-val" : "neg-val"},
        {v: "£" + (y.wealth ? Number(y.wealth).toLocaleString() : "—"), cls: "k"},
        {v: "£" + (y.benchmarkWealth ? Number(y.benchmarkWealth).toLocaleString() : "—"), cls: ""}
      ];
    });
    buildTable($("#tblDotcom"), ["Year", "Lodestar World", "MSCI World Core", "Excess Alpha", "Lodestar Balance (£10k)", "MSCI World Balance (£10k)"], dcRows);
  }

  // ── 2. LYW Live Position & Contenders ──
  if (DATA.lyw){
    var lp = DATA.lyw.livePosition;
    if (lp){
      var badge = $("#lywLiveStatusBadge");
      if (badge){
        badge.textContent = lp.statusLabel;
        badge.className = "lyw-status-badge " + (lp.isStopped ? "red" : "green");
      }
      var tTicker = $("#lywLiveTicker");
      if (tTicker) tTicker.textContent = lp.ticker;
      var tName = $("#lywLiveName");
      if (tName) tName.textContent = lp.name + " · " + lp.broker;

      var bText = $("#lywBufferText");
      if (bText) bText.textContent = "+$" + lp.bufferDollars.toFixed(2) + " (+" + lp.bufferPercent.toFixed(1) + "%)";

      var gFill = $("#lywGaugeFill");
      if (gFill){
        var pctVal = Math.min(100, Math.max(5, lp.bufferPercent * 2.5));
        gFill.style.width = pctVal + "%";
      }

      var sLbl = $("#lywStopPriceLbl");
      if (sLbl) sLbl.textContent = "Stop: $" + lp.stopLossPrice.toFixed(2) + " (-35%)";
      var pLbl = $("#lywPeakPriceLbl");
      if (pLbl) pLbl.textContent = "Peak: $" + lp.peakPrice.toFixed(2);

      var pLive = $("#lywLivePrice");
      if (pLive) pLive.textContent = "$" + lp.currentPrice.toFixed(2);
      var pPeak = $("#lywLivePeak");
      if (pPeak) pPeak.textContent = "$" + lp.peakPrice.toFixed(2);
      var pStop = $("#lywLiveStop");
      if (pStop) pStop.textContent = "$" + lp.stopLossPrice.toFixed(2);
      var pEntry = $("#lywLiveEntry");
      if (pEntry) pEntry.textContent = "$" + lp.entryPrice.toFixed(2);
      var pBroker = $("#lywLiveBroker");
      if (pBroker) pBroker.textContent = lp.broker;
    }

    // Render Top 4 Contender Cards Dynamically
    var cardsBox = $("#cardsLeaderboard2027");
    if (cardsBox && DATA.lyw.race2027 && DATA.lyw.race2027.length >= 4){
      cardsBox.innerHTML = "";
      DATA.lyw.race2027.slice(0, 4).forEach(function(c){
        var isLeader = (c.rank === 1);
        var isHolder = (c.ticker === "SNDK");
        var cardDiv = el("div", {
          class: "engine-card",
          style: (isLeader ? "border:2px solid var(--s1);background:var(--surface-sunk);" : "") + "display:flex;flex-direction:column;justify-content:space-between"
        });
        var tagBg = isLeader ? "var(--s1)" : (isHolder ? "rgba(42,120,214,0.12)" : "var(--surface-sunk)");
        var tagColor = isLeader ? "#fff" : (isHolder ? "var(--s1)" : "var(--muted)");
        var retColor = isLeader ? "var(--s1)" : "var(--pos-ink)";
        var logoImg = c.logo ? '<img src="' + c.logo + '" class="contenders-pill-logo" style="width:28px;height:28px;margin-right:10px;vertical-align:middle;border-radius:50%;object-fit:cover;border:1px solid var(--rule-2);background:#fff" alt="' + c.ticker + '" onerror="this.hidden=true">' : '';

        cardDiv.innerHTML = '<div>' +
          '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">' +
            '<span class="badge-tag proj" style="background:' + tagBg + ';color:' + tagColor + '">' + c.status + '</span>' +
            '<span style="font-family:var(--mono);font-size:12px;font-weight:700;color:' + retColor + '">+' + c.ytd.toFixed(1) + '% YTD</span>' +
          '</div>' +
          '<div style="display:flex;align-items:center;gap:4px">' +
            logoImg +
            '<div>' +
              '<div style="font-size:24px;font-weight:800;color:var(--ink);letter-spacing:-.02em;line-height:1.1">' + c.ticker + '</div>' +
              '<div style="font-size:12px;color:var(--muted);font-weight:500">' + c.name + '</div>' +
            '</div>' +
          '</div>' +
          '<p style="font-size:12px;color:var(--ink-2);line-height:1.52;margin-top:12px">' + c.desc + '</p>' +
        '</div>' +
        '<div style="margin-top:14px;padding-top:10px;border-top:1px solid var(--rule);display:flex;justify-content:space-between;align-items:center;font-size:11.5px">' +
          '<span style="color:var(--muted)">' + (isLeader ? "Rotation Action:" : (isHolder ? "Current Status:" : "Distance to #1:")) + '</span>' +
          '<strong style="' + (isLeader ? "color:var(--s1)" : (isHolder ? "color:var(--pos-ink)" : "font-family:var(--mono);color:var(--muted)")) + '">' + c.action + '</strong>' +
        '</div>';
        cardsBox.appendChild(cardDiv);
      });
    }

    // Render Full Contenders Table with Logos
    if (DATA.lyw.race2027){
      var cRows = DATA.lyw.race2027.map(function(c){
        var isHolder = (c.ticker === "SNDK");
        var logoImg = c.logo ? '<img src="' + c.logo + '" style="width:20px;height:20px;border-radius:50%;object-fit:cover;vertical-align:middle;margin-right:8px;border:1px solid var(--rule-2);background:#fff" onerror="this.hidden=true">' : '';
        return [
          {v: "#" + c.rank, cls: isHolder ? "k pos-val" : "k"},
          {html: '<div style="display:flex;align-items:center">' + logoImg + '<strong style="font-size:13px">' + c.ticker + '</strong></div>', cls: isHolder ? "k pos-val" : "k"},
          {v: c.name + (isHolder ? " (Active 2026 Holding)" : ""), cls: isHolder ? "pos-val" : ""},
          {v: sgn(c.ytd, 1), cls: "k"},
          c.rank === 1 ? "Leader" : sgnpp(c.gap, 1),
          {v: c.status, cls: c.rank === 1 ? "pos-val" : (isHolder ? "pos-val" : "")}
        ];
      });
      buildTable($("#tblContenders"), ["Rank", "Contender", "Company", "2026 YTD Return", "Gap to Leader", "Status"], cRows);
    }

    // Render 2026 Performance Surge Multi-Line SVG Chart
    renderContendersChart = function(){
      var container = $("#contendersChartContainer");
      var legend = $("#chartContendersLegend");
      var tooltip = $("#contendersTooltip");
      if (!container || !DATA.lyw || !DATA.lyw.contendersChart) return;

      var chartData = DATA.lyw.contendersChart;
      var dates = chartData.dates || [];
      var seriesList = chartData.series || [];
      if (!dates.length || !seriesList.length) return;

      var W = 1000, H = 460;
      var padL = 60, padR = 175, padT = 32, padB = 44;
      var pw = W - padL - padR;
      var ph = H - padT - padB;
      var N = dates.length;

      var yMax = 800;
      var yMin = -20;
      function xPos(i){ return padL + pw * (i / (N - 1)); }
      function yPos(val){ return padT + ph * (1 - (val - yMin) / (yMax - yMin)); }

      var activeTicker = null;

      function updateChart(){
        var svg = [];
        svg.push('<svg viewBox="0 0 ' + W + ' ' + H + '" style="width:100%;height:auto;display:block;overflow:visible;font-family:var(--sans)">');

        // Y-Axis Horizontal Gridlines & Ticks
        var yTicks = [0, 100, 200, 300, 400, 500, 600, 700, 800];
        yTicks.forEach(function(yt){
          var y = yPos(yt);
          var isZero = (yt === 0);
          svg.push('<line x1="' + padL + '" y1="' + y.toFixed(1) + '" x2="' + (padL + pw) + '" y2="' + y.toFixed(1) + '" stroke="' + (isZero ? 'var(--rule-2)' : 'var(--rule)') + '" stroke-width="' + (isZero ? '1.5' : '1') + '" stroke-dasharray="' + (isZero ? 'none' : '3,4') + '" />');
          var lbl = (yt > 0 ? '+' : '') + yt + '%';
          svg.push('<text x="' + (padL - 10) + '" y="' + (y + 4).toFixed(1) + '" text-anchor="end" font-family="var(--mono)" font-size="11" fill="var(--muted)">' + lbl + '</text>');
        });

        // X-Axis Vertical Months & Labels
        var monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
        var lastMonth = "";
        dates.forEach(function(dStr, i){
          var mStr = dStr.slice(0, 7);
          if (mStr !== lastMonth){
            lastMonth = mStr;
            var x = xPos(i);
            var mIdx = parseInt(dStr.slice(5, 7), 10) - 1;
            svg.push('<line x1="' + x.toFixed(1) + '" y1="' + padT + '" x2="' + x.toFixed(1) + '" y2="' + (padT + ph) + '" stroke="var(--rule)" stroke-width="1" stroke-dasharray="2,5" opacity="0.6" />');
            svg.push('<text x="' + x.toFixed(1) + '" y="' + (H - padB + 18) + '" text-anchor="middle" font-size="11.5" font-weight="600" fill="var(--ink-2)">' + monthNames[mIdx] + '</text>');
          }
        });

        // Plot Area Border
        svg.push('<rect x="' + padL + '" y="' + padT + '" width="' + pw + '" height="' + ph + '" fill="none" stroke="var(--rule)" stroke-width="1" />');

        // Paths for Contender Series
        seriesList.forEach(function(s){
          var isDimmed = (activeTicker && activeTicker !== s.ticker);
          var isHighlighted = (activeTicker === s.ticker);
          var isBench = (s.ticker === "SPY");
          var strokeW = isHighlighted ? "3.8" : (isBench ? "1.6" : "2.6");
          var op = isDimmed ? "0.15" : "1.0";

          var d = s.points.map(function(pt, i){
            return (i === 0 ? "M " : "L ") + xPos(i).toFixed(1) + " " + yPos(pt).toFixed(1);
          }).join(" ");

          svg.push('<path id="seriesPath-' + s.ticker + '" d="' + d + '" fill="none" stroke="' + s.color + '" stroke-width="' + strokeW + '" ' + (isBench ? 'stroke-dasharray="4,4"' : '') + ' opacity="' + op + '" style="transition:all .15s ease" />');
        });

        // Peak Markers for Top Leaders
        seriesList.forEach(function(s){
          if (s.rank === 1 || s.ticker === "SNDK"){
            var isDimmed = (activeTicker && activeTicker !== s.ticker);
            var op = isDimmed ? "0.15" : "1.0";
            var peakVal = s.peakYtd;
            var peakIdx = s.points.indexOf(peakVal);
            if (peakIdx >= 0){
              var px = xPos(peakIdx);
              var py = yPos(peakVal);
              svg.push('<circle cx="' + px.toFixed(1) + '" cy="' + py.toFixed(1) + '" r="4.5" fill="' + s.color + '" stroke="#fff" stroke-width="1.8" opacity="' + op + '" />');
              var peakLbl = s.ticker + " Peak: +" + peakVal + "%";
              svg.push('<rect x="' + (px - 58).toFixed(1) + '" y="' + (py - 24).toFixed(1) + '" width="116" height="18" rx="4" fill="var(--surface)" stroke="' + s.color + '" stroke-width="1" opacity="' + op + '" />');
              svg.push('<text x="' + px.toFixed(1) + '" y="' + (py - 11).toFixed(1) + '" text-anchor="middle" font-size="10" font-family="var(--mono)" font-weight="700" fill="' + s.color + '" opacity="' + op + '">' + peakLbl + '</text>');
            }
          }
        });

        // Badges on Right Margin (with Logos & Collision Avoidance)
        var badges = seriesList.map(function(s, idx){
          var lastVal = s.points[s.points.length - 1];
          var origY = yPos(lastVal);
          return {
            s: s,
            ticker: s.ticker,
            name: s.name,
            color: s.color,
            logo: s.logo,
            val: lastVal,
            origY: origY,
            y: origY,
            idx: idx
          };
        });
        badges.sort(function(a, b){ return a.y - b.y; });

        // Relaxation for badges to avoid overlap
        var minDist = 34;
        for (var p = 0; p < 8; p++){
          for (var i = 1; i < badges.length; i++){
            if (badges[i].y - badges[i-1].y < minDist){
              var diff = minDist - (badges[i].y - badges[i-1].y);
              badges[i-1].y -= diff * 0.5;
              badges[i].y += diff * 0.5;
            }
          }
        }
        badges.forEach(function(b){
          if (b.y < padT + 14) b.y = padT + 14;
          if (b.y > H - padB - 14) b.y = H - padB - 14;
        });

        // Render Right Margin Badges
        badges.forEach(function(b){
          var isDimmed = (activeTicker && activeTicker !== b.ticker);
          var op = isDimmed ? "0.15" : "1.0";
          var bx = padL + pw;

          // Connector line if displaced
          if (Math.abs(b.y - b.origY) > 3){
            svg.push('<path d="M ' + bx + ' ' + b.origY.toFixed(1) + ' C ' + (bx + 8) + ' ' + b.origY.toFixed(1) + ', ' + (bx + 8) + ' ' + b.y.toFixed(1) + ', ' + (bx + 14) + ' ' + b.y.toFixed(1) + '" fill="none" stroke="' + b.color + '" stroke-width="1.2" opacity="' + op + '" />');
          } else {
            svg.push('<line x1="' + bx + '" y1="' + b.origY.toFixed(1) + '" x2="' + (bx + 14) + '" y2="' + b.y.toFixed(1) + '" stroke="' + b.color + '" stroke-width="1.2" opacity="' + op + '" />');
          }

          // Circular Logo Badge
          var cx = bx + 28;
          var cy = b.y;
          if (b.logo){
            svg.push('<g opacity="' + op + '">');
            svg.push('<circle cx="' + cx + '" cy="' + cy.toFixed(1) + '" r="12" fill="#fff" stroke="' + b.color + '" stroke-width="1.8" />');
            svg.push('<image href="' + b.logo + '" x="' + (cx - 10) + '" y="' + (cy - 10).toFixed(1) + '" width="20" height="20" preserveAspectRatio="xMidYMid slice" />');
            svg.push('</g>');
          } else {
            svg.push('<circle cx="' + cx + '" cy="' + cy.toFixed(1) + '" r="11" fill="var(--surface-sunk)" stroke="' + b.color + '" stroke-width="1.8" opacity="' + op + '" />');
            svg.push('<text x="' + cx + '" y="' + (cy + 3.5).toFixed(1) + '" text-anchor="middle" font-size="9" font-weight="700" fill="' + b.color + '" opacity="' + op + '">SPY</text>');
          }

          // Ticker & Percentage Labels
          svg.push('<g opacity="' + op + '">');
          svg.push('<text x="' + (cx + 17) + '" y="' + (cy - 1).toFixed(1) + '" font-size="12" font-weight="700" fill="' + b.color + '">' + b.ticker + '</text>');
          var valSign = b.val >= 0 ? "+" : "";
          svg.push('<text x="' + (cx + 17) + '" y="' + (cy + 12).toFixed(1) + '" font-family="var(--mono)" font-size="11" font-weight="600" fill="var(--ink)">' + valSign + b.val.toFixed(1) + '%</text>');
          svg.push('</g>');
        });

        // Hover Crosshair Elements (hidden by default)
        svg.push('<g id="hoverGroup" style="display:none">');
        svg.push('<line id="hoverGuideLine" x1="0" y1="' + padT + '" x2="0" y2="' + (padT + ph) + '" stroke="var(--ink)" stroke-width="1" stroke-dasharray="3,3" opacity="0.75" />');
        seriesList.forEach(function(s, idx){
          svg.push('<circle id="hoverDot-' + idx + '" cx="0" cy="0" r="5" fill="' + s.color + '" stroke="#fff" stroke-width="2" />');
        });
        svg.push('</g>');

        // Interactive Overlay Rect
        svg.push('<rect id="chartOverlay" x="' + padL + '" y="' + padT + '" width="' + pw + '" height="' + ph + '" fill="transparent" style="cursor:crosshair" />');
        svg.push('</svg>');

        container.innerHTML = svg.join("");
        attachHoverEvents();
      }

      function attachHoverEvents(){
        var overlay = $("#chartOverlay");
        var hoverGroup = $("#hoverGroup");
        var guideLine = $("#hoverGuideLine");
        if (!overlay || !hoverGroup || !guideLine) return;

        overlay.addEventListener("mousemove", handlePointer);
        overlay.addEventListener("touchmove", handlePointer);
        overlay.addEventListener("mouseleave", hideHover);
        overlay.addEventListener("touchend", hideHover);

        function handlePointer(e){
          var rect = overlay.getBoundingClientRect();
          var clientX = e.touches ? e.touches[0].clientX : e.clientX;
          var clientY = e.touches ? e.touches[0].clientY : e.clientY;
          var frac = (clientX - rect.left) / rect.width;
          if (frac < 0) frac = 0;
          if (frac > 1) frac = 1;
          var idx = Math.round(frac * (N - 1));
          idx = Math.max(0, Math.min(N - 1, idx));

          hoverGroup.style.display = "block";
          var x = xPos(idx);
          guideLine.setAttribute("x1", x.toFixed(1));
          guideLine.setAttribute("x2", x.toFixed(1));

          var dateStr = dates[idx];
          var sortedDay = seriesList.map(function(s, sIdx){
            var val = s.points[idx];
            return { s: s, val: val, sIdx: sIdx, y: yPos(val) };
          }).sort(function(a, b){ return b.val - a.val; });

          seriesList.forEach(function(s, sIdx){
            var dot = $("#hoverDot-" + sIdx);
            if (dot){
              var y = yPos(s.points[idx]);
              dot.setAttribute("cx", x.toFixed(1));
              dot.setAttribute("cy", y.toFixed(1));
              var isDimmed = (activeTicker && activeTicker !== s.ticker);
              dot.style.opacity = isDimmed ? "0.15" : "1.0";
            }
          });

          // Tooltip HTML
          var ttHtml = ['<div class="contenders-tooltip-hd"><span>' + dateStr + '</span><span>Day ' + (idx + 1) + '/' + N + '</span></div>'];
          sortedDay.forEach(function(item){
            var logoImg = item.s.logo ? '<img src="' + item.s.logo + '" style="width:14px;height:14px;border-radius:50%;object-fit:cover;vertical-align:middle;margin-right:5px;background:#fff">' : '';
            var valSign = item.val >= 0 ? "+" : "";
            ttHtml.push('<div class="contenders-tooltip-row">');
            ttHtml.push('<div class="contenders-tooltip-name">' + logoImg + '<strong style="color:' + item.s.color + '">' + item.s.ticker + '</strong><span style="color:var(--muted);font-size:11px">' + item.s.name.split(" ")[0] + '</span></div>');
            ttHtml.push('<div class="contenders-tooltip-val" style="color:' + item.s.color + '">' + valSign + item.val.toFixed(1) + '%</div>');
            ttHtml.push('</div>');
          });

          tooltip.innerHTML = ttHtml.join("");
          tooltip.style.display = "block";

          var cRect = container.getBoundingClientRect();
          var tipX = clientX - cRect.left + 15;
          var tipY = clientY - cRect.top + 10;
          if (tipX + 260 > cRect.width) tipX = clientX - cRect.left - 270;
          if (tipY + 220 > cRect.height) tipY = cRect.height - 230;
          if (tipY < 0) tipY = 10;
          tooltip.style.left = tipX + "px";
          tooltip.style.top = tipY + "px";
        }

        function hideHover(){
          hoverGroup.style.display = "none";
          tooltip.style.display = "none";
        }
      }

      function renderLegend(){
        if (!legend) return;
        legend.innerHTML = "";
        var allBtn = el("button", {
          class: "contenders-pill" + (!activeTicker ? " active" : ""),
          type: "button"
        }, "All Contenders");
        allBtn.addEventListener("click", function(){
          activeTicker = null;
          renderLegend();
          updateChart();
        });
        legend.appendChild(allBtn);

        seriesList.forEach(function(s){
          var isAct = (activeTicker === s.ticker);
          var btn = el("button", {
            class: "contenders-pill" + (isAct ? " active" : ""),
            type: "button"
          });
          if (s.logo){
            var img = el("img", {
              src: s.logo,
              class: "contenders-pill-logo",
              alt: s.ticker
            });
            btn.appendChild(img);
          }
          var nameSpan = el("span", {}, s.ticker);
          btn.appendChild(nameSpan);
          var valSpan = el("strong", {
            style: "color:" + s.color + ";font-family:var(--mono);font-size:11px"
          }, (s.currentYtd >= 0 ? "+" : "") + s.currentYtd.toFixed(1) + "%");
          btn.appendChild(valSpan);

          btn.addEventListener("click", function(){
            activeTicker = isAct ? null : s.ticker;
            renderLegend();
            updateChart();
          });
          legend.appendChild(btn);
        });
      }

      renderLegend();
      updateChart();
    }

    renderContendersChart();
    window.addEventListener("resize", function(){
      renderContendersChart();
    });

    // Render LYW 29-Year Archive
    if (DATA.lyw.archive){
      var lywRows = DATA.lyw.archive.map(function(a){
        var statusStr = a.stopped ? "Stopped (-35.0%)" : "Full Runner";
        return [
          String(a.year),
          {v: a.ticker + " (" + a.name + ")", cls: "k"},
          sgn(a.priorWinnerReturn, 1),
          {v: sgn(a.return), cls: "k"},
          sgn(a.benchmarkReturn),
          {v: sgnpp(a.excess), cls: a.excess >= 0 ? "pos-val" : "neg-val"},
          {v: statusStr, cls: a.stopped ? "neg-val" : "pos-val"},
          {v: "$" + (a.wealth ? Number(a.wealth).toLocaleString() : "—"), cls: "k font-bold"},
          {v: "$" + (a.benchmarkWealth ? Number(a.benchmarkWealth).toLocaleString() : "—"), cls: ""}
        ];
      });
      buildTable($("#tblLywArchive"),
        ["Year", "Held Stock", "Prior Win Score", "LYW Return", "SPY Return", "Excess Alpha", "Stop Outcome", "LYW Balance ($10k)", "SPY Balance ($10k)"],
        lywRows);
    }
  }

  // ── 3. Combined 50/50 Dual Engine ──
  if (DATA.combined && DATA.combined.years){
    var combRows = DATA.combined.years.map(function(y){
      return [
        String(y.year),
        {v: sgn(y.lodestar), cls: "k"},
        {v: sgn(y.lyw), cls: "k"},
        {v: sgn(y.blend), cls: "k", style: "font-weight:700"},
        {v: y.blend >= 0 ? "Positive" : "Negative", cls: y.blend >= 0 ? "pos-val" : "neg-val"}
      ];
    });
    buildTable($("#tblCombined"),
      ["Year", "Lodestar World (50%)", "Last Year's Winner (50%)", "Combined 50/50 Return", "Outcome"],
      combRows);
  }
})();
"""

# Insert EXTRA_JS right before the last closing script tag
html = html.replace("applyTheme();   // stamps the theme and performs the first (animated) render", EXTRA_JS + "\napplyTheme();   // stamps the theme and performs the first (animated) render")

OUT_HTML.write_text(html, encoding="utf-8")
print(f"Successfully generated updated {OUT_HTML} ({len(html)} bytes)")
