import time
import pandas as pd
import numpy as np
import os

os.environ['ALPACA_API_KEY'] = 'test'
os.environ['ALPACA_SECRET_KEY'] = 'test'
os.environ['GOOGLE_SERVICE_ACCOUNT_JSON'] = '{"type":"service_account"}'
os.environ['GOOGLE_SHEET_ID'] = 'test'
os.environ['WATCHLIST'] = 'AAPL'

from bot.strategy import decide, detect_regime, calculate_atr

def run_benchmark():
    # create dummy price history
    np.random.seed(42)
    n = 1000
    df = pd.DataFrame({
        'high': np.random.rand(n) * 10 + 100,
        'low': np.random.rand(n) * 10 + 90,
        'close': np.random.rand(n) * 10 + 95,
    })

    start = time.time()
    for _ in range(100):
        decision = decide('AAPL', df)
        # simulate bot/main.py logic
        action = decision["action"]

        # calculate ATR redundant
        atr_s = calculate_atr(df, length=14)
        atr = atr_s.iloc[-1] if (atr_s is not None and not atr_s.empty) else 0

    end = time.time()

    print(f"Time taken (baseline): {end - start:.4f} seconds")

if __name__ == '__main__':
    run_benchmark()
