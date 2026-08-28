import unittest
import pandas as pd
import numpy as np

from bot.strategy import (
    calculate_atr,
    calculate_adx,
    calculate_bbands,
    calculate_rsi,
    calculate_macd,
    detect_regime,
    trend_signal,
    mean_reversion_signal,
    get_middle_band,
    decide
)

class TestIndicators(unittest.TestCase):
    def setUp(self):
        # Create a synthetic dataframe with enough rows for all indicators
        # Needs at least 50+ rows for MACD and BBands
        np.random.seed(42)
        n = 100
        self.df = pd.DataFrame({
            'open': np.random.randn(n).cumsum() + 100,
            'high': np.random.randn(n).cumsum() + 105,
            'low': np.random.randn(n).cumsum() + 95,
            'close': np.random.randn(n).cumsum() + 100,
            'volume': np.random.randint(100, 1000, n)
        })

        # Ensure high is highest and low is lowest
        self.df['high'] = self.df[['open', 'close', 'high']].max(axis=1)
        self.df['low'] = self.df[['open', 'close', 'low']].min(axis=1)

    def test_calculate_atr(self):
        atr = calculate_atr(self.df, length=14)
        self.assertIsInstance(atr, pd.Series)
        self.assertEqual(len(atr), len(self.df))

        # Test empty
        empty_df = pd.DataFrame(columns=['high', 'low', 'close'])
        empty_atr = calculate_atr(empty_df)
        self.assertTrue(empty_atr.empty)

    def test_calculate_adx(self):
        adx = calculate_adx(self.df, length=14)
        self.assertIsInstance(adx, pd.Series)
        self.assertEqual(len(adx), len(self.df))

        # Test empty
        empty_df = pd.DataFrame(columns=['high', 'low', 'close'])
        empty_adx = calculate_adx(empty_df)
        self.assertTrue(empty_adx.empty)

    def test_calculate_bbands(self):
        lower_band, sma, upper_band, bandwidth = calculate_bbands(self.df, length=20)
        self.assertIsInstance(lower_band, pd.Series)
        self.assertIsInstance(sma, pd.Series)
        self.assertIsInstance(upper_band, pd.Series)
        self.assertIsInstance(bandwidth, pd.Series)
        self.assertEqual(len(lower_band), len(self.df))

        # Test empty
        empty_df = pd.DataFrame(columns=['close'])
        lower, mid, upper, bw = calculate_bbands(empty_df)
        self.assertTrue(lower.empty)
        self.assertTrue(mid.empty)
        self.assertTrue(upper.empty)
        self.assertTrue(bw.empty)

    def test_calculate_rsi(self):
        rsi = calculate_rsi(self.df, length=14)
        self.assertIsInstance(rsi, pd.Series)
        self.assertEqual(len(rsi), len(self.df))

        # Test empty
        empty_df = pd.DataFrame(columns=['close'])
        empty_rsi = calculate_rsi(empty_df)
        self.assertTrue(empty_rsi.empty)

    def test_calculate_macd(self):
        macd_hist = calculate_macd(self.df)
        self.assertIsInstance(macd_hist, pd.Series)
        self.assertEqual(len(macd_hist), len(self.df))

        # Test empty
        empty_df = pd.DataFrame(columns=['close'])
        empty_macd = calculate_macd(empty_df)
        self.assertTrue(empty_macd.empty)

class TestSignalsAndRegimes(unittest.TestCase):
    def setUp(self):
        np.random.seed(42)
        n = 100
        self.df = pd.DataFrame({
            'open': np.random.randn(n).cumsum() + 100,
            'high': np.random.randn(n).cumsum() + 105,
            'low': np.random.randn(n).cumsum() + 95,
            'close': np.random.randn(n).cumsum() + 100,
            'volume': np.random.randint(100, 1000, n)
        })
        self.df['high'] = self.df[['open', 'close', 'high']].max(axis=1)
        self.df['low'] = self.df[['open', 'close', 'low']].min(axis=1)

    def test_detect_regime(self):
        # Test len < 65
        short_df = self.df.iloc[-60:].copy()
        self.assertEqual(detect_regime(short_df), "transitional")

        # Test valid df
        # It's hard to precisely mock the conditions without injecting, so we just run it
        # to ensure it returns a valid string (trending, ranging, or transitional)
        regime = detect_regime(self.df)
        self.assertIn(regime, ["trending", "ranging", "transitional"])

        # Test empty df
        empty_df = pd.DataFrame(columns=['high', 'low', 'close'])
        self.assertEqual(detect_regime(empty_df), "transitional")

    def test_trend_signal(self):
        # Test len < 60
        short_df = self.df.iloc[-50:].copy()
        self.assertEqual(trend_signal(short_df), "hold")

        # Test valid df
        signal = trend_signal(self.df)
        self.assertIn(signal, ["buy", "sell", "hold"])

        # Test empty df
        empty_df = pd.DataFrame(columns=['close'])
        self.assertEqual(trend_signal(empty_df), "hold")

    def test_mean_reversion_signal(self):
        # Test not in eligible
        self.assertEqual(mean_reversion_signal("INVALID_SYM", self.df), "hold")

        # Test len < 25
        short_df = self.df.iloc[-20:].copy()
        self.assertEqual(mean_reversion_signal("SPY", short_df), "hold")

        # Test valid df
        signal = mean_reversion_signal("SPY", self.df)
        self.assertIn(signal, ["buy", "sell", "hold"])

        # Test empty df
        empty_df = pd.DataFrame(columns=['close'])
        self.assertEqual(mean_reversion_signal("SPY", empty_df), "hold")

    def test_get_middle_band(self):
        # Test valid df
        mid_band = get_middle_band(self.df)
        self.assertIsInstance(mid_band, float)

        # Test empty df
        empty_df = pd.DataFrame(columns=['close'])
        self.assertIsNone(get_middle_band(empty_df))

    def test_decide(self):
        # Test empty
        empty_df = pd.DataFrame(columns=['high', 'low', 'close'])
        decision = decide("SPY", empty_df)
        self.assertEqual(decision["action"], "hold")
        self.assertEqual(decision["regime"], "unknown")

        # Test valid df
        decision = decide("SPY", self.df)
        self.assertIn("action", decision)
        self.assertIn("regime", decision)
        self.assertIn("sleeve", decision)

if __name__ == '__main__':
    unittest.main()
