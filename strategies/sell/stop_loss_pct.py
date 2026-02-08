"""固定比例止损卖出：盘中触及止损价则按止损价卖出，单笔亏损不超过配置比例。"""
from typing import Any
import pandas as pd
from core.types import Signal, SignalAction
from strategies.sell.base import BaseSellStrategy


class StopLossPctSellStrategy(BaseSellStrategy):
    name = "stop_loss_pct_sell"

    def __init__(self, stop_loss_pct: float = 8.0) -> None:
        self.stop_loss_pct = stop_loss_pct

    def next(self, current_bar: pd.Series, history_df: pd.DataFrame, current_position: int, **kwargs: Any) -> Signal:
        if current_position <= 0:
            return self._hold("空仓")
        cost = kwargs.get("position_avg_cost") or 0.0
        current_price = kwargs.get("current_price")
        if current_price is None:
            current_price = float(current_bar.get("close", 0))
        if cost <= 0:
            return self._hold("无成本价")
        stop_price = cost * (1 - self.stop_loss_pct / 100.0)
        low = float(current_bar.get("low", current_price))
        if low <= stop_price:
            return Signal(
                action=SignalAction.SELL,
                strength=1.0,
                reason=f"止损{self.stop_loss_pct}%",
                price=stop_price,
            )
        return self._hold("持仓")
