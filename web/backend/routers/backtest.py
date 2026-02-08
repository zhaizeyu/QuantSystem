"""回测 API：列表、详情（资金曲线 + 交割单）。"""
import json
from pathlib import Path

from fastapi import APIRouter, HTTPException
import pandas as pd

from core.config import BACKTEST_RESULTS_DIR

router = APIRouter()


def _df_to_records(df: pd.DataFrame):
    """转为 JSON 可序列化列表（NaN -> null，日期为字符串）。"""
    if df.empty:
        return []
    return json.loads(df.to_json(orient="records", date_format="iso", default_handler=str))


@router.get("/list")
def backtest_list():
    """列出所有回测记录文件（仅 trades CSV，不含 _equity）。"""
    path = BACKTEST_RESULTS_DIR.resolve()
    if not path.exists():
        return {"items": []}
    files = [
        f.name
        for f in path.iterdir()
        if f.suffix == ".csv" and "_equity" not in f.stem
    ]
    files.sort(reverse=True)
    return {"items": files}


@router.get("/detail/{result_id}")
def backtest_detail(result_id: str):
    """返回某次回测的资金曲线和完整交割单。result_id 为文件名（可含或不含 .csv）。"""
    base = result_id.replace(".csv", "").strip()
    if not base:
        raise HTTPException(status_code=400, detail="Invalid result_id")
    path = BACKTEST_RESULTS_DIR.resolve()
    trades_path = path / f"{base}.csv"
    equity_path = path / f"{base}_equity.csv"
    if not trades_path.exists():
        raise HTTPException(status_code=404, detail=f"Backtest result not found: {result_id}")
    try:
        trades_df = pd.read_csv(trades_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read trades CSV: {e}") from e
    trades = _df_to_records(trades_df)
    equity = []
    if equity_path.exists():
        try:
            eq_df = pd.read_csv(equity_path)
            equity = _df_to_records(eq_df)
        except Exception:
            equity = []
    return {"equity_curve": equity, "trades": trades}
