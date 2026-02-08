import { useEffect, useRef } from "react";
import { createChart, IChartApi, LineData, LineStyle } from "lightweight-charts";

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
      grid: { vertLines: { visible: false }, horzLines: { visible: false } },
      crosshair: {
        horzLine: { visible: true, style: LineStyle.Solid, labelVisible: true },
        vertLine: { visible: true, style: LineStyle.Solid, labelVisible: true },
      },
      width: containerRef.current.clientWidth,
      height: 400,
      timeScale: { timeVisible: true, secondsVisible: false, borderColor: "#475569" },
      rightPriceScale: { borderColor: "#475569" },
    });
    const lineSeries = chart.addLineSeries({
      color: "#f59e0b",
      lineWidth: 2,
      lastValueVisible: false,
      priceLineVisible: false,
    });
    const parsed: LineData[] = data
      .filter((d) => d != null && (d as { date?: string }).date != null)
      .map((d) => ({
        time: String((d as { date?: string }).date).slice(0, 10),
        value: Number((d as { equity?: number }).equity) || 0,
      }));
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
