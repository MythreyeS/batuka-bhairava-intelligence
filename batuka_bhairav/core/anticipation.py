# batuka_bhairav/core/anticipation.py
from __future__ import annotations

from typing import List, Dict
from batuka_bhairav.providers.news import news_sentiment_score
from batuka_bhairav.config import SOURCE_WEIGHT


def summarize_news(news_items: List[Dict], max_items: int = 6) -> Dict:
    """
    Returns:
      - drivers: list of strings with [SOURCE] title
      - sentiment: 0..1
    """
    if not news_items:
        return {"drivers": [], "sentiment": 0.5}

    scored = []
    for n in news_items:
        src = n.get("source", "Unknown")
        w = SOURCE_WEIGHT.get(src, 0.75)
        s = news_sentiment_score(n.get("title", ""))
        scored.append((w, s, n))

    # weighted sentiment
    total_w = sum(x[0] for x in scored) or 1.0
    sent = sum(x[0] * x[1] for x in scored) / total_w

    # top drivers by weight (recentness is already in feed ordering)
    drivers = []
    for w, s, n in scored[:max_items]:
        title = n.get("title", "").strip()
        src = n.get("source", "Unknown")
        if title:
            drivers.append(f"[{src}] {title}")

    return {"drivers": drivers, "sentiment": float(round(sent, 2))}


def build_tomorrow_view(regime: str, sector_table: List[Dict], news_summary: Dict) -> Dict:
    """
    Returns base/bull/bear scenarios with tagged sources.
    """
    top_sector = sector_table[0]["sector"] if sector_table else "Mixed"
    weak_sector = sector_table[-1]["sector"] if sector_table else "Mixed"
    sentiment = news_summary.get("sentiment", 0.5)

    base = f"Range-to-positive bias if {top_sector} leadership sustains; watch opening breadth."
    bull = f"Breakout continuation possible if early breadth is strong; {top_sector} could extend."
    bear = f"Failure to hold gains may drag; {weak_sector} weakness can cap upside."

    # nudge text by sentiment/regime
    if regime == "BEARISH":
        base = "Cautious tone; rallies may face selling unless breadth flips strongly."
        bull = "Only if index reclaims key averages early; else avoid aggressive bets."
        bear = "Higher probability of sell-on-rise; protect capital."

    if sentiment < 0.45:
        base += " News tone is slightly cautious."
    elif sentiment > 0.55:
        base += " News tone is supportive."

    return {"base": base, "bull": bull, "bear": bear}
