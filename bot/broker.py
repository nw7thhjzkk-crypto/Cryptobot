import logging
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime, timedelta

from bot.config import ALPACA_API_KEY, ALPACA_SECRET_KEY, PAPER_MODE

logger = logging.getLogger(__name__)

api_key_preview = str(ALPACA_API_KEY)[:4] if ALPACA_API_KEY else "None"
base_url = "https://paper-api.alpaca.markets" if PAPER_MODE else "https://api.alpaca.markets"
logger.info(f"Initializing Alpaca TradingClient. PAPER_MODE={PAPER_MODE}, Base URL={base_url}, API_KEY startswith={api_key_preview}")

trading_client = TradingClient(ALPACA_API_KEY, ALPACA_SECRET_KEY, paper=PAPER_MODE)
data_client = StockHistoricalDataClient(ALPACA_API_KEY, ALPACA_SECRET_KEY)

def get_latest_price(symbol):
    try:
        # Get the latest trade
        from alpaca.data.requests import StockLatestTradeRequest
        req = StockLatestTradeRequest(symbol_or_symbols=[symbol])
        res = data_client.get_stock_latest_trade(req)
        return {"success": True, "price": res[symbol].price}
    except Exception as e:
        logger.error(f"Error fetching latest price for {symbol}: {e}")
        return {"success": False, "reason": str(e)}

def get_price_history(symbol, lookback_days=100):
    try:
        end = datetime.now()
        start = end - timedelta(days=lookback_days)
        req = StockBarsRequest(
            symbol_or_symbols=[symbol],
            timeframe=TimeFrame.Day,
            start=start,
            end=end
        )
        bars = data_client.get_stock_bars(req)
        return {"success": True, "data": bars.df}
    except Exception as e:
        logger.error(f"Error fetching price history for {symbol}: {e}")
        return {"success": False, "reason": str(e)}

def submit_market_order(symbol, qty, side):
    try:
        order_side = OrderSide.BUY if side.lower() == 'buy' else OrderSide.SELL
        req = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=order_side,
            time_in_force=TimeInForce.DAY
        )
        order = trading_client.submit_order(req)
        return {"success": True, "order_id": str(order.id), "status": order.status.value}
    except Exception as e:
        logger.error(f"Error submitting market order for {symbol}: {e}")
        return {"success": False, "reason": str(e)}

def get_account():
    try:
        # Diagnostic logging for authentication failures
        actual_url = trading_client._base_url if hasattr(trading_client, '_base_url') else "Unknown"
        logger.info(f"Using Alpaca base URL: {actual_url}")

        key_str = str(ALPACA_API_KEY) if ALPACA_API_KEY else ""
        key_preview = key_str[:4] if len(key_str) >= 4 else "None"
        logger.info(f"API Key starts with: {key_preview}, length: {len(key_str)}")

        headers = trading_client._get_auth_headers() if hasattr(trading_client, '_get_auth_headers') else {}
        logger.info(f"Request Headers keys: {list(headers.keys())}")

        acct = trading_client.get_account()
        return {
            "success": True,
            "equity": float(acct.equity),
            "cash": float(acct.cash),
            "buying_power": float(acct.buying_power)
        }
    except Exception as e:
        logger.error(f"Error fetching account info: {e}")
        return {"success": False, "reason": str(e)}

def get_positions():
    try:
        positions = trading_client.get_all_positions()
        pos_list = []
        for p in positions:
            pos_list.append({
                "symbol": p.symbol,
                "qty": float(p.qty),
                "avg_entry_price": float(p.avg_entry_price),
                "current_price": float(p.current_price),
                "unrealized_pl": float(p.unrealized_pl)
            })
        return {"success": True, "positions": pos_list}
    except Exception as e:
        logger.error(f"Error fetching positions: {e}")
        return {"success": False, "reason": str(e)}
