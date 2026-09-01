import logging
from datetime import datetime, timedelta

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.historical import StockHistoricalDataClient, CryptoHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockLatestTradeRequest, CryptoBarsRequest, CryptoLatestTradeRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.enums import DataFeed

from bot.config import ALPACA_API_KEY, ALPACA_SECRET_KEY, PAPER_MODE

logger = logging.getLogger(__name__)

api_key_preview = str(ALPACA_API_KEY)[:4] if ALPACA_API_KEY else "None"
base_url = "https://paper-api.alpaca.markets" if PAPER_MODE else "https://api.alpaca.markets"
logger.info(
    f"Initializing Alpaca TradingClient. PAPER_MODE={PAPER_MODE}, "
    f"Base URL={base_url}, API_KEY startswith={api_key_preview}"
)

trading_client = TradingClient(ALPACA_API_KEY, ALPACA_SECRET_KEY, paper=PAPER_MODE)

# Free paper accounts cannot use SIP feed. Use IEX (free) for stocks.
stock_data_client = StockHistoricalDataClient(ALPACA_API_KEY, ALPACA_SECRET_KEY)
crypto_data_client = CryptoHistoricalDataClient(ALPACA_API_KEY, ALPACA_SECRET_KEY)


def _is_crypto(symbol: str) -> bool:
    s = symbol.upper().replace("-", "/")
    return "/" in s or s.endswith("USD") and any(
        s.startswith(c) for c in ("BTC", "ETH", "SOL", "DOGE", "AVAX", "LINK", "DOT")
    )


def _normalize_crypto(symbol: str) -> str:
    """Alpaca crypto symbols use BTC/USD form."""
    s = symbol.upper().replace("-", "/")
    if "/" not in s and s.endswith("USD"):
        s = s[:-3] + "/USD"
    return s


def get_latest_price(symbol: str):
    try:
        if _is_crypto(symbol):
            sym = _normalize_crypto(symbol)
            req = CryptoLatestTradeRequest(symbol_or_symbols=[sym])
            res = crypto_data_client.get_crypto_latest_trade(req)
            return {"success": True, "price": float(res[sym].price)}

        req = StockLatestTradeRequest(
            symbol_or_symbols=[symbol],
            feed=DataFeed.IEX,  # free tier
        )
        res = stock_data_client.get_stock_latest_trade(req)
        return {"success": True, "price": float(res[symbol].price)}
    except Exception as e:
        logger.error(f"Error fetching latest price for {symbol}: {e}")
        return {"success": False, "reason": str(e)}


def get_price_history(symbol: str, lookback_days: int = 100):
    """
    Daily bars for indicators.
    Stocks use IEX feed (available on free Alpaca paper).
    Crypto uses crypto bars endpoint.
    """
    try:
        end = datetime.utcnow()
        start = end - timedelta(days=lookback_days + 5)  # buffer for weekends

        if _is_crypto(symbol):
            sym = _normalize_crypto(symbol)
            req = CryptoBarsRequest(
                symbol_or_symbols=[sym],
                timeframe=TimeFrame.Day,
                start=start,
                end=end,
            )
            bars = crypto_data_client.get_crypto_bars(req)
            df = bars.df
            if df is not None and not df.empty:
                # Flatten multi-index if present
                if hasattr(df.index, "names") and df.index.nlevels > 1:
                    df = df.reset_index(level=0, drop=True)
            return {"success": True, "data": df}

        req = StockBarsRequest(
            symbol_or_symbols=[symbol],
            timeframe=TimeFrame.Day,
            start=start,
            end=end,
            feed=DataFeed.IEX,  # critical: free paper accounts cannot use SIP
        )
        bars = stock_data_client.get_stock_bars(req)
        df = bars.df
        if df is not None and not df.empty:
            if hasattr(df.index, "names") and df.index.nlevels > 1:
                df = df.reset_index(level=0, drop=True)
        return {"success": True, "data": df}
    except Exception as e:
        logger.error(f"Error fetching price history for {symbol}: {e}")
        return {"success": False, "reason": str(e)}


def submit_market_order(symbol: str, qty, side: str):
    try:
        order_side = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL
        # Crypto often needs GTC; stocks use DAY
        tif = TimeInForce.GTC if _is_crypto(symbol) else TimeInForce.DAY
        sym = _normalize_crypto(symbol) if _is_crypto(symbol) else symbol

        req = MarketOrderRequest(
            symbol=sym,
            qty=qty,
            side=order_side,
            time_in_force=tif,
        )
        order = trading_client.submit_order(req)
        return {"success": True, "order_id": str(order.id), "status": order.status.value}
    except Exception as e:
        logger.error(f"Error submitting market order for {symbol}: {e}")
        return {"success": False, "reason": str(e)}


def get_account():
    try:
        actual_url = trading_client._base_url if hasattr(trading_client, "_base_url") else "Unknown"
        logger.info(f"Using Alpaca base URL: {actual_url}")

        key_str = str(ALPACA_API_KEY) if ALPACA_API_KEY else ""
        key_preview = key_str[:4] if len(key_str) >= 4 else "None"
        logger.info(f"API Key starts with: {key_preview}, length: {len(key_str)}")

        acct = trading_client.get_account()
        return {
            "success": True,
            "equity": float(acct.equity),
            "cash": float(acct.cash),
            "buying_power": float(acct.buying_power),
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
                "unrealized_pl": float(p.unrealized_pl),
            })
        return {"success": True, "positions": pos_list}
    except Exception as e:
        logger.error(f"Error fetching positions: {e}")
        return {"success": False, "reason": str(e)}
