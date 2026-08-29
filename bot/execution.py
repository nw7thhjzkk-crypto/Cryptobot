import logging
import time
from typing import Dict, Any
from bot.broker import submit_market_order

logger = logging.getLogger(__name__)

class ExecutionEngine:
    def __init__(self, paper_mode: bool):
        self.paper_mode = paper_mode
        self.submitted_orders_cache = set()

    def execute_order(self, symbol: str, signal: str, qty: int) -> Dict[str, Any]:
        if not self.paper_mode:
            logger.warning(f"LIVE EXECUTION ENGINE ENGAGED FOR {symbol}. PAPER_MODE IS FALSE.")

        cache_key = f"{symbol}_{signal}_{qty}"
        if cache_key in self.submitted_orders_cache:
            return {"success": False, "reason": "Duplicate order detected in cache"}

        max_retries = 3
        retry_delay = 2

        for attempt in range(1, max_retries + 1):
            logger.info(f"Submitting {signal} order for {qty} of {symbol} (Attempt {attempt}/{max_retries})")

            try:
                order_res = submit_market_order(symbol, qty, signal)

                if order_res["success"]:
                    self.submitted_orders_cache.add(cache_key)
                    return order_res
                else:
                    reason = order_res.get("reason", "Unknown error")
                    logger.warning(f"Order submission failed for {symbol}: {reason}")

                    if "insufficient buying power" in reason.lower() or "qty must be" in reason.lower():
                        logger.error(f"Unrecoverable error for {symbol}. Aborting retries.")
                        return order_res

            except Exception as e:
                 logger.error(f"Exception during order submission for {symbol}: {e}")

            if attempt < max_retries:
                time.sleep(retry_delay)
                retry_delay *= 2

        return {"success": False, "reason": "Max retries reached"}
