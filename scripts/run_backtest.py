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
from strategies.factory import create_buy_strategies, create_sell_strategies


def main() -> None:
    cfg = get_backtest_config()
    if not cfg.symbols:
        print("未找到标的：请确保 store/market_data/ 下存在 *_daily.csv 文件。")
        return

    buy_list = create_buy_strategies(
        cfg.buy_strategies,
        fast_period=cfg.fast_period,
        slow_period=cfg.slow_period,
        oversold_threshold=cfg.oversold_threshold,
    )
    sell_list = create_sell_strategies(
        cfg.sell_strategies,
        fast_period=cfg.fast_period,
        slow_period=cfg.slow_period,
        stop_loss_pct=cfg.stop_loss_pct,
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
        total_trades += len(result.trades)
        results_summary.append({
            "symbol": symbol,
            "trades": len(result.trades),
            "return_pct": result.total_return_pct,
            "max_dd_pct": result.max_drawdown_pct,
            "sharpe": result.sharpe_ratio,
            "final_capital": result.final_capital,
            "path": path.name,
        })
        print(
            f"  {symbol}: 成交 {len(result.trades)} 笔, "
            f"收益 {result.total_return_pct:.2f}%, 最大回撤 {result.max_drawdown_pct:.2f}%, "
            f"夏普比率 {result.sharpe_ratio:.2f}  -> {path.name}"
        )

    print("-" * 60)
    print(f"回测完成. 共 {len(cfg.symbols)} 只标的, 总成交 {total_trades} 笔.")
    for r in results_summary:
        print(f"  {r['symbol']}: {r['path']}")


if __name__ == "__main__":
    main()
