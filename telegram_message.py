# batuka_bhairav/core/telegram_message.py
from __future__ import annotations

from typing import List, Dict
from batuka_bhairav.config import MOM_MAX_ROWS_IN_TELEGRAM, SECTOR_TOP_N, SECTOR_BOTTOM_N


def _fmt_money(x):
    try:
        return f"{x:.2f}"
    except Exception:
        return str(x)


def render_message(
    regime: Dict,
    sector_table: List[Dict],
    man_of_match: List[Dict],
    news_drivers: List[str],
    tomorrow: Dict,
    btst_cards: List[Dict],
) -> str:

    close = regime.get("close")
    prev = regime.get("prev_close")
    chg = regime.get("change")
    chg_pct = regime.get("change_pct")
    sma20 = regime.get("sma20")
    reg = regime.get("regime")

    msg = []
    msg.append("🛡️ Batuka Bhairava Intelligence — Market Wrap\n")
    msg.append(f"NIFTY: Close {_fmt_money(close)} | Prev {_fmt_money(prev)} | Chg {_fmt_money(chg)} ({_fmt_money(chg_pct)}%)")
    msg.append(f"Regime: {reg} (rule: Close vs SMA20)")
    msg.append(f"SMA20: {_fmt_money(sma20)}")

    # Sector pulse
    msg.append("\n📌 Sector Strength (today)")
    if sector_table:
        top = sector_table[:SECTOR_TOP_N]
        bottom = sector_table[-SECTOR_BOTTOM_N:] if len(sector_table) >= SECTOR_BOTTOM_N else sector_table[-1:]
        top_txt = " | ".join([f"{s['sector']} ↑ {s['avg_change_pct']}% (breadth {s['breadth']})" for s in top])
        bot_txt = " | ".join([f"{s['sector']} ↓ {s['avg_change_pct']}% (breadth {s['breadth']})" for s in bottom])
        msg.append(f"Leaders: {top_txt}")
        msg.append(f"Laggards: {bot_txt}")
    else:
        msg.append("Sector data: unavailable (missing sector mapping).")

    # Why + sources
    msg.append("\n📰 Why market moved (authenticated sources)")
    if news_drivers:
        for d in news_drivers[:10]:
            msg.append(f"• {d}")
    else:
        msg.append("• No RSS headlines fetched (feeds unavailable or rate-limited).")

    # Man of the Match (not limited to 5)
    msg.append("\n🔥 Man of the Match (meaningful movers — not Top 5 only)")
    if not man_of_match:
        msg.append("• No major movers passed filters today.")
    else:
        shown = man_of_match[:MOM_MAX_ROWS_IN_TELEGRAM]
        for r in shown:
            msg.append(
                f"• {r['symbol']} | O:{_fmt_money(r['open'])} C:{_fmt_money(r['close'])} "
                f"| {r['day_change_pct']:.2f}% | Vol×{r['vol_ratio']:.2f}"
            )
        if len(man_of_match) > MOM_MAX_ROWS_IN_TELEGRAM:
            msg.append(f"…and {len(man_of_match) - MOM_MAX_ROWS_IN_TELEGRAM} more meaningful movers (stored in logs).")

    # Tomorrow view
    msg.append("\n🔮 Anticipation for Tomorrow (scenarios)")
    msg.append(f"Base case: {tomorrow.get('base','')}")
    msg.append(f"Bull case: {tomorrow.get('bull','')}")
    msg.append(f"Bear case: {tomorrow.get('bear','')}")

    # BTST action card
    msg.append("\n🎯 BTST Action Card (₹5,000 plan)")
    if not btst_cards:
        msg.append("• No BTST action today (regime/conviction gating).")
    else:
        for c in btst_cards[:3]:
            msg.append(
                f"• {c['symbol']} | Entry {c['entry']} | Tgt {c['target']} | SL {c['stop']} "
                f"| Qty {c['qty']} | R:R {c['rr']}"
            )

    return "\n".join(msg)
