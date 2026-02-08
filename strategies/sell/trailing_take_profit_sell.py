"""移动止盈：盈利超过成本 2% 后进入监控，止盈价 = max((成本+最高价)/2, 最高价×95%) 且不低于成本，盘中触及则按该价卖出。"""
from typing import Any
import pandas as pd
from core.types import Signal, SignalAction
from strategies.sell.base import BaseSellStrategy


class TrailingTakeProfitSellStrategy(BaseSellStrategy):
    name = "trailing_take_profit_sell"

    def __init__(self, trigger_pct: float = 2.0, pullback_pct: float = 5.0) -> None:
        self.trigger_pct = trigger_pct
        self.pullback_pct = pullback_pct

    def next(
        self,
        current_bar: pd.Series,
        history_df: pd.DataFrame,
        current_position: int,
        **kwargs: Any,
    ) -> Signal:
        if current_position <= 0:
            return self._hold("空仓")
        cost = kwargs.get("position_avg_cost") or 0.0
        current_price = kwargs.get("current_price")
        if current_price is None:
            current_price = float(current_bar.get("close", 0))
        high_since_entry = kwargs.get("high_since_entry")
        if high_since_entry is None or high_since_entry <= 0:
            high_since_entry = float(current_bar.get("high", current_price))
        if cost <= 0:
            return self._hold("无成本价")
        # 用「买入后最高价」判断是否曾达到监控阈值，避免回落后误退出监控
        if high_since_entry < cost * (1 + self.trigger_pct / 100.0):
            return self._hold("未达监控阈值")
        high = high_since_entry
        low = float(current_bar.get("low", current_price))
        midpoint = (cost + high) * 0.5
        trail_price = high * (1 - self.pullback_pct / 100.0)
        exit_price = max(cost, max(midpoint, trail_price))  # 止盈价 = max((成本+最高价)/2, 最高价×95%)，且不低于成本
        if low <= exit_price:
            return Signal(
                action=SignalAction.SELL,
                strength=1.0,
                reason="移动止盈",
                price=exit_price,
            )
        return self._hold("未触及止盈价")
