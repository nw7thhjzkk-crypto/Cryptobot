import pytest
from unittest.mock import patch
from bot.broker import get_account

@patch('bot.broker.trading_client')
def test_get_account_exception(mock_trading_client):
    # Setup mock to raise an exception when get_account is called
    error_message = "mocked error"
    mock_trading_client.get_account.side_effect = Exception(error_message)

    # Call the function
    result = get_account()

    # Assert the expected dictionary is returned
    assert result == {"success": False, "reason": error_message}
