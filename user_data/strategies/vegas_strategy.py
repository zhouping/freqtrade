"""Vegas Channel Strategy

- Uses the custom ``vegas_channel`` indicator (EMA30 & EMA60).
- Entry Long:
    * EMA144 > EMA169 (bullish arrangement)
    * Current candle forms a bullish engulfing pattern.
- Entry Short:
    * EMA144 < EMA169 (bearish arrangement)
    * Current candle forms a bearish engulfing pattern.
- Fixed stop‑loss: 10% of entry price.
- Fixed take‑profit: 2R (20% profit).
"""

import pandas as pd
from pandas import DataFrame
from freqtrade.strategy import IStrategy, merge_informative_pair

# Import the custom indicator helper
from user_data.indicators.vegas_channel import populate_vegas

class VegasChannelStrategy(IStrategy):
    # Minimal ROI – 2R when stop‑loss is 10%
    minimal_roi = {
        "0": 0.20  # 20% profit target
    }
    # Fixed stop‑loss of 10%
    stoploss = -0.10
    timeframe = "5m"
    # No trailing stop, no p&l protection
    trailing_stop = False
    use_exit_signal = False
    # We use the default order types
    order_types = {
        "entry": "limit",
        "exit": "limit",
        "stoploss": "market",
        "stoploss_on_exchange": False,
    }
    # Optional: plot the EMA lines for visual debugging
    plot_config = {
        "main_plot": {
            "vegas_ema30": {"color": "green"},
            "vegas_ema60": {"color": "red"},
        }
    }

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """Add the Vegas channel EMA indicators to the dataframe."""
        # Use the helper from the custom indicator file
        dataframe = populate_vegas(dataframe)
        return dataframe

    def bullish_engulfing(self, df: DataFrame) -> pd.Series:
        """Return True where a bullish engulfing pattern occurs.
        Conditions:
        - Previous candle is bearish (close < open)
        - Current candle is bullish (close > open)
        - Current candle's body completely engulfs previous candle's body.
        """
        prev_open = df['open'].shift(1)
        prev_close = df['close'].shift(1)
        cond1 = prev_close < prev_open  # previous bearish
        cond2 = df['close'] > df['open']  # current bullish
        cond3 = df['close'] > prev_open  # current close above previous open
        cond4 = df['open'] < prev_close  # current open below previous close
        return cond1 & cond2 & cond3 & cond4

    def bearish_engulfing(self, df: DataFrame) -> pd.Series:
        """Return True where a bearish engulfing pattern occurs."""
        prev_open = df['open'].shift(1)
        prev_close = df['close'].shift(1)
        cond1 = prev_close > prev_open  # previous bullish
        cond2 = df['close'] < df['open']  # current bearish
        cond3 = df['close'] < prev_open  # current close below previous open
        cond4 = df['open'] > prev_close  # current open above previous close
        return cond1 & cond2 & cond3 & cond4

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """Generate entry signals based on Vegas channel and engulfing patterns."""
        dataframe.loc[
            (dataframe['vegas_bull'] == 1) &
            self.bullish_engulfing(dataframe),
            'enter_long'] = 1
        dataframe.loc[
            (dataframe['vegas_bear'] == 1) &
            self.bearish_engulfing(dataframe),
            'enter_short'] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """No custom exit logic – rely on ROI/stop‑loss."""
        return dataframe