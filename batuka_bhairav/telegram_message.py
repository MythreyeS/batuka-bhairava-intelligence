# batuka_bhairav/telegram_message.py
# ── Enhanced: multi-market aware, buy-range format ─────────────────────────

def render_message(regime, sector_table, man_of_match, news_drivers,
                   tomorrow, btst_cards,
                   market_name="India (NSE)", currency="₹"):

    reg   = regime.get("regime", "UNKNOWN") if isinstance(regime, dict) else str(regime)
    index = regime.get("index", "Index")    if isinstance(regime, dict) else "Index"

    header = f"🧠 *Batuka Bhairava — {market_name}*\n\n"

    regime_block = f"🧭 *Regime:* {reg}  |  {index}\n\n"

    # ── Sector strength ───────────────────────────────────────────────────
    sector_block = "📊 *Sector Strength:*\n"
    for s in (sector_table or [])[:5]:
        if not isinstance(s, dict):
            continue
        pct   = s.get("avg_change_pct", 0)
        arrow = "▲" if pct >= 0 else "▼"
        sector_block += f"• {s.get('sector','?')} {arrow} {pct:+.2f}%\n"
    sector_block += "\n"

    # ── News drivers ──────────────────────────────────────────────────────
    news_block = "📰 *News Drivers:*\n"
    for n in (news_drivers or [])[:4]:
        if isinstance(n, dict):
            news_block += f"• [{n.get('source','')}] {n.get('title','')}\n"
        elif isinstance(n, str):
            news_block += f"• {n}\n"
    news_block += "\n"

    # ── Man of the Match ──────────────────────────────────────────────────
    mom_block = ""
    if man_of_match and isinstance(man_of_match, dict):
        sym  = man_of_match.get("symbol", "")
        name = man_of_match.get("name", sym)
        op   = man_of_match.get("open",  0)
        cl   = man_of_match.get("close", 0)
        pct  = man_of_match.get("day_change_pct", man_of_match.get("pct_change", 0))
        try:
            mom_block = (
                f"🏅 *Man of the Match:*\n"
                f"{name} ({sym})\n"
                f"Open {currency}{float(op):.2f} → "
                f"Close {currency}{float(cl):.2f} | "
                f"{float(pct):+.2f}%\n\n"
            )
        except Exception:
            mom_block = f"🏅 *Man of the Match:* {name}\n\n"

    # ── BTST picks ────────────────────────────────────────────────────────
    btst_block = ""
    if btst_cards:
        btst_block = f"🔥 *BTST Picks:*\n\n"
        for c in (btst_cards or []):
            if not isinstance(c, dict):
                continue
            name     = c.get("name",     c.get("symbol", ""))
            buy_low  = c.get("buy_low",  0)
            buy_high = c.get("buy_high", 0)
            qty      = c.get("qty",      0)
            close    = c.get("entry",    c.get("close", 0))
            chg      = c.get("day_change_pct", 0)
            conv     = c.get("conviction", 0)
            try:
                btst_block += f"*{name}* — Share investment\n"
                btst_block += (
                    f"if price is between "
                    f"{currency}{float(buy_low):.0f}–{currency}{float(buy_high):.0f} "
                    f"buy this share — {qty} Nos\n"
                )
                btst_block += (
                    f"_(Close: {currency}{float(close):.2f} | "
                    f"{float(chg):+.2f}% | "
                    f"Conviction: {float(conv):.0f}/100)_\n\n"
                )
            except Exception:
                btst_block += f"*{name}*\n\n"

    # ── Tomorrow outlook ──────────────────────────────────────────────────
    tomorrow_block = ""
    if tomorrow and isinstance(tomorrow, dict):
        tomorrow_block = (
            f"📅 *Tomorrow Outlook:*\n"
            f"Base: {tomorrow.get('base', '')}\n"
            f"Bull: {tomorrow.get('bull', '')}\n"
            f"Bear: {tomorrow.get('bear', '')}\n"
        )

    return (
        header
        + regime_block
        + sector_block
        + news_block
        + mom_block
        + btst_block
        + tomorrow_block
    )
