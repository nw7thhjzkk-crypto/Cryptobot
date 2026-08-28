import unittest
from unittest.mock import patch
import pandas as pd
import numpy as np

from bot.strategy import detect_regime

def make_series(last_val, avg_val=None, length=70):
    if avg_val is None:
        return pd.Series([last_val] * length)

    val = (50 * avg_val - last_val) / 49.0
    arr = [val] * (length - 1) + [last_val]
    return pd.Series(arr)

class TestStrategyRegime(unittest.TestCase):
    def setUp(self):
        # 70 rows of data so len(df) >= 65
        self.df = pd.DataFrame({'close': np.random.uniform(100, 110, 70)})

    def test_detect_regime_insufficient_data(self):
        small_df = pd.DataFrame({'close': range(50)})
        self.assertEqual(detect_regime(small_df), "transitional")

    @patch('bot.strategy.calculate_adx')
    @patch('bot.strategy.calculate_atr')
    @patch('bot.strategy.calculate_bbands')
    def test_detect_regime_trending(self, mock_bbands, mock_atr, mock_adx):
        mock_adx.return_value = make_series(last_val=30)  # > 25
        mock_atr.return_value = make_series(last_val=1.0, avg_val=1.0) # no override (1.0 < 1.5 * 1.0)

        # calculate_bbands returns lower, mid, upper, bandwidth
        dummy_band = make_series(100)
        mock_bbands.return_value = (dummy_band, dummy_band, dummy_band, make_series(last_val=10, avg_val=10))

        self.assertEqual(detect_regime(self.df), "trending")

    @patch('bot.strategy.calculate_adx')
    @patch('bot.strategy.calculate_atr')
    @patch('bot.strategy.calculate_bbands')
    def test_detect_regime_ranging(self, mock_bbands, mock_atr, mock_adx):
        mock_adx.return_value = make_series(last_val=15)  # < 20
        mock_atr.return_value = make_series(last_val=1.0, avg_val=1.0) # no override

        # bb_width contracting: current_bb_width (8) < bb_width_50_avg (10)
        dummy_band = make_series(100)
        mock_bbands.return_value = (dummy_band, dummy_band, dummy_band, make_series(last_val=8, avg_val=10))

        self.assertEqual(detect_regime(self.df), "ranging")

    @patch('bot.strategy.calculate_adx')
    @patch('bot.strategy.calculate_atr')
    @patch('bot.strategy.calculate_bbands')
    def test_detect_regime_transitional_atr_override(self, mock_bbands, mock_atr, mock_adx):
        # Even if ADX > 25 (trending)
        mock_adx.return_value = make_series(last_val=30)
        # ATR override: current_atr (2.0) > 1.5 * atr_50_avg (1.0) => 2.0 > 1.5
        mock_atr.return_value = make_series(last_val=2.0, avg_val=1.0)

        dummy_band = make_series(100)
        mock_bbands.return_value = (dummy_band, dummy_band, dummy_band, make_series(last_val=10, avg_val=10))

        self.assertEqual(detect_regime(self.df), "transitional")

    @patch('bot.strategy.calculate_adx')
    @patch('bot.strategy.calculate_atr')
    @patch('bot.strategy.calculate_bbands')
    def test_detect_regime_transitional_default(self, mock_bbands, mock_atr, mock_adx):
        # ADX between 20 and 25
        mock_adx.return_value = make_series(last_val=22)
        mock_atr.return_value = make_series(last_val=1.0, avg_val=1.0)

        dummy_band = make_series(100)
        mock_bbands.return_value = (dummy_band, dummy_band, dummy_band, make_series(last_val=10, avg_val=10))

        self.assertEqual(detect_regime(self.df), "transitional")

    @patch('bot.strategy.calculate_adx')
    @patch('bot.strategy.calculate_atr')
    @patch('bot.strategy.calculate_bbands')
    def test_detect_regime_adx_none(self, mock_bbands, mock_atr, mock_adx):
        mock_adx.return_value = None
        self.assertEqual(detect_regime(self.df), "transitional")

if __name__ == '__main__':
    unittest.main()
