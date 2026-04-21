# GodStra_hyperopt Strategy (支持 Hyperopt 优化)
# Author: @Mablue (Masoud Azizi)
# github: https://github.com/mablue/
# IMPORTANT:Add to your pairlists inside config.json (Under StaticPairList):
#   {
#       "method": "AgeFilter",
#       "min_days_listed": 30
#   },
# IMPORTANT: INSTALL TA BEFOUR RUN(pip install ta)
# IMPORTANT: Use Smallest "max_open_trades" for getting best results inside config.json

# --- Do not remove these libs ---
import logging
from functools import reduce

import freqtrade.vendor.qtpylib.indicators as qtpylib
import numpy as np
# Add your lib to import here
# import talib.abstract as ta
import pandas as pd
from freqtrade.strategy import IStrategy, IntParameter, RealParameter, CategoricalParameter
from numpy.lib import math
from pandas import DataFrame
# import talib.abstract as ta
from ta import add_all_ta_features
from ta.utils import dropna

# --------------------------------



# 常用技术指标列表（从TOP 20优化结果中提取）
INDICATOR_LIST = [
    # 动量指标
    'momentum_rsi', 'momentum_stoch', 'momentum_stoch_rsi', 'momentum_tsi',
    'momentum_uo', 'momentum_ppo', 'momentum_ppo_hist',
    'momentum_kama', 'momentum_roc', 'momentum_ao',
    # 趋势指标
    'trend_macd', 'trend_macd_signal', 'trend_macd_diff',
    'trend_sma_fast', 'trend_sma_slow', 'trend_ema_fast', 'trend_ema_slow',
    'trend_cci', 'trend_aroon_up', 'trend_aroon_down', 'trend_aroon_ind',
    # 成交量指标
    'volume_mfi', 'volume_adi', 'volume_obv', 'volume_cmf', 'volume_vwap',
    # 波动率指标
    'volatility_atr', 'volatility_bbh', 'volatility_bbl',
]

class GodStra_hyperopt_fixinds(IStrategy):
    # 支持 --spaces all 优化的版本
    
    INTERFACE_VERSION: int = 3
    
    # 可优化的 buy 参数空间 - 使用完整指标列表
    buy_indicator = CategoricalParameter(
        INDICATOR_LIST,
        default='momentum_rsi', space='buy', optimize=True
    )
    buy_cross = CategoricalParameter(
        INDICATOR_LIST,
        default='volume_mfi', space='buy', optimize=True
    )
    buy_int = IntParameter(-1, 100, default=30, space='buy', optimize=True)
    buy_real = RealParameter(-1.1, 1.1, default=0.5, space='buy', optimize=True)
    buy_oper = CategoricalParameter(
        ['>', '<', '=', '>I', '<I', '>R', '<R'],
        default='>I', space='buy', optimize=True
    )
    
    # 可优化的 sell 参数空间 - 使用完整指标列表
    sell_indicator = CategoricalParameter(
        INDICATOR_LIST,
        default='momentum_rsi', space='sell', optimize=True
    )
    sell_cross = CategoricalParameter(
        INDICATOR_LIST,
        default='volume_mfi', space='sell', optimize=True
    )
    sell_int = IntParameter(-1, 100, default=70, space='sell', optimize=True)
    sell_real = RealParameter(-0.01, 1.01, default=0.7, space='sell', optimize=True)
    sell_oper = CategoricalParameter(
        ['>', '<', '=', '>I', '<I', '>R', '<R'],
        default='<I', space='sell', optimize=True
    )

    # 默认参数
    buy_params = {
        'buy-cross-0': 'volume_mfi',
        'buy-indicator-0': 'momentum_rsi',
        'buy-int-0': 30,
        'buy-oper-0': '<I',
        'buy-real-0': 30
    }

    # Sell hyperspace params:
    sell_params = {
        'sell-cross-0': 'volume_mfi',
        'sell-indicator-0': 'momentum_rsi',
        'sell-int-0': 70,
        'sell-oper-0': '>I',
        'sell-real-0': 70
    }

    # ROI table:
    minimal_roi = {
        "0": 0.01,
        "60": 0.05,
        "180": 0.10
    }

    # Stoploss:
    stoploss = -0.34549

    # Trailing stop:
    trailing_stop = True
    trailing_stop_positive = 0.22673
    trailing_stop_positive_offset = 0.2684
    trailing_only_offset_is_reached = True
    # Buy hypers
    timeframe = '5m'
    print('Add {\n\t"method": "AgeFilter",\n\t"min_days_listed": 30\n},\n to your pairlists in config (Under StaticPairList)')

    def dna_size(self, dct: dict):
        def int_from_str(st: str):
            str_int = ''.join([d for d in st if d.isdigit()])
            if str_int:
                return int(str_int)
            return -1  # in case if the parameter somehow doesn't have index
        return len({int_from_str(digit) for digit in dct.keys()})

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Add all ta features
        dataframe = dropna(dataframe)
        dataframe = add_all_ta_features(
            dataframe, open="open", high="high", low="low", close="close", volume="volume",
            fillna=True)
        # dataframe.to_csv("df.csv", index=True)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # 使用可优化参数
        conditions = []
        ind = dataframe[self.buy_indicator.value]
        cross = dataframe[self.buy_cross.value]
        int_val = self.buy_int.value
        real_val = self.buy_real.value
        oper = self.buy_oper.value
        
        if oper == ">":
            conditions.append(ind > cross)
        elif oper == "=":
            conditions.append(np.isclose(ind, cross))
        elif oper == "<":
            conditions.append(ind < cross)
        elif oper == "CA":
            conditions.append(qtpylib.crossed_above(ind, cross))
        elif oper == "CB":
            conditions.append(qtpylib.crossed_below(ind, cross))
        elif oper == ">I":
            conditions.append(ind > int_val)
        elif oper == "=I":
            conditions.append(ind == int_val)
        elif oper == "<I":
            conditions.append(ind < int_val)
        elif oper == ">R":
            conditions.append(ind > real_val)
        elif oper == "=R":
            conditions.append(np.isclose(ind, real_val))
        elif oper == "<R":
            conditions.append(ind < real_val)

        if conditions:
            dataframe.loc[
                reduce(lambda x, y: x & y, conditions),
                'enter_long'] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # 使用可优化参数
        conditions = []
        ind = dataframe[self.sell_indicator.value]
        cross = dataframe[self.sell_cross.value]
        int_val = self.sell_int.value
        real_val = self.sell_real.value
        oper = self.sell_oper.value
        
        if oper == ">":
            conditions.append(ind > cross)
        elif oper == "=":
            conditions.append(np.isclose(ind, cross))
        elif oper == "<":
            conditions.append(ind < cross)
        elif oper == "CA":
            conditions.append(qtpylib.crossed_above(ind, cross))
        elif oper == "CB":
            conditions.append(qtpylib.crossed_below(ind, cross))
        elif oper == ">I":
            conditions.append(ind > int_val)
        elif oper == "=I":
            conditions.append(ind == int_val)
        elif oper == "<I":
            conditions.append(ind < int_val)
        elif oper == ">R":
            conditions.append(ind > real_val)
        elif oper == "=R":
            conditions.append(np.isclose(ind, real_val))
        elif oper == "<R":
            conditions.append(ind < real_val)

        if conditions:
            dataframe.loc[
                reduce(lambda x, y: x & y, conditions),
                'exit_long'] = 1

        return dataframe
