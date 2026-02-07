"""
核心数据模型 - 系统的"法律"。
定义 Bar、Signal、TradeRecord 等 Pydantic 模型。
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


# ----- Bar (K线数据) -----
class Bar(BaseModel):
    """K线单条数据，对应 CSV 列: date, open, high, low, close, volume, average, barCount"""
    date: str  # 日期字符串，如 YYYY-MM-DD
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
    average: Optional[float] = None
    barCount: Optional[int] = None


# ----- Signal (策略输出) -----
class SignalAction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class Signal(BaseModel):
    """策略输出：只接收数据，只输出信号"""
    action: SignalAction = SignalAction.HOLD
    strength: float = Field(ge=0.0, le=1.0, description="信号强度 0.0-1.0")
    reason: str = ""  # 关键：如 "MA5_Cross_Up_MA20"


# ----- TradeRecord (详细交割单 - 回测与实盘共用) -----
class TradeRecord(BaseModel):
    """详细交割单，包含开平仓原因、盈亏、ROI、成交后持仓等"""
    trade_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime
    symbol: str
    side: str  # BUY / SELL
    price: float  # 成交均价
    quantity: int  # 成交数量
    commission: float = 0.0  # 手续费
    strategy_name: str = ""
    entry_reason: str = ""  # 开仓原因，来自 Signal
    exit_reason: str = ""   # 平仓原因，如 "StopLoss", "TakeProfit"
    pnl: float = 0.0       # 平仓时盈亏金额，开仓为 0
    roi: float = 0.0       # 平仓时收益率 %
    holdings_after: int = 0  # 成交后该股剩余持仓

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
