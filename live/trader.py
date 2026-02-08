"""
实盘/模拟盘守护进程：维护 IB 连接、拉 K 线、跑策略、风控、下单、导出状态。
"""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.config import LIVE_STATE_DIR, LIVE_STATE_EXPORT_INTERVAL
from data.loader import append_bars, get_bars
from skills import ib_client
from strategies.buy import OversoldFactorsBuyStrategy
from strategies.sell import StopLossPctSellStrategy


def export_state() -> None:
    """将账户与持仓写入 store/live_state/*.json。"""
    LIVE_STATE_DIR.mkdir(parents=True, exist_ok=True)
    account = ib_client.get_account_summary()
    positions = ib_client.get_positions()
    with open(LIVE_STATE_DIR / "account.json", "w", encoding="utf-8") as f:
        json.dump(account, f, indent=2, ensure_ascii=False)
    with open(LIVE_STATE_DIR / "positions.json", "w", encoding="utf-8") as f:
        json.dump(positions, f, indent=2, ensure_ascii=False)


def run_once(symbol: str = "AAPL") -> None:
    """单次循环：拉 K 线、更新 CSV、跑策略、风控、可选下单、导出状态。"""
    if not ib_client.connect():
        return
    # 拉取最新日 K 并追加
    df = ib_client.fetch_daily_bars(symbol)
    if df is not None and not df.empty:
        append_bars(symbol, df)
    # 策略（此处仅示例：不实际下单，仅导出状态）
    buy_strategy = OversoldFactorsBuyStrategy(rsi_period=6)
    sell_strategy = StopLossPctSellStrategy(stop_loss_pct=10.0)
    bars = get_bars(symbol)
    if len(bars) >= 20:
        last = bars.iloc[-1]
        buy_strategy.next(last, bars, 0)
        sell_strategy.next(last, bars, 0)
        # 风控示例：单笔亏损不超过总资金 1% 等，此处省略
        # 若需下单可调用 ib_client.place_market_order(...)
    export_state()


def main() -> None:
    """主循环：每分钟拉 K 线跑策略，每 5 秒导出状态。"""
    symbol = "AAPL"
    last_bar_minute = -1
    last_export = 0.0
    while True:
        try:
            now = time.time()
            if int(now // 60) != last_bar_minute:
                last_bar_minute = int(now // 60)
                run_once(symbol)
            if now - last_export >= LIVE_STATE_EXPORT_INTERVAL:
                last_export = now
                if ib_client.connect():
                    export_state()
        except KeyboardInterrupt:
            break
        except Exception:
            pass
        time.sleep(1)
    ib_client.disconnect()


if __name__ == "__main__":
    main()
