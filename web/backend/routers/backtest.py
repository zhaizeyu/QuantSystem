"""回测 API：列表、详情（资金曲线 + 交割单）。"""
from pathlib import Path

from fastapi import APIRouter, HTTPException
import pandas as pd

from core.config import BACKTEST_RESULTS_DIR

router = APIRouter()


@router.get("/list")
def backtest_list():
    """列出所有回测记录文件（仅 trades CSV，不含 _equity）。"""
    if not BACKTEST_RESULTS_DIR.exists():
        return {"items": []}
    files = [
        f.name
        for f in BACKTEST_RESULTS_DIR.iterdir()
        if f.suffix == ".csv" and "_equity" not in f.stem
    ]
    files.sort(reverse=True)
    return {"items": files}


@router.get("/detail/{result_id}")
def backtest_detail(result_id: str):
    """返回某次回测的资金曲线和完整交割单。result_id 为文件名（可含或不含 .csv）。"""
    base = result_id.replace(".csv", "")
    trades_path = BACKTEST_RESULTS_DIR / f"{base}.csv"
    equity_path = BACKTEST_RESULTS_DIR / f"{base}_equity.csv"
    if not trades_path.exists():
        raise HTTPException(status_code=404, detail=f"Backtest result not found: {result_id}")
    try:
        trades_df = pd.read_csv(trades_path)
    except Exception:
        trades_df = pd.DataFrame()
    if not trades_df.empty and "timestamp" in trades_df.columns:
        trades_df["timestamp"] = pd.to_datetime(trades_df["timestamp"]).astype(str)
    trades = trades_df.to_dict(orient="records")
    equity = []
    if equity_path.exists():
        eq_df = pd.read_csv(equity_path)
        equity = eq_df.to_dict(orient="records")
    return {"equity_curve": equity, "trades": trades}
