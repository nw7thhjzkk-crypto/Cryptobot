import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Mock environment variables before importing anything from bot
os.environ['ALPACA_API_KEY'] = 'test_api_key'
os.environ['ALPACA_SECRET_KEY'] = 'test_secret_key'
os.environ['GOOGLE_SERVICE_ACCOUNT_JSON'] = 'test_json'
os.environ['GOOGLE_SHEET_ID'] = 'test_sheet_id'

# Add parent directory to path to import bot
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from bot.broker import get_latest_price

class TestBroker(unittest.TestCase):
    @patch('bot.broker.data_client.get_stock_latest_trade')
    def test_get_latest_price_success(self, mock_get_stock_latest_trade):
        mock_symbol_data = MagicMock()
        mock_symbol_data.price = 150.0
        mock_get_stock_latest_trade.return_value = {"AAPL": mock_symbol_data}

        result = get_latest_price("AAPL")

        self.assertTrue(result["success"])
        self.assertEqual(result["price"], 150.0)

    @patch('bot.broker.data_client.get_stock_latest_trade')
    def test_get_latest_price_error(self, mock_get_stock_latest_trade):
        mock_get_stock_latest_trade.side_effect = Exception("API connection error")

        result = get_latest_price("AAPL")

        self.assertFalse(result["success"])
        self.assertEqual(result["reason"], "API connection error")

if __name__ == '__main__':
    unittest.main()
