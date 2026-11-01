# Lodestar World

Systematic ETF rotation strategy across five London-listed global UCITS ETFs, evaluated on trailing eight-month momentum with a defensive cash filter.

Live site: [https://soylee22.github.io/lodestar-world/](https://soylee22.github.io/lodestar-world/)

---

## Strategy Universe

Five London-listed, ISA/SIPP-eligible physical UCITS ETFs covering major equity factors and defensive dividend leaders across developed world markets:

| Code | Ticker | Name | ISIN | Factor / Style |
|---|---|---|---|---|
| `WLD_MOM` | `IWMO.L` | iShares Edge MSCI World Momentum Factor | `IE00BP3QZ825` | Momentum |
| `WLD_QUAL` | `IWQU.L` | iShares Edge MSCI World Quality Factor | `IE00BP3QZ601` | Quality |
| `WLD_VAL` | `IWVL.L` | iShares Edge MSCI World Value Factor | `IE00BP3QZB59` | Enhanced Value |
| `WLD_SMALL` | `WSML.L` | iShares MSCI World Small Cap | `IE00BF4RFH31` | Small Cap Size |
| `WLD_DIV` | `TDGB.L` | VanEck Developed Markets Dividend Leaders | `NL0011683594` | Dividend Yield & Quality |

### Benchmarks
- **FTSE All-World**: `VWRL.L` (Vanguard FTSE All-World UCITS ETF)
- **S&P 500**: `VUSA.L` (Vanguard S&P 500 UCITS ETF)
- **MSCI World**: `SWDA.L` (iShares Core MSCI World UCITS ETF)

---

## Strategy Rules

1. **Ranking:** At each month-end close, rank all five ETFs on their trailing eight-month total return in sterling (GBP).
2. **Allocation:** Hold 100% of the single top-ranking ETF.
3. **Rebalancing:** Trade on the first London trading day of the new month only if the top pick has changed.
4. **Cash Filter:** Move 100% to cash if the S&P 500 drops more than 25% below its close 19 months earlier.

---

## Performance Summary (Feb 2017 – Oct 2026)

| Metric | Lodestar World | FTSE All-World | S&P 500 | MSCI World |
|---|---|---|---|---|
| **CAGR** | **16.30%** | 11.31% | 13.96% | 11.95% |
| **Volatility** | 13.01% | 11.61% | 13.00% | 11.90% |
| **Sharpe Ratio (rf=2%)** | **1.10** | 0.80 | 0.92 | 0.84 |
| **Sortino Ratio** | **1.97** | 1.18 | 1.34 | 1.25 |
| **Max Drawdown** | **-13.38%** | -15.48% | -15.70% | -14.95% |
| **Growth of £1** | **£4.36** | £2.84 | £3.58 | £3.01 |
| **Positive Years** | **10 / 10 (100%)** | 7 / 10 | 8 / 10 | 7 / 10 |

### Calendar Year Returns (GBP Total Return)

| Year | Lodestar World | FTSE All-World | Excess vs All-World | Active Holdings |
|---|---|---|---|---|
| **2017** | +11.93% | +13.25% | -1.32pp | `IWMO.L`, `IWQU.L` |
| **2018** | **+1.45%** | -4.70% | **+6.15pp** | `IWMO.L`, `IWQU.L`, `WSML.L` |
| **2019** | **+22.26%** | +22.03% | +0.23pp | `IWQU.L`, `IWMO.L` |
| **2020** | **+19.96%** | +12.13% | **+7.83pp** | `IWMO.L`, `IWQU.L` |
| **2021** | **+21.16%** | +20.04% | +1.12pp | `IWVL.L`, `WSML.L`, `IWMO.L` |
| **2022** | **+7.67%** | -8.44% | **+16.11pp** | `TDGB.L`, `IWVL.L` |
| **2023** | +7.81% | +15.61% | -7.80pp | `TDGB.L`, `IWQU.L` |
| **2024** | **+28.26%** | +19.60% | **+8.66pp** | `IWMO.L`, `IWQU.L` |
| **2025** | **+23.54%** | +13.99% | **+9.54pp** | `IWMO.L`, `IWQU.L`, `IWVL.L` |
| **2026 YTD** | **+17.41%** | +11.12% | **+6.29pp** | `IWVL.L` |

---

## Repository Structure

```
lodestar-world/
├── index.html                 # Institutional frontend dashboard
├── data.js                    # Precompiled data literal consumed by index.html
├── build_data.py              # Compiles data.js from data/*.csv
├── daily.py                   # Intraday / intra-month momentum drumbeat monitor
├── run_monthly.py             # Monthly rebalance job & alert dispatcher
├── universe.py                # ETF definitions, tickers, ISINs, and benchmarks
├── pipeline/
│   ├── build.py               # Rebuilds the track record and monthly signals
│   ├── holdings.py            # Fetches fund lookthrough holdings & fundamentals
│   ├── issuer_holdings.py     # Direct issuer disclosure parsers
│   ├── lookthrough.py         # Company domain & portfolio consolidation
│   └── logos.py               # Favicon & logo cache
├── data/
│   ├── final_book.csv         # Complete monthly holding history
│   ├── final_tradable.csv     # Monthly returns for strategy and benchmarks
│   ├── final_tradable_annual.csv # Calendar year returns
│   ├── fund_prices_gbp.csv    # Underlying monthly total return price series
│   ├── holdings.json          # Lookthrough data for current holding
│   └── signal.json            # Current month-end signal
└── .github/workflows/
    ├── daily.yml              # Weekday morning drumbeat monitor
    └── monthly.yml            # Automated month-end signal computation & site build
```

---

## Local Usage

### Requirements
```bash
pip install -r requirements.txt
```

### Daily Drumbeat Monitor
Check current intraday momentum standings:
```bash
python daily.py
```

### Monthly Signal & Page Rebuild
Compute the latest month-end signal and compile `data.js`:
```bash
python run_monthly.py
```

### View Website Locally
Open `index.html` in any browser:
```bash
open index.html
```
