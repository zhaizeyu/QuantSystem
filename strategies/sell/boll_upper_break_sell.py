"""突破上布林带卖出：收盘价站上布林带上轨时卖出。"""
from typing import Any
import pandas as pd
from core.types import Signal, SignalAction
from strategies.sell.base import BaseSellStrategy
from strategies.indicators import bollinger_bands


class BollUpperBreakSellStrategy(BaseSellStrategy):
    name = "boll_upper_break_sell"

    def __init__(self, period: int = 20, num_std: float = 2.0) -> None:
        self.period = period
        self.num_std = num_std

    def next(
        self,
        current_bar: pd.Series,
        history_df: pd.DataFrame,
        current_position: int,
        **kwargs: Any,
    ) -> Signal:
        if current_position <= 0:
            return self._hold("空仓")
        close_series = history_df["close"].astype(float)
        # history_df 已含当日 K 线，直接用其算布林带，避免重复拼接导致上轨被抬高
        if len(close_series) < self.period:
            return self._hold("数据不足")
        _, upper, _ = bollinger_bands(close_series, period=self.period, num_std=self.num_std)
        current_close = float(current_bar.get("close", 0))
        upper_last = float(upper.iloc[-1])
        if current_close >= upper_last:
            return Signal(
                action=SignalAction.SELL,
                strength=1.0,
                reason="突破上布林带",
            )
        return self._hold("未破上轨")
