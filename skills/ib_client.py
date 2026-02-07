"""
IBKR 客户端封装：连接、拉取日 K、下单、查持仓/账户。
"""
from typing import Any, Dict, List, Optional

import pandas as pd

from core.config import IB_ACCOUNT_ID, IB_CLIENT_ID, IB_HOST, IB_PORT


_ib = None  # 单例连接


def _get_ib():
    """延迟导入并返回 ib_insync 的 IB() 实例。"""
    global _ib
    if _ib is not None:
        return _ib
    try:
        from ib_insync import IB
        _ib = IB()
        return _ib
    except ImportError:
        return None


def connect() -> bool:
    """连接 TWS/Gateway，返回是否成功。"""
    ib = _get_ib()
    if ib is None:
        return False
    try:
        if ib.isConnected():
            return True
        ib.connect(IB_HOST, IB_PORT, clientId=IB_CLIENT_ID)
        return ib.isConnected()
    except Exception:
        return False


def disconnect() -> None:
    global _ib
    if _ib is not None:
        try:
            _ib.disconnect()
        except Exception:
            pass
        _ib = None


def fetch_daily_bars(symbol: str, duration: str = "1 M", bar_size: str = "1 day") -> Optional[pd.DataFrame]:
    """
    请求日 K 历史数据，返回 DataFrame，列: date, open, high, low, close, volume。
    若未安装 ib_insync 或连接失败则返回 None。
    """
    ib = _get_ib()
    if ib is None:
        return None
    if not ib.isConnected() and not connect():
        return None
    try:
        from ib_insync import Stock, util
        contract = Stock(symbol, "SMART", "USD")
        bars = ib.reqHistoricalData(
            contract,
            endDateTime="",
            durationStr=duration,
            barSizeSetting=bar_size,
            whatToShow="TRADES",
            useRTH=True,
            formatDate=1,
        )
        if not bars:
            return None
        df = util.df(bars)
        df = df.rename(columns={"date": "date"})
        if "Date" in df.columns and "date" not in df.columns:
            df = df.rename(columns={"Date": "date"})
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
        return df[["date", "open", "high", "low", "close", "volume"]]
    except Exception:
        return None


def get_account_summary() -> Dict[str, Any]:
    """获取账户摘要，返回可序列化字典（供写入 account.json）。"""
    ib = _get_ib()
    if ib is None or not ib.isConnected():
        return {}
    try:
        summary = ib.accountSummary(IB_ACCOUNT_ID or None)
        out = {}
        for s in summary:
            out[s.tag] = s.value
        return out
    except Exception:
        return {}


def get_positions() -> List[Dict[str, Any]]:
    """获取持仓列表，每项可序列化（供写入 positions.json）。"""
    ib = _get_ib()
    if ib is None or not ib.isConnected():
        return []
    try:
        positions = ib.positions(IB_ACCOUNT_ID or None)
        out = []
        for p in positions:
            out.append({
                "symbol": p.contract.symbol if p.contract else "",
                "quantity": p.position,
                "avgCost": p.avgCost,
                "marketPrice": 0.0,  # 需另行请求行情
            })
        return out
    except Exception:
        return []


def place_market_order(symbol: str, side: str, quantity: int) -> Optional[Any]:
    """市价单：side 为 BUY/SELL，返回 Order 或 None。"""
    ib = _get_ib()
    if ib is None or not ib.isConnected():
        return None
    try:
        from ib_insync import MarketOrder, Stock
        contract = Stock(symbol, "SMART", "USD")
        order = MarketOrder("BUY" if side.upper() == "BUY" else "SELL", quantity)
        trade = ib.placeOrder(contract, order)
        return trade
    except Exception:
        return None
