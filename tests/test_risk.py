import unittest
from bot.risk import calculate_position_size

class TestRisk(unittest.TestCase):
    def test_normal_atr(self):
        # account_equity=10000, atr=2.5, risk_per_trade_pct=0.01, stop_multiple=2.0
        # risk_amount = 10000 * 0.01 = 100
        # risk_per_share = 2.5 * 2.0 = 5.0
        # shares = floor(100 / 5.0) = 20
        shares = calculate_position_size(10000, 2.5, 0.01, 2.0)
        self.assertEqual(shares, 20)

    def test_zero_atr(self):
        shares = calculate_position_size(10000, 0, 0.01, 2.0)
        self.assertEqual(shares, 0)

    def test_negative_atr(self):
        shares = calculate_position_size(10000, -1.0, 0.01, 2.0)
        self.assertEqual(shares, 0)

if __name__ == '__main__':
    unittest.main()
