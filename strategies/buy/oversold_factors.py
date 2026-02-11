"""
超跌买入策略：收盘价小于 MA5/MA10/MA20，且 RSI<20，且 MACD 为绿柱时买入。
"""
from typing import Any

import pandas as pd

from core.types import Signal, SignalAction
from strategies.buy.base import BaseBuyStrategy
from strategies.indicators import macd, rsi_wilder


class OversoldFactorsBuyStrategy(BaseBuyStrategy):
    """
    超跌买入：同时满足以下三条才买入，否则不买。
    1. 收盘价 < MA5 且 收盘价 < MA10 且 收盘价 < MA20
    2. RSI < 20
    3. MACD 为绿柱（hist < 0）。
    """

    name = "oversold_score_buy"

    def __init__(self, rsi_period: int = 6) -> None:
        self.rsi_period = rsi_period

    def next(
        self,
        current_bar: pd.Series,
        history_df: pd.DataFrame,
        current_position: int,
        **kwargs: Any,
    ) -> Signal:
        # MACD(12,26,9) 需要约 35 根，MA20 需 20 根，RSI(6) 需 7 根
        min_bars = 36
        if history_df is None or len(history_df) < min_bars:
            return self._hold("数据不足")

        close = history_df["close"].astype(float)
        price = float(close.iloc[-1])

        ma5 = close.rolling(5, min_periods=5).mean()
        ma10 = close.rolling(10, min_periods=10).mean()
        ma20 = close.rolling(20, min_periods=20).mean()
        ma5_val = ma5.iloc[-1]
        ma10_val = ma10.iloc[-1]
        ma20_val = ma20.iloc[-1]

        if pd.isna(ma5_val) or pd.isna(ma10_val) or pd.isna(ma20_val):
            return self._hold("均线未就绪")
        if not (price < ma5_val and price < ma10_val and price < ma20_val):
            return self._hold("收盘价未同时小于MA5/MA10/MA20")

        rsi_series = rsi_wilder(close, self.rsi_period)
        rsi_val = rsi_series.iloc[-1]
        if pd.isna(rsi_val) or float(rsi_val) >= 20:
            return self._hold("RSI不小于20")

        _, _, hist_series = macd(close, 12, 26, 9)
        if len(hist_series) < 1:
            return self._hold("MACD未就绪")
        hist = float(hist_series.iloc[-1])
        if pd.isna(hist):
            return self._hold("MACD未就绪")
        if hist >= 0:
            return self._hold("MACD非绿柱不买")

        reason = (
            f"超跌买入(价<MA5/10/20 RSI<20 MACD绿柱)"
        )
        return Signal(action=SignalAction.BUY, strength=1.0, reason=reason)
