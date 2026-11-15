"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api, demoNotice, Person } from "@/lib/api";
import PriceChart, { PricePoint } from "@/components/PriceChart";

type Report = {
  ticker: string; company_name: string; sector: string; network_overlay: Person[];
  source_status?: string; data_notice?: string; live_data_error?: string;
  live_data?: {
    source: string;
    quote_date: string;
    currency?: string | null;
    financial_currency?: string | null;
    quote: { current_price: number; change_percent: number; volume_multiple: number; volume_20d_avg: number; day_volume: number };
    technicals: Record<string, number | null>;
    fundamentals: Record<string, Record<string, number | string>>;
    price_history: PricePoint[];
  };
  report: {
    module_status: Record<string, string>;
    module_sources?: Record<string, { label: string; url: string }[]>;
  };
};
type Narrative = { management_credibility_score: number; credibility_summary: string; quarters_audited: number; source_status: string };

function formatStatementValue(value: number | string, currency?: string | null): string {
  if (typeof value !== "number") return value;
  if (currency === "INR") {
    const crore = value / 10_000_000;
    const absoluteCrore = Math.abs(crore);
    if (absoluteCrore >= 100_000) return `₹${(crore / 100_000).toFixed(2)} lakh Cr`;
    if (absoluteCrore >= 1_000) return `₹${(crore / 1_000).toFixed(2)}k Cr`;
    if (absoluteCrore >= 1) return `₹${crore.toFixed(2)} Cr`;
    return `₹${(value / 100_000).toFixed(2)} lakh`;
  }
  const compact = new Intl.NumberFormat("en-IN", { notation: "compact", maximumFractionDigits: 2 }).format(value);
  return currency ? `${currency} ${compact}` : `${compact} (currency unknown)`;
}

function MetricCard({ title, data, currency, financial = false }: { title: string; data: Record<string, number | string>; currency?: string | null; financial?: boolean }) {
  return <article className="metric-card panel"><p className="eyebrow">{title}</p>{Object.entries(data).map(([key, value]) => <div className="metric-row" key={key}><span>{key.replaceAll("_", " ")}</span><strong>{financial ? formatStatementValue(value, currency) : typeof value === "number" ? value.toLocaleString("en-IN") : value}</strong></div>)}</article>;
}

export default function ResearchPage() {
  const params = useParams<{ ticker: string }>();
  const ticker = decodeURIComponent(params.ticker).toUpperCase();
  const [data, setData] = useState<Report | null>(null);
  const [narrative, setNarrative] = useState<Narrative | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    Promise.all([api<Report>(`/research/${ticker}`), api<Narrative>(`/research/${ticker}/narrative`)])
      .then(([report, audit]) => { if (active) { setData(report); setNarrative(audit); } })
      .catch((reason) => { if (active) setError(reason instanceof Error ? reason.message : "Could not load research."); });
    return () => { active = false; };
  }, [ticker]);

  if (error) return <div className="screen"><Link href="/research" className="back-link">← Companies</Link><div className="error-card">{error}</div></div>;
  if (!data || !narrative) return <div className="screen"><div className="loading-state">Preparing illustrative research…</div></div>;
  const report = data.report;
  return <div className="screen">
    <Link href="/research" className="back-link">← Company explorer</Link>
    <section className="company-hero">
      <div className="hero-top"><span className="ticker-badge large">{data.ticker.slice(0, 2)}</span><span className={data.live_data ? "source-live" : "synthetic-tag"}>{data.live_data ? "LIVE MARKET DATA" : "SOURCE DATA NEEDED"}</span></div>
      <p className="eyebrow">{data.sector}</p><h1>{data.ticker}</h1><p>{data.company_name}</p>
      <div className="demo-banner">{data.data_notice ?? demoNotice} No verified primary documents are connected.</div>
    </section>
    {data.live_data_error && <div className="error-card">Live market data unavailable: {data.live_data_error} Showing labeled demo values instead.</div>}
    {data.live_data && <section className="section">
      <div className="section-heading"><div><p className="eyebrow">LIVE DATA · {data.live_data.quote_date}</p><h2>Yahoo Finance snapshot</h2></div></div>
      <div className="demo-banner">{data.live_data.source}. Latest daily bar may be partial or delayed, not a real-time exchange quote. Technical indicators are calculated from daily history; verify before relying on them.</div>
      <PriceChart history={data.live_data.price_history} />
      <div className="metrics-grid">
        <MetricCard title="Latest daily quote" data={{
          close_inr: data.live_data.quote.current_price,
          change_percent: data.live_data.quote.change_percent,
          volume_multiple: data.live_data.quote.volume_multiple,
          volume_20d_average: data.live_data.quote.volume_20d_avg
        }} />
        <MetricCard title="Technical indicators" data={Object.fromEntries(
          Object.entries(data.live_data.technicals).map(([key, value]) => [key, value ?? "Insufficient history"])
        )} />
      </div>
      <p className="footnote">Yahoo financial statement values are formatted to readable units (INR converted to ₹ crore/lakh crore when Yahoo reports INR). Reporting basis may vary; cross-check company filings.</p>
    </section>}
    <section className="section">
      <div className="section-heading"><div><p className="eyebrow">WHO TO CALL</p><h2>Network context</h2></div><Link href="/network" className="text-link">Explore →</Link></div>
      <div className="person-strip">{data.network_overlay.map((person) => <Link key={person.id} href={`/network/diligence/${person.id}`} className="person-mini panel"><span className="avatar">{person.name.split(" ").map((p) => p[0]).join("")}</span><strong>{person.name}</strong><small>{person.expertise_tags[0]} · synthetic</small></Link>)}</div>
    </section>
    {!data.live_data && <PriceChart history={[]} />}
    <section className="section">
      <div className="section-heading"><div><p className="eyebrow">FUNDAMENTALS</p><h2>What the sources support</h2></div><span className="muted small">No synthetic estimates</span></div>
      {data.live_data && Object.keys(data.live_data.fundamentals).length > 0
        ? <div className="metrics-grid">{Object.entries(data.live_data.fundamentals).map(([statement, values]) =>
          <MetricCard key={statement} title={`Yahoo annual ${statement.replaceAll("_", " ")}`} data={values} currency={data.live_data?.financial_currency} financial />
        )}</div>
        : <div className="audit-empty panel"><span className="audit-mark">!</span><h3>Financial statements unavailable</h3><p>FINN does not fill gaps with estimated revenue, margins, debt, or growth. Enable live data or verify the latest company filings.</p></div>}
      <div className="module-status-grid">{Object.entries(report.module_status).map(([module, status]) =>
        <div className="module-status panel" key={module}><strong>{module.replaceAll("_", " ")}</strong><span>{status.replaceAll("_", " ")}</span>
          {report.module_sources?.[module]?.map((source) => <a key={source.url} href={source.url} target="_blank" rel="noopener noreferrer">{source.label} ↗</a>)}
        </div>
      )}</div>
    </section>
    <section className="section">
      <div className="section-heading"><div><p className="eyebrow">FLAGSHIP · NARRATIVE VS NUMBERS</p><h2>Commitments vs delivery</h2></div><span className="count-pill">{narrative.quarters_audited} audited</span></div>
      <div className="audit-empty panel"><span className="audit-mark">≋</span><h3>No audited quarters yet</h3><p>{narrative.credibility_summary}</p><p className="muted small">Module 6 remains empty until primary concall transcripts and matching reported results are available. No management statements have been fabricated.</p></div>
    </section>
    <p className="footnote">Only fetched Yahoo fields and derived chart indicators are shown as market data. Verify all financial figures against primary company filings; this is not investment advice.</p>
  </div>;
}
