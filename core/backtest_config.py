"""
回测配置：从 config/config.properties 的 default.* 读取，简洁格式。
"""
import re
from dataclasses import dataclass, field
from typing import List, Optional

from core.config import MARKET_DATA_DIR
from core.properties_loader import get, get_float, get_int


def _default_symbols() -> List[str]:
    """当 default.symbols 为空时：扫描 market_data 下所有 *_daily.csv。"""
    if not MARKET_DATA_DIR.exists():
        return []
    symbols = []
    for f in MARKET_DATA_DIR.iterdir():
        if f.suffix.lower() == ".csv" and f.stem.endswith("_daily"):
            symbols.append(f.stem.replace("_daily", "").upper())
    return sorted(symbols)


def _parse_symbols(value: Optional[str]) -> List[str]:
    if value is None or value.strip() == "":
        return _default_symbols()
    return [s.strip().upper() for s in value.split(",") if s.strip()]


def _parse_list(value: Optional[str]) -> List[str]:
    """逗号分隔列表（支持英文、全角逗号），去空，小写。"""
    if value is None or value.strip() == "":
        return []
    parts = re.split(r"[,，]", value)
    return [s.strip().lower() for s in parts if s.strip()]


@dataclass
class BacktestConfig:
    """回测配置：来自 default.*。"""

    symbols: List[str] = field(default_factory=list)
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    initial_capital: float = 100_000.0
    slippage_pct: float = 0.001
    commission_per_share: float = 0.005
    strategy_name: str = "Default"
    buy_strategies: List[str] = field(default_factory=list)
    sell_strategies: List[str] = field(default_factory=list)
    slow_period: int = 20
    rsi_period: int = 6
    stop_loss_pct: float = 8.0
    trailing_trigger_pct: float = 2.0
    trailing_pullback_pct: float = 5.0

    def __post_init__(self) -> None:
        if not self.symbols:
            self.symbols = _default_symbols()
        if self.start_date == "":
            self.start_date = None
        if self.end_date == "":
            self.end_date = None


def get_backtest_config(
    symbols: Optional[List[str]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    initial_capital: Optional[float] = None,
    slippage_pct: Optional[float] = None,
    commission_per_share: Optional[float] = None,
    strategy_name: Optional[str] = None,
    buy_strategies: Optional[List[str]] = None,
    sell_strategies: Optional[List[str]] = None,
    slow_period: Optional[int] = None,
    rsi_period: Optional[int] = None,
    stop_loss_pct: Optional[float] = None,
) -> BacktestConfig:
    """从 config 的 default.* 加载；传入参数可覆盖。"""
    buy_list = _parse_list(get("default.buy"))
    sell_list = _parse_list(get("default.sell"))
    if not buy_list:
        buy_list = ["oversold_score_buy"]
    if not sell_list:
        sell_list = ["stop_loss_8pct_sell"]

    cfg = BacktestConfig(
        symbols=_parse_symbols(get("default.symbols")),
        start_date=get("default.start_date") or None,
        end_date=get("default.end_date") or None,
        initial_capital=get_float("default.initial_capital") or 100_000.0,
        slippage_pct=get_float("default.slippage_pct") or 0.001,
        commission_per_share=get_float("default.commission_per_share") or 0.005,
        strategy_name=get("default.strategy_name") or "Default",
        buy_strategies=buy_list,
        sell_strategies=sell_list,
        slow_period=get_int("default.slow_period") or 20,
        rsi_period=get_int("default.rsi_period") or 6,
        stop_loss_pct=get_float("default.stop_loss_pct") or 8.0,
        trailing_trigger_pct=get_float("default.trailing_trigger_pct") or 2.0,
        trailing_pullback_pct=get_float("default.trailing_pullback_pct") or 5.0,
    )
    if symbols is not None:
        cfg.symbols = [s.upper() for s in symbols]
    if start_date is not None:
        cfg.start_date = start_date
    if end_date is not None:
        cfg.end_date = end_date
    if initial_capital is not None:
        cfg.initial_capital = initial_capital
    if slippage_pct is not None:
        cfg.slippage_pct = slippage_pct
    if commission_per_share is not None:
        cfg.commission_per_share = commission_per_share
    if strategy_name is not None:
        cfg.strategy_name = strategy_name
    if stop_loss_pct is not None:
        cfg.stop_loss_pct = stop_loss_pct
    if buy_strategies is not None:
        cfg.buy_strategies = [s.strip().lower() for s in buy_strategies if s and str(s).strip()]
    if sell_strategies is not None:
        cfg.sell_strategies = [s.strip().lower() for s in sell_strategies if s and str(s).strip()]
    if slow_period is not None:
        cfg.slow_period = slow_period
    if rsi_period is not None:
        cfg.rsi_period = rsi_period
    return cfg
