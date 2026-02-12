"""买入后第一次红柱缩小卖出。"""
from typing import Any

import pandas as pd

from core.types import Signal, SignalAction
from strategies.indicators import macd
from strategies.sell.base import BaseSellStrategy


class FirstRedHistShrinkSellStrategy(BaseSellStrategy):
    """买入后，MACD 红柱首次较前一日缩小时触发卖出。"""

    name = "first_red_hist_shrink_sell"

    def next(
        self,
        current_bar: pd.Series,
        history_df: pd.DataFrame,
        current_position: int,
        **kwargs: Any,
    ) -> Signal:
        if current_position <= 0:
            return self._hold("空仓")

        entry_bar_index = kwargs.get("entry_bar_index")
        if entry_bar_index is None or int(entry_bar_index) < 0:
            return self._hold("无买入索引")
        entry_bar_index = int(entry_bar_index)

        current_idx = len(history_df) - 1
        if current_idx <= entry_bar_index:
            return self._hold("买入当日不判断")

        close_series = history_df["close"].astype(float)
        _, _, hist = macd(close_series)
        if len(hist) < 2:
            return self._hold("MACD 数据不足")

        current_hist = hist.iloc[current_idx]
        prev_hist = hist.iloc[current_idx - 1]
        if pd.isna(current_hist) or pd.isna(prev_hist):
            return self._hold("MACD 数据不足")

        # 红柱缩小：两天均为红柱，且当日柱体低于昨日
        if float(current_hist) > 0 and float(prev_hist) > 0 and float(current_hist) < float(prev_hist):
            # 仅在买入后第一次触发
            for j in range(entry_bar_index + 1, current_idx):
                h = hist.iloc[j]
                hp = hist.iloc[j - 1]
                if pd.isna(h) or pd.isna(hp):
                    continue
                if float(h) > 0 and float(hp) > 0 and float(h) < float(hp):
                    return self._hold("红柱缩小非首次")
            return Signal(
                action=SignalAction.SELL,
                strength=1.0,
                reason="买入后首次红柱缩小卖出",
                price=float(current_bar.get("close", 0.0)),
            )

        return self._hold("红柱未缩小")
