import pytest
from unittest.mock import patch
import pandas as pd
from bot.strategy import decide

@patch('bot.strategy.detect_regime')
@patch('bot.strategy.trend_signal')
@patch('bot.strategy.mean_reversion_signal')
def test_decide_trending(mock_mean_reversion, mock_trend, mock_detect):
    mock_detect.return_value = 'trending'
    mock_trend.return_value = 'buy'

    df = pd.DataFrame({'close': [1, 2, 3]})
    result = decide('AAPL', df)

    assert result == {'action': 'buy', 'regime': 'trending', 'sleeve': 'trend'}
    mock_detect.assert_called_once_with(df)
    mock_trend.assert_called_once_with(df)
    mock_mean_reversion.assert_not_called()

@patch('bot.strategy.detect_regime')
@patch('bot.strategy.trend_signal')
@patch('bot.strategy.mean_reversion_signal')
def test_decide_ranging_eligible(mock_mean_reversion, mock_trend, mock_detect):
    mock_detect.return_value = 'ranging'
    mock_mean_reversion.return_value = 'sell'

    # We need to mock MEAN_REVERSION_ELIGIBLE if 'AAPL' is not in it by default
    with patch('bot.strategy.MEAN_REVERSION_ELIGIBLE', ['AAPL']):
        df = pd.DataFrame({'close': [1, 2, 3]})
        result = decide('AAPL', df)

        assert result == {'action': 'sell', 'regime': 'ranging', 'sleeve': 'mean_reversion'}
        mock_detect.assert_called_once_with(df)
        mock_mean_reversion.assert_called_once_with('AAPL', df)
        mock_trend.assert_not_called()

@patch('bot.strategy.detect_regime')
@patch('bot.strategy.trend_signal')
@patch('bot.strategy.mean_reversion_signal')
def test_decide_ranging_ineligible(mock_mean_reversion, mock_trend, mock_detect):
    mock_detect.return_value = 'ranging'
    # mean_reversion_signal should still be called (it handles eligibility internally too, but strategy logic passes it)
    mock_mean_reversion.return_value = 'hold'

    with patch('bot.strategy.MEAN_REVERSION_ELIGIBLE', ['MSFT']): # AAPL not eligible
        df = pd.DataFrame({'close': [1, 2, 3]})
        result = decide('AAPL', df)

        # In current logic, action = mean_reversion_signal(symbol, price_history), sleeve = "none" if not eligible
        assert result == {'action': 'hold', 'regime': 'ranging', 'sleeve': 'none'}
        mock_detect.assert_called_once_with(df)
        mock_mean_reversion.assert_called_once_with('AAPL', df)
        mock_trend.assert_not_called()

@patch('bot.strategy.detect_regime')
@patch('bot.strategy.trend_signal')
@patch('bot.strategy.mean_reversion_signal')
def test_decide_transitional(mock_mean_reversion, mock_trend, mock_detect):
    mock_detect.return_value = 'transitional'

    df = pd.DataFrame({'close': [1, 2, 3]})
    result = decide('AAPL', df)

    assert result == {'action': 'hold', 'regime': 'transitional', 'sleeve': 'none'}
    mock_detect.assert_called_once_with(df)
    mock_trend.assert_not_called()
    mock_mean_reversion.assert_not_called()

def test_decide_empty_history():
    df = pd.DataFrame()
    result = decide('AAPL', df)

    assert result == {'action': 'hold', 'regime': 'unknown', 'sleeve': 'none'}
