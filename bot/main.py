import time
import logging
import uuid
from datetime import datetime, timezone

from bot.config import (
    WATCHLIST, POLL_INTERVAL_SECONDS, LOOP_MAX_MINUTES,
    RISK_PER_TRADE_PCT, MAX_TOTAL_RISK_PCT, MAX_DRAWDOWN_PCT,
    PAPER_MODE, MAX_POSITION_PCT, MAX_PORTFOLIO_EXPOSURE, MAX_POSITIONS,
    MIN_SIGNAL_CONFIDENCE
)
from bot.broker import (
    get_latest_price, get_price_history,
    get_account, get_positions
)
from bot.sheets import (
    init_tabs, log_trade, update_positions, log_equity,
    update_watchlist, log_agent_signal, log_bot_run
)

from bot.agents.trend import TrendAgent
from bot.agents.momentum import MomentumAgent
from bot.agents.mean_reversion import MeanReversionAgent
from bot.agents.breakout import BreakoutAgent
from bot.agents.volatility import VolatilityAgent
from bot.agents.volume import VolumeAgent
from bot.agents.relative_strength import RelativeStrengthAgent
from bot.agents.market_regime import MarketRegimeAgent
from bot.agents.gemini_agents import GeminiContextAgent

from bot.consensus import ConsensusEngine
from bot.portfolio import PortfolioEngine
from bot.risk import RiskEngine, check_drawdown_breaker, calculate_position_size, check_portfolio_risk
from bot.execution import ExecutionEngine
from bot.strategy import calculate_atr

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

equity_history_run = []

def main_loop():
    logger.info("Initializing Google Sheets tabs...")
    init_tabs()

    run_id = str(uuid.uuid4())[:8]
    run_started_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    start_time = time.time()
    max_seconds = LOOP_MAX_MINUTES * 60
    iteration = 0

    quant_agents = [
        TrendAgent(), MomentumAgent(), MeanReversionAgent(),
        BreakoutAgent(), VolatilityAgent(), VolumeAgent(),
        RelativeStrengthAgent()
    ]
    regime_agent = MarketRegimeAgent()
    gemini_agent = GeminiContextAgent()

    consensus_engine = ConsensusEngine(min_confidence=MIN_SIGNAL_CONFIDENCE)
    portfolio_engine = PortfolioEngine(max_portfolio_exposure=MAX_PORTFOLIO_EXPOSURE, max_positions=MAX_POSITIONS)
    risk_engine = RiskEngine(paper_mode=PAPER_MODE, max_position_pct=MAX_POSITION_PCT)
    execution_engine = ExecutionEngine(paper_mode=PAPER_MODE)

    total_symbols_processed = 0
    total_orders_submitted = 0
    total_errors = 0

    while True:
        elapsed = time.time() - start_time
        if elapsed > max_seconds:
            logger.info("Time budget reached. Exiting cleanly.")
            break

        try:
            iteration += 1
            logger.info(f"--- Iteration {iteration} ---")

            acct_res = get_account()
            if not acct_res["success"]:
                logger.error("Could not fetch account info, skipping iteration.")
                time.sleep(POLL_INTERVAL_SECONDS)
                total_errors += 1
                continue

            equity = acct_res["equity"]
            cash = acct_res["cash"]
            buying_power = acct_res["buying_power"]
            equity_history_run.append(equity)

            pos_res = get_positions()
            open_positions = pos_res.get("positions", []) if pos_res["success"] else []

            if iteration % 10 == 1:
                now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                equity_row = [now_str, equity, cash, buying_power]
                log_equity(equity_row)
                if pos_res["success"]:
                    pos_rows = [[now_str, p['symbol'], p['qty'], p['avg_entry_price'], p['current_price'], p['unrealized_pl']] for p in open_positions]
                    update_positions(pos_rows)

            breaker_active = check_drawdown_breaker(equity_history_run, MAX_DRAWDOWN_PCT)
            if breaker_active:
                logger.warning("Drawdown breaker active. Halting new entries.")

            bench_res = get_price_history("SPY", lookback_days=250)
            benchmark_df = bench_res["data"] if bench_res["success"] else None

            watchlist_updates = []
            now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

            for symbol in WATCHLIST:
                try:
                    total_symbols_processed += 1

                    hist_res = get_price_history(symbol, lookback_days=250)
                    if not hist_res["success"] or hist_res["data"] is None or hist_res["data"].empty:
                        logger.warning(f"Failed to fetch price history for {symbol}")
                        continue

                    df = hist_res["data"]
                    num_bars = len(df)
                    logger.info(f"Fetched {num_bars} bars for {symbol}")

                    latest_res = get_latest_price(symbol)
                    if not latest_res["success"]:
                        continue
                    current_price = latest_res["price"]

                    regime_signal = regime_agent.analyze(symbol, df)
                    regime_str = regime_signal["features"].get("regime", "unknown")

                    quant_signals = []
                    for agent in quant_agents:
                        if isinstance(agent, RelativeStrengthAgent):
                            sig = agent.analyze(symbol, df, benchmark_history=benchmark_df)
                        else:
                            sig = agent.analyze(symbol, df)
                        quant_signals.append(sig)

                    gemini_signal = gemini_agent.analyze(symbol, df, quant_signals=quant_signals)

                    consensus_result = consensus_engine.aggregate_signals(symbol, quant_signals, regime_signal, gemini_signal)
                    proposed_signal = consensus_result["signal"]

                    logger.info(f"Consensus for {symbol}: {proposed_signal} (Score: {consensus_result['score']:.2f}, Conf: {consensus_result['confidence']:.2f})")

                    log_agent_signal([
                        now_str, symbol, "Consensus", proposed_signal, consensus_result['score'],
                        consensus_result['confidence'], consensus_result['reason'], regime_str,
                        proposed_signal, "", ""
                    ])

                    watchlist_updates.append([symbol, regime_str, now_str])

                    if proposed_signal == "HOLD":
                        logger.info(f"Symbol: {symbol} | Regime: {regime_str} | Sleeve: none | Action: hold")
                        continue

                    if proposed_signal == "BUY" and breaker_active:
                         logger.info(f"Skipping buy for {symbol} due to drawdown breaker.")
                         continue

                    portfolio_eval = portfolio_engine.evaluate(symbol, proposed_signal, open_positions, current_price, equity)
                    if not portfolio_eval["approved"]:
                        logger.info(f"Portfolio rejected {proposed_signal} for {symbol}: {portfolio_eval['reason']}")
                        continue

                    if proposed_signal == "BUY":
                        atr_s = calculate_atr(df, length=14)
                        atr = atr_s.iloc[-1] if (atr_s is not None and not atr_s.empty) else (current_price * 0.05)

                        qty = calculate_position_size(equity, atr, RISK_PER_TRADE_PCT)
                        if qty <= 0:
                            logger.info(f"Calculated size for {symbol} is 0, skipping.")
                            continue

                        new_risk = qty * (2.0 * atr)
                        if not check_portfolio_risk(open_positions, new_risk, MAX_TOTAL_RISK_PCT, equity):
                            logger.info(f"Portfolio total risk exceeded, skipping buy for {symbol}.")
                            continue
                    else: # SELL
                        existing_pos = next((p for p in open_positions if p['symbol'] == symbol), None)
                        qty = existing_pos["qty"] if existing_pos else 0

                    risk_eval = risk_engine.evaluate_order(symbol, proposed_signal, qty, current_price, equity, buying_power)

                    if not risk_eval["approved"]:
                         logger.warning(f"Risk rejected {proposed_signal} for {symbol}: {risk_eval['reason']}")
                         continue

                    logger.info(f"Symbol: {symbol} | Regime: {regime_str} | Sleeve: multi-agent | Action: {proposed_signal}")

                    order_res = execution_engine.execute_order(symbol, proposed_signal, qty)
                    total_orders_submitted += 1

                    status = order_res.get("status", "failed")
                    order_id = order_res.get("order_id", "none")
                    reason = order_res.get("reason", "")

                    log_trade([now_str, symbol, proposed_signal, qty, current_price, order_id, status, regime_str, "multi-agent", reason])

                except Exception as inner_e:
                     logger.error(f"Error processing symbol {symbol}: {inner_e}", exc_info=True)
                     total_errors += 1

            if watchlist_updates:
                update_watchlist(watchlist_updates)

        except Exception as e:
            logger.error(f"Error in main loop iteration: {e}", exc_info=True)
            total_errors += 1

        time.sleep(POLL_INTERVAL_SECONDS)

    run_finished_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    log_bot_run([run_id, run_started_at, run_finished_at, "completed", total_symbols_processed, total_orders_submitted, total_errors])

if __name__ == "__main__":
    logger.info("Starting Multi-Agent Paper Trading Bot")
    main_loop()
