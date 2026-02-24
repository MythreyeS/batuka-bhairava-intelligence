# batuka_bhairav/providers/news.py
from __future__ import annotations

from typing import List, Dict
import feedparser

from batuka_bhairav.config import NEWS_FEEDS


def fetch_all_news(limit_per_feed: int = 10) -> List[Dict]:
    """
    RSS-based aggregator: stable + source-attributed.
    Returns list of {source,title,link,published}.
    """
    items: List[Dict] = []
    for feed in NEWS_FEEDS:
        src = feed["source"]
        rss = feed["rss"]
        try:
            parsed = feedparser.parse(rss)
            for entry in parsed.entries[:limit_per_feed]:
                items.append({
                    "source": src,
                    "title": getattr(entry, "title", "").strip(),
                    "link": getattr(entry, "link", "").strip(),
                    "published": getattr(entry, "published", "") or getattr(entry, "updated", ""),
                })
        except Exception:
            continue
    return items


def news_sentiment_score(title: str) -> float:
    """
    Very lightweight sentiment rule engine.
    Returns 0..1 (bearish..bullish)
    """
    t = (title or "").lower()
    pos = ["surge", "rally", "jump", "gain", "beats", "record", "strong", "upgrade", "bullish", "positive"]
    neg = ["fall", "drop", "slump", "weak", "miss", "downgrade", "bearish", "negative", "crash", "selloff"]

    score = 0.5
    if any(w in t for w in pos):
        score += 0.20
    if any(w in t for w in neg):
        score -= 0.20

    # clamp
    return max(0.0, min(1.0, score))
