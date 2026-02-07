"""买入策略：仅输出 BUY 或 HOLD。"""
from strategies.buy.base import BaseBuyStrategy
from strategies.buy.ma_cross import MACrossBuyStrategy
from strategies.buy.oversold_factors import OversoldFactorsBuyStrategy

__all__ = ["BaseBuyStrategy", "MACrossBuyStrategy", "OversoldFactorsBuyStrategy"]
