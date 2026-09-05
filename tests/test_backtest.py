import pytest
import pandas as pd
from bot.backtest.engine import BacktestEngine
from bot.research.validator import WalkForwardValidator
from bot.agents.base import BaseAgent

class MockAgent(BaseAgent):
    def __init__(self):
        super().__init__("MockAgent")
    def analyze(self, symbol, data, **kwargs):
        close = data['close'].iloc[-1]
        # Buy below 105, sell above 115
        if close < 105:
            return {"signal": "BUY", "confidence": 1.0}
        elif close > 115:
            return {"signal": "SELL", "confidence": 1.0}
        return {"signal": "HOLD"}

def test_backtest_engine():
    prices = [100.0] * 70 + [120.0] * 10
    df = pd.DataFrame({
        'close': prices,
        'open': prices,
        'high': prices,
        'low': prices,
        'volume': [1000] * 80
    })

    engine = BacktestEngine(initial_capital=10000, transaction_cost=0)
    agent = MockAgent()
    metrics = engine.run(agent, "AAPL", df)

    assert metrics["num_trades"] == 1
    assert metrics["total_return"] > 0
    assert metrics["win_rate"] == 1.0

def test_walk_forward_validator():
    # Make sure we have 65 points of warmup for BOTH train and validate datasets!
    # Train: 100 points
    # Val: 100 points
    train_prices = [100.0] * 80 + [120.0] * 20
    val_prices = [100.0] * 80 + [120.0] * 20
    prices = train_prices + val_prices

    df = pd.DataFrame({
        'close': prices,
        'open': prices,
        'high': prices,
        'low': prices,
        'volume': [1000] * len(prices)
    })

    validator = WalkForwardValidator(train_ratio=0.5)
    agent = MockAgent()

    report = validator.validate(agent, "AAPL", df)
    assert report["agent"] == "MockAgent"
    assert report["passed"] is True
    assert report["train"]["num_trades"] > 0
    assert report["validate"]["num_trades"] > 0
