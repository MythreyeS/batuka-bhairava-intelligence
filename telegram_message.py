# batuka_bhairav/telegram_message.py

def render_message(
    regime,
    sector_table,
    man_of_match,
    news_drivers,
    tomorrow,
    btst_cards,
):

    header = "Batuka Bhairava Intelligence — Market Wrap\n\n"

    regime_block = (
        f"NIFTY Regime: {regime.get('regime')}\n"
        f"Close: {regime.get('close')}\n"
        f"SMA20: {regime.get('sma20')}\n\n"
    )

    sector_block = "Sector Strength:\n"
    for s in sector_table[:5]:
        sector_block += f"• {s['sector']} → {round(s['score'],2)}\n"
    sector_block += "\n"

    news_block = "Top News Drivers:\n"
    for n in news_drivers[:5]:
        news_block += f"• {n}\n"
    news_block += "\n"

    mom_block = ""
    if man_of_match:
        mom_block = (
            "Man of the Match:\n"
            f"{man_of_match['symbol']} — "
            f"Open {man_of_match['open']} / "
            f"Close {man_of_match['close']} / "
            f"{man_of_match['pct_change']}%\n\n"
        )

    btst_block = ""
    if btst_cards:
        btst_block = "BTST Action Card (₹5,000 Plan)\n"
        for c in btst_cards:
            btst_block += (
                f"{c['symbol']} | Entry {c['entry']} | "
                f"Target {c['target']} | "
                f"SL {c['stop']} | "
                f"Conviction {c['conviction']}\n"
            )

    tomorrow_block = (
        "\nTomorrow Outlook:\n"
        f"Base: {tomorrow.get('base')}\n"
        f"Bull: {tomorrow.get('bull')}\n"
        f"Bear: {tomorrow.get('bear')}\n"
    )

    return (
        header
        + regime_block
        + sector_block
        + news_block
        + mom_block
        + tomorrow_block
        + btst_block
    )
