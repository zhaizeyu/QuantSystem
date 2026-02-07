"""
超卖买入策略：四大因子加权打分，高分时发出买入信号。
- 均线压制 30% | RSI极值 30% | 布林带 20% | MACD动能衰竭 20%
"""
from typing import Any

import pandas as pd

from core.types import Signal, SignalAction
from strategies.buy.base import BaseBuyStrategy
from strategies.indicators import bollinger_bands, macd, rsi


class OversoldFactorsBuyStrategy(BaseBuyStrategy):
    """
    四大因子超卖买入：
    1. 均线压制 30%：同时跌破 MA5/10/20=100，跌破 MA5/10=60，跌破 MA5=30
    2. RSI-6 极值 30%：<20=100，<30=70，<40=30，<50=20
    3. 布林带 20%：跌破下轨=100，接近下轨(1%)=70，挤压且中轨下=50
    4. MACD 动能衰竭 20%：绿柱缩短=100，红柱变长=50，其余=0
    """

    name = "Oversold_Factors_Buy"

    # 因子权重
    W_MA = 0.30
    W_RSI = 0.30
    W_BB = 0.20
    W_MACD = 0.20

    # 综合得分阈值，超过则发出买入
    BUY_THRESHOLD = 55.0

    def __init__(
        self,
        buy_threshold: float = 55.0,
        bb_period: int = 20,
        rsi_period: int = 6,
    ) -> None:
        self.BUY_THRESHOLD = buy_threshold
        self.bb_period = bb_period
        self.rsi_period = rsi_period

    def next(
        self,
        current_bar: pd.Series,
        history_df: pd.DataFrame,
        current_position: int,
        **kwargs: Any,
    ) -> Signal:
        # MACD(12,26,9) 需要约 35 根，布林 20 根，RSI 6 根
        min_bars = 36
        if history_df is None or len(history_df) < min_bars:
            return self._hold("数据不足")

        close = history_df["close"].astype(float)
        # 均线
        ma5 = close.rolling(5, min_periods=5).mean()
        ma10 = close.rolling(10, min_periods=10).mean()
        ma20 = close.rolling(20, min_periods=20).mean()
        price = float(close.iloc[-1])

        # 1. 均线压制得分 0~100
        ma_score = self._score_ma_suppression(price, ma5.iloc[-1], ma10.iloc[-1], ma20.iloc[-1])

        # 2. RSI-6 得分 0~100
        rsi_series = rsi(close, self.rsi_period)
        rsi_val = rsi_series.iloc[-1]
        if pd.isna(rsi_val):
            rsi_score = 0
        else:
            rsi_score = self._score_rsi(float(rsi_val))

        # 3. 布林带得分 0~100
        middle, upper, lower = bollinger_bands(close, self.bb_period, 2.0)
        m, u, l = middle.iloc[-1], upper.iloc[-1], lower.iloc[-1]
        if pd.isna(m) or pd.isna(l):
            bb_score = 0
        else:
            bb_score = self._score_bollinger(price, float(m), float(u), float(l), middle, lower, close)

        # 4. MACD 动能衰竭得分 0~100
        dif_series, _, hist_series = macd(close, 12, 26, 9)
        dif = dif_series.iloc[-1]
        hist = hist_series.iloc[-1]
        hist_prev = hist_series.iloc[-2] if len(hist_series) >= 2 else None
        if pd.isna(dif) or pd.isna(hist) or pd.isna(hist_prev):
            macd_score = 0
        else:
            macd_score = self._score_macd(float(dif), float(hist), float(hist_prev))

        # 加权综合
        total = self.W_MA * ma_score + self.W_RSI * rsi_score + self.W_BB * bb_score + self.W_MACD * macd_score
        if total < self.BUY_THRESHOLD:
            return self._hold(f"综合得分{total:.0f}未达阈值{self.BUY_THRESHOLD:.0f}")

        strength = min(1.0, (total - self.BUY_THRESHOLD) / 30.0)
        reason = (
            f"超卖得分{total:.0f} "
            f"(均线{ma_score:.0f} RSI{rsi_score:.0f} 布林{bb_score:.0f} MACD{macd_score:.0f})"
        )
        return Signal(action=SignalAction.BUY, strength=strength, reason=reason)

    def _score_ma_suppression(
        self,
        price: float,
        ma5: float,
        ma10: float,
        ma20: float,
    ) -> float:
        if pd.isna(ma5) or pd.isna(ma10) or pd.isna(ma20):
            return 0.0
        below5 = price < ma5
        below10 = price < ma10
        below20 = price < ma20
        if below5 and below10 and below20:
            return 100.0
        if below5 and below10:
            return 60.0
        if below5:
            return 30.0
        return 0.0

    def _score_rsi(self, rsi_val: float) -> float:
        if rsi_val < 20:
            return 100.0
        if rsi_val < 30:
            return 70.0
        if rsi_val < 40:
            return 30.0
        if rsi_val < 50:
            return 20.0
        return 0.0

    def _score_bollinger(
        self,
        price: float,
        middle: float,
        upper: float,
        lower: float,
        middle_series: pd.Series,
        lower_series: pd.Series,
        close_series: pd.Series,
    ) -> float:
        if lower <= 0:
            return 0.0
        # 跌破下轨
        if price <= lower:
            return 100.0
        # 接近下轨 1%
        if price <= lower * 1.01:
            return 70.0
        # 挤压且在中轨下：带宽较窄（如 <5%）且价格低于中轨
        width = (upper - lower) / (middle + 1e-10)
        if width < 0.05 and price < middle:
            return 50.0
        return 0.0

    def _score_macd(self, dif: float, hist: float, hist_prev: float) -> float:
        """绿柱缩短=100，红柱变长=50，其余=0。"""
        # 绿柱缩短：dif<0 且 hist > 昨日hist（柱变短）
        if dif < 0 and hist > hist_prev:
            return 100.0
        # 红柱变长：dif>0 且 hist > 昨日hist
        if dif > 0 and hist > hist_prev:
            return 50.0
        return 0.0
