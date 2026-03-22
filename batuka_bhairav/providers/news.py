# batuka_bhairav/providers/news.py
# ── Market-relevant news only — filters out irrelevant stories ────────────
from __future__ import annotations

import re
from typing import List, Dict
import feedparser
from batuka_bhairav.config import SOURCE_WEIGHT


# ── MUST contain at least one of these to be considered market-relevant ───
_MARKET_KEYWORDS = [
    # Market / index
    "nifty","sensex","bse","nse","market","stock","share","equity",
    "index","ftse","nasdaq","s&p","dow","sti","hang seng",
    # Corporate actions
    "earnings","results","profit","revenue","quarterly","q1","q2","q3","q4",
    "dividend","buyback","acquisition","merger","ipo","listing","stake",
    "board","agm","mgmt","management","ceo","cfo","chairman",
    # Macro that moves markets
    "rbi","fed","rate","inflation","gdp","fiscal","budget","policy",
    "fii","dii","inflow","outflow","rupee","dollar","crude","oil",
    "interest rate","repo","monetary","economic","economy",
    # Sectors
    "banking","pharma","it sector","auto","fmcg","realty","metal",
    "energy","telecom","infrastructure","capital goods",
    # Actions
    "rally","surge","fall","drop","gain","loss","buy","sell",
    "upgrade","downgrade","target","analyst","forecast","outlook",
    "ipo","ncd","fpo","rights issue","bonus","split",
]

# ── BLOCK these — clearly irrelevant to stock market ─────────────────────
_BLOCK_KEYWORDS = [
    "accident","crash","killed","died","death","murder","crime",
    "weather","flood","earthquake","cyclone","storm",
    "cricket","football","sport","ipl","match","tournament","player",
    "bollywood","movie","film","celebrity","actor","actress",
    "recipe","food","health tip","fitness","diet","yoga",
    "astrology","horoscope","vastu",
    "helicopter","speedboat","plane crash","train accident",
    "politics","election","vote","parliament","minister","cm","pm modi",
    "war","army","military","missile","attack","terrorist",
    "covid","vaccine","hospital","disease","pandemic",
]


def _is_market_relevant(title: str) -> bool:
    """Returns True only if the news title is relevant to stock markets."""
    t = title.lower()

    # Block irrelevant content first
    if any(w in t for w in _BLOCK_KEYWORDS):
        return False

    # Must contain at least one market keyword
    return any(w in t for w in _MARKET_KEYWORDS)


def _clean_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()


def fetch_all_news(limit_per_feed: int = 8) -> List[Dict]:
    """
    Fetches from ALL configured news feeds.
    Filters to market-relevant stories only.
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
                if not title:
                    continue
                # Skip duplicates
                if title.lower() in seen_titles:
                    continue
                # Skip irrelevant news
                if not _is_market_relevant(title):
                    continue
                seen_titles.add(title.lower())
                items.append({
                    "source":    src,
                    "title":     title,
                    "link":      getattr(entry, "link", "").strip(),
                    "published": getattr(entry, "published", "") or getattr(entry, "updated", ""),
                    "weight":    SOURCE_WEIGHT.get(src, 0.75),
                })
        except Exception:
            continue

    # Sort by source credibility
    items.sort(key=lambda x: x["weight"], reverse=True)
    return items


# ── Positive / negative keyword sentiment scorer ──────────────────────────
_POS = [
    "surge","rally","jump","gain","beats","record","strong","upgrade",
    "bullish","positive","rise","soar","boom","breakout","outperform",
    "profit","growth","beat","exceed","buy","upside","recovery",
    "rebound","high","peak","expand","robust","inflow","fii buying",
]

_NEG = [
    "fall","drop","slump","weak","miss","downgrade","bearish","negative",
    "crash","selloff","plunge","tumble","decline","loss","below","cut",
    "risk","warn","concern","fear","volatile","uncertainty","sell",
    "underperform","downside","recession","inflation","rate hike",
    "outflow","fii selling","npa","fraud",
]


def news_sentiment_score(title: str) -> float:
    t = (title or "").lower()
    pos_hits = sum(1 for w in _POS if w in t)
    neg_hits = sum(1 for w in _NEG if w in t)
    score = 0.5 + (pos_hits * 0.12) - (neg_hits * 0.12)
    return round(max(0.0, min(1.0, score)), 2)


def summarize_news(news_items: List[Dict], max_items: int = 10) -> Dict:
    if not news_items:
        return {"drivers": [], "sentiment": 0.5}

    scored = []
    for n in news_items:
        w = n.get("weight", SOURCE_WEIGHT.get(n.get("source", ""), 0.75))
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
                "link":      n.get("link", ""),
                "sentiment": s,
            })

    return {"drivers": drivers, "sentiment": round(sent, 2)}
