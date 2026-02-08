"""买入策略：仅输出 BUY 或 HOLD。"""
from strategies.buy.base import BaseBuyStrategy
from strategies.buy.boll_trend_pullback_buy import BollTrendPullbackBuyStrategy
from strategies.buy.oversold_factors import OversoldFactorsBuyStrategy

__all__ = ["BaseBuyStrategy", "BollTrendPullbackBuyStrategy", "OversoldFactorsBuyStrategy"]
