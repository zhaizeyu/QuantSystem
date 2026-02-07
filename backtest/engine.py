"""
回测引擎：加载数据、逐 bar 运行策略、模拟撮合、生成交割单并持久化。
"""
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd

from core.config import (
    BACKTEST_COMMISSION_PER_SHARE,
    BACKTEST_INITIAL_CAPITAL,
    BACKTEST_RESULTS_DIR,
    BACKTEST_SLIPPAGE_PCT,
)
from core.types import SignalAction, TradeRecord
from data.loader import get_bars
from strategies.buy.base import BaseBuyStrategy
from strategies.sell.base import BaseSellStrategy


@dataclass
class BacktestResult:
    """回测结果：交割单、资金曲线、绩效摘要"""
    trades: List[TradeRecord] = field(default_factory=list)
    equity_curve: pd.DataFrame = field(default_factory=pd.DataFrame)  # date, equity
    total_return_pct: float = 0.0
    max_drawdown_pct: float = 0.0
    sharpe_ratio: float = 0.0
    initial_capital: float = 0.0
    final_capital: float = 0.0


class BacktestEngine:
    """
    回测引擎：支持多策略。
    买入：buy_strategies 全部命中才买入；卖出：sell_strategies 任一命中即卖出。
    可传入列表或单个策略（单个会自动包装为列表）。
    """

    def __init__(
        self,
        buy_strategy: Optional[BaseBuyStrategy] = None,
        sell_strategy: Optional[BaseSellStrategy] = None,
        buy_strategies: Optional[List[BaseBuyStrategy]] = None,
        sell_strategies: Optional[List[BaseSellStrategy]] = None,
        symbol: str = "",
        initial_capital: float = BACKTEST_INITIAL_CAPITAL,
        slippage_pct: float = BACKTEST_SLIPPAGE_PCT,
        commission_per_share: float = BACKTEST_COMMISSION_PER_SHARE,
        strategy_name: Optional[str] = None,
    ) -> None:
        self.buy_strategies = buy_strategies if buy_strategies is not None else ([buy_strategy] if buy_strategy is not None else [])
        self.sell_strategies = sell_strategies if sell_strategies is not None else ([sell_strategy] if sell_strategy is not None else [])
        if not self.buy_strategies or not self.sell_strategies:
            raise ValueError("至少各提供一个买入策略与一个卖出策略")
        self.symbol = symbol.upper()
        self.initial_capital = initial_capital
        self.slippage_pct = slippage_pct
        self.commission_per_share = commission_per_share
        names = "_".join(s.name for s in self.buy_strategies) + "_" + "_".join(s.name for s in self.sell_strategies)
        self.strategy_name = strategy_name or names

    def run(
        self,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> BacktestResult:
        """执行回测，返回 BacktestResult。"""
        df = get_bars(self.symbol, start=start, end=end)
        if df.empty or len(df) < 30:
            return BacktestResult(initial_capital=self.initial_capital, final_capital=self.initial_capital)

        cash = self.initial_capital
        position = 0
        position_avg_cost = 0.0
        position_entry_reason = ""
        trades: List[TradeRecord] = []
        equity_by_date: List[tuple] = []

        for i in range(len(df)):
            row = df.iloc[i]
            date_str = str(row["date"])
            close = float(row["close"])
            history = df.iloc[: i + 1]

            # 买入：全部策略都出 BUY 才触发
            buy_signals = [
                s.next(current_bar=row, history_df=history, current_position=position)
                for s in self.buy_strategies
            ]
            buy_triggered = all(s.action == SignalAction.BUY for s in buy_signals)
            buy_reason = " | ".join(s.reason for s in buy_signals) if buy_signals else ""

            # 卖出：任一策略出 SELL 即触发（传入成本与现价供止损等使用）
            sell_signals = [
                s.next(
                    current_bar=row,
                    history_df=history,
                    current_position=position,
                    position_avg_cost=position_avg_cost,
                    current_price=close,
                )
                for s in self.sell_strategies
            ]
            sell_triggered = any(s.action == SignalAction.SELL for s in sell_signals)
            sell_reason = next((s.reason for s in sell_signals if s.action == SignalAction.SELL), "") or "信号"

            if buy_triggered and position >= 0:
                # 买入：按收盘价 + 滑点，扣手续费
                fill_price = close * (1 + self.slippage_pct)
                size = int(cash / fill_price)  # 简单全仓一股
                if size <= 0:
                    pass
                else:
                    commission = size * self.commission_per_share
                    cost = size * fill_price + commission
                    if cost <= cash:
                        cash -= cost
                        if position == 0:
                            position_avg_cost = fill_price
                            position_entry_reason = buy_reason
                        else:
                            position_avg_cost = (position_avg_cost * position + fill_price * size) / (position + size)
                        position += size
                        rec = TradeRecord(
                            timestamp=datetime.strptime(date_str, "%Y-%m-%d"),
                            symbol=self.symbol,
                            side="买入",
                            price=fill_price,
                            quantity=size,
                            commission=commission,
                            strategy_name=self.strategy_name,
                            entry_reason=buy_reason,
                            exit_reason="",
                            pnl=0.0,
                            roi=0.0,
                            holdings_after=position,
                        )
                        trades.append(rec)

            elif sell_triggered and position > 0:
                # 卖出：按收盘价 - 滑点，计算 pnl/roi
                fill_price = close * (1 - self.slippage_pct)
                size = position  # 简单全平
                commission = size * self.commission_per_share
                cash += size * fill_price - commission
                gross_pnl = (fill_price - position_avg_cost) * size
                pnl = gross_pnl - commission
                roi = (pnl / (position_avg_cost * size)) * 100.0 if position_avg_cost else 0.0
                position = 0
                rec = TradeRecord(
                    timestamp=datetime.strptime(date_str, "%Y-%m-%d"),
                    symbol=self.symbol,
                    side="卖出",
                    price=fill_price,
                    quantity=size,
                    commission=commission,
                    strategy_name=self.strategy_name,
                    entry_reason=position_entry_reason,
                    exit_reason=sell_reason,
                    pnl=pnl,
                    roi=roi,
                    holdings_after=0,
                )
                trades.append(rec)
                position_avg_cost = 0.0
                position_entry_reason = ""

            # 资金曲线：当日收盘后权益
            equity = cash + position * close
            equity_by_date.append((date_str, equity))

        final_capital = cash + position * float(df.iloc[-1]["close"])
        equity_df = pd.DataFrame(equity_by_date, columns=["date", "equity"])

        # 绩效
        total_return_pct = (final_capital - self.initial_capital) / self.initial_capital * 100.0
        max_dd = 0.0
        peak = self.initial_capital
        for _, eq in equity_by_date:
            if eq > peak:
                peak = eq
            dd = (peak - eq) / peak * 100.0 if peak else 0.0
            if dd > max_dd:
                max_dd = dd
        sharpe = 0.0
        if len(equity_df) >= 2:
            equity_df["ret"] = equity_df["equity"].pct_change().fillna(0)
            std = equity_df["ret"].std()
            if std and std > 0:
                sharpe = (equity_df["ret"].mean() / std) * (252 ** 0.5)  # 年化

        result = BacktestResult(
            trades=trades,
            equity_curve=equity_df,
            total_return_pct=total_return_pct,
            max_drawdown_pct=max_dd,
            sharpe_ratio=sharpe,
            initial_capital=self.initial_capital,
            final_capital=final_capital,
        )
        return result

    def run_and_save(
        self,
        start: Optional[str] = None,
        end: Optional[str] = None,
        result_id: Optional[str] = None,
    ) -> Tuple[BacktestResult, Path]:
        """执行回测并将交割单保存到 store/backtest_results，返回 (result, csv_path)。"""
        result = self.run(start=start, end=end)
        BACKTEST_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        suffix = datetime.now().strftime("%Y%m%d_%H%M%S") if not result_id else result_id
        filename = f"bt_{self.strategy_name}_{suffix}.csv"
        path = BACKTEST_RESULTS_DIR / filename
        columns = [
            "trade_id", "timestamp", "symbol", "side", "price", "quantity",
            "commission", "strategy_name", "entry_reason", "exit_reason",
            "pnl", "roi", "holdings_after",
        ]
        rows = [
            {
                "trade_id": t.trade_id,
                "timestamp": t.timestamp.isoformat(),
                "symbol": t.symbol,
                "side": t.side,
                "price": t.price,
                "quantity": t.quantity,
                "commission": t.commission,
                "strategy_name": t.strategy_name,
                "entry_reason": t.entry_reason,
                "exit_reason": t.exit_reason,
                "pnl": t.pnl,
                "roi": t.roi,
                "holdings_after": t.holdings_after,
            }
            for t in result.trades
        ]
        pd.DataFrame(rows, columns=columns).to_csv(path, index=False)
        # 同时保存资金曲线供 Web 展示
        equity_path = path.with_name(path.stem + "_equity.csv")
        if not result.equity_curve.empty:
            result.equity_curve.to_csv(equity_path, index=False)
        else:
            pd.DataFrame(columns=["date", "equity"]).to_csv(equity_path, index=False)
        return result, path
