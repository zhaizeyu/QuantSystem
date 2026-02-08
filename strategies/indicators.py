"""
技术指标：RSI、布林带、MACD 等，供策略使用。
"""
import pandas as pd


def rsi_wilder(close: pd.Series, period: int = 14) -> pd.Series:
    """Wilder 平滑 RSI(period)，与东财等主流软件一致。首期用 period 内涨跌的简单平均，之后用 Wilder 递推。"""
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)
    out = pd.Series(index=close.index, dtype=float)
    if len(close) < period + 1:
        return out
    avg_g = gain.iloc[1 : period + 1].mean()
    avg_l = loss.iloc[1 : period + 1].mean()
    for i in range(period, len(close)):
        if i > period:
            avg_g = (avg_g * (period - 1) + gain.iloc[i]) / period
            avg_l = (avg_l * (period - 1) + loss.iloc[i]) / period
        rs = avg_g / (avg_l + 1e-10)
        out.iloc[i] = 100 - (100 / (1 + rs))
    return out


def bollinger_bands(close: pd.Series, period: int = 20, num_std: float = 2.0) -> tuple:
    """布林带：返回 (middle, upper, lower)，均为 Series。"""
    middle = close.rolling(period, min_periods=period).mean()
    std = close.rolling(period, min_periods=period).std()
    upper = middle + num_std * std
    lower = middle - num_std * std
    return middle, upper, lower


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> tuple:
    """MACD：返回 (dif, dea, hist)，均为 Series。"""
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    dif = ema_fast - ema_slow
    dea = dif.ewm(span=signal, adjust=False).mean()
    hist = dif - dea
    return dif, dea, hist


def _wilder_smooth(series: pd.Series, period: int) -> pd.Series:
    """Wilder 平滑：首值为 period 内和，之后递推 S = S_prev*(period-1)/period + value."""
    out = pd.Series(index=series.index, dtype=float)
    if len(series) < period:
        return out
    out.iloc[period - 1] = series.iloc[:period].sum()
    for i in range(period, len(series)):
        out.iloc[i] = out.iloc[i - 1] * (period - 1) / period + series.iloc[i]
    return out


def adx(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14,
) -> tuple:
    """
    平均趋向指标 ADX，用于过滤假突破。
    返回 (adx_series, plus_di, minus_di)，均为 Series。
    ADX > 25 且上升表示真趋势；突破时 ADX < 20 多为假突破。
    """
    if len(high) < period + 2:
        n = len(high)
        return (
            pd.Series(index=high.index, dtype=float),
            pd.Series(index=high.index, dtype=float),
            pd.Series(index=high.index, dtype=float),
        )
    prev_high = high.shift(1)
    prev_low = low.shift(1)
    prev_close = close.shift(1)
    tr = pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    up_move = high - prev_high
    down_move = prev_low - low
    plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0.0)
    minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0.0)
    tr_smooth = _wilder_smooth(tr, period)
    plus_dm_smooth = _wilder_smooth(plus_dm, period)
    minus_dm_smooth = _wilder_smooth(minus_dm, period)
    plus_di = 100 * plus_dm_smooth / (tr_smooth + 1e-10)
    minus_di = 100 * minus_dm_smooth / (tr_smooth + 1e-10)
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di + 1e-10)
    adx_series = _wilder_smooth(dx, period)
    return adx_series, plus_di, minus_di
