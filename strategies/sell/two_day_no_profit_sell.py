"""买入后满两天仍不盈利则卖出：按当日收盘价平仓。"""
from typing import Any

import pandas as pd

from core.types import Signal, SignalAction
from strategies.sell.base import BaseSellStrategy


class TwoDayNoProfitSellStrategy(BaseSellStrategy):
    """持仓满两天后若当前价不高于成本价，则触发卖出。"""

    name = "two_day_no_profit_sell"

    def __init__(self, min_hold_days: int = 2) -> None:
        self.min_hold_days = max(1, int(min_hold_days))

    def next(
        self,
        current_bar: pd.Series,
        history_df: pd.DataFrame,
        current_position: int,
        **kwargs: Any,
    ) -> Signal:
        if current_position <= 0:
            return self._hold("空仓")

        hold_days = int(kwargs.get("holding_days_since_entry") or 0)
        if hold_days < self.min_hold_days:
            return self._hold(f"持仓未满{self.min_hold_days}天")

        cost = float(kwargs.get("position_avg_cost") or 0.0)
        if cost <= 0:
            return self._hold("无成本价")

        current_price = kwargs.get("current_price")
        if current_price is None:
            current_price = float(current_bar.get("close", 0.0))
        current_price = float(current_price)

        if current_price <= cost:
            return Signal(
                action=SignalAction.SELL,
                strength=1.0,
                reason=f"持仓满{self.min_hold_days}天未盈利卖出",
                price=current_price,
            )
        return self._hold("已盈利继续持有")
