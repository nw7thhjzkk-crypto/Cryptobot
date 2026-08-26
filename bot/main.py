import time
import logging
from datetime import datetime, timezone

from bot.config import (
    WATCHLIST, POLL_INTERVAL_SECONDS, LOOP_MAX_MINUTES,
    RISK_PER_TRADE_PCT, MAX_TOTAL_RISK_PCT, MAX_DRAWDOWN_PCT
)
from bot.broker import (
    get_latest_price, get_price_history, submit_market_order,
    get_account, get_positions
)
from bot.sheets import init_tabs, log_trade, update_positions, log_equity
from bot.strategy import decide, get_middle_band, calculate_atr
from bot.risk import calculate_position_size, check_portfolio_risk, check_drawdown_breaker

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# To hold pseudo equity history during this run to check drawdown breaker
equity_history_run = []

def main_loop():
    logger.info("Initializing Google Sheets tabs...")
    init_tabs()

    start_time = time.time()
    max_seconds = LOOP_MAX_MINUTES * 60
    iteration = 0

    while True:
        elapsed = time.time() - start_time
        if elapsed > max_seconds:
            logger.info("Time budget reached. Exiting cleanly.")
            break

        try:
            iteration += 1
            logger.info(f"--- Iteration {iteration} ---")

            # 1. Fetch Account Info
            acct_res = get_account()
            if not acct_res["success"]:
                logger.error("Could not fetch account info, skipping iteration.")
                time.sleep(POLL_INTERVAL_SECONDS)
                continue

            equity = acct_res["equity"]
            cash = acct_res["cash"]
            buying_power = acct_res["buying_power"]
            equity_history_run.append(equity)

            # 2. Fetch Open Positions
            pos_res = get_positions()
            open_positions = pos_res.get("positions", []) if pos_res["success"] else []

            # Log equity & positions every ~10 iterations (or first iteration)
            if iteration % 10 == 1:
                now_str = datetime.now(timezone.utc).isoformat()
                log_equity([now_str, equity, cash, buying_power])
                if pos_res["success"]:
                    pos_rows = [[now_str, p['symbol'], p['qty'], p['avg_entry_price'], p['current_price'], p['unrealized_pl']] for p in open_positions]
                    update_positions(pos_rows)

            # 3. Check Drawdown Breaker
            if check_drawdown_breaker(equity_history_run, MAX_DRAWDOWN_PCT):
                logger.warning("Drawdown breaker active. Halting new entries.")
                breaker_active = True
            else:
                breaker_active = False

            # 4. Iterate Watchlist
            for symbol in WATCHLIST:
                # Get price history
                hist_res = get_price_history(symbol, lookback_days=100)
                if not hist_res["success"]:
                    continue
                df = hist_res["data"]

                # Check for existing position
                existing_pos = next((p for p in open_positions if p['symbol'] == symbol), None)

                decision = decide(symbol, df)
                action = decision["action"]
                regime = decision["regime"]
                sleeve = decision["sleeve"]

                latest_res = get_latest_price(symbol)
                if not latest_res["success"]: continue
                current_price = latest_res["price"]

                # Exit logic for mean-reversion if already in position
                if existing_pos and existing_pos["qty"] > 0 and regime == "ranging" and sleeve == "mean_reversion":
                     mid_band = get_middle_band(df)
                     if mid_band is not None and current_price >= mid_band:
                          logger.info(f"Exit condition met for {symbol} (mean-reversion to mid band).")
                          action = "sell"

                if action == "hold":
                    continue

                if action == "buy" and breaker_active:
                    logger.info(f"Skipping buy for {symbol} due to drawdown breaker.")
                    continue

                if action == "buy" and existing_pos:
                    logger.info(f"Already in position for {symbol}, skipping buy.")
                    continue

                # Calculate size and risk for new buy
                if action == "buy":
                    atr_s = calculate_atr(df, length=14)
                    atr = atr_s.iloc[-1] if (atr_s is not None and not atr_s.empty) else 0

                    qty = calculate_position_size(equity, atr, RISK_PER_TRADE_PCT)
                    if qty <= 0:
                        logger.info(f"Calculated size for {symbol} is 0, skipping.")
                        continue

                    new_risk = qty * (2.0 * atr) # approx risk based on 2x ATR stop
                    if not check_portfolio_risk(open_positions, new_risk, MAX_TOTAL_RISK_PCT, equity):
                        logger.info(f"Portfolio risk exceeded, skipping buy for {symbol}.")
                        continue
                else: # sell
                    if not existing_pos:
                        logger.info(f"No existing position to sell for {symbol}.")
                        continue
                    qty = existing_pos["qty"]

                # Submit Order
                logger.info(f"Submitting {action} order for {qty} of {symbol}")
                order_res = submit_market_order(symbol, qty, action)

                status = order_res.get("status", "failed")
                order_id = order_res.get("order_id", "none")
                reason = order_res.get("reason", "")

                now_str = datetime.now(timezone.utc).isoformat()
                log_row = [now_str, symbol, action, qty, current_price, order_id, status, regime, sleeve, reason]
                log_trade(log_row)

        except Exception as e:
            logger.error(f"Error in main loop iteration: {e}", exc_info=True)

        time.sleep(POLL_INTERVAL_SECONDS)

if __name__ == "__main__":
    logger.info("Starting Paper Trading Bot")
    main_loop()