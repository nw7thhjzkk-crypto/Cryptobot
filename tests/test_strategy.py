import pandas as pd
import pytest
from bot.strategy import trend_signal

def test_trend_signal_insufficient_data():
    """Test that it returns hold when length < 60."""
    prices = [100.0] * 59
    df = pd.DataFrame({"close": prices})
    assert trend_signal(df) == "hold"

def test_trend_signal_empty_data():
    """Test that it returns hold when dataframe is empty."""
    df = pd.DataFrame({"close": []})
    assert trend_signal(df) == "hold"

def test_trend_signal_buy():
    """Test that it returns buy on a bullish crossover."""
    # 59 periods of flat price, then a jump up on the 60th period
    # This will cause the fast EMA (20) to spike above the slow EMA (50)
    prices = [100.0] * 59 + [110.0]
    df = pd.DataFrame({"close": prices})
    assert trend_signal(df) == "buy"

def test_trend_signal_sell():
    """Test that it returns sell on a bearish crossover."""
    # 59 periods of flat price, then a drop down on the 60th period
    # This will cause the fast EMA (20) to drop below the slow EMA (50)
    prices = [100.0] * 59 + [90.0]
    df = pd.DataFrame({"close": prices})
    assert trend_signal(df) == "sell"

def test_trend_signal_hold():
    """Test that it returns hold when there is no crossover."""
    # Flat price, no crossovers
    prices = [100.0] * 60
    df = pd.DataFrame({"close": prices})
    assert trend_signal(df) == "hold"
