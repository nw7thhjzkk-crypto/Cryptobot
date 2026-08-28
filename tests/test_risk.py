import unittest
from bot.risk import check_drawdown_breaker

class TestRisk(unittest.TestCase):

    def test_check_drawdown_breaker_empty_history(self):
        """Test with empty history"""
        self.assertFalse(check_drawdown_breaker([], 0.1))

    def test_check_drawdown_breaker_no_drawdown(self):
        """Test when equity is monotonically increasing (no drawdown)"""
        self.assertFalse(check_drawdown_breaker([100, 110, 120], 0.1))

    def test_check_drawdown_breaker_drawdown_below_max(self):
        """Test with a drawdown that is below the maximum allowed percentage"""
        # Peak is 100, current is 95, drawdown is 5% which is < 10%
        self.assertFalse(check_drawdown_breaker([100, 95], 0.10))

    def test_check_drawdown_breaker_drawdown_above_max(self):
        """Test with a drawdown that exceeds the maximum allowed percentage"""
        # Peak is 100, current is 80, drawdown is 20% which is > 10%
        self.assertTrue(check_drawdown_breaker([100, 80], 0.10))

    def test_check_drawdown_breaker_window_days(self):
        """Test that the function only considers the recent window_days"""
        # History: peak 200, drops to 100 (50% drop), then stays around 100
        # If window_days is 3, it should only look at [100, 101, 100]
        # In this window, peak is 101, current is 100, drawdown is ~1% < 10%
        history = [200, 100, 100, 101, 100]
        self.assertFalse(check_drawdown_breaker(history, 0.10, window_days=3))

        # If window_days is 5, it looks at the whole history
        # Peak 200, current 100, drawdown 50% > 10%
        self.assertTrue(check_drawdown_breaker(history, 0.10, window_days=5))

if __name__ == '__main__':
    unittest.main()
