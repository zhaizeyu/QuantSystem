"""
布林带 + 均线 + 成交量 趋势跟随：挤压→开口→贴轨→破位。
适用 TSLA、NVDA、BTC 等高波动单边行情，只做全仓买入。
- 买点1：挤压后放量突破上轨（开口确认 + ADX 过滤）
- 买点2：趋势中回踩 MA5 或上轨-中轨 1/2 处，不破 MA10
"""
from typing import Any

import pandas as pd

from core.types import Signal, SignalAction
from strategies.buy.base import BaseBuyStrategy
from strategies.indicators import adx, bollinger_bands


class BollTrendPullbackBuyStrategy(BaseBuyStrategy):
    """
    口诀：缩口不动，开口冲；贴着上轨是行踪；跌破均线才放松。
    1. 蓄势：带宽收缩（挤压）→ 观望
    2. 启动：挤压后收盘突破上轨 + 上轨上拐/下轨下拐 + MA20 上行 + ADX>25 → 突破买
    3. 发酵：趋势中回踩 MA5 或 (上轨+中轨)/2，不破 MA10 → 回踩买
    带宽过大（历史极值）时不追，等回踩。买入即全仓。
    """

    name = "boll_trend_pullback_buy"

    def __init__(
        self,
        boll_period: int = 20,
        num_std: float = 2.0,
        adx_period: int = 14,
        adx_min: float = 25.0,
        squeeze_lookback: int = 20,
        squeeze_quantile: float = 0.25,
        breakout_squeeze_days: int = 10,
        band_extreme_quantile: float = 0.95,
        band_extreme_lookback: int = 60,
        trend_days: int = 5,
        trend_above_ma10_min_days: int = 3,
        pullback_near_ma5_tol: float = 0.015,
        pullback_near_midpoint_tol: float = 0.02,
        slope_lookback: int = 3,
    ) -> None:
        self.boll_period = boll_period
        self.num_std = num_std
        self.adx_period = adx_period
        self.adx_min = adx_min
        self.squeeze_lookback = squeeze_lookback
        self.squeeze_quantile = squeeze_quantile
        self.breakout_squeeze_days = breakout_squeeze_days
        self.band_extreme_quantile = band_extreme_quantile
        self.band_extreme_lookback = band_extreme_lookback
        self.trend_days = trend_days
        self.trend_above_ma10_min_days = trend_above_ma10_min_days
        self.pullback_near_ma5_tol = pullback_near_ma5_tol
        self.pullback_near_midpoint_tol = pullback_near_midpoint_tol
        self.slope_lookback = slope_lookback

    def next(
        self,
        current_bar: pd.Series,
        history_df: pd.DataFrame,
        current_position: int,
        **kwargs: Any,
    ) -> Signal:
        need = max(
            self.boll_period + self.slope_lookback,
            self.band_extreme_lookback,
            self.adx_period + 5,
        ) + 5
        if history_df is None or len(history_df) < need:
            return self._hold("数据不足")

        close_series = history_df["close"].astype(float)
        high_series = history_df["high"].astype(float)
        low_series = history_df["low"].astype(float)
        middle, upper, lower = bollinger_bands(
            close_series, self.boll_period, self.num_std
        )
        ma20 = middle
        ma5 = close_series.rolling(5, min_periods=5).mean()
        ma10 = close_series.rolling(10, min_periods=10).mean()

        bandwidth = upper - lower
        adx_series, _, _ = adx(high_series, low_series, close_series, self.adx_period)

        close = float(close_series.iloc[-1])
        current_low = float(current_bar.get("low", close))
        up = float(upper.iloc[-1])
        mid = float(middle.iloc[-1])
        ma5_val = float(ma5.iloc[-1]) if not pd.isna(ma5.iloc[-1]) else None
        ma10_val = float(ma10.iloc[-1]) if not pd.isna(ma10.iloc[-1]) else None

        # 当前带宽、斜率
        bw_now = float(bandwidth.iloc[-1])
        up_now = float(upper.iloc[-1])
        up_old = float(upper.iloc[-1 - self.slope_lookback])
        low_now = float(lower.iloc[-1])
        low_old = float(lower.iloc[-1 - self.slope_lookback])
        ma20_now = float(ma20.iloc[-1])
        ma20_old = float(ma20.iloc[-1 - 5])
        adx_now = float(adx_series.iloc[-1]) if not pd.isna(adx_series.iloc[-1]) else 0.0
        adx_old = (
            float(adx_series.iloc[-1 - self.slope_lookback])
            if len(adx_series) > self.slope_lookback
            else 0.0
        )

        # ---------- 买点1：突破进场（挤压后开口 + 站稳上轨） ----------
        # 近期是否出现过挤压：过去 N 天内带宽曾处于过去 20 天的下 25%
        bw_last_20 = bandwidth.iloc[-self.squeeze_lookback :]
        bw_last_10 = bandwidth.iloc[-self.breakout_squeeze_days :]
        if len(bw_last_20) >= self.squeeze_lookback and len(bw_last_10) >= 1:
            p25 = float(bw_last_20.quantile(self.squeeze_quantile))
            squeeze_occurred = float(bw_last_10.min()) <= p25
        else:
            squeeze_occurred = False

        # 带宽未处于历史极值（不追高）
        bw_roll = bandwidth.iloc[-self.band_extreme_lookback :]
        if len(bw_roll) >= self.band_extreme_lookback:
            p95 = float(bw_roll.quantile(self.band_extreme_quantile))
            band_not_extreme = bw_now <= p95
        else:
            band_not_extreme = True

        if (
            squeeze_occurred
            and close >= up * 0.998
            and up_now > up_old
            and low_now < low_old
            and ma20_now > ma20_old
            and band_not_extreme
            and adx_now >= self.adx_min
            and adx_now > adx_old
        ):
            return Signal(
                action=SignalAction.BUY,
                strength=1.0,
                reason="布林趋势突破(挤压后开口+站稳上轨+ADX确认)",
            )

        # ---------- 买点2：回踩进场（趋势中回踩 MA5 或 上轨-中轨 1/2，不破 MA10） ----------
        if ma10_val is None or ma5_val is None or mid <= 0:
            return self._hold("均线未就绪")

        # 趋势状态：近 N 日收盘多在 MA10 之上，或曾站上过上轨
        closes_last = close_series.iloc[-self.trend_days :]
        ma10_last = ma10.iloc[-self.trend_days :]
        upper_last = upper.iloc[-self.trend_days :]
        above_ma10_count = (closes_last.values > ma10_last.values).sum()
        ever_above_upper = (closes_last.values >= upper_last.values).any()
        trend_ok = (
            above_ma10_count >= self.trend_above_ma10_min_days or ever_above_upper
        )

        if not trend_ok:
            return self._hold("未形成趋势")

        # 必须在均线之上：不破 MA10（收盘与最低价），且在中轨之上（强趋势很少回踩到 MA20）
        if close < ma10_val or current_low < ma10_val * 0.995 or close <= mid:
            return self._hold("破MA10或在中轨下")

        midpoint_upper_mid = (up + mid) / 2.0
        near_ma5 = (
            ma5_val > 0
            and (1 - self.pullback_near_ma5_tol) * ma5_val
            <= close
            <= (1 + self.pullback_near_ma5_tol) * ma5_val
        )
        near_midpoint = (
            (1 - self.pullback_near_midpoint_tol) * midpoint_upper_mid
            <= close
            <= (1 + self.pullback_near_midpoint_tol) * midpoint_upper_mid
        )

        if near_ma5 or near_midpoint:
            return Signal(
                action=SignalAction.BUY,
                strength=1.0,
                reason="布林趋势回踩(MA5或上中轨1/2+不破MA10)",
            )

        return self._hold("无买点")
