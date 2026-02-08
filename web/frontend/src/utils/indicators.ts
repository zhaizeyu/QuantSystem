/**
 * 技术指标：与 strategies/indicators.py 逻辑一致，供 K 线主图/副图使用。
 */

/** 简单移动平均，前 period-1 个为 null */
export function sma(arr: number[], period: number): (number | null)[] {
  const n = arr.length;
  const out: (number | null)[] = new Array(n).fill(null);
  for (let i = period - 1; i < n; i++) {
    let sum = 0;
    for (let j = i - period + 1; j <= i; j++) sum += arr[j];
    out[i] = sum / period;
  }
  return out;
}

/** Wilder 平滑 RSI(period)，与东财等主流一致。 */
export function rsiWilder(close: number[], period: number = 6): (number | null)[] {
  const n = close.length;
  const out: (number | null)[] = new Array(n).fill(null);
  if (n < period + 1) return out;
  let avgGain = 0;
  let avgLoss = 0;
  for (let j = 1; j <= period; j++) {
    const delta = close[j] - close[j - 1];
    if (delta > 0) avgGain += delta;
    else avgLoss -= delta;
  }
  avgGain /= period;
  avgLoss /= period;
  const rs0 = avgLoss < 1e-10 ? 100 : avgGain / avgLoss;
  out[period] = 100 - 100 / (1 + rs0);
  for (let i = period + 1; i < n; i++) {
    const delta = close[i] - close[i - 1];
    const gain = delta > 0 ? delta : 0;
    const loss = delta < 0 ? -delta : 0;
    avgGain = (avgGain * (period - 1) + gain) / period;
    avgLoss = (avgLoss * (period - 1) + loss) / period;
    const rs = avgLoss < 1e-10 ? 100 : avgGain / avgLoss;
    out[i] = 100 - 100 / (1 + rs);
  }
  return out;
}

export function ema(arr: number[], span: number): (number | null)[] {
  const n = arr.length;
  const out: (number | null)[] = new Array(n).fill(null);
  if (n === 0) return out;
  const k = 2 / (span + 1);
  let prev = arr[0];
  out[0] = prev;
  for (let i = 1; i < n; i++) {
    prev = arr[i] * k + prev * (1 - k);
    out[i] = prev;
  }
  return out;
}

export function macd(
  close: number[],
  fast: number = 12,
  slow: number = 26,
  signal: number = 9
): { dif: (number | null)[]; dea: (number | null)[]; hist: (number | null)[] } {
  const emaFast = ema(close, fast);
  const emaSlow = ema(close, slow);
  const n = close.length;
  const dif: (number | null)[] = new Array(n).fill(null);
  for (let i = 0; i < n; i++) {
    if (emaFast[i] != null && emaSlow[i] != null) dif[i] = emaFast[i]! - emaSlow[i]!;
  }
  const deaArr: number[] = [];
  let deaPrev = 0;
  for (let i = 0; i < n; i++) {
    if (dif[i] == null) {
      deaArr.push(NaN);
      continue;
    }
    if (i === 0 || Number.isNaN(deaArr[i - 1])) {
      deaPrev = dif[i]!;
    } else {
      deaPrev = dif[i]! * (2 / (signal + 1)) + deaPrev * (1 - 2 / (signal + 1));
    }
    deaArr.push(deaPrev);
  }
  const dea: (number | null)[] = deaArr.map((v) => (Number.isNaN(v) ? null : v));
  const hist: (number | null)[] = dif.map((d, i) =>
    d != null && dea[i] != null ? d - dea[i]! : null
  );
  return { dif, dea, hist };
}

export function bollingerBands(
  close: number[],
  period: number = 20,
  numStd: number = 2
): { middle: (number | null)[]; upper: (number | null)[]; lower: (number | null)[] } {
  const n = close.length;
  const middle: (number | null)[] = new Array(n).fill(null);
  const upper: (number | null)[] = new Array(n).fill(null);
  const lower: (number | null)[] = new Array(n).fill(null);
  for (let i = period - 1; i < n; i++) {
    let sum = 0;
    for (let j = i - period + 1; j <= i; j++) sum += close[j];
    const m = sum / period;
    let sq = 0;
    for (let j = i - period + 1; j <= i; j++) sq += (close[j] - m) ** 2;
    const std = Math.sqrt(sq / period) || 0;
    middle[i] = m;
    upper[i] = m + numStd * std;
    lower[i] = m - numStd * std;
  }
  return { middle, upper, lower };
}
