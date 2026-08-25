import pandas as pd
import pandas_ta as ta

from bot.config import MEAN_REVERSION_ELIGIBLE

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
    adx_df = ta.adx(df['high'], df['low'], df['close'], length=14)
    if adx_df is None or adx_df.empty:
        return "transitional"
    adx_col = [col for col in adx_df.columns if col.startswith('ADX_')][0]
    current_adx = adx_df[adx_col].iloc[-1]

    # Calculate ATR (14)
    atr = ta.atr(df['high'], df['low'], df['close'], length=14)
    if atr is None or atr.empty:
         return "transitional"
    current_atr = atr.iloc[-1]
    atr_50_avg = atr.rolling(window=50).mean().iloc[-1]

    # Check ATR override
    if current_atr > 1.5 * atr_50_avg:
        return "transitional"

    # Calculate Bollinger Bands (20)
    bbands = ta.bbands(df['close'], length=20)
    if bbands is None or bbands.empty:
         return "transitional"

    bb_width_col = [col for col in bbands.columns if col.startswith('BBB_')][0]
    bb_width = bbands[bb_width_col]
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
    ema20 = ta.ema(df['close'], length=20)
    ema50 = ta.ema(df['close'], length=50)
    macd = ta.macd(df['close'])

    if ema20 is None or ema50 is None or macd is None:
         return "hold"

    macd_hist_col = [col for col in macd.columns if col.startswith('MACDh_')][0]

    prev_ema20, curr_ema20 = ema20.iloc[-2], ema20.iloc[-1]
    prev_ema50, curr_ema50 = ema50.iloc[-2], ema50.iloc[-1]
    curr_macd_hist = macd[macd_hist_col].iloc[-1]

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
    rsi = ta.rsi(df['close'], length=14)
    bbands = ta.bbands(df['close'], length=20)

    if rsi is None or bbands is None:
         return "hold"

    lower_col = [col for col in bbands.columns if col.startswith('BBL_')][0]
    upper_col = [col for col in bbands.columns if col.startswith('BBU_')][0]

    curr_rsi = rsi.iloc[-1]
    curr_close = df['close'].iloc[-1]
    curr_lower = bbands[lower_col].iloc[-1]
    curr_upper = bbands[upper_col].iloc[-1]

    if curr_rsi < 30 and curr_close <= curr_lower:
        return "buy"
    elif curr_rsi > 70 and curr_close >= curr_upper:
        return "sell"

    return "hold"

def get_middle_band(price_history: pd.DataFrame):
    df = price_history.copy()
    bbands = ta.bbands(df['close'], length=20)
    if bbands is None: return None
    mid_col = [col for col in bbands.columns if col.startswith('BBM_')][0]
    return bbands[mid_col].iloc[-1]

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
