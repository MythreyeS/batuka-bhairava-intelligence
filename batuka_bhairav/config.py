# batuka_bhairav/config.py

# Universe
UNIVERSE_CSV = "batuka_bhairav/universe/nifty500.csv"

# Index symbols (Yahoo Finance)
NIFTY_INDEX = "^NSEI"

# Price fetching
YFINANCE_PERIOD = "15d"
YFINANCE_INTERVAL = "1d"
YFINANCE_BATCH_SIZE = 75  # safer for GitHub Actions

# Man of the Match filtering (not limited to 5; filtered by meaningfulness)
MOM_MIN_ABS_PCT_MOVE = 1.75      # include if |%move| >= this
MOM_MIN_VOL_RATIO = 1.80         # include if volume spike >= this
MOM_MAX_ROWS_IN_TELEGRAM = 30    # Telegram message length protection; we still show many

# Sector strength
SECTOR_TOP_N = 3
SECTOR_BOTTOM_N = 3

# News sources (RSS) – stable approach for “authenticated sources”
NEWS_FEEDS = [
    {"source": "Moneycontrol", "rss": "https://www.moneycontrol.com/rss/marketreports.xml"},
    {"source": "Moneycontrol", "rss": "https://www.moneycontrol.com/rss/business.xml"},
    {"source": "NDTV Profit",  "rss": "https://feeds.feedburner.com/ndtvprofit-latest"},
    # ET Markets RSS availability varies; you can add your preferred ET RSS here if you have a stable one
    # {"source": "ET Markets",   "rss": "<your-et-rss>"},
]

# Source credibility weight (for conviction)
SOURCE_WEIGHT = {
    "NSE": 1.00,
    "Reuters": 0.95,
    "NDTV Profit": 0.90,
    "ET Markets": 0.90,
    "Moneycontrol": 0.85,
    "Business Standard": 0.85,
    "Livemint": 0.85,
}

# Conviction weights (out of 100)
CONVICTION_WEIGHTS = {
    "price_momentum": 30,
    "volume_expansion": 20,
    "sector_strength": 15,
    "news_sentiment": 20,
    "breakout_technical": 10,
    "market_regime_fit": 5,
}

# BTST action defaults
BTST_CAPITAL_PER_TRADE = 5000
BTST_TARGET_PCT = 0.020  # 2%
BTST_STOP_PCT = 0.010    # 1%
