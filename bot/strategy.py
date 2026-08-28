import pandas as pd
import numpy as np

from bot.config import MEAN_REVERSION_ELIGIBLE

def calculate_atr(df: pd.DataFrame, length: int = 14) -> pd.Series:
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    # Wilder's smoothing
    atr = true_range.ewm(alpha=1/length, min_periods=length, adjust=False).mean()
    return atr

def calculate_adx(df: pd.DataFrame, length: int = 14) -> pd.Series:
    up_move = df['high'] - df['high'].shift(1)
    down_move = df['low'].shift(1) - df['low']

    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

    plus_dm = pd.Series(plus_dm, index=df.index)
    minus_dm = pd.Series(minus_dm, index=df.index)

    atr = calculate_atr(df, length)

    plus_di = 100 * (plus_dm.ewm(alpha=1/length, min_periods=length, adjust=False).mean() / atr)
    minus_di = 100 * (minus_dm.ewm(alpha=1/length, min_periods=length, adjust=False).mean() / atr)

    dx = (np.abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
    adx = dx.ewm(alpha=1/length, min_periods=length, adjust=False).mean()
    return adx

def calculate_bbands(df: pd.DataFrame, length: int = 20, std: float = 2.0):
    sma = df['close'].rolling(window=length).mean()
    rolling_std = df['close'].rolling(window=length).std(ddof=0)
    upper_band = sma + (rolling_std * std)
    lower_band = sma - (rolling_std * std)
    bandwidth = ((upper_band - lower_band) / sma) * 100
    return lower_band, sma, upper_band, bandwidth

def calculate_rsi(df: pd.DataFrame, length: int = 14) -> pd.Series:
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/length, min_periods=length, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/length, min_periods=length, adjust=False).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
    ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    macd_hist = macd_line - signal_line
    return macd_hist

def detect_regime(price_history: pd.DataFrame) -> str:
    """
    Detects the current market regime.
    - ADX(14) > 25 -> "trending"
    - ADX(14) < 20 AND Bollinger Band width (20-period) contracting
      relative to its own 50-day average -> "ranging"
    - ATR(14) > 1.5x its 50-day average -> "transitional" (overrides above)
    - Default -> "transitional"
    """
    if len(price_history) < 65:
        return "transitional"

    df = price_history.copy()

    # Calculate ADX (14)
    adx = calculate_adx(df, length=14)
    if adx is None or adx.empty or pd.isna(adx.iloc[-1]):
        return "transitional"
    current_adx = adx.iloc[-1]

    # Calculate ATR (14)
    atr = calculate_atr(df, length=14)
    if atr is None or atr.empty or pd.isna(atr.iloc[-1]):
         return "transitional"
    current_atr = atr.iloc[-1]
    atr_50_avg = atr.rolling(window=50).mean().iloc[-1]

    # Check ATR override
    if current_atr > 1.5 * atr_50_avg:
        return "transitional"

    # Calculate Bollinger Bands (20)
    lower_band, mid_band, upper_band, bb_width = calculate_bbands(df, length=20)
    if bb_width is None or bb_width.empty or pd.isna(bb_width.iloc[-1]):
         return "transitional"

    current_bb_width = bb_width.iloc[-1]
    bb_width_50_avg = bb_width.rolling(window=50).mean().iloc[-1]

    if current_adx > 25:
        return "trending"
    elif current_adx < 20 and current_bb_width < bb_width_50_avg:
        return "ranging"

    return "transitional"

def trend_signal(price_history: pd.DataFrame) -> str:
    """
    Trend sleeve logic:
    - 20-period EMA crosses above 50-period EMA -> buy
    - crosses below -> sell
    - Confirm with MACD histogram agreeing with crossover direction
    """
    if len(price_history) < 60:
        return "hold"

    df = price_history.copy()
    ema20 = df['close'].ewm(span=20, adjust=False).mean()
    ema50 = df['close'].ewm(span=50, adjust=False).mean()
    macd_hist = calculate_macd(df)

    if ema20.empty or ema50.empty or macd_hist.empty:
         return "hold"

    prev_ema20, curr_ema20 = ema20.iloc[-2], ema20.iloc[-1]
    prev_ema50, curr_ema50 = ema50.iloc[-2], ema50.iloc[-1]
    curr_macd_hist = macd_hist.iloc[-1]

    cross_above = prev_ema20 <= prev_ema50 and curr_ema20 > curr_ema50
    cross_below = prev_ema20 >= prev_ema50 and curr_ema20 < curr_ema50

    if cross_above and curr_macd_hist > 0:
        return "buy"
    elif cross_below and curr_macd_hist < 0:
        return "sell"

    return "hold"

def mean_reversion_signal(symbol: str, price_history: pd.DataFrame) -> str:
    """
    Mean-reversion sleeve logic:
    - RSI(14) < 30 AND price at/below lower Bollinger Band -> buy
    - RSI(14) > 70 AND price at/above upper Bollinger Band -> sell
    Only called when regime == "ranging" AND symbol in MEAN_REVERSION_ELIGIBLE.
    """
    if symbol not in MEAN_REVERSION_ELIGIBLE:
        return "hold"

    if len(price_history) < 25:
        return "hold"

    df = price_history.copy()
    rsi = calculate_rsi(df, length=14)
    lower_band, mid_band, upper_band, _ = calculate_bbands(df, length=20)

    if rsi is None or rsi.empty:
         return "hold"

    curr_rsi = rsi.iloc[-1]
    curr_close = df['close'].iloc[-1]
    curr_lower = lower_band.iloc[-1]
    curr_upper = upper_band.iloc[-1]

    if curr_rsi < 30 and curr_close <= curr_lower:
        return "buy"
    elif curr_rsi > 70 and curr_close >= curr_upper:
        return "sell"

    return "hold"

def get_middle_band(price_history: pd.DataFrame):
    df = price_history.copy()
    _, mid_band, _, _ = calculate_bbands(df, length=20)
    if mid_band is None or mid_band.empty: return None
    return mid_band.iloc[-1]

def decide(symbol: str, price_history: pd.DataFrame) -> dict:
    """
    Combined decision:
    Calls detect_regime(), routes to the appropriate sleeve, returns dict.
    """
    if price_history.empty:
        return {"action": "hold", "regime": "unknown", "sleeve": "none"}

    regime = detect_regime(price_history)

    action = "hold"
    sleeve = "none"

    if regime == "trending":
        action = trend_signal(price_history)
        sleeve = "trend"
    elif regime == "ranging":
        action = mean_reversion_signal(symbol, price_history)
        sleeve = "mean_reversion" if symbol in MEAN_REVERSION_ELIGIBLE else "none"

    return {
        "action": action,
        "regime": regime,
        "sleeve": sleeve
    }
