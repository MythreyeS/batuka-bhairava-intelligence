# batuka_bhairav/providers/news.py
# ── Multi-source news aggregator — all free RSS feeds ─────────────────────
from __future__ import annotations

import re
from typing import List, Dict
import feedparser
from batuka_bhairav.config import SOURCE_WEIGHT


# ── Positive / negative keyword banks (expanded for all markets) ──────────
_POS = [
    # English universal
    "surge","rally","jump","gain","beats","record","strong","upgrade",
    "bullish","positive","rise","soar","boom","breakout","outperform",
    "profit","growth","beat","exceed","buy","recommend","upside",
    "momentum","recovery","rebound","high","peak","expand","robust",
    # India specific
    "nifty high","sensex high","fii buying","dii buying","inflow",
    # US specific
    "fed pause","rate cut","earnings beat","guidance raised","buyback",
    # UK specific
    "ftse high","boe hold","dividend raised",
    # SG specific
    "mas easing","sti high","distribution",
]

_NEG = [
    # English universal
    "fall","drop","slump","weak","miss","downgrade","bearish","negative",
    "crash","selloff","plunge","tumble","decline","loss","below","cut",
    "risk","warn","concern","fear","volatile","uncertainty","sell",
    "underperform","downside","recession","inflation","rate hike",
    # India specific
    "fii selling","outflow","rbi hike","npa","fraud",
    # US specific
    "fed hike","earnings miss","guidance cut","layoff","default",
    # UK specific
    "ftse low","boe hike","brexit","recession",
    # SG specific
    "mas tighten","sti low","rights issue",
]


def _clean_html(text: str) -> str:
    """Strip HTML tags from news titles."""
    return re.sub(r"<[^>]+>", "", text or "").strip()


def fetch_all_news(limit_per_feed: int = 8) -> List[Dict]:
    """
    Fetches from ALL configured news feeds for the active market.
    Returns deduplicated list sorted by source weight.
    """
    from batuka_bhairav.config import NEWS_FEEDS

    items: List[Dict] = []
    seen_titles = set()

    for feed in NEWS_FEEDS:
        src = feed.get("source", "Unknown")
        rss = feed.get("rss", "")
        if not rss:
            continue
        try:
            parsed = feedparser.parse(rss)
            for entry in parsed.entries[:limit_per_feed]:
                title = _clean_html(getattr(entry, "title", "")).strip()
                if not title or title.lower() in seen_titles:
                    continue
                seen_titles.add(title.lower())
                items.append({
                    "source":    src,
                    "title":     title,
                    "link":      getattr(entry, "link",      "").strip(),
                    "published": getattr(entry, "published", "") or getattr(entry, "updated", ""),
                    "weight":    SOURCE_WEIGHT.get(src, 0.75),
                })
        except Exception:
            continue

    # Sort by source credibility weight (most trusted first)
    items.sort(key=lambda x: x["weight"], reverse=True)
    return items


def news_sentiment_score(title: str) -> float:
    """
    Keyword-based sentiment scorer for any market.
    Returns 0.0 (very bearish) → 1.0 (very bullish). Default 0.5.
    """
    t = (title or "").lower()

    pos_hits = sum(1 for w in _POS if w in t)
    neg_hits = sum(1 for w in _NEG if w in t)

    score = 0.5 + (pos_hits * 0.12) - (neg_hits * 0.12)
    return round(max(0.0, min(1.0, score)), 2)


def summarize_news(news_items: List[Dict], max_items: int = 10) -> Dict:
    """
    Returns:
      drivers   — top news items as dicts {source, title, link, sentiment}
      sentiment — weighted average sentiment 0..1
    """
    if not news_items:
        return {"drivers": [], "sentiment": 0.5}

    scored = []
    for n in news_items:
        w = n.get("weight", SOURCE_WEIGHT.get(n.get("source",""), 0.75))
        s = news_sentiment_score(n.get("title", ""))
        scored.append((w, s, n))

    total_w = sum(x[0] for x in scored) or 1.0
    sent    = sum(x[0] * x[1] for x in scored) / total_w

    drivers = []
    for w, s, n in scored[:max_items]:
        title = n.get("title", "").strip()
        if title:
            drivers.append({
                "source":    n.get("source", ""),
                "title":     title,
                "link":      n.get("link",   ""),
                "sentiment": s,
            })

    return {"drivers": drivers, "sentiment": round(sent, 2)}
