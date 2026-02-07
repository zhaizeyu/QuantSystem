import { useMemo, useState } from "react";

interface TradeRow {
  timestamp?: string;
  symbol?: string;
  side?: string;
  price?: number;
  entry_reason?: string;
  exit_reason?: string;
  roi?: number;
  pnl?: number;
  quantity?: number;
  [key: string]: unknown;
}

interface TradeTableProps {
  trades: TradeRow[];
}

export default function TradeTable({ trades }: TradeTableProps) {
  const [sortBy, setSortBy] = useState<"roi" | "timestamp" | null>("timestamp");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");

  const sorted = useMemo(() => {
    const list = [...trades];
    if (!sortBy) return list;
    list.sort((a, b) => {
      const va = a[sortBy] as number | string;
      const vb = b[sortBy] as number | string;
      const cmp = typeof va === "number" && typeof vb === "number" ? va - vb : String(va).localeCompare(String(vb));
      return sortDir === "asc" ? cmp : -cmp;
    });
    return list;
  }, [trades, sortBy, sortDir]);

  let cumulative = 0;

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-slate-400 border-b border-slate-700">
            <th className="text-left p-3">时间</th>
            <th className="text-left p-3">代码</th>
            <th className="text-left p-3">方向</th>
            <th className="text-right p-3">价格</th>
            <th className="text-left p-3">策略原因</th>
            <th
              className="text-right p-3 cursor-pointer hover:text-slate-200"
              onClick={() => {
                setSortBy("roi");
                setSortDir((d) => (d === "asc" ? "desc" : "asc"));
              }}
            >
              收益率(ROI) %
            </th>
            <th className="text-right p-3">累计收益</th>
          </tr>
        </thead>
        <tbody>
          {sorted.length === 0 ? (
            <tr>
              <td colSpan={7} className="p-4 text-slate-500 text-center">
                暂无交割单，请先运行回测
              </td>
            </tr>
          ) : (
            sorted.map((t, i) => {
              const pnl = Number(t.pnl ?? 0);
              cumulative += pnl;
              const roi = Number(t.roi ?? 0);
              const reason = (t.side === "BUY" ? t.entry_reason : t.exit_reason) ?? "-";
              return (
                <tr key={i} className="border-b border-slate-700/50 hover:bg-slate-800">
                  <td className="p-3 font-mono text-slate-300">
                    {(t.timestamp as string)?.slice(0, 19).replace("T", " ") ?? "-"}
                  </td>
                  <td className="p-3 font-mono">{t.symbol ?? "-"}</td>
                  <td className="p-3">
                    <span className={t.side === "BUY" || t.side === "买入" ? "text-emerald-400" : "text-red-400"}>
                      {t.side === "BUY" ? "买入" : t.side === "SELL" ? "卖出" : (t.side ?? "-")}
                    </span>
                  </td>
                  <td className="p-3 text-right font-mono">{Number(t.price ?? 0).toFixed(2)}</td>
                  <td className="p-3 text-slate-300 max-w-[200px] truncate" title={String(reason)}>
                    {reason}
                  </td>
                  <td className={`p-3 text-right font-mono ${roi >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                    {roi.toFixed(2)}%
                  </td>
                  <td className={`p-3 text-right font-mono ${cumulative >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                    {cumulative.toFixed(2)}
                  </td>
                </tr>
              );
            })
          )}
        </tbody>
      </table>
    </div>
  );
}
