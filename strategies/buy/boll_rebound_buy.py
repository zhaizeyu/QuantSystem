"""
布林下轨回升买入：沿下轨下跌一段时间后，连续三天显著脱离下轨回升则买入。
"""
from typing import Any

import pandas as pd

from core.types import Signal, SignalAction
from strategies.buy.base import BaseBuyStrategy
from strategies.indicators import bollinger_bands


class BollReboundBuyStrategy(BaseBuyStrategy):
    """
    沿布林下轨下跌一段时间后，连续 3 天脱离下轨回升，且当日需显著离开下轨（占带宽一定比例）才买入，避免弱反弹即买导致亏损。
    """

    name = "boll_rebound_buy"

    def __init__(
        self,
        boll_period: int = 20,
        num_std: float = 2.0,
        along_lower_days: int = 5,
        rebound_days: int = 3,
        lower_touch_tol: float = 0.02,
        min_spread_pct_band: float = 0.40,
    ) -> None:
        self.boll_period = boll_period
        self.num_std = num_std
        self.along_lower_days = along_lower_days
        self.rebound_days = rebound_days
        self.lower_touch_tol = lower_touch_tol
        # 当日 (close - lower) 占 (upper - lower) 的最小比例，如 0.40 表示至少离开下轨 40% 带宽
        self.min_spread_pct_band = min_spread_pct_band

    def next(
        self,
        current_bar: pd.Series,
        history_df: pd.DataFrame,
        current_position: int,
        **kwargs: Any,
    ) -> Signal:
        min_bars = self.boll_period + self.along_lower_days + self.rebound_days
        if history_df is None or len(history_df) < min_bars:
            return self._hold("数据不足")

        close = history_df["close"].astype(float)
        middle, upper, lower = bollinger_bands(close, self.boll_period, self.num_std)
        spread = close - lower

        # 最近 rebound_days 天（含当日）脱离下轨回升：spread 严格递增
        n = self.rebound_days
        recent_spread = spread.iloc[-n:]
        if recent_spread.isna().any():
            return self._hold("布林未就绪")
        for i in range(n - 1):
            if spread.iloc[-n + i] >= spread.iloc[-n + i + 1]:
                return self._hold("未满足连续脱离下轨回升")
        if spread.iloc[-1] <= 0:
            return self._hold("尚未脱离下轨")

        # 显著离开下轨：当日 (close - lower) 占带宽 (upper - lower) 的比例不低于阈值
        band_width = float(upper.iloc[-1] - lower.iloc[-1])
        if band_width <= 0:
            return self._hold("带宽无效")
        spread_ratio = float(spread.iloc[-1]) / band_width
        if spread_ratio < self.min_spread_pct_band:
            return self._hold("脱离下轨不显著")

        # 此前 along_lower_days 天内至少有一段时间“沿下轨”（收盘接近或低于下轨）
        window = spread.iloc[-(n + self.along_lower_days) : -n]
        lower_vals = lower.iloc[-(n + self.along_lower_days) : -n]
        close_vals = close.iloc[-(n + self.along_lower_days) : -n]
        along_count = (close_vals <= lower_vals * (1 + self.lower_touch_tol)).sum()
        if along_count < 2:
            return self._hold("此前沿下轨不足")

        reason = f"布林下轨回升(连续{n}日脱离下轨且显著离开)"
        return Signal(action=SignalAction.BUY, strength=1.0, reason=reason)
