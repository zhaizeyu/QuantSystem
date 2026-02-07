"""
全局配置：路径、IB、回测、实盘等。可修改项从 config/config.properties 读取，未配置则用下方默认值。
"""
from pathlib import Path

from core.properties_loader import get, get_float, get_int

# 项目根目录（QuantSystem）
ROOT = Path(__file__).resolve().parent.parent

# 数据中心 - 文件数据库（路径固定，不通过 properties 修改）
STORE = ROOT / "store"
MARKET_DATA_DIR = STORE / "market_data"
BACKTEST_RESULTS_DIR = STORE / "backtest_results"
LIVE_STATE_DIR = STORE / "live_state"

# IBKR 连接配置（来自 config.properties，未配置则用默认）
IB_HOST = get("ib.host") or "127.0.0.1"
IB_PORT = get_int("ib.port") or 7497
IB_CLIENT_ID = get_int("ib.client_id") or 1
IB_ACCOUNT_ID = get("ib.account_id") or ""

# 回测默认参数（来自 config.properties）
BACKTEST_INITIAL_CAPITAL = get_float("backtest.initial_capital") or 100_000.0
BACKTEST_SLIPPAGE_PCT = get_float("backtest.slippage_pct") or 0.001
BACKTEST_COMMISSION_PER_SHARE = get_float("backtest.commission_per_share") or 0.005

# 实盘状态导出间隔（秒）
LIVE_STATE_EXPORT_INTERVAL = get_int("live.state_export_interval") or 5
