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
    equity_curve: pd.DataFrame = field(default_factory=pd.DataFrame)  # date, equity, in_position
    total_return_pct: float = 0.0
    max_drawdown_pct: float = 0.0
    sharpe_ratio: float = 0.0
    initial_capital: float = 0.0
    final_capital: float = 0.0
    holding_days: int = 0  # 有持仓的交易日天数
    annualized_return_holding_pct: Optional[float] = None  # 按持仓时间年化收益率(%)


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
        high_since_entry = 0.0  # 买入后到当日（含）经历过的最高价，供移动止盈等使用
        trades: List[TradeRecord] = []
        equity_by_date: List[tuple] = []

        for i in range(len(df)):
            row = df.iloc[i]
            date_str = str(row["date"])
            close = float(row["close"])
            history = df.iloc[: i + 1]
            if position > 0:
                high_since_entry = max(high_since_entry, float(row["high"]))

            # 买入：全部策略都出 BUY 才触发
            buy_signals = [
                s.next(current_bar=row, history_df=history, current_position=position)
                for s in self.buy_strategies
            ]
            buy_triggered = all(s.action == SignalAction.BUY for s in buy_signals)
            buy_reason = " | ".join(s.reason for s in buy_signals) if buy_signals else ""

            # 卖出：任一策略出 SELL 即触发（传入成本、现价、买入后最高价等）
            sell_signals = [
                s.next(
                    current_bar=row,
                    history_df=history,
                    current_position=position,
                    position_avg_cost=position_avg_cost,
                    current_price=close,
                    high_since_entry=high_since_entry,
                )
                for s in self.sell_strategies
            ]
            sell_triggered = any(s.action == SignalAction.SELL for s in sell_signals)
            # 多策略同时触发时，取报价最高的信号（优先止盈、避免误用止损价）
            sell_candidates = [s for s in sell_signals if s.action == SignalAction.SELL]
            best_sell_price: Optional[float] = None
            if sell_candidates:
                def _sell_price(sig):
                    p = getattr(sig, "price", None)
                    return float(p) if p is not None and p > 0 else 0.0
                best_sell = max(sell_candidates, key=_sell_price)
                sell_reason = best_sell.reason
                best_sell_price = getattr(best_sell, "price", None)
            else:
                sell_reason = "信号"

            if buy_triggered and position >= 0:
                # 买入：统一按收盘价
                fill_price = close
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
                        # 买入日不当日最高价计入，从下一根 bar 起再累加，避免“未真正涨过就触发移动止盈”
                        high_since_entry = 0.0
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
                # 卖出：多策略同时触发时已选报价最高者；价格限制在当日 bar 的 [low, high] 内
                raw_price = best_sell_price
                if raw_price is None or raw_price <= 0:
                    first_sell = next((s for s in sell_signals if s.action == SignalAction.SELL), None)
                    raw_price = getattr(first_sell, "price", None) if first_sell else None
                if raw_price is not None and raw_price > 0:
                    bar_low = float(row.get("low", close))
                    bar_high = float(row.get("high", close))
                    fill_price = max(bar_low, min(bar_high, raw_price))
                else:
                    fill_price = close
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
                high_since_entry = 0.0

            # 资金曲线：当日收盘后权益，以及当日是否持仓（用于仅按持仓期算绩效）
            equity = cash + position * close
            equity_by_date.append((date_str, equity, position > 0))

        final_capital = cash + position * float(df.iloc[-1]["close"])
        equity_df = pd.DataFrame(equity_by_date, columns=["date", "equity", "in_position"])

        # 总收益：按整体资金曲线（最终 vs 初始），与多笔交易一致
        total_return_pct = (final_capital - self.initial_capital) / self.initial_capital * 100.0
        # 持仓天数与按持仓时间年化收益
        holding_days = int(equity_df["in_position"].sum())
        annualized_return_holding_pct: Optional[float] = None
        if holding_days >= 1 and self.initial_capital > 0:
            total_return = (final_capital - self.initial_capital) / self.initial_capital
            # 年化 = (1 + 总收益率)^(252/持仓天数) - 1
            annualized_return_holding_pct = ((1.0 + total_return) ** (252.0 / holding_days) - 1.0) * 100.0
        # 最大回撤、夏普：仅使用有持仓日的序列
        eq_in = equity_df[equity_df["in_position"]].copy()
        if len(eq_in) < 2:
            max_dd = 0.0
            sharpe = 0.0
        else:
            max_dd = 0.0
            peak = float(eq_in["equity"].iloc[0])
            for _, row in eq_in.iterrows():
                eq = float(row["equity"])
                if eq > peak:
                    peak = eq
                dd = (peak - eq) / peak * 100.0 if peak else 0.0
                if dd > max_dd:
                    max_dd = dd
            eq_in = eq_in.copy()
            eq_in["ret"] = eq_in["equity"].pct_change().fillna(0)
            std = eq_in["ret"].std()
            sharpe = (eq_in["ret"].mean() / std) * (252 ** 0.5) if std and std > 0 else 0.0

        result = BacktestResult(
            trades=trades,
            equity_curve=equity_df,
            total_return_pct=total_return_pct,
            max_drawdown_pct=max_dd,
            sharpe_ratio=sharpe,
            initial_capital=self.initial_capital,
            final_capital=final_capital,
            holding_days=holding_days,
            annualized_return_holding_pct=annualized_return_holding_pct,
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
        filename = f"bt_{self.strategy_name}_{self.symbol}_{suffix}.csv"
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
