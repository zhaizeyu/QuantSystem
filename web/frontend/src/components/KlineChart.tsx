import { useEffect, useRef } from "react";
import { createChart, IChartApi, ISeriesApi, CandlestickData } from "lightweight-charts";

interface KlineItem {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
}

interface MarkerItem {
  time: string;
  side: string;
  reason: string;
}

interface KlineChartProps {
  data: KlineItem[];
  markers?: MarkerItem[];
}

export default function KlineChart({ data, markers = [] }: KlineChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);

  useEffect(() => {
    if (!containerRef.current || data.length === 0) return;
    const chart = createChart(containerRef.current, {
      layout: { background: { color: "#1e293b" }, textColor: "#94a3b8" },
      grid: { vertLines: { color: "#334155" }, horzLines: { color: "#334155" } },
      width: containerRef.current.clientWidth,
      height: 400,
      timeScale: { timeVisible: true, secondsVisible: false, borderColor: "#475569" },
      rightPriceScale: { borderColor: "#475569" },
    });
    const candlestickSeries = chart.addCandlestickSeries({
      upColor: "#22c55e",
      downColor: "#ef4444",
      borderVisible: false,
    });
    const parsed: CandlestickData[] = data.map((d) => ({
      time: d.date as string,
      open: Number(d.open),
      high: Number(d.high),
      low: Number(d.low),
      close: Number(d.close),
    }));
    candlestickSeries.setData(parsed);
    const markMap = new Map<string, { side: string; reason: string }>();
    markers.forEach((m) => markMap.set(m.time, { side: m.side, reason: m.reason }));
    const marks = parsed
      .filter((p) => markMap.has(p.time as string))
      .map((p) => {
        const t = p.time as string;
        const { side, reason } = markMap.get(t)!;
        const isBuy = side === "BUY" || side === "买入";
        return {
          time: t,
          position: isBuy ? ("belowBar" as const) : ("aboveBar" as const),
          color: isBuy ? "#22c55e" : "#ef4444",
          shape: isBuy ? ("arrowUp" as const) : ("arrowDown" as const),
          text: reason || side,
        };
      });
    candlestickSeries.setMarkers(marks);
    chart.timeScale().fitContent();
    chartRef.current = chart;
    seriesRef.current = candlestickSeries;
    return () => {
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
    };
  }, [data, markers]);

  return <div ref={containerRef} className="w-full h-full" />;
}
