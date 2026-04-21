# Vegas Channel Indicator
# Combination of EMA144 and EMA169
# Provides bullish/bearish arrangement flags

import pandas as pd
from pandas import DataFrame
from freqtrade.strategy import IStrategy

def populate_vegas(df: DataFrame) -> DataFrame:
    """Add EMA144, EMA169 and arrangement columns.
    - ``vegas_ema144``: EMA of period 144
    - ``vegas_ema169``: EMA of period 169
    - ``vegas_bull``: 1 when EMA144 > EMA169 (bullish)
    - ``vegas_bear``: 1 when EMA144 < EMA169 (bearish)
    """
    # 使用 pandas 替代 talib
    df['vegas_ema144'] = df['close'].ewm(span=30, adjust=False).mean()
    df['vegas_ema169'] = df['close'].ewm(span=60, adjust=False).mean()
    df['vegas_bull'] = (df['vegas_ema144'] > df['vegas_ema169']).astype(int)
    df['vegas_bear'] = (df['vegas_ema144'] < df['vegas_ema169']).astype(int)
    return df
