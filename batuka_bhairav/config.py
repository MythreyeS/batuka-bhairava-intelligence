# batuka_bhairav/config.py
import os

ACTIVE_MARKET = os.getenv("MARKET", "IN").upper()

MARKETS = {
    "IN": {
        "name":         "India (NSE)",
        "index":        "^NSEI",
        "index_label":  "NIFTY 50",
        "currency":     "₹",
        "timezone":     "Asia/Kolkata",
        "universe_csv": "batuka_bhairav/universe/nifty500.csv",
        "news_feeds": [
            # Moneycontrol
            {"source": "Moneycontrol",      "rss": "https://www.moneycontrol.com/rss/marketreports.xml"},
            {"source": "Moneycontrol",      "rss": "https://www.moneycontrol.com/rss/business.xml"},
            {"source": "Moneycontrol",      "rss": "https://www.moneycontrol.com/rss/results.xml"},
            # Economic Times
            {"source": "Economic Times",    "rss": "https://economictimes.indiatimes.com/markets/stocks/rssfeeds/2146842.cms"},
            {"source": "Economic Times",    "rss": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"},
            # Business Standard
            {"source": "Business Standard", "rss": "https://www.business-standard.com/rss/markets-106.rss"},
            {"source": "Business Standard", "rss": "https://www.business-standard.com/rss/stocks-10601.rss"},
            # NDTV Profit
            {"source": "NDTV Profit",       "rss": "https://feeds.feedburner.com/ndtvprofit-latest"},
            {"source": "NDTV Profit",       "rss": "https://feeds.feedburner.com/ndtvprofit-markets"},
            # Livemint
            {"source": "Livemint",          "rss": "https://www.livemint.com/rss/markets"},
            {"source": "Livemint",          "rss": "https://www.livemint.com/rss/companies"},
            # Financial Express
            {"source": "Financial Express", "rss": "https://www.financialexpress.com/market/feed/"},
            # Reuters India
            {"source": "Reuters",           "rss": "https://feeds.reuters.com/reuters/INbusinessNews"},
            # NSE/BSE announcements (free)
            {"source": "The Hindu Business","rss": "https://www.thehindubusinessline.com/markets/?service=rss"},
            # Zee Business
            {"source": "Zee Business",      "rss": "https://www.zeebiz.com/rss/markets.xml"},
        ],
    },
    "US": {
        "name":         "USA (NYSE/NASDAQ)",
        "index":        "^GSPC",
        "index_label":  "S&P 500",
        "currency":     "$",
        "timezone":     "America/New_York",
        "universe_csv": "batuka_bhairav/universe/usa500.csv",
        "news_feeds": [
            # Reuters
            {"source": "Reuters",           "rss": "https://feeds.reuters.com/reuters/businessNews"},
            {"source": "Reuters",           "rss": "https://feeds.reuters.com/reuters/companyNews"},
            # MarketWatch
            {"source": "MarketWatch",       "rss": "https://feeds.marketwatch.com/marketwatch/topstories/"},
            {"source": "MarketWatch",       "rss": "https://feeds.marketwatch.com/marketwatch/marketpulse/"},
            # CNBC
            {"source": "CNBC",              "rss": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114"},
            {"source": "CNBC",              "rss": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=20910258"},
            # Seeking Alpha (free)
            {"source": "Seeking Alpha",     "rss": "https://seekingalpha.com/market_currents.xml"},
            # Motley Fool
            {"source": "Motley Fool",       "rss": "https://www.fool.com/feeds/index.aspx"},
            # Benzinga
            {"source": "Benzinga",          "rss": "https://www.benzinga.com/feed"},
            # Yahoo Finance
            {"source": "Yahoo Finance",     "rss": "https://finance.yahoo.com/news/rssindex"},
            # Investopedia
            {"source": "Investopedia",      "rss": "https://www.investopedia.com/feedbuilder/feed/getfeed?feedName=rss_headline"},
            # Barron's (free articles)
            {"source": "Barrons",           "rss": "https://www.barrons.com/xml/rss/3_7510.xml"},
        ],
    },
    "UK": {
        "name":         "UK (LSE)",
        "index":        "^FTSE",
        "index_label":  "FTSE 100",
        "currency":     "£",
        "timezone":     "Europe/London",
        "universe_csv": "batuka_bhairav/universe/ftse100.csv",
        "news_feeds": [
            # Reuters UK
            {"source": "Reuters",           "rss": "https://feeds.reuters.com/reuters/UKBusinessNews"},
            {"source": "Reuters",           "rss": "https://feeds.reuters.com/reuters/UKTopNews"},
            # BBC Business
            {"source": "BBC Business",      "rss": "https://feeds.bbci.co.uk/news/business/rss.xml"},
            # The Guardian Business
            {"source": "Guardian",          "rss": "https://www.theguardian.com/uk/business/rss"},
            # Financial Times (free)
            {"source": "Financial Times",   "rss": "https://www.ft.com/rss/home/uk"},
            # Sky News Business
            {"source": "Sky News",          "rss": "https://feeds.skynews.com/feeds/rss/business.xml"},
            # This is Money
            {"source": "This is Money",     "rss": "https://www.thisismoney.co.uk/money/markets/index.rss"},
            # Shares Magazine
            {"source": "Shares Mag",        "rss": "https://www.sharesmagazine.co.uk/rss/news"},
            # Interactive Investor
            {"source": "Interactive Inv",   "rss": "https://www.iii.co.uk/rss/news"},
        ],
    },
    "SG": {
        "name":         "Singapore (SGX)",
        "index":        "^STI",
        "index_label":  "STI",
        "currency":     "S$",
        "timezone":     "Asia/Singapore",
        "universe_csv": "batuka_bhairav/universe/sgx.csv",
        "news_feeds": [
            # Business Times Singapore
            {"source": "Business Times SG", "rss": "https://www.businesstimes.com.sg/rss/all"},
            {"source": "Business Times SG", "rss": "https://www.businesstimes.com.sg/rss/companies-markets"},
            # Straits Times Business
            {"source": "Straits Times",     "rss": "https://www.straitstimes.com/news/business/rss.xml"},
            # Channel News Asia
            {"source": "CNA",               "rss": "https://www.channelnewsasia.com/rssfeeds/8395986"},
            {"source": "CNA Business",      "rss": "https://www.channelnewsasia.com/rssfeeds/8395990"},
            # Reuters Asia
            {"source": "Reuters Asia",      "rss": "https://feeds.reuters.com/reuters/AsiaBusinessNews"},
            # SGX announcements (free)
            {"source": "SGX",               "rss": "https://www.sgx.com/securities/company-announcements/rss"},
            # The Edge Singapore
            {"source": "The Edge SG",       "rss": "https://www.theedgesingapore.com/rss.xml"},
        ],
    },
}

# ── Active market config ───────────────────────────────────────────────────
_cfg = MARKETS.get(ACTIVE_MARKET, MARKETS["IN"])

MARKET_NAME     = _cfg["name"]
MARKET_CURRENCY = _cfg["currency"]
MARKET_TIMEZONE = _cfg["timezone"]
UNIVERSE_CSV    = _cfg["universe_csv"]
INDEX_SYMBOL    = _cfg["index"]
INDEX_LABEL     = _cfg["index_label"]
NEWS_FEEDS      = _cfg["news_feeds"]

# backward compat
NIFTY_INDEX = INDEX_SYMBOL

# ── Price fetching ─────────────────────────────────────────────────────────
YFINANCE_PERIOD     = "3mo"
YFINANCE_INTERVAL   = "1d"
YFINANCE_BATCH_SIZE = 75

# ── Man of Match filters ───────────────────────────────────────────────────
MOM_MIN_ABS_PCT_MOVE     = 1.75
MOM_MIN_VOL_RATIO        = 1.80
MOM_MAX_ROWS_IN_TELEGRAM = 30
SECTOR_TOP_N             = 3
SECTOR_BOTTOM_N          = 3

# ── Source credibility weights ─────────────────────────────────────────────
SOURCE_WEIGHT = {
    # India
    "NSE":               1.00,
    "Economic Times":    0.95,
    "Business Standard": 0.92,
    "NDTV Profit":       0.90,
    "Moneycontrol":      0.88,
    "Livemint":          0.87,
    "Financial Express": 0.85,
    "The Hindu Business":0.85,
    "Zee Business":      0.75,
    # US
    "Reuters":           0.95,
    "CNBC":              0.90,
    "MarketWatch":       0.87,
    "Barrons":           0.87,
    "Seeking Alpha":     0.80,
    "Motley Fool":       0.78,
    "Benzinga":          0.75,
    "Yahoo Finance":     0.75,
    "Investopedia":      0.72,
    # UK
    "Financial Times":   0.95,
    "BBC Business":      0.90,
    "Guardian":          0.85,
    "Sky News":          0.80,
    "This is Money":     0.75,
    "Shares Mag":        0.73,
    "Interactive Inv":   0.72,
    # SG
    "Business Times SG": 0.92,
    "Straits Times":     0.90,
    "CNA":               0.88,
    "CNA Business":      0.88,
    "Reuters Asia":      0.90,
    "SGX":               1.00,
    "The Edge SG":       0.82,
}

# ── Conviction weights ─────────────────────────────────────────────────────
CONVICTION_WEIGHTS = {
    "price_momentum":     30,
    "volume_expansion":   20,
    "sector_strength":    15,
    "news_sentiment":     20,
    "breakout_technical": 10,
    "market_regime_fit":   5,
}

# ── BTST trade defaults ────────────────────────────────────────────────────
BTST_CAPITAL_PER_TRADE = float(os.getenv("BTST_CAPITAL", "5000"))
BTST_TARGET_PCT        = 0.020
BTST_STOP_PCT          = 0.010
