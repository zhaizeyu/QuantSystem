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
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);
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
      setDetailError(null);
      return;
    }
    setDetailLoading(true);
    setDetailError(null);
    fetch(`${API}/backtest/detail/${encodeURIComponent(selectedId)}`)
      .then((r) => {
        if (!r.ok) throw new Error(r.status === 404 ? "未找到该回测记录" : `请求失败 ${r.status}`);
        return r.json();
      })
      .then((d) => {
        const tradesList = Array.isArray(d.trades) ? d.trades : [];
        const equityList = Array.isArray(d.equity_curve) ? d.equity_curve : [];
        setDetail({ equity_curve: equityList, trades: tradesList });
        setDetailError(null);
        // 根据交割单中的标的自动更新 K 线标的（取首笔交易的 symbol，多标的时以首笔为准）
        if (tradesList.length > 0 && tradesList[0].symbol) {
          const sym = String(tradesList[0].symbol).trim();
          if (sym) setSymbol(sym);
        }
      })
      .catch((e) => {
        setDetail(null);
        setDetailError(e instanceof Error ? e.message : "加载失败");
      })
      .finally(() => setDetailLoading(false));
  }, [selectedId]);

  useEffect(() => {
    if (!symbol) return;
    fetch(`${API}/market/kline/${symbol}`)
      .then((r) => r.json())
      .then((d) => setKline(d.data || []))
      .catch(() => setKline([]));
  }, [symbol]);

  const trades = Array.isArray(detail?.trades) ? detail!.trades : [];
  const equityCurve = Array.isArray(detail?.equity_curve) ? detail!.equity_curve : [];
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
        {detailError && <span className="text-red-400 text-sm">{detailError}</span>}
        {detailLoading && selectedId && <span className="text-slate-500 text-sm">加载中…</span>}
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
          <div className="px-4 py-2 border-b border-slate-700 text-slate-400 text-sm">K 线 + MA / BOLL / 买卖标记 · 副图 RSI / MACD</div>
          <div className="min-h-[520px] overflow-auto">
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
