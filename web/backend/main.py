"""
FastAPI 入口：提供 K 线、回测列表/详情、实盘快照 API。
"""
from pathlib import Path
import sys

# 将项目根目录加入 path，便于导入 core / data
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from web.backend.routers import market, backtest, live

app = FastAPI(title="US Stock Quant System API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(market.router, prefix="/api/market", tags=["market"])
app.include_router(backtest.router, prefix="/api/backtest", tags=["backtest"])
app.include_router(live.router, prefix="/api/live", tags=["live"])


@app.get("/")
def root():
    return {"service": "QuantSystem API", "docs": "/docs"}
