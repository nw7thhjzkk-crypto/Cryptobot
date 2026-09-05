import pandas as pd
import numpy as np

def calculate_atr(df: pd.DataFrame, length: int = 14) -> pd.Series:
    """Calculate Average True Range (ATR)."""
    if df.empty or len(df) < length + 1:
        return pd.Series(dtype=float)
    high_low = df['high'] - df['low']
    high_close = (df['high'] - df['close'].shift()).abs()
    low_close = (df['low'] - df['close'].shift()).abs()
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    return true_range.rolling(window=length, min_periods=length).mean()

def calculate_adx(df: pd.DataFrame, length: int = 14) -> pd.Series:
    """Calculate Average Directional Index (ADX)."""
    if len(df) < length * 2:
        return pd.Series(dtype=float)

    plus_dm = df['high'].diff()
    minus_dm = -df['low'].diff()

    plus_dm = np.where((plus_dm > minus_dm) & (plus_dm > 0), plus_dm, 0.0)
    minus_dm = np.where((minus_dm > plus_dm) & (minus_dm > 0), minus_dm, 0.0)

    plus_dm = pd.Series(plus_dm, index=df.index)
    minus_dm = pd.Series(minus_dm, index=df.index)

    tr = calculate_atr(df, 1) * 1 # Get 1-period TR

    atr = tr.rolling(window=length, min_periods=length).mean()
    plus_di = 100 * (plus_dm.rolling(window=length, min_periods=length).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(window=length, min_periods=length).mean() / atr)

    dx = 100 * (abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, 1)) # avoid div by zero
    adx = dx.rolling(window=length, min_periods=length).mean()
    return adx

def calculate_bbands(df: pd.DataFrame, length: int = 20, std: float = 2.0):
    """Calculate Bollinger Bands."""
    if len(df) < length:
        return None, None, None
    sma = df['close'].rolling(window=length, min_periods=length).mean()
    rstd = df['close'].rolling(window=length, min_periods=length).std()
    upper = sma + (std * rstd)
    lower = sma - (std * rstd)
    return lower, sma, upper

def calculate_rsi(df: pd.DataFrame, length: int = 14) -> pd.Series:
    """Calculate Relative Strength Index (RSI)."""
    if len(df) < length + 1:
        return pd.Series(dtype=float)
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=length, min_periods=length).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=length, min_periods=length).mean()
    rs = gain / loss.replace(0, 1) # avoid div by 0
    rsi = 100 - (100 / (1 + rs))
    rsi = rsi.where(loss != 0, 100.0) # Handle edge case of loss being 0
    return rsi

def calculate_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9):
    """Calculate MACD."""
    if len(df) < slow + signal:
        return None, None, None

    ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
    ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def calculate_volatility(df: pd.DataFrame, length: int = 20) -> pd.Series:
    """Calculate realized volatility (annualized)."""
    if len(df) < length:
         return pd.Series(dtype=float)
    returns = df['close'].pct_change()
    # Assuming daily bars for crypto trading in this context, 365 days
    vol = returns.rolling(window=length).std() * np.sqrt(365)
    return vol
