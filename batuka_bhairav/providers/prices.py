import yfinance as yf

def fetch_ohlcv(symbol, period="3mo", interval="1d"):
    try:
        df = yf.download(symbol, period=period, interval=interval, progress=False)
        if df is None or df.empty:
            return None
        return df.dropna()
    except Exception:
        return None
