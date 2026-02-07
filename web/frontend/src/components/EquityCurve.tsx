import { useEffect, useRef } from "react";
import { createChart, IChartApi, ISeriesApi, LineData } from "lightweight-charts";

interface EquityCurveProps {
  data: { date: string; equity: number }[];
}

export default function EquityCurve({ data }: EquityCurveProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    const chart = createChart(containerRef.current, {
      layout: { background: { color: "#1e293b" }, textColor: "#94a3b8" },
      grid: { vertLines: { color: "#334155" }, horzLines: { color: "#334155" } },
      width: containerRef.current.clientWidth,
      height: 400,
      timeScale: { timeVisible: true, secondsVisible: false, borderColor: "#475569" },
      rightPriceScale: { borderColor: "#475569" },
    });
    const lineSeries = chart.addLineSeries({ color: "#f59e0b", lineWidth: 2 });
    const parsed: LineData[] = data.map((d) => ({ time: d.date, value: Number(d.equity) }));
    if (parsed.length > 0) {
      lineSeries.setData(parsed);
      chart.timeScale().fitContent();
    }
    chartRef.current = chart;
    return () => {
      chart.remove();
      chartRef.current = null;
    };
  }, [data]);

  return <div ref={containerRef} className="w-full h-full" />;
}
