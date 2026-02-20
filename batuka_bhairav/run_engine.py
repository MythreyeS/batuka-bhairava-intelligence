import csv
from batuka_bhairav.providers.prices import fetch_ohlcv
from batuka_bhairav.core.scoring import score_stock
from batuka_bhairav.config import YFINANCE_PERIOD, YFINANCE_INTERVAL

def load_universe(path="batuka_bhairav/universe/nifty500.csv"):
    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def main():
    stocks = load_universe()
    results = []

    for stock in stocks:
        symbol = stock["symbol"]
        name = stock["name"]

        df = fetch_ohlcv(symbol, YFINANCE_PERIOD, YFINANCE_INTERVAL)
        score, explanation = score_stock(df)

        results.append((name, symbol, score, explanation))

    results.sort(key=lambda x: x[2], reverse=True)

    for r in results:
        print("=" * 40)
        print(f"{r[0]} ({r[1]})")
        print(r[3])

if __name__ == "__main__":
    main()
