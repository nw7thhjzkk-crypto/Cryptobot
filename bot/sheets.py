import json
import logging
import gspread
from google.oauth2.service_account import Credentials
from bot.config import GOOGLE_SERVICE_ACCOUNT_JSON, GOOGLE_SHEET_ID

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_client():
    raw_json = GOOGLE_SERVICE_ACCOUNT_JSON
    if raw_json is None:
        logger.error("GOOGLE_SERVICE_ACCOUNT_JSON is None")
        return None

    raw_json = str(raw_json).strip()
    raw_json = raw_json.replace('“', '"').replace('”', '"').replace("‘", "'").replace("’", "'")

    try:
        creds_dict = json.loads(raw_json)
    except Exception as e:
        safe_str = raw_json
        if len(safe_str) > 40:
            safe_str = f"{safe_str[:20]}...{safe_str[-20:]}"
        raise ValueError(f"Error parsing GOOGLE_SERVICE_ACCOUNT_JSON: {e}. String preview: {safe_str}") from e

    try:
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        return gspread.authorize(creds)
    except Exception as e:
        logger.error(f"Error authenticating with Google Sheets: {e}")
        return None

def get_sheet(client):
    try:
        return client.open_by_key(GOOGLE_SHEET_ID)
    except Exception as e:
        logger.error(f"Error opening Google Sheet {GOOGLE_SHEET_ID}: {e}")
        return None

def init_tabs():
    client = get_client()
    if not client: return
    sheet = get_sheet(client)
    if not sheet: return

    tabs_needed = {
        "AgentSignals": ["timestamp", "symbol", "agent", "signal", "score", "confidence", "reason", "regime", "consensus", "risk_decision", "final_decision"],
        "BotRuns": ["run_id", "started_at", "finished_at", "status", "symbols_processed", "orders_submitted", "errors"],
        "Trades": ["timestamp", "symbol", "side", "qty", "price", "order_id", "status", "regime", "sleeve", "notes"],
        "Positions": ["timestamp", "symbol", "qty", "avg_entry_price", "current_price", "unrealized_pl"],
        "Equity": ["timestamp", "equity", "cash", "buying_power"],
        "Watchlist": ["symbol", "regime", "last_updated"]
    }

    existing_tabs = [ws.title for ws in sheet.worksheets()]

    for title, headers in tabs_needed.items():
        if title not in existing_tabs:
            ws = sheet.add_worksheet(title=title, rows=2000, cols=len(headers))
            ws.append_row(headers)
        else:
            ws = sheet.worksheet(title)
            if not ws.row_values(1):
                ws.append_row(headers)

def load_recent_equity(max_rows: int = 100) -> list:
    """
    Load the most recent equity values from the Equity tab.
    Used so drawdown breaker works across multiple GitHub Actions runs.
    Returns a list of floats (equity values), oldest → newest.
    """
    try:
        client = get_client()
        if not client:
            return []
        sheet = get_sheet(client)
        if not sheet:
            return []

        ws = sheet.worksheet("Equity")
        records = ws.get_all_records()
        if not records:
            return []

        # Take the last max_rows
        recent = records[-max_rows:]
        equities = []
        for r in recent:
            try:
                eq = float(r.get("equity", 0))
                if eq > 0:
                    equities.append(eq)
            except (TypeError, ValueError):
                continue
        return equities
    except Exception as e:
        logger.warning(f"Could not load recent equity history: {e}")
        return []

def log_trade(row):
    try:
        client = get_client()
        if not client: return
        sheet = get_sheet(client)
        if not sheet: return

        ws = sheet.worksheet("Trades")
        ws.append_row(row)
    except Exception as e:
        logger.error(f"Error logging trade to sheets: {e}")

def update_positions(rows):
    try:
        client = get_client()
        if not client: return
        sheet = get_sheet(client)
        if not sheet: return

        ws = sheet.worksheet("Positions")
        ws.clear()

        headers = ["timestamp", "symbol", "qty", "avg_entry_price", "current_price", "unrealized_pl"]
        data = [headers] + rows
        ws.update(values=data, range_name="A1")
    except Exception as e:
        logger.error(f"Error updating positions in sheets: {e}")

def log_equity(row):
    try:
        client = get_client()
        if not client: return
        sheet = get_sheet(client)
        if not sheet: return

        ws = sheet.worksheet("Equity")
        ws.append_row(row)
    except Exception as e:
        logger.error(f"Error logging equity to sheets: {e}")

def update_watchlist(rows):
    try:
        client = get_client()
        if not client: return
        sheet = get_sheet(client)
        if not sheet: return

        ws = sheet.worksheet("Watchlist")
        ws.clear()

        headers = ["symbol", "regime", "last_updated"]
        data = [headers] + rows
        ws.update(values=data, range_name="A1")
    except Exception as e:
        logger.error(f"Error updating watchlist in sheets: {e}")

def log_agent_signal(row_data):
    try:
        client = get_client()
        if not client: return
        sheet = get_sheet(client)
        if not sheet: return

        ws = sheet.worksheet("AgentSignals")
        ws.append_row(row_data)
    except Exception as e:
        logger.error(f"Error logging agent signal to sheets: {e}")

def log_bot_run(row_data):
    try:
        client = get_client()
        if not client: return
        sheet = get_sheet(client)
        if not sheet: return

        ws = sheet.worksheet("BotRuns")
        ws.append_row(row_data)
    except Exception as e:
        logger.error(f"Error logging bot run to sheets: {e}")
