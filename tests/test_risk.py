import unittest
from bot.risk import check_drawdown_breaker

class TestCheckDrawdownBreaker(unittest.TestCase):
    def test_empty_history(self):
        """Test with empty equity history."""
        self.assertFalse(check_drawdown_breaker([], 0.1))

    def test_no_drawdown(self):
        """Test with constantly rising equity curve."""
        history = [100.0, 105.0, 110.0]
        self.assertFalse(check_drawdown_breaker(history, 0.1))

    def test_drawdown_below_max(self):
        """Test with drawdown that does not exceed max_drawdown_pct."""
        # Peak is 100, current is 95, drawdown is 5%
        history = [90.0, 100.0, 95.0]
        self.assertFalse(check_drawdown_breaker(history, 0.1))

    def test_drawdown_exceeds_max(self):
        """Test with drawdown that exceeds max_drawdown_pct."""
        # Peak is 100, current is 85, drawdown is 15%
        history = [90.0, 100.0, 85.0]
        self.assertTrue(check_drawdown_breaker(history, 0.1))

    def test_drawdown_exactly_max(self):
        """Test with drawdown exactly equal to max_drawdown_pct."""
        # Peak is 100, current is 90, drawdown is 10%
        history = [100.0, 90.0]
        # Should return False because function is `>` not `>=`
        self.assertFalse(check_drawdown_breaker(history, 0.1))

        # Test just over the max
        history = [100.0, 89.9]
        self.assertTrue(check_drawdown_breaker(history, 0.1))

    def test_window_days(self):
        """Test that drawdown is only calculated within the trailing window."""
        # Peak of 100 was outside the window (if window is 2)
        # Inside window: peak is 90, current is 85, drawdown is 5/90 = 5.5%
        history = [100.0, 50.0, 90.0, 85.0]
        self.assertFalse(check_drawdown_breaker(history, 0.1, window_days=2))

        # Peak of 100 is inside window of 4
        # Peak is 100, current is 85, drawdown is 15%
        self.assertTrue(check_drawdown_breaker(history, 0.1, window_days=4))

    def test_zero_peak(self):
        """Test edge case where peak equity is zero."""
        history = [-10.0, 0.0, 0.0]
        self.assertFalse(check_drawdown_breaker(history, 0.1))

    def test_negative_equity(self):
        """Test edge case with negative equity."""
        # Peak is -50, current is -100
        # Formula: (-50 - (-100)) / -50 = 50 / -50 = -1 (not > 0.1)
        # Actually logic is `if peak > 0 else 0`, so drawdown is 0
        history = [-150.0, -50.0, -100.0]
        self.assertFalse(check_drawdown_breaker(history, 0.1))

    def test_history_smaller_than_window(self):
        """Test when equity history has fewer elements than window_days."""
        history = [100.0, 80.0] # Drawdown is 20%
        self.assertTrue(check_drawdown_breaker(history, 0.1, window_days=30))


if __name__ == '__main__':
    unittest.main()
