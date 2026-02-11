import { useEffect, useRef } from "react";
import {
  createChart,
  IChartApi,
  CandlestickData,
  LineData,
  HistogramData,
  LineStyle,
} from "lightweight-charts";
import { rsiWilder, macd, bollingerBands, sma } from "../utils/indicators";

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
  reason?: string;
}

interface KlineChartProps {
  data: KlineItem[];
  markers?: MarkerItem[];
}

const CHART_HEIGHT = 280;
const SUB_CHART_HEIGHT = 120;
const MAX_BAR_SPACING = 12;
const MIN_BAR_SPACING = 1.5;

const CHART_OPTIONS = {
  layout: { background: { color: "#1e293b" }, textColor: "#94a3b8" },
  grid: {
    vertLines: { visible: false },
    horzLines: { visible: false },
  },
  crosshair: {
    horzLine: { visible: true, style: LineStyle.Solid, labelVisible: false },
    vertLine: { visible: true, style: LineStyle.Solid, labelVisible: false },
  },
  timeScale: {
    timeVisible: true,
    secondsVisible: false,
    borderColor: "#475569",
    barSpacing: 6,
    minBarSpacing: MIN_BAR_SPACING,
  },
  rightPriceScale: { borderColor: "#475569" },
  // 长按拖动只移动时间轴，不触发缩放
  handleScale: { axisPressedMouseMove: false },
  handleScroll: { pressedMouseMove: true },
};

export default function KlineChart({ data, markers = [] }: KlineChartProps) {
  const mainRef = useRef<HTMLDivElement>(null);
  const rsiRef = useRef<HTMLDivElement>(null);
  const macdRef = useRef<HTMLDivElement>(null);
  const chartsRef = useRef<IChartApi[]>([]);
  const syncRef = useRef(false);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const wrapperRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!mainRef.current || data.length === 0) return;
    const w = mainRef.current.clientWidth || 600;
    const close = data.map((d) => Number(d.close));
    const times = data.map((d) => String(d.date).slice(0, 10));

    const ma5 = sma(close, 5);
    const ma10 = sma(close, 10);
    const ma20 = sma(close, 20);
    const rsiValues = rsiWilder(close, 6);
    const { dif, dea, hist } = macd(close, 12, 26, 9);
    const { middle, upper, lower } = bollingerBands(close, 20, 2);

    const charts: IChartApi[] = [];

    const panelRefMap = {
      main: mainRef.current,
      rsi: rsiRef.current,
      macd: macdRef.current,
    } as const;

    // 主图 K 线
    const mainChart = createChart(mainRef.current, {
      ...CHART_OPTIONS,
      width: w,
      height: CHART_HEIGHT,
    });
    const candlestickSeries = mainChart.addCandlestickSeries({
      upColor: "#ef4444",
      downColor: "#22c55e",
      borderVisible: false,
      lastValueVisible: false,
      priceLineVisible: false,
      thinBars: true,
    });
    const parsed: CandlestickData[] = data.map((d) => ({
      time: d.date as string,
      open: Number(d.open),
      high: Number(d.high),
      low: Number(d.low),
      close: Number(d.close),
    }));
    candlestickSeries.setData(parsed);
    const markMap = new Map<string, string>();
    markers.forEach((m) => markMap.set(m.time, m.side === "BUY" || m.side === "买入" ? "买" : "卖"));
    const marks = parsed
      .filter((p) => markMap.has(p.time as string))
      .map((p) => {
        const t = p.time as string;
        const isBuy = markMap.get(t) === "买";
        return {
          time: t,
          position: isBuy ? ("belowBar" as const) : ("aboveBar" as const),
          color: isBuy ? "#ef4444" : "#22c55e",
          shape: isBuy ? ("arrowUp" as const) : ("arrowDown" as const),
          text: isBuy ? "买" : "卖",
        };
      });
    candlestickSeries.setMarkers(marks);
    // MA5 / MA10 / MA20 均线（与 K 线同坐标）
    const ma5Series = mainChart.addLineSeries({
      color: "#f59e0b",
      lineWidth: 2,
      lastValueVisible: false,
      priceLineVisible: false,
    });
    const ma10Series = mainChart.addLineSeries({
      color: "#8b5cf6",
      lineWidth: 2,
      lastValueVisible: false,
      priceLineVisible: false,
    });
    const ma20Series = mainChart.addLineSeries({
      color: "#06b6d4",
      lineWidth: 2,
      lastValueVisible: false,
      priceLineVisible: false,
    });
    const ma5Data: LineData[] = times
      .map((t, i) => (ma5[i] != null ? { time: t, value: ma5[i]! } : null))
      .filter((x): x is LineData => x != null);
    const ma10Data: LineData[] = times
      .map((t, i) => (ma10[i] != null ? { time: t, value: ma10[i]! } : null))
      .filter((x): x is LineData => x != null);
    const ma20Data: LineData[] = times
      .map((t, i) => (ma20[i] != null ? { time: t, value: ma20[i]! } : null))
      .filter((x): x is LineData => x != null);
    if (ma5Data.length) ma5Series.setData(ma5Data);
    if (ma10Data.length) ma10Series.setData(ma10Data);
    if (ma20Data.length) ma20Series.setData(ma20Data);
    // BOLL(20,2) 上/中/下轨画在主图
    const bollUpperSeries = mainChart.addLineSeries({
      color: "#ef4444",
      lineWidth: 1,
      lastValueVisible: false,
      priceLineVisible: false,
      lineStyle: LineStyle.Solid,
    });
    const bollMidSeries = mainChart.addLineSeries({
      color: "#94a3b8",
      lineWidth: 1,
      lastValueVisible: false,
      priceLineVisible: false,
      lineStyle: LineStyle.Solid,
    });
    const bollLowerSeries = mainChart.addLineSeries({
      color: "#22c55e",
      lineWidth: 1,
      lastValueVisible: false,
      priceLineVisible: false,
      lineStyle: LineStyle.Solid,
    });
    const upperData: LineData[] = times
      .map((t, i) => (upper[i] != null ? { time: t, value: upper[i]! } : null))
      .filter((x): x is LineData => x != null);
    const midData: LineData[] = times
      .map((t, i) => (middle[i] != null ? { time: t, value: middle[i]! } : null))
      .filter((x): x is LineData => x != null);
    const lowerData: LineData[] = times
      .map((t, i) => (lower[i] != null ? { time: t, value: lower[i]! } : null))
      .filter((x): x is LineData => x != null);
    if (upperData.length) bollUpperSeries.setData(upperData);
    if (midData.length) bollMidSeries.setData(midData);
    if (lowerData.length) bollLowerSeries.setData(lowerData);
    charts.push(mainChart);

    // 副图 RSI
    if (rsiRef.current) {
      const rsiChart = createChart(rsiRef.current, {
        ...CHART_OPTIONS,
        width: w,
        height: SUB_CHART_HEIGHT,
      });
      const rsiSeries = rsiChart.addLineSeries({
        color: "#a78bfa",
        lineWidth: 2,
        lastValueVisible: false,
        priceLineVisible: false,
      });
      const rsiData: LineData[] = times
        .map((t, i) => (rsiValues[i] != null ? { time: t, value: rsiValues[i]! } : null))
        .filter((x): x is LineData => x != null);
      if (rsiData.length) rsiSeries.setData(rsiData);
      rsiChart.priceScale("right").applyOptions({ scaleMargins: { top: 0.1, bottom: 0.1 } });
      charts.push(rsiChart);
    }

    // 副图 MACD
    if (macdRef.current) {
      const macdChart = createChart(macdRef.current, {
        ...CHART_OPTIONS,
        width: w,
        height: SUB_CHART_HEIGHT,
      });
      const histSeries = macdChart.addHistogramSeries({
        color: "#26a69a",
        priceFormat: { type: "volume" },
        lastValueVisible: false,
        priceLineVisible: false,
      });
      const histData: HistogramData[] = times
        .map((t, i) =>
          hist[i] != null ? { time: t, value: hist[i]!, color: hist[i]! >= 0 ? "#ef4444" : "#22c55e" } : null
        )
        .filter((x): x is HistogramData => x != null);
      if (histData.length) histSeries.setData(histData);
      const difSeries = macdChart.addLineSeries({
        color: "#f59e0b",
        lineWidth: 1,
        lastValueVisible: false,
        priceLineVisible: false,
      });
      const deaSeries = macdChart.addLineSeries({
        color: "#6366f1",
        lineWidth: 1,
        lastValueVisible: false,
        priceLineVisible: false,
      });
      const difData: LineData[] = times
        .map((t, i) => (dif[i] != null ? { time: t, value: dif[i]! } : null))
        .filter((x): x is LineData => x != null);
      const deaData: LineData[] = times
        .map((t, i) => (dea[i] != null ? { time: t, value: dea[i]! } : null))
        .filter((x): x is LineData => x != null);
      if (difData.length) difSeries.setData(difData);
      if (deaData.length) deaSeries.setData(deaData);
      charts.push(macdChart);
    }

    chartsRef.current = charts;

    // 按时间范围同步主图与副图，使日期轴对齐
    const syncByTimeRange = (source: IChartApi) => {
      if (syncRef.current) return;
      const range = source.timeScale().getVisibleRange();
      if (!range) return;
      syncRef.current = true;
      charts.forEach((c) => {
        if (c !== source) {
          try {
            c.timeScale().setVisibleRange(range);
          } catch {
            // 副图数据可能不包含该时间范围，忽略
          }
        }
      });
      syncRef.current = false;
    };
    charts.forEach((c) => {
      c.timeScale().subscribeVisibleTimeRangeChange(() => syncByTimeRange(c));
    });
    // 限制最大 barSpacing，放大看日 K 时 K 线/柱子不会过宽、保持长宽比
    const capBarSpacing = () => {
      const opts = mainChart.timeScale().options();
      const current = opts.barSpacing ?? 6;
      if (current > MAX_BAR_SPACING) {
        charts.forEach((c) => {
          try {
            c.timeScale().applyOptions({ barSpacing: MAX_BAR_SPACING });
          } catch {
            // ignore
          }
        });
      }
    };
    mainChart.timeScale().subscribeVisibleLogicalRangeChange(capBarSpacing);
    mainChart.timeScale().fitContent();
    capBarSpacing();
    // 初始对齐：将主图当前可见时间范围应用到所有副图
    const initialRange = mainChart.timeScale().getVisibleRange();
    if (initialRange) {
      charts.forEach((c) => {
        if (c !== mainChart) {
          try {
            c.timeScale().setVisibleRange(initialRange);
          } catch {
            // ignore
          }
        }
      });
    }

    const tooltipEl = tooltipRef.current;
    const onCrosshairMove = (
      panel: keyof typeof panelRefMap,
      param: { time?: string; point?: { x: number; y: number } }
    ) => {
      if (!tooltipEl || !param.point || param.time == null) {
        tooltipEl?.classList.add("opacity-0");
        return;
      }
      const t = String(param.time).slice(0, 10);
      const idx = times.indexOf(t);
      if (idx < 0) {
        tooltipEl.classList.add("opacity-0");
        return;
      }
      const bar = data[idx];
      const fmt = (v: number | null | undefined, p = 2) =>
        v != null ? (p > 0 ? v.toFixed(p) : String(v)) : "--";
      const rows: string[] = [
        `<div class="text-slate-300 font-medium border-b border-slate-600 pb-1 mb-1">${t}</div>`,
        `<div class="flex justify-between gap-4"><span class="text-slate-500">开</span><span>${fmt(bar?.open)}</span></div>`,
        `<div class="flex justify-between gap-4"><span class="text-slate-500">高</span><span>${fmt(bar?.high)}</span></div>`,
        `<div class="flex justify-between gap-4"><span class="text-slate-500">低</span><span>${fmt(bar?.low)}</span></div>`,
        `<div class="flex justify-between gap-4"><span class="text-slate-500">收</span><span>${fmt(bar?.close)}</span></div>`,
        `<div class="flex justify-between gap-4"><span class="text-amber-500/90">MA5</span><span>${fmt(ma5[idx])}</span></div>`,
        `<div class="flex justify-between gap-4"><span class="text-violet-400/90">MA10</span><span>${fmt(ma10[idx])}</span></div>`,
        `<div class="flex justify-between gap-4"><span class="text-cyan-400/90">MA20</span><span>${fmt(ma20[idx])}</span></div>`,
        `<div class="flex justify-between gap-4"><span class="text-red-400/90">上轨</span><span>${fmt(upper[idx])}</span></div>`,
        `<div class="flex justify-between gap-4"><span class="text-slate-400">中轨</span><span>${fmt(middle[idx])}</span></div>`,
        `<div class="flex justify-between gap-4"><span class="text-green-400/90">下轨</span><span>${fmt(lower[idx])}</span></div>`,
        `<div class="flex justify-between gap-4 border-t border-slate-600 pt-1 mt-1"><span class="text-purple-400/90">RSI(6)</span><span>${fmt(rsiValues[idx], 2)}</span></div>`,
        `<div class="flex justify-between gap-4"><span class="text-amber-500/90">DIF</span><span>${fmt(dif[idx], 4)}</span></div>`,
        `<div class="flex justify-between gap-4"><span class="text-indigo-400/90">DEA</span><span>${fmt(dea[idx], 4)}</span></div>`,
        `<div class="flex justify-between gap-4"><span class="text-slate-400">MACD</span><span>${fmt(hist[idx], 4)}</span></div>`,
      ];
      tooltipEl.innerHTML = rows.join("");
      const rect = panelRefMap[panel]?.getBoundingClientRect();
      if (rect) {
        tooltipEl.style.left = `${rect.left + param.point!.x + 12}px`;
        tooltipEl.style.top = `${rect.top + param.point!.y + 8}px`;
      }
      tooltipEl.classList.remove("opacity-0");
    };
    const mainCrosshairHandler = (param: { time?: string; point?: { x: number; y: number } }) =>
      onCrosshairMove("main", param);
    const rsiCrosshairHandler = (param: { time?: string; point?: { x: number; y: number } }) =>
      onCrosshairMove("rsi", param);
    const macdCrosshairHandler = (param: { time?: string; point?: { x: number; y: number } }) =>
      onCrosshairMove("macd", param);

    mainChart.subscribeCrosshairMove(mainCrosshairHandler);
    if (charts[1]) charts[1].subscribeCrosshairMove(rsiCrosshairHandler);
    if (charts[2]) charts[2].subscribeCrosshairMove(macdCrosshairHandler);

    return () => {
      mainChart.unsubscribeCrosshairMove(mainCrosshairHandler);
      if (charts[1]) charts[1].unsubscribeCrosshairMove(rsiCrosshairHandler);
      if (charts[2]) charts[2].unsubscribeCrosshairMove(macdCrosshairHandler);
      charts.forEach((c) => c.remove());
      chartsRef.current = [];
    };
  }, [data, markers]);

  return (
    <div ref={wrapperRef} className="w-full flex flex-col gap-0 relative">
      <div
        ref={tooltipRef}
        className="pointer-events-none fixed z-50 opacity-0 transition-opacity bg-slate-800 border border-slate-600 rounded-lg shadow-xl px-3 py-2 text-xs min-w-[160px]"
        style={{ left: 0, top: 0 }}
      />
      <div ref={mainRef} className="w-full" style={{ minHeight: CHART_HEIGHT }} />
      <div className="border-t border-slate-700/50 px-1 pt-1 text-slate-500 text-xs">RSI(6)</div>
      <div ref={rsiRef} className="w-full" style={{ minHeight: SUB_CHART_HEIGHT }} />
      <div className="border-t border-slate-700/50 px-1 pt-1 text-slate-500 text-xs">MACD(12,26,9)</div>
      <div ref={macdRef} className="w-full" style={{ minHeight: SUB_CHART_HEIGHT }} />
    </div>
  );
}
