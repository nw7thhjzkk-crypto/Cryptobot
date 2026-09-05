# GitHub Quant Ecosystem Analysis

## Freqtrade
- **Purpose**: Open source crypto trading bot.
- **Useful Concepts**: Backtesting engine, hyperopt, custom strategies.
- **Adopted**: Strategy structure concepts.
- **Rejected**: Entire framework (too heavy, introduces unnecessary dependencies).
- **Implementation**: `bot/strategy.py`

## QuantConnect LEAN
- **Purpose**: Algorithmic trading engine.
- **Useful Concepts**: Event-driven architecture, factor libraries.
- **Adopted**: Factor-based indicator structures.
- **Rejected**: Full engine (C# based, too complex for this python system).
- **Implementation**: `bot/factors.py`

## vectorbt
- **Purpose**: Fast backtesting using pandas/numpy.
- **Useful Concepts**: Vectorized backtesting for speed.
- **Adopted**: Vectorized indicator calculations.
- **Rejected**: Complex plotting and non-standard metrics.
- **Implementation**: `bot/factors.py`
