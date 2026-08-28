import unittest
from unittest.mock import patch, MagicMock

import bot.broker as broker

class TestBroker(unittest.TestCase):
    @patch('bot.broker.data_client')
    def test_get_latest_price_error(self, mock_data_client):
        mock_data_client.get_stock_latest_trade.side_effect = Exception("API error")
        result = broker.get_latest_price("AAPL")
        self.assertFalse(result["success"])
        self.assertEqual(result["reason"], "API error")

    @patch('bot.broker.data_client')
    def test_get_price_history_error(self, mock_data_client):
        mock_data_client.get_stock_bars.side_effect = Exception("API error")
        result = broker.get_price_history("AAPL")
        self.assertFalse(result["success"])
        self.assertEqual(result["reason"], "API error")

if __name__ == '__main__':
    unittest.main()
