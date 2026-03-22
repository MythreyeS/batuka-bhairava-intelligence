# batuka_bhairav/telegram_message.py
# ── Full message: schedule-aware, justified, 3 strategies ─────────────────

def _bar(pct: float, width: int = 8) -> str:
    filled = min(width, max(0, int(abs(pct) / 5.0 * width)))
    return "█" * filled + "░" * (width - filled)

def _stars(conv: float) -> str:
    if conv >= 85: return "⭐⭐⭐"
    if conv >= 75: return "⭐⭐"
    return "⭐"

def _conv_label(conv: float) -> str:
    if conv >= 85: return "Very High"
    if conv >= 75: return "High"
    if conv >= 65: return "Moderate"
    return "Low"

def _rsi_label(rsi: float) -> str:
    if rsi >= 70:   return "Overbought ⚠️"
    if rsi >= 55:   return "Strong 📈"
    if rsi >= 45:   return "Neutral"
    return "Oversold 🔽"

def _trend_label(above20, above50) -> str:
    if above20 and above50: return "Above SMA20 & SMA50 ✅"
    if above20:             return "Above SMA20 only"
    if above50:             return "Below SMA20 ⚠️"
    return "Below both SMAs 🔴"


def render_message(regime, sector_table, man_of_match, news_drivers,
                   tomorrow, btst_cards,
                   intraday_cards=None, longterm_cards=None,
                   market_name="India (NSE)", currency="₹",
                   run_type="BTST"):
    """
    run_type: MORNING | BTST | CLOSING | WEEKEND
    """
    reg   = regime.get("regime", "NEUTRAL") if isinstance(regime, dict) else str(regime)
    index = regime.get("index",  "Index")   if isinstance(regime, dict) else "Index"
    regime_icon = {"BULLISH": "🟢", "BEARISH": "🔴", "NEUTRAL": "🟡"}.get(reg, "⚪")

    lines = []

    # ── HEADER ────────────────────────────────────────────────────────────
    run_labels = {
        "MORNING": "☀️ Morning Briefing",
        "BTST":    "🌙 BTST & Evening Report",
        "CLOSING": "📊 Closing Summary",
        "WEEKEND": "📅 Weekend Recap (Friday Review)",
    }
    run_label = run_labels.get(run_type, "📊 Market Report")

    lines += [
        "━━━━━━━━━━━━━━━━━━━━━━━━",
        f"🧠 *BATUKA BHAIRAVA*",
        f"📍 {market_name}  |  {run_label}",
        "━━━━━━━━━━━━━━━━━━━━━━━━\n",
        f"{regime_icon} *Market Regime: {reg}*  |  {index}\n",
    ]

    # ── SECTOR LEADERS & LAGGARDS ─────────────────────────────────────────
    if sector_table:
        valid   = [s for s in sector_table if isinstance(s, dict)]
        top3    = valid[:3]
        bottom3 = list(reversed(valid))[:3]

        lines.append("*📈 HOT SECTORS TODAY*")
        for s in top3:
            pct = s.get("avg_change_pct", 0)
            lines.append(f"▲ *{s.get('sector','?')}*  {_bar(pct)}  +{pct:.2f}%")

        lines += ["", "*📉 WEAK SECTORS TODAY*"]
        for s in bottom3:
            pct = s.get("avg_change_pct", 0)
            sym = "▼" if pct < 0 else "▷"
            lines.append(f"{sym} *{s.get('sector','?')}*  {_bar(abs(pct))}  {pct:+.2f}%")
        lines.append("")

    # ── STAR OF THE DAY ───────────────────────────────────────────────────
    if man_of_match and isinstance(man_of_match, dict):
        sym  = man_of_match.get("symbol", "")
        name = man_of_match.get("name", man_of_match.get("company", sym))
        op   = man_of_match.get("open",  0)
        cl   = man_of_match.get("close", 0)
        pct  = man_of_match.get("day_change_pct", 0)
        sec  = man_of_match.get("sector", "")
        vol  = man_of_match.get("vol_ratio", 1)
        try:
            lines += [
                "━━━━━━━━━━━━━━━━━━━━━━━━",
                "*🏅 STAR OF THE DAY*",
                f"*{name}*",
                f"Sector: {sec}  |  Symbol: {sym}",
                f"Open: {currency}{float(op):.2f} → Close: {currency}{float(cl):.2f}",
                f"Change: *{float(pct):+.2f}%*  |  Volume: {float(vol):.1f}x avg 🚀",
                f"_Why: Strong momentum + volume surge confirms institutional interest_\n",
            ]
        except Exception:
            lines += [f"*🏅 STAR:* {name}\n"]

    # ── MORNING: INTRADAY PICKS ───────────────────────────────────────────
    if run_type in ("MORNING", "BTST") and intraday_cards:
        lines += [
            "━━━━━━━━━━━━━━━━━━━━━━━━",
            "⚡ *INTRADAY PICKS*",
            "_(Buy at open, exit before 3:20 PM)_",
            "━━━━━━━━━━━━━━━━━━━━━━━━\n",
        ]
        for i, c in enumerate(intraday_cards, 1):
            if not isinstance(c, dict): continue
            try:
                name  = c.get("name", c.get("symbol",""))
                sym   = c.get("symbol","")
                bl    = c.get("buy_low",  c.get("entry", 0))
                bh    = c.get("buy_high", c.get("entry", 0))
                qty   = c.get("qty", 0)
                tgt   = c.get("target", 0)
                stp   = c.get("stop",   0)
                rr    = c.get("rr",     0)
                conv  = c.get("conviction", 0)
                chg   = c.get("day_change_pct", 0)
                intra = c.get("intraday_pct", 0)
                vol   = c.get("vol_ratio", 1)
                sec   = c.get("sector", "")
                rsi   = c.get("rsi", 50)

                # Justification
                reasons = []
                if float(chg) > 1.5:   reasons.append(f"strong day move +{float(chg):.1f}%")
                if float(vol) > 1.5:   reasons.append(f"volume {float(vol):.1f}x above avg")
                if float(intra) > 1.0: reasons.append("closing near day high")
                if 45 < float(rsi) < 65: reasons.append(f"RSI healthy at {float(rsi):.0f}")
                justification = " + ".join(reasons) if reasons else "momentum setup"

                lines += [
                    f"*{i}. {name}* _{sym}_",
                    f"Buy: {currency}{float(bl):.0f}–{currency}{float(bh):.0f}  |  Qty: {qty} Nos",
                    f"🎯 Target: {currency}{float(tgt):.2f}  |  🛡 Stop: {currency}{float(stp):.2f}  |  R:R {float(rr):.1f}x",
                    f"📊 Sector: {sec}  |  RSI: {float(rsi):.0f} ({_rsi_label(float(rsi))})",
                    f"💡 Score: {float(conv):.0f}/100 {_stars(conv)} — {_conv_label(conv)}",
                    f"📝 _Why: {justification}_\n",
                ]
            except Exception:
                lines += [f"*{i}. {c.get('name','')}*\n"]
    elif run_type == "MORNING":
        lines += [
            "━━━━━━━━━━━━━━━━━━━━━━━━",
            "⚡ *INTRADAY PICKS*",
            "⚠️ No strong intraday setups today. Wait for better entry.\n",
        ]

    # ── BTST PICKS ────────────────────────────────────────────────────────
    if run_type in ("BTST", "CLOSING"):
        lines += [
            "━━━━━━━━━━━━━━━━━━━━━━━━",
            "🌙 *BTST PICKS*",
            "_(Buy today close, sell tomorrow opening)_",
            "━━━━━━━━━━━━━━━━━━━━━━━━\n",
        ]
        if btst_cards:
            for i, c in enumerate(btst_cards, 1):
                if not isinstance(c, dict): continue
                try:
                    name  = c.get("name", c.get("symbol",""))
                    sym   = c.get("symbol","")
                    bl    = c.get("buy_low",  0)
                    bh    = c.get("buy_high", 0)
                    qty   = c.get("qty",      0)
                    cl    = c.get("entry",    c.get("close", 0))
                    tgt   = c.get("target",   0)
                    stp   = c.get("stop",     0)
                    rr    = c.get("rr",       0)
                    conv  = c.get("conviction", 0)
                    chg   = c.get("day_change_pct", 0)
                    vol   = c.get("vol_ratio", 1)
                    sec   = c.get("sector","")

                    # Justification
                    reasons = []
                    if float(chg) > 1.5:  reasons.append(f"+{float(chg):.1f}% day momentum")
                    if float(vol) > 1.5:  reasons.append(f"{float(vol):.1f}x volume")
                    if float(conv) >= 80: reasons.append("high conviction setup")
                    justification = " + ".join(reasons) if reasons else "momentum + sector strength"

                    lines += [
                        f"*{i}. {name}* — Share investment",
                        f"if price is between {currency}{float(bl):.0f}–{currency}{float(bh):.0f} buy this share — {qty} Nos",
                        f"📊 Sector: {sec}  |  Close: {currency}{float(cl):.2f}  |  {float(chg):+.2f}%",
                        f"🎯 Target: {currency}{float(tgt):.2f}  |  🛡 Stop: {currency}{float(stp):.2f}  |  R:R {float(rr):.1f}x",
                        f"💡 Conviction: {float(conv):.0f}/100 {_stars(conv)} — {_conv_label(conv)}",
                        f"📝 _Why: {justification}_\n",
                    ]
                except Exception:
                    lines += [f"*{i}. {c.get('name','')}*\n"]
        else:
            lines.append(f"⚠️ No BTST picks — Regime is {reg}. Avoid overnight risk.\n")

    # ── LONG TERM PICKS ───────────────────────────────────────────────────
    if run_type in ("BTST", "WEEKEND") and longterm_cards:
        lines += [
            "━━━━━━━━━━━━━━━━━━━━━━━━",
            "📈 *LONG-TERM PICKS*",
            "_(Accumulate over weeks/months — SIP approach)_",
            "━━━━━━━━━━━━━━━━━━━━━━━━\n",
        ]
        for i, c in enumerate(longterm_cards, 1):
            if not isinstance(c, dict): continue
            try:
                name  = c.get("name", c.get("symbol",""))
                sym   = c.get("symbol","")
                bl    = c.get("buy_low",  0)
                bh    = c.get("buy_high", 0)
                qty   = c.get("qty",      0)
                cl    = c.get("close",    0)
                tgt   = c.get("target",   0)
                stp   = c.get("stop",     0)
                rr    = c.get("rr",       0)
                conv  = c.get("conviction", 0)
                m20   = c.get("mom_20d",  0)
                m60   = c.get("mom_60d",  0)
                sec   = c.get("sector",   "")
                rsi   = c.get("rsi",      50)
                a20   = c.get("above_sma20", 0)
                a50   = c.get("above_sma50", 0)

                # Justification
                reasons = []
                if float(m60) > 10:   reasons.append(f"strong 60D momentum +{float(m60):.1f}%")
                if float(a20) and float(a50): reasons.append("above all key MAs")
                if 45 <= float(rsi) <= 65: reasons.append("RSI in buy zone")
                justification = " + ".join(reasons) if reasons else "trend + fundamentals"

                lines += [
                    f"*{i}. {name}* — Long Term Investment",
                    f"Accumulate between {currency}{float(bl):.0f}–{currency}{float(bh):.0f}  |  {qty} Nos",
                    f"📊 Sector: {sec}  |  {_trend_label(bool(a20), bool(a50))}",
                    f"📅 20D: {float(m20):+.1f}%  |  60D: {float(m60):+.1f}%  |  RSI: {float(rsi):.0f}",
                    f"🎯 Target: {currency}{float(tgt):.2f}  |  🛡 Stop: {currency}{float(stp):.2f}  |  R:R {float(rr):.1f}x",
                    f"💡 Score: {float(conv):.0f}/100 {_stars(conv)} — {_conv_label(conv)}",
                    f"📝 _Why: {justification}_\n",
                ]
            except Exception:
                lines += [f"*{i}. {c.get('name','')}*\n"]

    # ── CLOSING SUMMARY ───────────────────────────────────────────────────
    if run_type == "CLOSING":
        lines += [
            "━━━━━━━━━━━━━━━━━━━━━━━━",
            "*📊 CLOSING SUMMARY*",
            "━━━━━━━━━━━━━━━━━━━━━━━━",
        ]
        if sector_table:
            valid = [s for s in sector_table if isinstance(s, dict)]
            best  = valid[0]  if valid else None
            worst = valid[-1] if valid else None
            if best:
                lines.append(f"🏆 Best sector: *{best.get('sector','')}* +{best.get('avg_change_pct',0):.2f}%")
            if worst:
                lines.append(f"💔 Worst sector: *{worst.get('sector','')}* {worst.get('avg_change_pct',0):+.2f}%")
        lines.append("")

    # ── MARKET NEWS (relevant only) ───────────────────────────────────────
    if news_drivers:
        lines.append("*📰 MARKET NEWS*")
        for n in (news_drivers or [])[:5]:
            if isinstance(n, dict):
                sent  = n.get("sentiment", 0.5)
                icon  = "📈" if sent > 0.55 else "📉" if sent < 0.45 else "📌"
                lines.append(f"{icon} [{n.get('source','')}] {n.get('title','')}")
            elif isinstance(n, str):
                lines.append(f"📌 {n}")
        lines.append("")

    # ── TOMORROW OUTLOOK ──────────────────────────────────────────────────
    if tomorrow and isinstance(tomorrow, dict):
        lines += [
            "━━━━━━━━━━━━━━━━━━━━━━━━",
            "*📅 TOMORROW OUTLOOK*",
            f"🔵 Base: {tomorrow.get('base','')}",
            f"🟢 Bull: {tomorrow.get('bull','')}",
            f"🔴 Bear: {tomorrow.get('bear','')}",
        ]

    lines += [
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━",
        "⚠️ _Not financial advice. DYOR before investing._",
        "━━━━━━━━━━━━━━━━━━━━━━━━",
    ]

    return "\n".join(lines)
