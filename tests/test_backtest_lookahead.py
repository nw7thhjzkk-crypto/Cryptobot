import pytest
import pandas as pd
from bot.backtest.engine import BacktestEngine

class DummyAgent:
    def __init__(self):
        self.parameters = {}
    def analyze(self, symbol, data, **kwargs):
        if len(data) > 50 and len(data) < 55:
            return {"signal": "BUY", "confidence": 1.0}
        elif len(data) >= 55:
            return {"signal": "SELL", "confidence": 1.0}
        return {"signal": "HOLD"}

def test_backtest_no_lookahead():
    engine = BacktestEngine(initial_capital=10000.0, transaction_cost=0.0, slippage=0.0)
    agent = DummyAgent()
    dates = pd.date_range("2023-01-01", periods=100)
    df = pd.DataFrame({"open": [10.0]*100, "high": [10.0]*100, "low": [10.0]*100, "close": [10.0]*100, "volume": [1000]*100}, index=dates)
    df.iloc[52, df.columns.get_loc("close")] = 20.0
    metrics = engine.run(agent, "TEST", df)
    assert metrics is not None
