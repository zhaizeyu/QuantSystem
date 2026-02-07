"""
策略基类：只接收数据，只输出信号，不直接下单。
"""
from abc import ABC, abstractmethod
from typing import Any

import pandas as pd

from core.types import Signal


class BaseStrategy(ABC):
    """策略抽象基类。输入：当前 K 线、历史 DataFrame、当前持仓；输出：Signal。"""

    name: str = "BaseStrategy"

    @abstractmethod
    def next(
        self,
        current_bar: pd.Series,
        history_df: pd.DataFrame,
        current_position: int,
        **kwargs: Any,
    ) -> Signal:
        """
        根据当前 bar、历史数据、当前持仓量计算并返回信号。
        - current_position > 0 表示多头持仓数量，< 0 表示空头（若支持）。
        """
        ...
