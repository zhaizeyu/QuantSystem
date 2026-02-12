"""卖出策略：仅输出 SELL 或 HOLD。"""
from strategies.sell.base import BaseSellStrategy
from strategies.sell.boll_upper_break_sell import BollUpperBreakSellStrategy
from strategies.sell.stop_loss_pct import StopLossPctSellStrategy
from strategies.sell.trailing_take_profit_sell import TrailingTakeProfitSellStrategy
from strategies.sell.two_day_no_profit_sell import TwoDayNoProfitSellStrategy
from strategies.sell.dif_next_day_weaker_sell import DifNextDayWeakerSellStrategy
from strategies.sell.first_red_hist_shrink_sell import FirstRedHistShrinkSellStrategy

__all__ = [
    "BaseSellStrategy",
    "BollUpperBreakSellStrategy",
    "StopLossPctSellStrategy",
    "TrailingTakeProfitSellStrategy",
    "TwoDayNoProfitSellStrategy",
    "DifNextDayWeakerSellStrategy",
    "FirstRedHistShrinkSellStrategy",
]
