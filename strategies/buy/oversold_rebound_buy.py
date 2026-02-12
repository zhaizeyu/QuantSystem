"""
超卖反弹买入策略：RSI 超卖拐头 + MACD 绿柱缩短 + DIF 转折向上。
"""
from typing import Any

import pandas as pd

from core.types import Signal, SignalAction
from strategies.buy.base import BaseBuyStrategy
from strategies.indicators import macd, rsi_wilder


class OversoldReboundBuyStrategy(BaseBuyStrategy):
    """
    超卖反弹买入：三条件同时满足才买入。
    1) RSI(14) 超卖且拐头：RSI_t < 30 且 RSI_t > RSI_{t-1}
    2) MACD 绿柱缩短：Hist_t < 0 且 Hist_t > Hist_{t-1}
    3) DIF 转折向上：DIF_t > DIF_{t-1} 且 DIF_{t-1} <= DIF_{t-2}
    """

    name = "oversold_rebound_buy"

    def __init__(
        self,
        rsi_period: int = 14,
        rsi_oversold_threshold: float = 30.0,
        macd_fast: int = 12,
        macd_slow: int = 26,
        macd_signal: int = 9,
    ) -> None:
        self.rsi_period = rsi_period
        self.rsi_oversold_threshold = rsi_oversold_threshold
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal

    def next(
        self,
        current_bar: pd.Series,
        history_df: pd.DataFrame,
        current_position: int,
        **kwargs: Any,
    ) -> Signal:
        _ = current_bar, current_position, kwargs
        min_bars = max(self.rsi_period + 2, self.macd_slow + self.macd_signal + 5)
        if history_df is None or len(history_df) < min_bars:
            return self._hold("数据不足")

        close = history_df["close"].astype(float)

        # 1) RSI 超卖 + 拐头
        rsi_series = rsi_wilder(close, self.rsi_period)
        if len(rsi_series) < 2:
            return self._hold("RSI未就绪")

        rsi_t = rsi_series.iloc[-1]
        rsi_prev = rsi_series.iloc[-2]
        if pd.isna(rsi_t) or pd.isna(rsi_prev):
            return self._hold("RSI未就绪")
        if not (float(rsi_t) < self.rsi_oversold_threshold and float(rsi_t) > float(rsi_prev)):
            return self._hold("RSI未满足超卖拐头")

        # 2) MACD 绿柱缩短
        dif_series, _, hist_series = macd(close, self.macd_fast, self.macd_slow, self.macd_signal)
        if len(hist_series) < 2 or len(dif_series) < 3:
            return self._hold("MACD未就绪")

        hist_t = hist_series.iloc[-1]
        hist_prev = hist_series.iloc[-2]
        if pd.isna(hist_t) or pd.isna(hist_prev):
            return self._hold("MACD未就绪")
        if not (float(hist_t) < 0 and float(hist_t) > float(hist_prev)):
            return self._hold("MACD绿柱未缩短")

        # 3) DIF 向上转折（Hook）
        dif_t = dif_series.iloc[-1]
        dif_prev = dif_series.iloc[-2]
        dif_prev2 = dif_series.iloc[-3]
        if pd.isna(dif_t) or pd.isna(dif_prev) or pd.isna(dif_prev2):
            return self._hold("DIF未就绪")
        if not (float(dif_t) > float(dif_prev) and float(dif_prev) <= float(dif_prev2)):
            return self._hold("DIF未形成向上转折")

        return Signal(
            action=SignalAction.BUY,
            strength=1.0,
            reason="超卖反弹买入(RSI超卖拐头+MACD绿柱缩短+DIF向上转折)",
        )
