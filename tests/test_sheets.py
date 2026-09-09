import unittest
from unittest.mock import patch, MagicMock
import json

from bot.sheets import (
    get_client,
    get_sheet,
    init_tabs,
    log_trade,
    update_positions,
    log_equity,
    update_watchlist
)

class TestSheets(unittest.TestCase):

    @patch('bot.sheets.GOOGLE_SERVICE_ACCOUNT_JSON', None)
    @patch('bot.sheets.logger')
    def test_get_client_none_json(self, mock_logger):
        client = get_client()
        self.assertIsNone(client)
        mock_logger.error.assert_called_with("GOOGLE_SERVICE_ACCOUNT_JSON is None")

    @patch('bot.sheets.GOOGLE_SERVICE_ACCOUNT_JSON', '{"type": "service_account"}')
    @patch('bot.sheets.Credentials.from_service_account_info')
    @patch('bot.sheets.gspread.authorize')
    def test_get_client_success(self, mock_authorize, mock_creds):
        mock_creds.return_value = MagicMock()
        mock_authorize.return_value = MagicMock()

        client = get_client()
        self.assertIsNotNone(client)
        mock_creds.assert_called_once()
        mock_authorize.assert_called_once()

    @patch('bot.sheets.GOOGLE_SERVICE_ACCOUNT_JSON', 'invalid json')
    def test_get_client_invalid_json(self):
        with self.assertRaises(ValueError) as context:
            get_client()
        self.assertIn("Error parsing GOOGLE_SERVICE_ACCOUNT_JSON", str(context.exception))

    @patch('bot.sheets.GOOGLE_SERVICE_ACCOUNT_JSON', '{"type": "service_account"}')
    @patch('bot.sheets.Credentials.from_service_account_info')
    @patch('bot.sheets.logger')
    def test_get_client_auth_exception(self, mock_logger, mock_creds):
        mock_creds.side_effect = Exception("Auth Error")

        client = get_client()
        self.assertIsNone(client)
        mock_logger.error.assert_called_with("Error authenticating with Google Sheets: Auth Error")

    @patch('bot.sheets.GOOGLE_SHEET_ID', 'test_sheet_id')
    def test_get_sheet_success(self):
        mock_client = MagicMock()
        mock_client.open_by_key.return_value = MagicMock()

        sheet = get_sheet(mock_client)
        self.assertIsNotNone(sheet)
        mock_client.open_by_key.assert_called_with('test_sheet_id')

    @patch('bot.sheets.GOOGLE_SHEET_ID', 'test_sheet_id')
    @patch('bot.sheets.logger')
    def test_get_sheet_exception(self, mock_logger):
        mock_client = MagicMock()
        mock_client.open_by_key.side_effect = Exception("Open Error")

        sheet = get_sheet(mock_client)
        self.assertIsNone(sheet)
        mock_logger.error.assert_called_with("Error opening Google Sheet test_sheet_id: Open Error")

    @patch('bot.sheets.get_client')
    @patch('bot.sheets.get_sheet')
    def test_init_tabs_missing_tabs(self, mock_get_sheet, mock_get_client):
        mock_client = MagicMock()
        mock_sheet = MagicMock()

        mock_get_client.return_value = mock_client
        mock_get_sheet.return_value = mock_sheet

        mock_ws = MagicMock()
        mock_ws.title = "OldTab"
        mock_sheet.worksheets.return_value = [mock_ws]

        mock_new_ws = MagicMock()
        mock_sheet.add_worksheet.return_value = mock_new_ws

        init_tabs()

        self.assertEqual(mock_sheet.add_worksheet.call_count, 4)
        self.assertEqual(mock_new_ws.append_row.call_count, 4)

    @patch('bot.sheets.get_client')
    @patch('bot.sheets.get_sheet')
    def test_init_tabs_existing_tabs_missing_headers(self, mock_get_sheet, mock_get_client):
        mock_client = MagicMock()
        mock_sheet = MagicMock()

        mock_get_client.return_value = mock_client
        mock_get_sheet.return_value = mock_sheet

        mock_ws_trades = MagicMock()
        mock_ws_trades.title = "Trades"
        mock_ws_trades.row_values.return_value = []

        mock_sheet.worksheets.return_value = [mock_ws_trades]
        mock_sheet.worksheet.return_value = mock_ws_trades

        init_tabs()

        mock_ws_trades.append_row.assert_called()

    @patch('bot.sheets.get_client')
    @patch('bot.sheets.get_sheet')
    def test_log_trade_success(self, mock_get_sheet, mock_get_client):
        mock_client = MagicMock()
        mock_sheet = MagicMock()
        mock_ws = MagicMock()

        mock_get_client.return_value = mock_client
        mock_get_sheet.return_value = mock_sheet
        mock_sheet.worksheet.return_value = mock_ws

        row = ["2023-01-01T00:00:00Z", "AAPL", "buy", 1, 150.0, "order123", "filled", "bull", "core", "test"]
        log_trade(row)

        mock_sheet.worksheet.assert_called_with("Trades")
        mock_ws.append_row.assert_called_with(row)

    @patch('bot.sheets.get_client')
    @patch('bot.sheets.get_sheet')
    @patch('bot.sheets.logger')
    def test_log_trade_exception(self, mock_logger, mock_get_sheet, mock_get_client):
        mock_get_client.side_effect = Exception("Log Error")

        log_trade([])
        mock_logger.error.assert_called_with("Error logging trade to sheets: Log Error")

    @patch('bot.sheets.get_client')
    @patch('bot.sheets.get_sheet')
    def test_update_positions_success(self, mock_get_sheet, mock_get_client):
        mock_client = MagicMock()
        mock_sheet = MagicMock()
        mock_ws = MagicMock()

        mock_get_client.return_value = mock_client
        mock_get_sheet.return_value = mock_sheet
        mock_sheet.worksheet.return_value = mock_ws

        rows = [["2023-01-01T00:00:00Z", "AAPL", 10, 140.0, 150.0, 100.0]]
        update_positions(rows)

        mock_sheet.worksheet.assert_called_with("Positions")
        mock_ws.clear.assert_called_once()
        expected_data = [["timestamp", "symbol", "qty", "avg_entry_price", "current_price", "unrealized_pl"]] + rows
        mock_ws.update.assert_called_with(values=expected_data, range_name="A1")

    @patch('bot.sheets.get_client')
    @patch('bot.sheets.get_sheet')
    @patch('bot.sheets.logger')
    def test_update_positions_exception(self, mock_logger, mock_get_sheet, mock_get_client):
        mock_get_client.side_effect = Exception("Update Error")

        update_positions([])
        mock_logger.error.assert_called_with("Error updating positions in sheets: Update Error")

    @patch('bot.sheets.get_client')
    @patch('bot.sheets.get_sheet')
    def test_log_equity_success(self, mock_get_sheet, mock_get_client):
        mock_client = MagicMock()
        mock_sheet = MagicMock()
        mock_ws = MagicMock()

        mock_get_client.return_value = mock_client
        mock_get_sheet.return_value = mock_sheet
        mock_sheet.worksheet.return_value = mock_ws

        row = ["2023-01-01T00:00:00Z", 10000.0, 5000.0, 10000.0]
        log_equity(row)

        mock_sheet.worksheet.assert_called_with("Equity")
        mock_ws.append_row.assert_called_with(row)

    @patch('bot.sheets.get_client')
    @patch('bot.sheets.get_sheet')
    @patch('bot.sheets.logger')
    def test_log_equity_exception(self, mock_logger, mock_get_sheet, mock_get_client):
        mock_get_client.side_effect = Exception("Equity Error")

        log_equity([])
        mock_logger.error.assert_called_with("Error logging equity to sheets: Equity Error")

    @patch('bot.sheets.get_client')
    @patch('bot.sheets.get_sheet')
    def test_update_watchlist_success(self, mock_get_sheet, mock_get_client):
        mock_client = MagicMock()
        mock_sheet = MagicMock()
        mock_ws = MagicMock()

        mock_get_client.return_value = mock_client
        mock_get_sheet.return_value = mock_sheet
        mock_sheet.worksheet.return_value = mock_ws

        rows = [["AAPL", "bull", "2023-01-01T00:00:00Z"]]
        update_watchlist(rows)

        mock_sheet.worksheet.assert_called_with("Watchlist")
        mock_ws.clear.assert_called_once()
        expected_data = [["symbol", "regime", "last_updated"]] + rows
        mock_ws.update.assert_called_with(values=expected_data, range_name="A1")

    @patch('bot.sheets.get_client')
    @patch('bot.sheets.get_sheet')
    @patch('bot.sheets.logger')
    def test_update_watchlist_exception(self, mock_logger, mock_get_sheet, mock_get_client):
        mock_get_client.side_effect = Exception("Watchlist Error")

        update_watchlist([])
        mock_logger.error.assert_called_with("Error updating watchlist in sheets: Watchlist Error")

if __name__ == '__main__':
    unittest.main()
