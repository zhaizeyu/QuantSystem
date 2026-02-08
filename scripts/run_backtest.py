#!/usr/bin/env python3
"""
运行回测并写入 store/backtest_results。
从 config 读取买入/卖出策略列表：买入需全部命中，卖出任一命中即生效。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backtest.engine import BacktestEngine
from core.backtest_config import get_backtest_config
from core.config import BACKTEST_RESULTS_DIR
from strategies.factory import create_buy_strategies, create_sell_strategies


def main() -> None:
    cfg = get_backtest_config()
    BACKTEST_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    for old in BACKTEST_RESULTS_DIR.glob("bt_*.csv"):
        old.unlink(missing_ok=True)
    if not cfg.symbols:
        print("未找到标的：请确保 store/market_data/ 下存在 *_daily.csv 文件。")
        return

    buy_list = create_buy_strategies(cfg.buy_strategies, rsi_period=cfg.rsi_period)
    sell_list = create_sell_strategies(
        cfg.sell_strategies,
        slow_period=cfg.slow_period,
        stop_loss_pct=cfg.stop_loss_pct,
        trailing_trigger_pct=cfg.trailing_trigger_pct,
        trailing_pullback_pct=cfg.trailing_pullback_pct,
    )
    if not buy_list:
        print("未配置有效买入策略，请检查 backtest.buy_strategies。")
        return
    if not sell_list:
        print("未配置有效卖出策略，请检查 backtest.sell_strategies。")
        return

    print(f"回测配置: 标的={cfg.symbols}, 区间={cfg.start_date or '全区间'}~{cfg.end_date or '全区间'}")
    print(f"  买入策略(全部命中): {cfg.buy_strategies}, 卖出策略(任一命中): {cfg.sell_strategies}")
    print(f"  策略名={cfg.strategy_name}, 初始资金={cfg.initial_capital:,.0f}")
    print("-" * 60)

    total_trades = 0
    results_summary = []

    for symbol in cfg.symbols:
        engine = BacktestEngine(
            buy_strategies=buy_list,
            sell_strategies=sell_list,
            symbol=symbol,
            initial_capital=cfg.initial_capital,
            slippage_pct=cfg.slippage_pct,
            commission_per_share=cfg.commission_per_share,
            strategy_name=cfg.strategy_name,
        )
        result, path = engine.run_and_save(
            start=cfg.start_date,
            end=cfg.end_date,
        )
        sells = [t for t in result.trades if t.side == "卖出"]
        win_sells = sum(1 for t in sells if t.pnl > 0)
        total_sells = len(sells)
        win_rate_pct = (win_sells / total_sells * 100.0) if total_sells else 0.0

        total_trades += len(result.trades)
        ann_holding = result.annualized_return_holding_pct
        ann_str = f"{ann_holding:.2f}%" if ann_holding is not None else "N/A"
        results_summary.append({
            "symbol": symbol,
            "trades": len(result.trades),
            "win_rate_pct": win_rate_pct,
            "return_pct": result.total_return_pct,
            "max_dd_pct": result.max_drawdown_pct,
            "sharpe": result.sharpe_ratio,
            "holding_days": result.holding_days,
            "annualized_holding_pct": ann_holding,
            "final_capital": result.final_capital,
            "path": path.name,
        })
        print(
            f"  {symbol}: 成交 {len(result.trades)} 笔, 交易成功率 {win_rate_pct:.1f}% ({win_sells}/{total_sells}), "
            f"收益 {result.total_return_pct:.2f}%, 最大回撤 {result.max_drawdown_pct:.2f}%, "
            f"夏普 {result.sharpe_ratio:.2f}, 持仓天数 {result.holding_days}, 年化(按持仓) {ann_str}  -> {path.name}"
        )

    print("-" * 60)
    print(f"回测完成. 共 {len(cfg.symbols)} 只标的, 总成交 {total_trades} 笔.")
    for r in results_summary:
        ann = r.get("annualized_holding_pct")
        ann_s = f", 年化(按持仓) {ann:.2f}%" if ann is not None else ""
        print(f"  {r['symbol']}: 交易成功率 {r['win_rate_pct']:.1f}%, 持仓 {r['holding_days']} 天{ann_s}  -> {r['path']}")


if __name__ == "__main__":
    main()
