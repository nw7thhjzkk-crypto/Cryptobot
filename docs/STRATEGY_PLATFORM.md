# Strategy Platform

Cryptobot's strategy platform is modular and built to run multiple deterministic quant strategies simultaneously, filtered by market regime.

## Factor Library
Technical indicator calculations (ADX, EMA, MACD, RSI, Bollinger Bands, ATR, Volatility) are manually implemented using `pandas` and `numpy` in `bot/factors.py`.

## Market Regime Engine
The `MarketRegimeEngine` dynamically detects conditions such as `trending_bull`, `trending_bear`, `ranging`, and `risk_off` using deterministic constraints.

## Consensus Engine
A sophisticated `ConsensusEngine` collects inputs from active strategy agents (Trend, Breakout, Mean Reversion, Momentum, Volatility, etc.), weights them by regime compatibility, and aggregates the signals to output a final deterministic decision.

## Adaptive Weights and Attribution
An `AttributionTracker` logs each strategy's historical returns, generating proxy metrics like Sharpe ratios, which the `ConsensusEngine` uses to dynamically adapt strategy weights, ensuring strong out-of-sample performers get higher authority.
