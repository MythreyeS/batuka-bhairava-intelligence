# batuka_bhairav/telegram_message.py

def render_message(
    regime,
    sector_table,
    man_of_match,
    news_drivers,
    tomorrow,
    btst_cards,
):
    close = regime.get("close")
    prev = regime.get("prev_close")
    chg = regime.get("change")
    chg_pct = regime.get("change_pct")
    sma20 = regime.get("sma20")
    reg = regime.get("regime")

    msg = []
    msg.append("🛡️ Batuka Bhairava Intelligence — Market Wrap\n")

    msg.append(
        f"NIFTY: Close {round(close,2)} | Prev {round(prev,2)} | "
        f"Chg {round(chg,2)} ({round(chg_pct,2)}%)"
    )
    msg.append(f"Regime: {reg} (rule: Close vs SMA20)")
    msg.append(f"SMA20: {round(sma20,2)}")

    # Sector Strength
    msg.append("\n📌 Sector Strength")
    for s in sector_table[:5]:
        msg.append(
            f"{s['sector']} | Avg {s['avg_change_pct']}% | Breadth {s['breadth']}"
        )

    # News
    msg.append("\n📰 Market Drivers")
    for n in news_drivers[:8]:
        msg.append(f"• {n}")

    # Man of Match
    msg.append("\n🔥 Man of the Match")
    for r in man_of_match[:20]:
        msg.append(
            f"{r['symbol']} | O:{round(r['open'],2)} "
            f"C:{round(r['close'],2)} "
            f"| {round(r['day_change_pct'],2)}% "
            f"| Vol×{round(r['vol_ratio'],2)}"
        )

    # Tomorrow View
    msg.append("\n🔮 Tomorrow Outlook")
    msg.append(f"Base: {tomorrow.get('base','')}")
    msg.append(f"Bull: {tomorrow.get('bull','')}")
    msg.append(f"Bear: {tomorrow.get('bear','')}")

    # BTST
    msg.append("\n🎯 BTST Action Card (₹5,000 Plan)")
    for c in btst_cards:
        msg.append(
            f"{c['symbol']} | Entry {c['entry']} | "
            f"Target {c['target']} | SL {c['stop']} | "
            f"Qty {c['qty']} | R:R {c['rr']}"
        )

    return "\n".join(msg)
