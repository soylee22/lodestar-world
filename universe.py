"""Lodestar World universe: 5 London-listed global UCITS ETFs.

Four MSCI World factors and one developed markets dividend leader:
  - IWMO.L: iShares Edge MSCI World Momentum Factor UCITS ETF
  - IWQU.L: iShares Edge MSCI World Quality Factor UCITS ETF
  - IWVL.L: iShares Edge MSCI World Value Factor UCITS ETF
  - WSML.L: iShares MSCI World Small Cap UCITS ETF
  - TDGB.L: VanEck Developed Markets Dividend Leaders UCITS ETF

Benchmarks:
  - VWRL.L: Vanguard FTSE All-World UCITS ETF
  - VUSA.L: Vanguard S&P 500 UCITS ETF
  - SWDA.L: iShares Core MSCI World UCITS ETF
"""

FACTOR = {
    "WLD_MOM":   "703022",   # MSCI World Momentum Index
    "WLD_QUAL":  "702787",   # MSCI World Sector Neutral Quality Index
    "WLD_VAL":   "705380",   # MSCI World Enhanced Value Index
    "WLD_SMALL": "105804",   # MSCI World Small Cap Index
    "WLD_DIV":   "NL0011683594", # VanEck Developed Markets Dividend Leaders
}

BENCHMARKS = {
    "allworld": ("VWRL.L", "FTSE All-World"),
    "sp500":    ("VUSA.L", "S&P 500"),
    "world":    ("SWDA.L", "MSCI World"),
}

FACTOR_NAMES = {
    "WLD_MOM":   "World Momentum",
    "WLD_QUAL":  "World Quality",
    "WLD_VAL":   "World Value",
    "WLD_SMALL": "World Small Cap",
    "WLD_DIV":   "Dividend Leaders",
}

STYLES = [
    ("MOM", "Momentum"),
    ("QUAL", "Quality"),
    ("VAL", "Value"),
    ("SMALL", "Size"),
    ("DIV", "Dividend"),
]

TRADABLE = {
    "WLD_MOM":   ("IE00BP3QZ825", "IS3R.DE", "IWMO.L",  "IWMO"),
    "WLD_QUAL":  ("IE00BP3QZ601", "IS3Q.DE", "IWQU.L",  "IWQU"),
    "WLD_VAL":   ("IE00BP3QZB59", "IS3S.DE", "IWVL.L",  "IWVL"),
    "WLD_SMALL": ("IE00BF4RFH31", "IUSN.DE", "WSML.L",  "WSML"),
    "WLD_DIV":   ("NL0011683594", "TDIV.AS", "TDGB.L",  "TDIV"),
}

FACTOR_SLOTS = list(FACTOR)
SLOT_NAMES = FACTOR_NAMES
