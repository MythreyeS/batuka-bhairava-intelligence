# batuka_bhairav/providers/news.py
# ✅ NEW FILE: News sentiment aggregation per BRD Section 5.2-5.3
 
"""
News feed aggregator with source credibility weighting.
Per BRD Section 5.2: 25 India feeds + 40+ global feeds
Per BRD Section 5.3: Source credibility weighted sentiment
"""
 
from __future__ import annotations
import feedparser
import logging
from datetime import datetime, timedelta
from batuka_bhairav.config import NEWS_FEEDS, POSITIVE_KEYWORDS, NEGATIVE_KEYWORDS
 
logger = logging.getLogger("batuka_news")
 
 
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SENTIMENT ANALYSIS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 
def compute_headline_sentiment(headline: str) -> float:
    """
    ✅ Simple keyword-based sentiment analysis
    
    Per BRD Section 5.3:
    - Positive keywords → score > 0.5
    - Negative keywords → score < 0.5
    - Neutral → 0.5
    
    Returns:
        float: Sentiment score [0, 1] where 0.5 = neutral
    """
    
    if not headline:
        return 0.5
    
    text = headline.lower()
    
    pos_count = sum(1 for kw in POSITIVE_KEYWORDS if kw in text)
    neg_count = sum(1 for kw in NEGATIVE_KEYWORDS if kw in text)
    
    total = pos_count + neg_count
    
    if total == 0:
        return 0.5  # Neutral
    
    sentiment = (pos_count - neg_count) / (total * 2.0)  # Normalize to [-0.5, 0.5]
    return 0.5 + sentiment  # Shift to [0, 1]
 
 
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# NEWS FETCHING (with error resilience per BRD)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 
def fetch_news_items(market_code: str = "IN", hours_back: int = 24) -> list[dict]:
    """
    ✅ Fetch news items from configured feeds for a market
    
    Per BRD Section 5.2-5.3:
    - Multiple tiered feeds with credibility weights
    - Graceful fallback if feeds become stale
    - Source-weighted sentiment aggregation
    
    Args:
        market_code: Market code (IN/US/UK/SG)
        hours_back: How many hours back to fetch news
    
    Returns:
        List of news items with sentiment and source weight
    """
    
    if market_code not in NEWS_FEEDS:
        logger.warning(f"No news config for market: {market_code}")
        return []
    
    news_items = []
    cutoff_time = datetime.now() - timedelta(hours=hours_back)
    
    market_feeds = NEWS_FEEDS[market_code]
    
    for tier_name, tier_config in market_feeds.items():
        source_weight = tier_config["weight"]
        feeds = tier_config["feeds"]
        
        for feed_url in feeds:
            try:
                logger.debug(f"Fetching {tier_name} feed: {feed_url[:50]}...")
                
                # Fetch with timeout
                feed = feedparser.parse(feed_url, timeout=10)
                
                if not feed.entries:
                    logger.debug(f"  ⚠️ Feed empty: {feed_url[:40]}")
                    continue
                
                # Process entries
                for entry in feed.entries[:10]:  # Max 10 per feed to avoid spam
                    try:
                        # Extract publication time
                        pub_time = None
                        if hasattr(entry, "published_parsed") and entry.published_parsed:
                            pub_time = datetime(*entry.published_parsed[:6])
                        
                        # Skip old news
                        if pub_time and pub_time < cutoff_time:
                            continue
                        
                        # Extract headline
                        headline = entry.get("title", "")
                        if not headline:
                            continue
                        
                        # Compute sentiment
                        sentiment = compute_headline_sentiment(headline)
                        
                        news_items.append({
                            "headline": headline,
                            "source_weight": source_weight,
                            "sentiment": sentiment,
                            "published": pub_time.isoformat() if pub_time else "",
                            "tier": tier_name,
                            "link": entry.get("link", ""),
                        })
                    
                    except Exception as e:
                        logger.debug(f"  Error processing entry: {e}")
                        continue
            
            except Exception as e:
                # Per BRD: Graceful fallback if feed goes stale
                logger.warning(f"  ❌ Feed error {tier_name}: {str(e)[:50]}")
                continue
    
    logger.info(f"Fetched {len(news_items)} news items for {market_code}")
    return news_items
 
 
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STOCK-SPECIFIC SENTIMENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 
def get_stock_sentiment(symbol: str, market_code: str = "IN") -> tuple[float, list[dict]]:
    """
    ✅ Compute sentiment specifically for a stock from recent news
    
    Per BRD Section 5.3:
    news_sentiment = Σ(source_weight × sentiment_score) / Σ(source_weight)
    
    Args:
        symbol: Stock symbol (e.g., "TCS", "AAPL")
        market_code: Market code
    
    Returns:
        Tuple of (weighted_sentiment [0, 1], top_articles)
    """
    
    items = fetch_news_items(market_code)
    
    # Filter for this stock
    relevant = [
        item for item in items
        if symbol.upper() in item["headline"].upper()
    ]
    
    if not relevant:
        return 0.5, []  # Neutral if no news
    
    # Weighted average sentiment per BRD Section 5.3
    weighted_sum = sum(item["source_weight"] * item["sentiment"] for item in relevant)
    weight_sum = sum(item["source_weight"] for item in relevant)
    
    if weight_sum == 0:
        return 0.5, []
    
    weighted_sentiment = weighted_sum / weight_sum
    
    logger.debug(f"{symbol}: Sentiment={weighted_sentiment:.2f} from {len(relevant)} articles")
    
    return weighted_sentiment, relevant[:3]  # Top 3 articles
 
 
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MARKET-WIDE SENTIMENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 
def get_market_sentiment(market_code: str = "IN") -> tuple[float, dict]:
    """
    ✅ Compute overall market sentiment
    
    Per BRD Section 7.1: Anticipation engine uses this for scenarios
    
    Returns:
        Tuple of (average_sentiment [0, 1], {tone: description})
    """
    
    items = fetch_news_items(market_code)
    
    if not items:
        return 0.5, {"tone": "neutral", "description": "No recent news"}
    
    # Weighted average
    weighted_sum = sum(item["source_weight"] * item["sentiment"] for item in items)
    weight_sum = sum(item["source_weight"] for item in items)
    
    avg_sentiment = weighted_sum / weight_sum if weight_sum > 0 else 0.5
    
    # Tone description
    if avg_sentiment > 0.60:
        tone = "bullish"
        description = "News tone is supportive"
    elif avg_sentiment < 0.40:
        tone = "bearish"
        description = "News tone is cautious"
    else:
        tone = "neutral"
        description = "Mixed news sentiment"
    
    return avg_sentiment, {
        "tone": tone,
        "sentiment_score": round(avg_sentiment, 2),
        "description": description,
        "article_count": len(items),
    }
 
 
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TOP NEWS DRIVERS (for anticipation engine)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 
def get_top_news_drivers(market_code: str = "IN", top_n: int = 6) -> list[str]:
    """
    ✅ Get top N news headlines weighted by source credibility
    
    Per BRD Section 7.1: Top 6 news drivers shown in anticipation
    
    Returns:
        List of top headline strings
    """
    
    items = fetch_news_items(market_code)
    
    # Sort by source weight (credibility) descending
    sorted_items = sorted(items, key=lambda x: x["source_weight"], reverse=True)
    
    return [item["headline"] for item in sorted_items[:top_n]]
 
 
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HEALTH CHECK
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 
def check_feed_health(market_code: str = "IN") -> dict:
    """
    ✅ Check which feeds are responsive (for monitoring)
    
    Returns:
        Dict of {feed_url: status}
    """
    
    if market_code not in NEWS_FEEDS:
        return {}
    
    health = {}
    market_feeds = NEWS_FEEDS[market_code]
    
    for tier_name, tier_config in market_feeds.items():
        for feed_url in tier_config["feeds"]:
            try:
                feed = feedparser.parse(feed_url, timeout=5)
                health[feed_url] = "ok" if feed.entries else "empty"
            except Exception as e:
                health[feed_url] = f"error: {type(e).__name__}"
    
    return health
