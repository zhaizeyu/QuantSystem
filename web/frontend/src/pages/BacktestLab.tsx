import { useEffect, useState } from "react";
import KlineChart from "../components/KlineChart";
import TradeTable from "../components/TradeTable";
import EquityCurve from "../components/EquityCurve";

const API = "/api";

export default function BacktestLab() {
  const [list, setList] = useState<string[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<{
    equity_curve: { date: string; equity: number }[];
    trades: Record<string, unknown>[];
  } | null>(null);
  const [kline, setKline] = useState<{ date: string; open: number; high: number; low: number; close: number; volume: number }[]>([]);
  const [symbol, setSymbol] = useState("AAPL");

  useEffect(() => {
    fetch(`${API}/backtest/list`)
      .then((r) => r.json())
      .then((d) => setList(d.items || []))
      .catch(() => setList([]));
  }, []);

  useEffect(() => {
    if (!selectedId) {
      setDetail(null);
      return;
    }
    fetch(`${API}/backtest/detail/${encodeURIComponent(selectedId)}`)
      .then((r) => r.json())
      .then(setDetail)
      .catch(() => setDetail(null));
  }, [selectedId]);

  useEffect(() => {
    if (!symbol) return;
    fetch(`${API}/market/kline/${symbol}`)
      .then((r) => r.json())
      .then((d) => setKline(d.data || []))
      .catch(() => setKline([]));
  }, [symbol]);

  const trades = detail?.trades ?? [];
  const equityCurve = detail?.equity_curve ?? [];
  const tradeMarkers =
    trades.length > 0 && kline.length > 0
      ? trades.map((t) => {
          const ts = (t.timestamp as string)?.slice(0, 10);
          const side = (t.side as string) ?? "";
          const reason = (t.entry_reason as string) || (t.exit_reason as string) || side;
          return { time: ts, side, reason };
        })
      : [];

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-slate-100">回测分析</h1>
      <div className="flex flex-wrap gap-4 items-center">
        <label className="text-slate-400 text-sm">
          回测记录
          <select
            className="ml-2 rounded bg-slate-800 border border-slate-600 text-slate-200 px-3 py-1.5"
            value={selectedId ?? ""}
            onChange={(e) => setSelectedId(e.target.value || null)}
          >
            <option value="">-- 选择一次回测 --</option>
            {list.map((id) => (
              <option key={id} value={id}>
                {id}
              </option>
            ))}
          </select>
        </label>
        <label className="text-slate-400 text-sm">
          K 线标的
          <input
            type="text"
            className="ml-2 rounded bg-slate-800 border border-slate-600 text-slate-200 px-3 py-1.5 w-24 font-mono"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value.trim() || "AAPL")}
          />
        </label>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 rounded-lg border border-slate-700 bg-slate-800/50 overflow-hidden">
          <div className="px-4 py-2 border-b border-slate-700 text-slate-400 text-sm">K 线 + 买卖标记</div>
          <div className="h-[400px]">
            <KlineChart data={kline} markers={tradeMarkers} />
          </div>
        </div>
        <div className="rounded-lg border border-slate-700 bg-slate-800/50 overflow-hidden">
          <div className="px-4 py-2 border-b border-slate-700 text-slate-400 text-sm">资金曲线</div>
          <div className="h-[400px]">
            <EquityCurve data={equityCurve} />
          </div>
        </div>
      </div>
      <div className="rounded-lg border border-slate-700 bg-slate-800/50 overflow-hidden">
        <div className="px-4 py-2 border-b border-slate-700 text-slate-400 text-sm">交割单</div>
        <TradeTable trades={trades} />
      </div>
    </div>
  );
}
