"""
卖出策略基类：只输出 SELL 或 HOLD，不输出 BUY。
"""
from abc import abstractmethod
from typing import Any

import pandas as pd

from core.types import Signal, SignalAction
from strategies.base import BaseStrategy


class BaseSellStrategy(BaseStrategy):
    """卖出策略：next() 仅返回 action in (SELL, HOLD)。"""

    @abstractmethod
    def next(
        self,
        current_bar: pd.Series,
        history_df: pd.DataFrame,
        current_position: int,
        **kwargs: Any,
    ) -> Signal:
        """返回 SELL 或 HOLD，不应返回 BUY。"""
        ...

    def _hold(self, reason: str = "hold") -> Signal:
        return Signal(action=SignalAction.HOLD, strength=0.0, reason=reason)
