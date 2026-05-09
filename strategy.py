import pandas as pd
import pandas_ta as ta
from typing import List, Dict, Optional, Tuple

def calculate_indicators(candles: List[Dict]) -> pd.DataFrame:
    """Computes technical indicators (EMA, ATR) from candle data."""
    if not candles:
        return pd.DataFrame()

    df = pd.DataFrame(candles)
    # Deriv returns 'epoch', 'open', 'high', 'low', 'close'
    df['close'] = df['close'].astype(float)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)

    # Calculate 50 EMA and 200 EMA
    df['ema_50'] = ta.ema(df['close'], length=50)
    df['ema_200'] = ta.ema(df['close'], length=200)

    # Calculate ATR
    df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)

    return df

def detect_trend(df: pd.DataFrame) -> Optional[str]:
    """Identifies the trend direction based on EMAs."""
    if df.empty or len(df) < 200:
        return None

    latest = df.iloc[-1]
    if latest['ema_50'] > latest['ema_200']:
        return "uptrend"
    elif latest['ema_50'] < latest['ema_200']:
        return "downtrend"

    return None

def calculate_trade_levels(df: pd.DataFrame, trend: str) -> Tuple[float, float, float]:
    """Calculates Entry, SL, and TP levels."""
    latest = df.iloc[-1]
    entry = latest['close']
    atr = latest['atr']

    if trend == "uptrend":
        sl = entry - (1.5 * atr)
        tp = entry + (3.0 * atr) # Example: Using 3x ATR for TP
    else: # downtrend
        sl = entry + (1.5 * atr)
        tp = entry - (3.0 * atr)

    return entry, sl, tp
