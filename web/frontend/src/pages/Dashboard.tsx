import { useEffect, useState } from "react";

const API = "/api";

interface AccountSnapshot {
  NetLiquidation?: number;
  UnrealizedPnL?: number;
  [key: string]: unknown;
}

interface PositionRow {
  symbol?: string;
  quantity?: number;
  avgCost?: number;
  marketPrice?: number;
  unrealizedPnL?: number;
  [key: string]: unknown;
}

export default function Dashboard() {
  const [account, setAccount] = useState<AccountSnapshot>({});
  const [positions, setPositions] = useState<PositionRow[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function fetchSnapshot() {
      try {
        const res = await fetch(`${API}/live/snapshot`);
        const data = await res.json();
        if (cancelled) return;
        setAccount(data.account || {});
        const pos = data.positions;
        setPositions(Array.isArray(pos) ? pos : pos?.positions ?? []);
      } catch {
        if (!cancelled) {
          setAccount({});
          setPositions([]);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    fetchSnapshot();
    const t = setInterval(fetchSnapshot, 5000);
    return () => {
      cancelled = true;
      clearInterval(t);
    };
  }, []);

  if (loading) {
    return <div className="text-slate-400">加载实盘状态...</div>;
  }

  const netLiq = account.NetLiquidation ?? account.netLiquidation ?? 0;
  const unrealized = account.UnrealizedPnL ?? account.unrealizedPnL ?? 0;

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-slate-100">实盘仪表盘</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-4">
          <div className="text-slate-400 text-sm">总资产</div>
          <div className="text-2xl font-mono text-slate-100">
            ${typeof netLiq === "number" ? netLiq.toLocaleString("en-US", { minimumFractionDigits: 2 }) : netLiq}
          </div>
        </div>
        <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-4">
          <div className="text-slate-400 text-sm">日内浮动盈亏</div>
          <div className={`text-2xl font-mono ${unrealized >= 0 ? "text-emerald-400" : "text-red-400"}`}>
            ${typeof unrealized === "number" ? unrealized.toLocaleString("en-US", { minimumFractionDigits: 2 }) : unrealized}
          </div>
        </div>
      </div>
      <div className="rounded-lg border border-slate-700 bg-slate-800/50 overflow-hidden">
        <div className="px-4 py-3 border-b border-slate-700 text-slate-200 font-medium">持仓</div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-slate-400 border-b border-slate-700">
                <th className="text-left p-3">代码</th>
                <th className="text-right p-3">数量</th>
                <th className="text-right p-3">成本价</th>
                <th className="text-right p-3">现价</th>
                <th className="text-right p-3">浮动盈亏</th>
                <th className="text-right p-3">操作</th>
              </tr>
            </thead>
            <tbody>
              {positions.length === 0 ? (
                <tr>
                  <td colSpan={6} className="p-4 text-slate-500 text-center">
                    暂无持仓（实盘状态来自 store/live_state/*.json）
                  </td>
                </tr>
              ) : (
                positions.map((p, i) => (
                  <tr key={i} className="border-b border-slate-700/50 hover:bg-slate-800">
                    <td className="p-3 font-mono">{p.symbol ?? p.contract?.symbol ?? "-"}</td>
                    <td className="p-3 text-right font-mono">{p.quantity ?? p.position ?? 0}</td>
                    <td className="p-3 text-right font-mono">${Number(p.avgCost ?? p.avg_cost ?? 0).toFixed(2)}</td>
                    <td className="p-3 text-right font-mono">${Number(p.marketPrice ?? p.market_price ?? 0).toFixed(2)}</td>
                    <td className={`p-3 text-right font-mono ${Number(p.unrealizedPnL ?? p.unrealized_pnl ?? 0) >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                      ${Number(p.unrealizedPnL ?? p.unrealized_pnl ?? 0).toFixed(2)}
                    </td>
                    <td className="p-3 text-right">
                      <button
                        type="button"
                        className="text-amber-400 hover:text-amber-300 text-xs"
                        onClick={() => alert("一键平仓需配合实盘 trader 与 ib_client 使用")}
                      >
                        一键平仓
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
