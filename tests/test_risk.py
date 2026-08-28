import unittest
from bot.risk import calculate_stop_price

class TestCalculateStopPrice(unittest.TestCase):

    def test_buy_side_default_multiple(self):
        # Entry: 100, ATR: 2, default multiple: 2.0 -> 100 - (2 * 2.0) = 96.0
        stop_price = calculate_stop_price(entry_price=100.0, atr=2.0, side='buy')
        self.assertEqual(stop_price, 96.0)

    def test_buy_side_custom_multiple(self):
        # Entry: 100, ATR: 2, custom multiple: 3.0 -> 100 - (2 * 3.0) = 94.0
        stop_price = calculate_stop_price(entry_price=100.0, atr=2.0, side='buy', stop_multiple=3.0)
        self.assertEqual(stop_price, 94.0)

    def test_buy_side_case_insensitivity(self):
        # Entry: 50, ATR: 1.5, default multiple: 2.0 -> 50 - (1.5 * 2.0) = 47.0
        stop_price = calculate_stop_price(entry_price=50.0, atr=1.5, side='BUY')
        self.assertEqual(stop_price, 47.0)

        stop_price_mixed = calculate_stop_price(entry_price=50.0, atr=1.5, side='Buy')
        self.assertEqual(stop_price_mixed, 47.0)

    def test_sell_side_default_multiple(self):
        # Entry: 100, ATR: 2, default multiple: 2.0 -> 100 + (2 * 2.0) = 104.0
        # Anything other than 'buy' (case-insensitive) is treated as sell
        stop_price = calculate_stop_price(entry_price=100.0, atr=2.0, side='sell')
        self.assertEqual(stop_price, 104.0)

    def test_sell_side_custom_multiple(self):
        # Entry: 100, ATR: 2, custom multiple: 1.5 -> 100 + (2 * 1.5) = 103.0
        stop_price = calculate_stop_price(entry_price=100.0, atr=2.0, side='sell', stop_multiple=1.5)
        self.assertEqual(stop_price, 103.0)

    def test_sell_side_case_insensitivity(self):
        # Entry: 50, ATR: 1.5, default multiple: 2.0 -> 50 + (1.5 * 2.0) = 53.0
        stop_price = calculate_stop_price(entry_price=50.0, atr=1.5, side='SELL')
        self.assertEqual(stop_price, 53.0)

        stop_price_short = calculate_stop_price(entry_price=50.0, atr=1.5, side='short')
        self.assertEqual(stop_price_short, 53.0)

    def test_zero_atr(self):
        # ATR = 0, stop price should equal entry price for both buy and sell
        stop_price_buy = calculate_stop_price(entry_price=150.0, atr=0.0, side='buy')
        self.assertEqual(stop_price_buy, 150.0)

        stop_price_sell = calculate_stop_price(entry_price=150.0, atr=0.0, side='sell')
        self.assertEqual(stop_price_sell, 150.0)

if __name__ == '__main__':
    unittest.main()
