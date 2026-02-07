"""
卖出策略：MA5 下穿 MA20（死叉）时发出 SELL。
"""
from typing import Any

import pandas as pd

from core.types import Signal, SignalAction
from strategies.sell.base import BaseSellStrategy


class MACrossSellStrategy(BaseSellStrategy):
    """均线死叉卖出：MA5 下穿 MA20 时卖出。"""

    name = "MA_Cross_Sell"
    fast_period: int = 5
    slow_period: int = 20

    def __init__(self, fast_period: int = 5, slow_period: int = 20) -> None:
        self.fast_period = fast_period
        self.slow_period = slow_period

    def next(
        self,
        current_bar: pd.Series,
        history_df: pd.DataFrame,
        current_position: int,
        **kwargs: Any,
    ) -> Signal:
        # 需要至少 slow_period+1 根 K 线，否则 ma_slow.iloc[-2] 为 NaN（MA20 首值在第 20 根）
        if history_df is None or len(history_df) < self.slow_period + 1:
            return self._hold("数据不足")

        close = history_df["close"].astype(float)
        ma_fast = close.rolling(self.fast_period, min_periods=self.fast_period).mean()
        ma_slow = close.rolling(self.slow_period, min_periods=self.slow_period).mean()
        prev_fast, curr_fast = ma_fast.iloc[-2], ma_fast.iloc[-1]
        prev_slow, curr_slow = ma_slow.iloc[-2], ma_slow.iloc[-1]
        if pd.isna(prev_slow) or pd.isna(curr_slow):
            return self._hold("均线数据不足")
        prev_fast, curr_fast = float(prev_fast), float(curr_fast)
        prev_slow, curr_slow = float(prev_slow), float(curr_slow)

        # 死叉：前一根 fast >= slow，当前 fast < slow
        if prev_fast >= prev_slow and curr_fast < curr_slow:
            return Signal(
                action=SignalAction.SELL,
                strength=min(1.0, (curr_slow - curr_fast) / (curr_fast + 1e-8) * 10),
                reason="MA5下穿MA20死叉",
            )
        return self._hold("持仓")
