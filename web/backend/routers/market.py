"""K 线数据 API：从 store/market_data 读取 CSV 返回 OHLC。"""
from typing import Optional

from fastapi import APIRouter, HTTPException
import pandas as pd

from core.config import MARKET_DATA_DIR

router = APIRouter()


@router.get("/kline/{symbol}")
def get_kline(symbol: str, start: Optional[str] = None, end: Optional[str] = None):
    """返回 OHLC 数组，供前端 K 线图使用。"""
    path = MARKET_DATA_DIR / f"{symbol.upper()}_daily.csv"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"No data for symbol {symbol}")
    df = pd.read_csv(path)
    if "Date" in df.columns and "date" not in df.columns:
        df = df.rename(columns={"Date": "date"})
    df["date"] = pd.to_datetime(df["date"]).astype(str)
    if start:
        df = df[df["date"] >= start]
    if end:
        df = df[df["date"] <= end]
    df = df.sort_values("date").reset_index(drop=True)
    return {
        "symbol": symbol.upper(),
        "data": df[["date", "open", "high", "low", "close", "volume"]].to_dict(orient="records"),
    }
