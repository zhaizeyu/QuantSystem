"""
数据模块：读取/清洗 CSV，更新 CSV。
提供 get_bars(symbol, start, end) 与 update_history(symbol)。
"""
from pathlib import Path
from typing import Optional

import pandas as pd

from core.config import MARKET_DATA_DIR


def _csv_path(symbol: str) -> Path:
    """某标的对应的日 K CSV 路径"""
    return MARKET_DATA_DIR / f"{symbol.upper()}_daily.csv"


def get_bars(
    symbol: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> pd.DataFrame:
    """
    读取日 K CSV，返回 DataFrame。
    列约定: date, open, high, low, close, volume, average, barCount
    """
    path = _csv_path(symbol)
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)
    if df.empty:
        return df

    # 确保 date 为字符串，便于筛选
    if "date" not in df.columns and "Date" in df.columns:
        df = df.rename(columns={"Date": "date"})
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")

    if start:
        df = df[df["date"] >= start]
    if end:
        df = df[df["date"] <= end]

    return df.reset_index(drop=True)


def save_bars(symbol: str, df: pd.DataFrame) -> None:
    """将 DataFrame 写入 CSV（用于初次创建或全量覆盖）。"""
    path = _csv_path(symbol)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def append_bars(symbol: str, new_df: pd.DataFrame) -> None:
    """
    将新 K 线追加到现有 CSV，按 date 去重（保留新数据）。
    """
    path = _csv_path(symbol)
    if not path.exists():
        save_bars(symbol, new_df)
        return

    existing = pd.read_csv(path)
    if "Date" in existing.columns and "date" not in existing.columns:
        existing = existing.rename(columns={"Date": "date"})
    existing["date"] = pd.to_datetime(existing["date"]).astype(str)

    new_df = new_df.copy()
    if "date" not in new_df.columns and "Date" in new_df.columns:
        new_df = new_df.rename(columns={"Date": "date"})
    new_df["date"] = pd.to_datetime(new_df["date"]).astype(str)

    combined = pd.concat([existing, new_df], ignore_index=True)
    combined = combined.drop_duplicates(subset=["date"], keep="last")
    combined = combined.sort_values("date").reset_index(drop=True)
    save_bars(symbol, combined)


def update_history(symbol: str) -> None:
    """
    调用 skills.ib_client 获取最新日 K 并追加到 store/market_data/*.csv。
    若 ib_client 未实现则跳过（避免 Phase 1 强依赖）。
    """
    try:
        from skills.ib_client import fetch_daily_bars
        new_df = fetch_daily_bars(symbol)
        if new_df is not None and not new_df.empty:
            append_bars(symbol, new_df)
    except Exception:
        # Phase 1/2 可能尚未实现 ib_client，静默跳过
        pass
