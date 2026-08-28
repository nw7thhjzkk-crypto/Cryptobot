import unittest
from bot.risk import calculate_stop_price

class TestRisk(unittest.TestCase):
    def test_calculate_stop_price_buy_casing(self):
        entry_price = 100.0
        atr = 2.0
        stop_multiple = 2.0

        # buy side -> 100.0 - (2.0 * 2.0) = 96.0
        expected = 96.0

        self.assertEqual(calculate_stop_price(entry_price, atr, 'buy', stop_multiple), expected)
        self.assertEqual(calculate_stop_price(entry_price, atr, 'BUY', stop_multiple), expected)
        self.assertEqual(calculate_stop_price(entry_price, atr, 'Buy', stop_multiple), expected)
        self.assertEqual(calculate_stop_price(entry_price, atr, 'bUy', stop_multiple), expected)

    def test_calculate_stop_price_sell_casing(self):
        entry_price = 100.0
        atr = 2.0
        stop_multiple = 2.0

        # sell side -> 100.0 + (2.0 * 2.0) = 104.0
        expected = 104.0

        self.assertEqual(calculate_stop_price(entry_price, atr, 'sell', stop_multiple), expected)
        self.assertEqual(calculate_stop_price(entry_price, atr, 'SELL', stop_multiple), expected)
        self.assertEqual(calculate_stop_price(entry_price, atr, 'Sell', stop_multiple), expected)
        self.assertEqual(calculate_stop_price(entry_price, atr, 'sElL', stop_multiple), expected)

if __name__ == '__main__':
    unittest.main()
