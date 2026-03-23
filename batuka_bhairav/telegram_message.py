# batuka_bhairav/telegram_message.py
# ── Human-friendly message — no jargon, clear justification ───────────────

def _stars(conv: float) -> str:
    if conv >= 85: return "⭐⭐⭐"
    if conv >= 75: return "⭐⭐"
    return "⭐"

def _conv_label(conv: float) -> str:
    if conv >= 85: return "Very High Confidence"
    if conv >= 75: return "High Confidence"
    if conv >= 65: return "Moderate Confidence"
    return "Low Confidence"

def _rsi_plain(rsi: float) -> str:
    """Plain English RSI explanation — no jargon."""
    if rsi >= 70: return "stock may be getting expensive, watch for pullback"
    if rsi >= 55: return "buyers are in control, momentum is strong"
    if rsi >= 45: return "price is balanced, no extreme either way"
    return "stock is oversold, could bounce back"

def _trend_plain(above20, above50) -> str:
    """Plain English trend explanation."""
    if above20 and above50:
        return "price is above both short and long-term averages — uptrend confirmed"
    if above20:
        return "short-term trend is up, long-term still catching up"
    return "price is below key averages — trend is weak"

def _rr_plain(rr: float) -> str:
    """Plain English R:R explanation."""
    if rr >= 2.5: return f"for every ₹1 risked you could make ₹{rr:.1f} — excellent"
    if rr >= 1.5: return f"for every ₹1 risked you could make ₹{rr:.1f} — good"
    return f"for every ₹1 risked you could make ₹{rr:.1f} — acceptable"

def _mom_plain(strategy: str) -> str:
    """Identify the pick strategy for man of match."""
    return {
        "INTRADAY": "Best for intraday trade today",
        "BTST":     "Best for buying today and selling tomorrow",
        "LONGTERM": "Best for long-term accumulation over weeks",
    }.get(strategy, "Top performer today")

def _news_source_confidence(source: str) -> str:
    """Human-readable source credibility."""
    tier1 = ["NSE India","BSE India","RBI","SEBI","SGX","Fed Reserve","Bank of England","MAS Singapore"]
    tier2 = ["Economic Times","Business Standard","Livemint","Reuters","Reuters India","Financial Times","WSJ Markets","Barrons"]
    if source in tier1: return f"📋 Official source ({source})"
    if source in tier2: return f"📰 Trusted financial media ({source})"
    return f"📱 Financial news ({source})"


def render_message(regime, sector_table, man_of_match, news_drivers,
                   tomorrow, btst_cards,
                   intraday_cards=None, longterm_cards=None,
                   market_name="India (NSE)", currency="₹",
                   run_type="BTST"):
    """
    run_type: MORNING | BTST | CLOSING | WEEKEND
    Tomorrow outlook shown ONLY in CLOSING and WEEKEND runs.
    Market news = predictions only, not general news.
    Man of match clearly tagged with which strategy it suits.
    All technical terms explained in plain English.
    """
    reg   = regime.get("regime", "NEUTRAL") if isinstance(regime, dict) else str(regime)
    index = regime.get("index",  "Index")   if isinstance(regime, dict) else "Index"
    regime_icon = {"BULLISH": "🟢", "BEARISH": "🔴", "NEUTRAL": "🟡"}.get(reg, "⚪")

    # Regime plain English
    regime_plain = {
        "BULLISH": "Market is in an uptrend — good time to look for buying opportunities",
        "BEARISH": "Market is in a downtrend — be cautious, reduce risk",
        "NEUTRAL": "Market is moving sideways — pick selectively, wait for clear signals",
    }.get(reg, "Market direction is unclear")

    lines = []

    # ── HEADER ────────────────────────────────────────────────────────────
    run_labels = {
        "MORNING": "☀️ Morning Briefing",
        "BTST":    "🌙 Evening BTST Report",
        "CLOSING": "📊 Closing Summary",
        "WEEKEND": "📅 Weekend Recap",
    }
    lines += [
        "━━━━━━━━━━━━━━━━━━━━━━━━",
        f"🧠 *BATUKA BHAIRAVA*",
        f"📍 {market_name}  |  {run_labels.get(run_type, '📊 Report')}",
        "━━━━━━━━━━━━━━━━━━━━━━━━\n",
        f"{regime_icon} *Market Today: {reg}*",
        f"_{regime_plain}_\n",
    ]

    # ── SECTOR MAP ────────────────────────────────────────────────────────
    if sector_table:
        valid   = [s for s in sector_table if isinstance(s, dict)]
        top3    = valid[:3]
        bottom3 = list(reversed(valid))[:3]

        lines.append("*📈 Sectors doing well today*")
        for s in top3:
            pct = s.get("avg_change_pct", 0)
            lines.append(f"▲ *{s.get('sector','?')}*  {pct:+.2f}%")

        lines += ["", "*📉 Sectors under pressure today*"]
        for s in bottom3:
            pct = s.get("avg_change_pct", 0)
            sym = "▼" if pct < 0 else "▷"
            lines.append(f"{sym} *{s.get('sector','?')}*  {pct:+.2f}%")
        lines.append("")

    # ── MAN OF THE MATCH — tagged with which strategy ─────────────────────
    if man_of_match and isinstance(man_of_match, dict):
        sym   = man_of_match.get("symbol", "")
        name  = man_of_match.get("name", man_of_match.get("company", sym))
        op    = man_of_match.get("open",  0)
        cl    = man_of_match.get("close", 0)
        pct   = man_of_match.get("day_change_pct", 0)
        sec   = man_of_match.get("sector", "")
        vol   = man_of_match.get("vol_ratio", 1)
        conv  = man_of_match.get("conviction", 70)

        # Determine best strategy fit for MoM
        if run_type == "MORNING":
            strategy_fit = "INTRADAY"
            strategy_line = "Best suited for: Intraday trade today"
        elif pct > 3 and vol > 1.5:
            strategy_fit = "BTST"
            strategy_line = "Best suited for: Buy today & sell tomorrow opening"
        else:
            strategy_fit = "LONGTERM"
            strategy_line = "Best suited for: Accumulate for long-term gains"

        try:
            lines += [
                "━━━━━━━━━━━━━━━━━━━━━━━━",
                "*🏅 STAR OF THE DAY*",
                f"*{name}*",
                f"Sector: {sec}",
                f"Opened at {currency}{float(op):.2f} → Closed at {currency}{float(cl):.2f}",
                f"Moved *{float(pct):+.2f}%* today with {float(vol):.1f}x normal trading volume",
                f"📌 _{strategy_line}_",
                f"💡 Confidence: {_conv_label(conv)}\n",
            ]
        except Exception:
            lines += [f"*🏅 STAR:* {name}\n"]

    # ── INTRADAY PICKS (MORNING only) ─────────────────────────────────────
    if run_type == "MORNING":
        lines += [
            "━━━━━━━━━━━━━━━━━━━━━━━━",
            "⚡ *INTRADAY PICKS*",
            "_(Buy in the morning, sell before 3:20 PM today)_",
            "━━━━━━━━━━━━━━━━━━━━━━━━\n",
        ]
        if intraday_cards:
            for i, c in enumerate(intraday_cards, 1):
                if not isinstance(c, dict): continue
                try:
                    name  = c.get("name", c.get("symbol",""))
                    bl    = c.get("buy_low",  c.get("entry", 0))
                    bh    = c.get("buy_high", c.get("entry", 0))
                    qty   = c.get("qty", 0)
                    tgt   = c.get("target", 0)
                    stp   = c.get("stop",   0)
                    rr    = c.get("rr",     0)
                    conv  = c.get("conviction", 0)
                    chg   = c.get("day_change_pct", 0)
                    vol   = c.get("vol_ratio", 1)
                    sec   = c.get("sector", "")
                    rsi   = c.get("rsi", 50)

                    # Pick the top news source that supports this
                    top_news = ""
                    if news_drivers:
                        for n in news_drivers:
                            if isinstance(n, dict) and n.get("sentiment", 0.5) > 0.55:
                                top_news = f"\n📰 Supported by: {_news_source_confidence(n.get('source',''))}"
                                break

                    lines += [
                        f"*{i}. {name}*",
                        f"Buy between {currency}{float(bl):.0f} and {currency}{float(bh):.0f}  |  Buy {qty} shares",
                        f"Exit target: {currency}{float(tgt):.2f}  |  Stop loss: {currency}{float(stp):.2f}",
                        f"",
                        f"📊 What this means:",
                        f"• Stock moved {float(chg):+.1f}% today in sector: {sec}",
                        f"• Trading volume is {float(vol):.1f}x higher than usual — strong interest",
                        f"• {_rsi_plain(float(rsi))}",
                        f"• Reward vs Risk: {_rr_plain(float(rr))}",
                        f"• {top_news.strip() if top_news else ''}",
                        f"",
                        f"💡 Confidence: {_conv_label(conv)} {_stars(conv)}\n",
                    ]
                except Exception:
                    lines += [f"*{i}. {c.get('name','')}*\n"]
        else:
            lines.append("⚠️ No strong intraday setups today. Better to stay in cash.\n")

    # ── BTST PICKS ────────────────────────────────────────────────────────
    if run_type in ("BTST", "CLOSING"):
        lines += [
            "━━━━━━━━━━━━━━━━━━━━━━━━",
            "🌙 *BTST PICKS*",
            "_(Buy at today's closing price, sell when market opens tomorrow)_",
            "━━━━━━━━━━━━━━━━━━━━━━━━\n",
        ]
        if btst_cards:
            for i, c in enumerate(btst_cards, 1):
                if not isinstance(c, dict): continue
                try:
                    name  = c.get("name", c.get("symbol",""))
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

                    # Find best supporting news
                    news_line = ""
                    if news_drivers:
                        for n in news_drivers:
                            if isinstance(n, dict) and n.get("sentiment", 0.5) > 0.55:
                                news_line = f"• News from {_news_source_confidence(n.get('source',''))} is positive"
                                break

                    lines += [
                        f"*{i}. {name}* — Share investment",
                        f"if price is between {currency}{float(bl):.0f}–{currency}{float(bh):.0f} buy this share — {qty} Nos",
                        f"",
                        f"📊 Why this pick:",
                        f"• Closed at {currency}{float(cl):.2f}, moved {float(chg):+.1f}% today in {sec}",
                        f"• {float(vol):.1f}x normal volume — institutions are buying",
                        f"• Exit tomorrow if price reaches {currency}{float(tgt):.2f}",
                        f"• If it falls to {currency}{float(stp):.2f} — exit immediately to protect capital",
                        f"• {_rr_plain(float(rr))}",
                        f"• {news_line}" if news_line else "",
                        f"",
                        f"💡 Confidence: {_conv_label(conv)} {_stars(conv)}\n",
                    ]
                except Exception:
                    lines += [f"*{i}. {c.get('name','')}*\n"]
        else:
            lines.append(f"⚠️ Market is {reg} — no safe BTST picks today. Hold cash.\n")

    # ── LONG TERM PICKS ───────────────────────────────────────────────────
    if run_type in ("BTST", "WEEKEND") and longterm_cards:
        lines += [
            "━━━━━━━━━━━━━━━━━━━━━━━━",
            "📈 *LONG-TERM PICKS*",
            "_(Accumulate slowly over weeks or months — SIP style)_",
            "━━━━━━━━━━━━━━━━━━━━━━━━\n",
        ]
        for i, c in enumerate(longterm_cards, 1):
            if not isinstance(c, dict): continue
            try:
                name  = c.get("name", c.get("symbol",""))
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

                lines += [
                    f"*{i}. {name}* — Long Term Investment",
                    f"Accumulate between {currency}{float(bl):.0f}–{currency}{float(bh):.0f}  |  {qty} shares",
                    f"",
                    f"📊 Why this pick:",
                    f"• Sector: {sec}",
                    f"• {_trend_plain(bool(a20), bool(a50))}",
                    f"• In the last 20 days it moved {float(m20):+.1f}%, in 60 days {float(m60):+.1f}%",
                    f"• {_rsi_plain(float(rsi))}",
                    f"• Target price: {currency}{float(tgt):.2f}  |  Stop loss: {currency}{float(stp):.2f}",
                    f"• {_rr_plain(float(rr))}",
                    f"",
                    f"💡 Confidence: {_conv_label(conv)} {_stars(conv)}\n",
                ]
            except Exception:
                lines += [f"*{i}. {c.get('name','')}*\n"]

    # ── CLOSING SUMMARY ───────────────────────────────────────────────────
    if run_type == "CLOSING":
        lines += [
            "━━━━━━━━━━━━━━━━━━━━━━━━",
            "*📊 TODAY IN A NUTSHELL*",
            "━━━━━━━━━━━━━━━━━━━━━━━━",
        ]
        if sector_table:
            valid = [s for s in sector_table if isinstance(s, dict)]
            best  = valid[0]  if valid else None
            worst = valid[-1] if valid else None
            if best:
                lines.append(f"🏆 Best sector today: *{best.get('sector','')}* ({best.get('avg_change_pct',0):+.2f}%)")
            if worst:
                lines.append(f"💔 Worst sector today: *{worst.get('sector','')}* ({worst.get('avg_change_pct',0):+.2f}%)")
        lines.append("")

    # ── MARKET PREDICTIONS (news must be forward-looking only) ────────────
    # Filter news to only show sentiment-based predictions, not past events
    prediction_news = []
    if news_drivers:
        prediction_keywords = [
            "forecast","outlook","expect","predict","likely","may","could",
            "week ahead","next week","tomorrow","target","upgrade","downgrade",
            "will","should","ahead","guidance","estimates","projection"
        ]
        for n in (news_drivers or []):
            if not isinstance(n, dict):
                continue
            title = n.get("title","").lower()
            if any(kw in title for kw in prediction_keywords):
                prediction_news.append(n)

    if prediction_news:
        lines.append("*🔮 MARKET PREDICTIONS*")
        lines.append("_(Only forward-looking news that affects your picks)_\n")
        for n in prediction_news[:4]:
            sent  = n.get("sentiment", 0.5)
            icon  = "📈" if sent > 0.55 else "📉" if sent < 0.45 else "📌"
            src   = _news_source_confidence(n.get("source",""))
            lines.append(f"{icon} {n.get('title','')}")
            lines.append(f"   _Source: {src}_\n")

    # ── TOMORROW OUTLOOK — ONLY in CLOSING and WEEKEND ────────────────────
    if run_type in ("CLOSING", "WEEKEND") and tomorrow and isinstance(tomorrow, dict):
        lines += [
            "━━━━━━━━━━━━━━━━━━━━━━━━",
            "*📅 WHAT TO EXPECT TOMORROW*",
            "━━━━━━━━━━━━━━━━━━━━━━━━",
            f"🔵 Most likely: {tomorrow.get('base','')}",
            f"🟢 Best case: {tomorrow.get('bull','')}",
            f"🔴 Worst case: {tomorrow.get('bear','')}",
        ]

    lines += [
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━",
        "⚠️ _This is AI-generated market intelligence, not financial advice._",
        "_Always invest based on your own judgement and risk capacity._",
        "━━━━━━━━━━━━━━━━━━━━━━━━",
    ]

    # Clean empty strings from lines
    return "\n".join(l for l in lines if l is not None)
