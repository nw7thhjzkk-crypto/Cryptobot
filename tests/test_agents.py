import pytest
import pandas as pd
import numpy as np

from bot.agents.trend import TrendAgent
from bot.agents.momentum import MomentumAgent

@pytest.fixture
def mock_bullish_df():
    prices = [100.0] * 50 + [102.0, 104.0, 106.0, 108.0, 110.0, 112.0, 114.0, 116.0, 118.0, 120.0]
    df = pd.DataFrame({
        'close': prices,
        'open': prices,
        'high': [p + 1 for p in prices],
        'low': [p - 1 for p in prices],
        'volume': [1000] * 60
    })
    return df

@pytest.fixture
def mock_bearish_df():
    prices = [100.0] * 50 + [98.0, 96.0, 94.0, 92.0, 90.0, 88.0, 86.0, 84.0, 82.0, 80.0]
    df = pd.DataFrame({
        'close': prices,
        'open': prices,
        'high': [p + 1 for p in prices],
        'low': [p - 1 for p in prices],
        'volume': [1000] * 60
    })
    return df

def test_trend_agent_bullish(mock_bullish_df):
    agent = TrendAgent()
    res = agent.analyze("AAPL", mock_bullish_df)
    assert res["agent"] == "TrendAgent"
    assert res["symbol"] == "AAPL"
    assert res["signal"] == "BUY"
    assert res["confidence"] > 0.0

def test_trend_agent_bearish(mock_bearish_df):
    agent = TrendAgent()
    res = agent.analyze("AAPL", mock_bearish_df)
    assert res["signal"] == "SELL"
    assert res["confidence"] > 0.0

def test_momentum_agent_oversold():
    prices = [100.0] * 20 + [95.0, 90.0, 85.0, 80.0, 75.0, 70.0, 60.0, 50.0]
    df = pd.DataFrame({'close': prices, 'open': prices, 'high': prices, 'low': prices, 'volume': [100]*28})

    agent = MomentumAgent()
    res = agent.analyze("AAPL", df)
    assert res["signal"] in ["SELL", "HOLD"]
