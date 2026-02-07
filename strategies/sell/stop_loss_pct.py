"""固定比例止损卖出：浮动亏损达到配置比例时卖出。"""
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
        position_avg_cost = kwargs.get("position_avg_cost") or 0.0
        current_price = kwargs.get("current_price")
        if current_price is None:
            current_price = float(current_bar.get("close", 0))
        if position_avg_cost <= 0:
            return self._hold("无成本价")
        pnl_pct = (current_price - position_avg_cost) / position_avg_cost * 100.0
        if pnl_pct <= -self.stop_loss_pct:
            return Signal(action=SignalAction.SELL, strength=1.0, reason=f"止损{self.stop_loss_pct}%")
        return self._hold("持仓")
