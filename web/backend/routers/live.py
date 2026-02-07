"""实盘快照 API：从 store/live_state 读取 JSON。"""
import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from core.config import LIVE_STATE_DIR

router = APIRouter()


def _read_json(name: str) -> dict:
    path = LIVE_STATE_DIR / name
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


@router.get("/snapshot")
def live_snapshot():
    """返回实盘账户状态：account.json + positions.json。"""
    account = _read_json("account.json")
    positions = _read_json("positions.json")
    return {"account": account, "positions": positions}
