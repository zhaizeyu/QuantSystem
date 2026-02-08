"""移动止盈：止盈价按「昨日及之前」最高价计算，仅在次日生效，当天不触发卖出。"""
from typing import Any

import pandas as pd

from core.types import Signal, SignalAction
from strategies.sell.base import BaseSellStrategy


class TrailingTakeProfitSellStrategy(BaseSellStrategy):
    """
    固定回落止盈，次日生效：用「买入日至昨日」的最高价算出止盈价，仅在今日检查是否触及。
    止盈价 = 昨日及之前最高价 × (1 - pullback_pct%)，今日最低价触及则卖；当天买入当天不生效。
    """
    name = "trailing_take_profit_sell"

    def __init__(self, pullback_pct: float = 5.0, **kwargs: Any) -> None:
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
        # 用「昨日收盘前」的最高价算止盈价，今日才生效，避免当天买卖同一天触发
        high_prev = kwargs.get("high_since_entry_prev")
        if high_prev is None or high_prev <= 0:
            return self._hold("止盈价未就绪(需昨日最高价)")
        exit_price = high_prev * (1.0 - self.pullback_pct / 100.0)
        low = float(current_bar.get("low", 0))
        if low <= exit_price:
            return Signal(
                action=SignalAction.SELL,
                strength=1.0,
                reason="移动止盈(固定回落%.1f%%)" % self.pullback_pct,
                price=exit_price,
            )
        return self._hold("未触及止盈价")
