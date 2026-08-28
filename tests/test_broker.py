import unittest
from unittest.mock import patch, MagicMock
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import MarketOrderRequest

from bot.broker import submit_market_order


class TestBroker(unittest.TestCase):

    @patch('bot.broker.trading_client')
    def test_submit_market_order_buy_success(self, mock_trading_client):
        # Setup mock return value
        mock_order = MagicMock()
        mock_order.id = "test-order-id-123"
        mock_order.status.value = "accepted"
        mock_trading_client.submit_order.return_value = mock_order

        # Call the function
        result = submit_market_order(symbol="AAPL", qty=10, side="buy")

        # Verify behavior
        expected_req = MarketOrderRequest(
            symbol="AAPL",
            qty=10,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY
        )
        # We need to manually verify the arguments because MarketOrderRequest doesn't have a simple __eq__
        mock_trading_client.submit_order.assert_called_once()
        actual_req = mock_trading_client.submit_order.call_args[0][0]
        self.assertEqual(actual_req.symbol, "AAPL")
        self.assertEqual(actual_req.qty, 10)
        self.assertEqual(actual_req.side, OrderSide.BUY)
        self.assertEqual(actual_req.time_in_force, TimeInForce.DAY)

        # Verify result
        self.assertTrue(result["success"])
        self.assertEqual(result["order_id"], "test-order-id-123")
        self.assertEqual(result["status"], "accepted")

    @patch('bot.broker.trading_client')
    def test_submit_market_order_sell_success(self, mock_trading_client):
        # Setup mock return value
        mock_order = MagicMock()
        mock_order.id = "test-order-id-456"
        mock_order.status.value = "filled"
        mock_trading_client.submit_order.return_value = mock_order

        # Call the function
        result = submit_market_order(symbol="TSLA", qty=5, side="sell")

        # Verify behavior
        mock_trading_client.submit_order.assert_called_once()
        actual_req = mock_trading_client.submit_order.call_args[0][0]
        self.assertEqual(actual_req.symbol, "TSLA")
        self.assertEqual(actual_req.qty, 5)
        self.assertEqual(actual_req.side, OrderSide.SELL)
        self.assertEqual(actual_req.time_in_force, TimeInForce.DAY)

        # Verify result
        self.assertTrue(result["success"])
        self.assertEqual(result["order_id"], "test-order-id-456")
        self.assertEqual(result["status"], "filled")

    @patch('bot.broker.trading_client')
    def test_submit_market_order_exception(self, mock_trading_client):
        # Setup mock to raise an exception
        mock_trading_client.submit_order.side_effect = Exception("API rate limit exceeded")

        # Call the function
        result = submit_market_order(symbol="MSFT", qty=1, side="buy")

        # Verify behavior
        mock_trading_client.submit_order.assert_called_once()

        # Verify result
        self.assertFalse(result["success"])
        self.assertEqual(result["reason"], "API rate limit exceeded")

if __name__ == '__main__':
    unittest.main()
