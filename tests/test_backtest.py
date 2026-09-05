import pytest
import pandas as pd
from bot.research.validator import WalkForwardValidator
from bot.agents.base import BaseAgent
from typing import Dict, Any

class MockAgent(BaseAgent):
    def __init__(self):
        super().__init__("MockAgent")

    def analyze(self, symbol: str, price_history: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        # Always buy on first day, then hold
        return {
            "agent": "MockAgent",
            "symbol": symbol,
            "signal": "BUY" if len(price_history) == 50 else "HOLD",
            "score": 0.8,
            "confidence": 0.8,
            "reason": "Test"
        }

def test_walk_forward_validator():
    # Make sure we have enough points of warmup for BOTH train and validate datasets!
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
    # Even if robustness rejects it, the function should run successfully
    assert "passed" in report
    assert "train" in report
    assert "validate" in report
    assert "robustness" in report
