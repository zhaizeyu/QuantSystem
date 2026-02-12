"""买入次日 DIF 低于买入当日 DIF 则卖出。"""
from typing import Any

import pandas as pd

from core.types import Signal, SignalAction
from strategies.indicators import macd
from strategies.sell.base import BaseSellStrategy


class DifNextDayWeakerSellStrategy(BaseSellStrategy):
    """买入后下一交易日，若 DIF 低于买入日 DIF 则卖出。"""

    name = "dif_next_day_weaker_sell"

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
        if current_idx != entry_bar_index + 1:
            return self._hold("非买入次日")

        close_series = history_df["close"].astype(float)
        dif, _, _ = macd(close_series)
        entry_dif = dif.iloc[entry_bar_index]
        current_dif = dif.iloc[current_idx]
        if pd.isna(entry_dif) or pd.isna(current_dif):
            return self._hold("DIF 数据不足")

        if float(current_dif) < float(entry_dif):
            return Signal(
                action=SignalAction.SELL,
                strength=1.0,
                reason="买入次日DIF走弱卖出",
                price=float(current_bar.get("close", 0.0)),
            )
        return self._hold("买入次日DIF未走弱")
