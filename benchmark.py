import time
from bot.broker import get_price_history
from bot.config import WATCHLIST

def run_n_plus_1():
    start = time.time()
    for symbol in WATCHLIST:
        get_price_history(symbol)
    end = time.time()
    print(f"N+1 time: {end - start:.2f}s")

def get_price_history_batch(symbols, lookback_days=100):
    from bot.broker import data_client, StockBarsRequest, TimeFrame, datetime, timedelta
    try:
        end = datetime.now()
        start = end - timedelta(days=lookback_days)
        req = StockBarsRequest(
            symbol_or_symbols=symbols,
            timeframe=TimeFrame.Day,
            start=start,
            end=end
        )
        bars = data_client.get_stock_bars(req)
        return {"success": True, "data": bars.df}
    except Exception as e:
        return {"success": False, "reason": str(e)}

def run_batch():
    start = time.time()
    get_price_history_batch(WATCHLIST)
    end = time.time()
    print(f"Batch time: {end - start:.2f}s")

if __name__ == '__main__':
    print(f"Watchlist: {WATCHLIST}")
    run_n_plus_1()
    run_batch()
