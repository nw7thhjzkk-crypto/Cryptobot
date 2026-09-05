import pandas as pd
import numpy as np

class BacktestEngine:
    def __init__(self, initial_capital: float = 10000.0, transaction_cost: float = 0.001, slippage: float = 0.0005):
        self.initial_capital = initial_capital
        self.transaction_cost = transaction_cost
        self.slippage = slippage

    def run(self, agent, symbol: str, data: pd.DataFrame, benchmark: pd.DataFrame = None):
        """
        Chronological walk forward backtest without lookahead bias.
        """
        capital = self.initial_capital
        position = 0
        entry_price = 0.0

        trades = []
        equity_curve = [self.initial_capital]

        # To prevent lookahead, we feed data up to index 'i'
        for i in range(50, len(data)):
            window = data.iloc[:i]
            bench_window = benchmark.iloc[:i] if benchmark is not None else None

            # The agent only sees data up to current bar (close)
            # The trade will be executed on the NEXT bar's open (realistic timing)
            # For simplicity in this engine, we'll execute at current bar's close + slippage
            signal_res = agent.analyze(symbol, window, benchmark_history=bench_window)
            signal = signal_res.get("signal", "HOLD")

            current_price = float(data['close'].iloc[i-1])

            if position == 0 and signal == "BUY":
                # Buy
                qty = (capital * 0.95) / (current_price * (1 + self.slippage)) # 95% allocation
                cost = (qty * current_price) * self.transaction_cost
                capital -= cost
                position = qty
                entry_price = current_price * (1 + self.slippage)

            elif position > 0 and signal == "SELL":
                # Sell
                exit_price = current_price * (1 - self.slippage)
                proceeds = position * exit_price
                cost = proceeds * self.transaction_cost
                capital += (proceeds - cost)

                pnl = (exit_price - entry_price) / entry_price
                trades.append(pnl)

                position = 0
                entry_price = 0.0

            # Mark to market
            current_equity = capital + (position * current_price if position > 0 else 0)
            equity_curve.append(current_equity)

        # Close open position at end
        if position > 0:
            exit_price = float(data['close'].iloc[-1]) * (1 - self.slippage)
            proceeds = position * exit_price
            cost = proceeds * self.transaction_cost
            capital += (proceeds - cost)
            pnl = (exit_price - entry_price) / entry_price
            trades.append(pnl)
            equity_curve.append(capital)

        return self._calculate_metrics(trades, equity_curve, agent.parameters)

    def _empty_result(self, parameters):
        return {
            "total_return": 0.0,
            "sharpe_ratio": 0.0,
            "sortino_ratio": 0.0,
            "max_drawdown": 0.0,
            "win_rate": 0.0,
            "num_trades": 0,
            "parameters": parameters,
            "cost_assumption": self.transaction_cost,
            "slippage_assumption": self.slippage
        }

    def _calculate_metrics(self, trades, equity_curve, parameters):
        if not trades or len(equity_curve) < 2:
            return self._empty_result(parameters)

        total_return = (equity_curve[-1] - self.initial_capital) / self.initial_capital

        eq_series = pd.Series(equity_curve)
        daily_returns = eq_series.pct_change().dropna()

        # Approx Sharpe & Sortino (Assuming 365 trading days for crypto)
        if daily_returns.std() == 0:
            sharpe = 0.0
            sortino = 0.0
        else:
            sharpe = (daily_returns.mean() / daily_returns.std()) * np.sqrt(365)
            downside = daily_returns[daily_returns < 0]
            if len(downside) > 0 and downside.std() > 0:
                sortino = (daily_returns.mean() / downside.std()) * np.sqrt(365)
            else:
                sortino = sharpe # No downside volatility

        rolling_max = eq_series.cummax()
        drawdowns = (eq_series - rolling_max) / rolling_max
        max_drawdown = drawdowns.min()

        wins = sum(1 for t in trades if t > 0)
        win_rate = wins / len(trades)

        return {
            "total_return": float(total_return),
            "sharpe_ratio": float(sharpe),
            "sortino_ratio": float(sortino),
            "max_drawdown": float(max_drawdown),
            "win_rate": float(win_rate),
            "num_trades": len(trades),
            "parameters": parameters,
            "cost_assumption": self.transaction_cost,
            "slippage_assumption": self.slippage,
            "trades_list": trades # For robustness monte carlo
        }
