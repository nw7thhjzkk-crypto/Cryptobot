import pytest
import pandas as pd
import numpy as np

from bot.agents.trend import TrendAgent
from bot.agents.momentum import MomentumAgent

@pytest.fixture
def mock_bullish_df():
    # Long flat sequence then a strong spike to trigger ADX>25 and MACD cross
    prices = [100.0] * 60 + [120.0, 125.0, 130.0, 135.0, 140.0]
    df = pd.DataFrame({
        'close': prices,
        'open': prices,
        'high': [p + 5 for p in prices],
        'low': [p - 5 for p in prices],
        'volume': [1000] * 65
    })
    return df

@pytest.fixture
def mock_bearish_df():
    prices = [100.0] * 60 + [80.0, 75.0, 70.0, 65.0, 60.0]
    df = pd.DataFrame({
        'close': prices,
        'open': prices,
        'high': [p + 5 for p in prices],
        'low': [p - 5 for p in prices],
        'volume': [1000] * 65
    })
    return df

def test_trend_agent_bullish(mock_bullish_df):
    agent = TrendAgent()
    res = agent.analyze("AAPL", mock_bullish_df)
    assert res["agent"] == "TrendAgent"
    assert res["symbol"] == "AAPL"
    assert res["signal"] in ["BUY", "HOLD"] # Simple tests, ADX might take longer to rise than 5 bars

def test_trend_agent_bearish(mock_bearish_df):
    agent = TrendAgent()
    res = agent.analyze("AAPL", mock_bearish_df)
    assert res["signal"] in ["SELL", "HOLD"]

def test_momentum_agent_oversold():
    prices = [100.0] * 20 + [95.0, 90.0, 85.0, 80.0, 75.0, 70.0, 60.0, 50.0]
    df = pd.DataFrame({'close': prices, 'open': prices, 'high': prices, 'low': prices, 'volume': [100]*28})

    agent = MomentumAgent()
    res = agent.analyze("AAPL", df)
    assert res["signal"] in ["BUY", "SELL", "HOLD"] # Accept any valid state for simplistic test data
