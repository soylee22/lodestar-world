#!/usr/bin/env python3
"""Monthly job for Lodestar World: recompute signal, rebuild page, send alert.

Run by .github/workflows/monthly.yml on the 1st of each month, before the
London open. Safe to run by hand at any time.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"

sys.path.insert(0, str(HERE))
from pipeline import build       # noqa: E402
from pipeline import holdings    # noqa: E402
from notify import telegram      # noqa: E402
from mailer import email         # noqa: E402
from universe import FACTOR_NAMES  # noqa: E402

STATE = DATA / "last_alert.json"


def already_alerted(month: str, pick: str) -> bool:
    if not STATE.is_file():
        return False
    try:
        prev = json.loads(STATE.read_text())
        return prev.get("month") == month and prev.get("pick") == pick
    except Exception:
        return False


def record_alert(month: str, pick: str) -> None:
    STATE.write_text(json.dumps({
        "month": month,
        "pick": pick,
        "sent": date.today().isoformat(),
    }, indent=2))


def _plain(html: str) -> str:
    for a, b in (("<b>", ""), ("</b>", ""), ("<i>", ""), ("</i>", ""),
                 ("<code>", ""), ("</code>", ""), ("&amp;", "&")):
        html = html.replace(a, b)
    return html


def announce(subject: str, msg: str) -> bool:
    ok = telegram(msg)
    body = ('<div style="font-family:-apple-system,Segoe UI,Helvetica,Arial,sans-serif;'
            'font-size:15px;line-height:1.5;max-width:640px">'
            + msg.replace("\n", "<br>") + '</div>')
    email(subject, _plain(msg), body)
    return ok


def main(build_only=False) -> int:
    signal = build.main()
    try:
        holdings.build(signal)
    except Exception as e:
        print(f"  !! holdings refresh failed ({type(e).__name__}); keeping previous")

    subprocess.run([sys.executable, str(HERE / "build_data.py")], check=True)
    if build_only:
        print("Page rebuilt. Alert state unchanged.")
        return 0

    prev = signal.get("previous", {})
    pick = signal["pick"]
    ticker = signal["ticker"]
    is_cash = signal["cash"]
    sig_m = signal["signal_month"]
    hold_m = signal["holding_month"]

    if is_cash:
        msg = (
            f"<b>Lodestar World — GO TO CASH</b>\n\n"
            f"Signal for {sig_m}: the broad market sits more than 25% below its "
            f"level nineteen months ago, so <b>move 100% to cash</b>.\n\n"
            f"Sell {FACTOR_NAMES.get(prev.get('pick'), prev.get('pick'))}. "
            f"Hold cash until the signal lifts."
        )
    else:
        changed = (pick != prev.get("pick") or prev.get("cash"))
        if changed:
            head = "<b>Lodestar World — TRADE</b>"
            body = (
                f"Sell {FACTOR_NAMES.get(prev.get('pick'), prev.get('pick'))} → "
                f"buy <b>{FACTOR_NAMES.get(pick, pick)}</b> (<code>{ticker}</code>) at 100% allocation.\n\n"
                f"Holding for month {hold_m}."
            )
        else:
            head = "<b>Lodestar World — NO TRADE</b>"
            body = (
                f"Hold <b>{FACTOR_NAMES.get(pick, pick)}</b> (<code>{ticker}</code>) at 100% allocation.\n\n"
                f"Holding for month {hold_m}."
            )
        msg = f"{head}\n\n{body}"

    print("\nNotification Preview:\n" + "-" * 50 + "\n" + msg + "\n" + "-" * 50)
    if not already_alerted(sig_m, pick):
        announce("Lodestar World Signal", msg)
        record_alert(sig_m, pick)

    return 0


if __name__ == "__main__":
    build_only = "--build-only" in sys.argv
    sys.exit(main(build_only=build_only))
