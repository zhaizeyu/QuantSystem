"""
策略工厂：根据配置名称创建买入/卖出策略实例。
买入：oversold_score_buy（超卖）；卖出：stop_loss_8pct_sell（止损）、boll_upper_break_sell（突破上布林带）。
"""
from typing import List

from strategies.buy.base import BaseBuyStrategy
from strategies.buy.oversold_factors import OversoldFactorsBuyStrategy
from strategies.sell.base import BaseSellStrategy
from strategies.sell.boll_upper_break_sell import BollUpperBreakSellStrategy
from strategies.sell.stop_loss_pct import StopLossPctSellStrategy


def _norm(name: str) -> str:
    return (name or "").strip().lower()


def create_buy_strategies(
    names: List[str],
    fast_period: int = 5,
    slow_period: int = 20,
    oversold_threshold: float = 55.0,
) -> List[BaseBuyStrategy]:
    """根据名称列表创建买入策略。仅支持 oversold_score_buy。"""
    out: List[BaseBuyStrategy] = []
    for n in names:
        n = _norm(n)
        if not n:
            continue
        if n == "oversold_score_buy":
            out.append(OversoldFactorsBuyStrategy(buy_threshold=oversold_threshold))
    return out


def create_sell_strategies(
    names: List[str],
    fast_period: int = 5,
    slow_period: int = 20,
    stop_loss_pct: float = 8.0,
) -> List[BaseSellStrategy]:
    """根据名称列表创建卖出策略。支持 stop_loss_8pct_sell、boll_upper_break_sell。"""
    out: List[BaseSellStrategy] = []
    for n in names:
        n = _norm(n)
        if not n:
            continue
        if n == "stop_loss_8pct_sell":
            out.append(StopLossPctSellStrategy(stop_loss_pct=stop_loss_pct))
        elif n == "boll_upper_break_sell":
            out.append(BollUpperBreakSellStrategy(period=slow_period))
    return out
