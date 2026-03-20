# batuka_bhairav/telegram_message.py
# ── Enhanced: multi-market aware, buy-range format ─────────────────────────

def render_message(regime, sector_table, man_of_match, news_drivers,
                   tomorrow, btst_cards,
                   market_name="India (NSE)", currency="₹"):

    reg    = regime.get("regime", "UNKNOWN")
    index  = regime.get("index",  "Index")

    header = f"🧠 *Batuka Bhairava — {market_name}*\n\n"

    regime_block = (
        f"🧭 *Regime:* {reg}  |  {index}\n\n"
    )

    # Sector strength
    sector_block = "📊 *Sector Strength:*\n"
    for s in sector_table[:5]:
        arrow = "▲" if s["avg_change_pct"] >= 0 else "▼"
        sector_block += f"• {s['sector']} {arrow} {s['avg_change_pct']:+.2f}%\n"
    sector_block += "\n"

    # News drivers
    news_block = "📰 *News Drivers:*\n"
    for n in news_drivers[:4]:
        if isinstance(n, dict):
            news_block += f"• [{n.get('source','')}] {n.get('title','')}\n"
        else:
            news_block += f"• {n}\n"
    news_block += "\n"

    # Man of the match
    mom_block = ""
    if man_of_match:
        sym  = man_of_match.get("symbol", "")
        name = man_of_match.get("name", sym)
        op   = man_of_match.get("open", "")
        cl   = man_of_match.get("close", "")
        pct  = man_of_match.get("day_change_pct", man_of_match.get("pct_change", ""))
        mom_block = (
            f"🏅 *Man of the Match:*\n"
            f"{name} ({sym})\n"
            f"Open {currency}{op} → Close {currency}{cl} | {pct:+.2f}%\n\n"
            if isinstance(pct, float) else
            f"🏅 *Man of the Match:* {name}\n\n"
        )

    # BTST picks — screenshot format
    btst_block = ""
    if btst_cards:
        btst_block = f"🔥 *BTST Picks ({currency}):*\n\n"
        for c in btst_cards:
            name     = c.get("name", c.get("symbol", ""))
            buy_low  = c.get("buy_low",  0)
            buy_high = c.get("buy_high", 0)
            qty      = c.get("qty",      0)
            close    = c.get("entry",    c.get("close", 0))
            chg      = c.get("day_change_pct", 0)
            conv     = c.get("conviction", 0)
            btst_block += f"*{name}* — Share investment\n"
            btst_block += (
                f"if price is between {currency}{buy_low:.0f}–{currency}{buy_high:.0f} "
                f"buy this share — {qty} Nos\n"
            )
            btst_block += f"_(Close: {currency}{close:.2f} | {chg:+.2f}% | Conviction: {conv:.0f}/100)_\n\n"

    # Tomorrow outlook
    tomorrow_block = (
        f"📅 *Tomorrow Outlook:*\n"
        f"Base: {tomorrow.get('base','')}\n"
        f"Bull: {tomorrow.get('bull','')}\n"
        f"Bear: {tomorrow.get('bear','')}\n"
    )

    return (
        header + regime_block + sector_block +
        news_block + mom_block + btst_block + tomorrow_block
    )
