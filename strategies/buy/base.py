"""
买入策略基类：只输出 BUY 或 HOLD，不输出 SELL。
"""
from abc import abstractmethod
from typing import Any

import pandas as pd

from core.types import Signal, SignalAction
from strategies.base import BaseStrategy


class BaseBuyStrategy(BaseStrategy):
    """买入策略：next() 仅返回 action in (BUY, HOLD)。"""

    @abstractmethod
    def next(
        self,
        current_bar: pd.Series,
        history_df: pd.DataFrame,
        current_position: int,
        **kwargs: Any,
    ) -> Signal:
        """返回 BUY 或 HOLD，不应返回 SELL。"""
        ...

    def _hold(self, reason: str = "hold") -> Signal:
        return Signal(action=SignalAction.HOLD, strength=0.0, reason=reason)
