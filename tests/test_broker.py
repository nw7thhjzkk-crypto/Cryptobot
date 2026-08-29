import pytest
from unittest.mock import patch, MagicMock

import bot.broker as broker
from alpaca.trading.enums import OrderSide

@patch('bot.broker.data_client')
def test_get_latest_price_success(mock_data_client):
    # Mocking the response for get_stock_latest_trade
    mock_response = MagicMock()
    mock_response['AAPL'].price = 150.5
    mock_data_client.get_stock_latest_trade.return_value = mock_response

    result = broker.get_latest_price('AAPL')
    assert result['success'] is True
    assert result['price'] == 150.5
    mock_data_client.get_stock_latest_trade.assert_called_once()

@patch('bot.broker.data_client')
def test_get_latest_price_error(mock_data_client):
    mock_data_client.get_stock_latest_trade.side_effect = Exception("API error")

    result = broker.get_latest_price('AAPL')
    assert result['success'] is False
    assert result['reason'] == "API error"
    mock_data_client.get_stock_latest_trade.assert_called_once()

@patch('bot.broker.data_client')
def test_get_price_history_success(mock_data_client):
    mock_response = MagicMock()
    mock_response.df = "mock_dataframe"
    mock_data_client.get_stock_bars.return_value = mock_response

    result = broker.get_price_history('AAPL', lookback_days=10)
    assert result['success'] is True
    assert result['data'] == "mock_dataframe"
    mock_data_client.get_stock_bars.assert_called_once()

@patch('bot.broker.data_client')
def test_get_price_history_error(mock_data_client):
    mock_data_client.get_stock_bars.side_effect = Exception("Bars error")

    result = broker.get_price_history('AAPL', lookback_days=10)
    assert result['success'] is False
    assert result['reason'] == "Bars error"
    mock_data_client.get_stock_bars.assert_called_once()

@patch('bot.broker.trading_client')
def test_submit_market_order_success(mock_trading_client):
    mock_order = MagicMock()
    mock_order.id = "order_123"
    mock_order.status.value = "accepted"
    mock_trading_client.submit_order.return_value = mock_order

    result = broker.submit_market_order('AAPL', 10, 'buy')
    assert result['success'] is True
    assert result['order_id'] == "order_123"
    assert result['status'] == "accepted"

    mock_trading_client.submit_order.assert_called_once()
    args, kwargs = mock_trading_client.submit_order.call_args
    assert args[0].symbol == 'AAPL'
    assert args[0].qty == 10
    assert args[0].side == OrderSide.BUY

@patch('bot.broker.trading_client')
def test_submit_market_order_error(mock_trading_client):
    mock_trading_client.submit_order.side_effect = Exception("Order error")

    result = broker.submit_market_order('AAPL', 10, 'sell')
    assert result['success'] is False
    assert result['reason'] == "Order error"

    mock_trading_client.submit_order.assert_called_once()
    args, kwargs = mock_trading_client.submit_order.call_args
    assert args[0].side == OrderSide.SELL

@patch('bot.broker.trading_client')
def test_get_account_success(mock_trading_client):
    mock_acct = MagicMock()
    mock_acct.equity = "100000.50"
    mock_acct.cash = "50000.25"
    mock_acct.buying_power = "200000.00"
    mock_trading_client.get_account.return_value = mock_acct

    result = broker.get_account()
    assert result['success'] is True
    assert result['equity'] == 100000.50
    assert result['cash'] == 50000.25
    assert result['buying_power'] == 200000.00
    mock_trading_client.get_account.assert_called_once()

@patch('bot.broker.trading_client')
def test_get_account_error(mock_trading_client):
    mock_trading_client.get_account.side_effect = Exception("Account error")

    result = broker.get_account()
    assert result['success'] is False
    assert result['reason'] == "Account error"
    mock_trading_client.get_account.assert_called_once()

@patch('bot.broker.trading_client')
def test_get_positions_success(mock_trading_client):
    mock_pos1 = MagicMock()
    mock_pos1.symbol = 'AAPL'
    mock_pos1.qty = "10.0"
    mock_pos1.avg_entry_price = "140.5"
    mock_pos1.current_price = "150.5"
    mock_pos1.unrealized_pl = "100.0"

    mock_pos2 = MagicMock()
    mock_pos2.symbol = 'MSFT'
    mock_pos2.qty = "5.0"
    mock_pos2.avg_entry_price = "250.0"
    mock_pos2.current_price = "260.0"
    mock_pos2.unrealized_pl = "50.0"

    mock_trading_client.get_all_positions.return_value = [mock_pos1, mock_pos2]

    result = broker.get_positions()
    assert result['success'] is True
    assert len(result['positions']) == 2

    assert result['positions'][0]['symbol'] == 'AAPL'
    assert result['positions'][0]['qty'] == 10.0
    assert result['positions'][0]['avg_entry_price'] == 140.5
    assert result['positions'][0]['current_price'] == 150.5
    assert result['positions'][0]['unrealized_pl'] == 100.0

    assert result['positions'][1]['symbol'] == 'MSFT'
    assert result['positions'][1]['qty'] == 5.0

    mock_trading_client.get_all_positions.assert_called_once()

@patch('bot.broker.trading_client')
def test_get_positions_error(mock_trading_client):
    mock_trading_client.get_all_positions.side_effect = Exception("Positions error")

    result = broker.get_positions()
    assert result['success'] is False
    assert result['reason'] == "Positions error"
    mock_trading_client.get_all_positions.assert_called_once()
