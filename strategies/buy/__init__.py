"""买入策略：仅输出 BUY 或 HOLD。"""
from strategies.buy.base import BaseBuyStrategy
from strategies.buy.boll_rebound_buy import BollReboundBuyStrategy
from strategies.buy.ma_cross import MACrossBuyStrategy
from strategies.buy.oversold_factors import OversoldFactorsBuyStrategy

__all__ = ["BaseBuyStrategy", "BollReboundBuyStrategy", "MACrossBuyStrategy", "OversoldFactorsBuyStrategy"]
