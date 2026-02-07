"""
策略层：买入策略与卖出策略分目录归档。
- strategies/buy/  仅输出 BUY 或 HOLD
- strategies/sell/ 仅输出 SELL 或 HOLD
"""
from strategies.base import BaseStrategy
from strategies.buy import BaseBuyStrategy, MACrossBuyStrategy, OversoldFactorsBuyStrategy
from strategies.sell import BaseSellStrategy, MACrossSellStrategy

__all__ = [
    "BaseStrategy",
    "BaseBuyStrategy",
    "BaseSellStrategy",
    "MACrossBuyStrategy",
    "MACrossSellStrategy",
    "OversoldFactorsBuyStrategy",
]
