"use client";

import { useMemo, useState } from "react";

export type PricePoint = { date: string; close: number };
type RangeWeeks = 4 | 13 | 26 | 52;

const RANGES: { weeks: RangeWeeks; label: string }[] = [
  { weeks: 4, label: "1M" },
  { weeks: 13, label: "3M" },
  { weeks: 26, label: "6M" },
  { weeks: 52, label: "1Y" }
];

export default function PriceChart({ history }: { history: PricePoint[] }) {
  const [range, setRange] = useState<RangeWeeks>(52);
  const points = useMemo(() => {
    const lastDate = history.at(-1)?.date;
    const end = lastDate ? new Date(lastDate).getTime() : 0;
    const cutoff = end - range * 7 * 24 * 60 * 60 * 1000;
    return history.filter((point) => new Date(point.date).getTime() >= cutoff);
  }, [history, range]);

  if (points.length < 2) {
    return <div className="chart-empty panel">
      <p className="eyebrow">52-WEEK PRICE HISTORY</p>
      <strong>Historical chart unavailable</strong>
      <p>Enable live data to load Yahoo daily prices. No sample line is substituted.</p>
    </div>;
  }

  const width = 360;
  const height = 172;
  const left = 34;
  const right = 8;
  const top = 14;
  const bottom = 22;
  const values = points.map((point) => point.close);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  const plotWidth = width - left - right;
  const plotHeight = height - top - bottom;
  const coordinates = points.map((point, index) => ({
    x: left + (index / (points.length - 1)) * plotWidth,
    y: top + ((max - point.close) / span) * plotHeight
  }));
  const line = coordinates.map((point, index) => `${index ? "L" : "M"}${point.x.toFixed(1)},${point.y.toFixed(1)}`).join(" ");
  const area = `${line} L${coordinates.at(-1)!.x.toFixed(1)},${(top + plotHeight).toFixed(1)} L${left},${(top + plotHeight).toFixed(1)} Z`;
  const first = points[0];
  const latest = points.at(-1)!;
  const changePct = first.close ? ((latest.close - first.close) / first.close) * 100 : 0;

  return <article className="price-chart panel">
    <div className="chart-heading">
      <div><p className="eyebrow">PRICE HISTORY · YAHOO DAILY BARS</p><strong className="chart-price">₹{latest.close.toLocaleString("en-IN", { maximumFractionDigits: 2 })}</strong><span className={changePct >= 0 ? "positive" : "negative"}> {changePct >= 0 ? "+" : ""}{changePct.toFixed(2)}%</span></div>
      <div className="chart-ranges">{RANGES.map((item) => <button key={item.weeks} className={range === item.weeks ? "selected" : ""} onClick={() => setRange(item.weeks)}>{item.label}</button>)}</div>
    </div>
    <svg className="chart-svg" viewBox={`0 0 ${width} ${height}`} role="img" aria-label={`${range} week stock price history`}>
      <defs><linearGradient id="price-fill" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stopColor="#6b9b7b" stopOpacity=".25"/><stop offset="100%" stopColor="#6b9b7b" stopOpacity="0"/></linearGradient></defs>
      {[0, 0.5, 1].map((fraction) => {
        const y = top + fraction * plotHeight;
        const value = max - fraction * span;
        return <g key={fraction}><line x1={left} x2={width - right} y1={y} y2={y} stroke="#edf0ed" strokeDasharray="3 4"/><text x="0" y={y + 3} fill="#87918a" fontSize="9">{value.toLocaleString("en-IN", { maximumFractionDigits: 0 })}</text></g>;
      })}
      <path d={area} fill="url(#price-fill)"/>
      <path d={line} fill="none" stroke="#367653" strokeWidth="2" strokeLinejoin="round" strokeLinecap="round"/>
      <circle cx={coordinates.at(-1)!.x} cy={coordinates.at(-1)!.y} r="3.5" fill="#367653" stroke="white" strokeWidth="2"/>
      <text x={left} y={height - 4} fill="#87918a" fontSize="9">{first.date.slice(5)}</text>
      <text x={width - right} y={height - 4} textAnchor="end" fill="#87918a" fontSize="9">{latest.date.slice(5)}</text>
    </svg>
    <p className="chart-footnote">Source: Yahoo Finance via yfinance · latest bar {latest.date} · may be delayed. Past performance is not predictive.</p>
  </article>;
}
