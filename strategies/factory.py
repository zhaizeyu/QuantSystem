"""
策略工厂：根据配置名称创建买入/卖出策略实例。
买入：oversold_score_buy（超卖）；卖出：stop_loss_8pct_sell（止损）、trailing_take_profit_sell（移动止盈）、boll_upper_break_sell（突破上布林带）、two_day_no_profit_sell（两天不盈利卖出）。
"""
from typing import List

from strategies.buy.base import BaseBuyStrategy
from strategies.buy.boll_trend_pullback_buy import BollTrendPullbackBuyStrategy
from strategies.buy.oversold_factors import OversoldFactorsBuyStrategy
from strategies.buy.oversold_rebound_buy import OversoldReboundBuyStrategy
from strategies.sell.base import BaseSellStrategy
from strategies.sell.boll_upper_break_sell import BollUpperBreakSellStrategy
from strategies.sell.stop_loss_pct import StopLossPctSellStrategy
from strategies.sell.trailing_take_profit_sell import TrailingTakeProfitSellStrategy
from strategies.sell.two_day_no_profit_sell import TwoDayNoProfitSellStrategy


def _norm(name: str) -> str:
    return (name or "").strip().lower()


def create_buy_strategies(
    names: List[str],
    rsi_period: int = 6,
) -> List[BaseBuyStrategy]:
    """根据名称列表创建买入策略。支持 oversold_score_buy、oversold_rebound_buy、boll_trend_pullback_buy。"""
    out: List[BaseBuyStrategy] = []
    for n in names:
        n = _norm(n)
        if not n:
            continue
        if n == "oversold_score_buy":
            out.append(OversoldFactorsBuyStrategy(rsi_period=rsi_period))
        elif n == "oversold_rebound_buy":
            out.append(OversoldReboundBuyStrategy())
        elif n == "boll_trend_pullback_buy":
            out.append(BollTrendPullbackBuyStrategy())
    return out


def create_sell_strategies(
    names: List[str],
    slow_period: int = 20,
    stop_loss_pct: float = 8.0,
    trailing_trigger_pct: float = 2.0,
    trailing_pullback_pct: float = 5.0,
) -> List[BaseSellStrategy]:
    """根据名称列表创建卖出策略。支持 stop_loss_8pct_sell、boll_upper_break_sell、trailing_take_profit_sell、two_day_no_profit_sell。"""
    out: List[BaseSellStrategy] = []
    for n in names:
        n = _norm(n)
        if not n:
            continue
        if n == "stop_loss_8pct_sell":
            out.append(StopLossPctSellStrategy(stop_loss_pct=stop_loss_pct))
        elif n == "boll_upper_break_sell":
            out.append(BollUpperBreakSellStrategy(period=slow_period))
        elif n == "trailing_take_profit_sell":
            out.append(
                TrailingTakeProfitSellStrategy(
                    trigger_pct=trailing_trigger_pct,
                    pullback_pct=trailing_pullback_pct,
                )
            )
        elif n == "two_day_no_profit_sell":
            out.append(TwoDayNoProfitSellStrategy(min_hold_days=2))
    return out
