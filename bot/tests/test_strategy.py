import pytest
import pandas as pd
import numpy as np
from bot.strategy import mean_reversion_signal
import bot.config

@pytest.fixture
def dummy_price_history():
    """Creates a basic DataFrame with 30 rows of dummy data."""
    dates = pd.date_range("2023-01-01", periods=30)
    df = pd.DataFrame({
        "open": np.linspace(100, 130, 30),
        "high": np.linspace(102, 132, 30),
        "low": np.linspace(98, 128, 30),
        "close": np.linspace(101, 131, 30),
        "volume": np.random.randint(1000, 5000, 30)
    }, index=dates)
    return df

def test_dummy_fixture(dummy_price_history):
    assert len(dummy_price_history) == 30
    assert 'close' in dummy_price_history.columns


def test_mean_reversion_symbol_not_eligible(dummy_price_history, mocker):
    # Temporarily remove symbol from eligible list to ensure it's not present

    mocker.patch("bot.strategy.MEAN_REVERSION_ELIGIBLE", ["SPY", "QQQ"])

    assert mean_reversion_signal("AAPL", dummy_price_history) == "hold"

    # Restore


def test_mean_reversion_short_history(dummy_price_history, mocker):
    # Provide a dataframe with length < 25
    short_df = dummy_price_history.iloc[:24]
    mocker.patch("bot.strategy.MEAN_REVERSION_ELIGIBLE", ["AAPL"])

    assert mean_reversion_signal("AAPL", short_df) == "hold"

def test_mean_reversion_empty_rsi(dummy_price_history, mocker):
    mocker.patch("bot.strategy.MEAN_REVERSION_ELIGIBLE", ["AAPL"])

    # Mock calculate_rsi to return empty
    mocker.patch('bot.strategy.calculate_rsi', return_value=pd.Series(dtype=float))

    # Mock calculate_bbands to return dummy data so it doesn't fail before RSI check
    mocker.patch('bot.strategy.calculate_bbands', return_value=(
        pd.Series([100]), pd.Series([110]), pd.Series([120]), pd.Series([20])
    ))

    assert mean_reversion_signal("AAPL", dummy_price_history) == "hold"

def test_mean_reversion_buy_signal(dummy_price_history, mocker):
    mocker.patch("bot.strategy.MEAN_REVERSION_ELIGIBLE", ["AAPL"])

    # Mock calculate_rsi to return 29 (oversold)
    mocker.patch('bot.strategy.calculate_rsi', return_value=pd.Series([29]))

    # Mock calculate_bbands to return lower_band=100
    mocker.patch('bot.strategy.calculate_bbands', return_value=(
        pd.Series([100]), pd.Series([110]), pd.Series([120]), pd.Series([20])
    ))

    # Modify the last close price to be <= lower_band
    dummy_price_history.loc[dummy_price_history.index[-1], 'close'] = 99

    assert mean_reversion_signal("AAPL", dummy_price_history) == "buy"

def test_mean_reversion_sell_signal(dummy_price_history, mocker):
    mocker.patch("bot.strategy.MEAN_REVERSION_ELIGIBLE", ["AAPL"])

    # Mock calculate_rsi to return 71 (overbought)
    mocker.patch('bot.strategy.calculate_rsi', return_value=pd.Series([71]))

    # Mock calculate_bbands to return upper_band=100
    mocker.patch('bot.strategy.calculate_bbands', return_value=(
        pd.Series([80]), pd.Series([90]), pd.Series([100]), pd.Series([20])
    ))

    # Modify the last close price to be >= upper_band
    dummy_price_history.loc[dummy_price_history.index[-1], 'close'] = 101

    assert mean_reversion_signal("AAPL", dummy_price_history) == "sell"

def test_mean_reversion_hold_normal_rsi(dummy_price_history, mocker):
    mocker.patch("bot.strategy.MEAN_REVERSION_ELIGIBLE", ["AAPL"])

    # Mock calculate_rsi to return 50 (neutral)
    mocker.patch('bot.strategy.calculate_rsi', return_value=pd.Series([50]))

    # Mock calculate_bbands
    mocker.patch('bot.strategy.calculate_bbands', return_value=(
        pd.Series([80]), pd.Series([90]), pd.Series([100]), pd.Series([20])
    ))

    assert mean_reversion_signal("AAPL", dummy_price_history) == "hold"

def test_mean_reversion_hold_inside_bands(dummy_price_history, mocker):
    mocker.patch("bot.strategy.MEAN_REVERSION_ELIGIBLE", ["AAPL"])

    # Mock calculate_rsi to return 29 (oversold)
    mocker.patch('bot.strategy.calculate_rsi', return_value=pd.Series([29]))

    # Mock calculate_bbands to return lower_band=100
    mocker.patch('bot.strategy.calculate_bbands', return_value=(
        pd.Series([100]), pd.Series([110]), pd.Series([120]), pd.Series([20])
    ))

    # Modify the last close price to be > lower_band (inside bands)
    dummy_price_history.loc[dummy_price_history.index[-1], 'close'] = 105

    assert mean_reversion_signal("AAPL", dummy_price_history) == "hold"
