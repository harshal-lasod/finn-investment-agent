"use client";

import { useEffect, useState } from "react";
import { api, demoNotice } from "@/lib/api";

type Announcement = { id: string; ticker: string; company_name: string; timestamp: string; title: string; category: string; summary: string; is_material: boolean; metric_headline?: string; network_context_text?: string };
type Alert = { id: string; ticker: string; severity: string; headline: string; trigger_value: string };
type Digest = { material_announcements: Announcement[]; routine_announcements: Announcement[]; material_count: number; routine_count: number; data_notice?: string };

export default function PushPage() {
  const [windowSize, setWindowSize] = useState<"24h" | "7d">("24h");
  const [ticker, setTicker] = useState("ALL");
  const [digest, setDigest] = useState<Digest | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [routineOpen, setRoutineOpen] = useState(false);
  const [error, setError] = useState("");
  const [dataNotice, setDataNotice] = useState(demoNotice);

  useEffect(() => {
    let active = true;
    Promise.all([
      api<Digest>(`/portfolio/${ticker}/digest?window=${windowSize}`),
      api<{ alerts: Alert[]; data_notice?: string }>("/portfolio/alerts")
    ]).then(([feed, triggerData]) => {
      if (active) {
        setDigest(feed);
        setAlerts(triggerData.alerts);
        setDataNotice(`${triggerData.data_notice ?? demoNotice} Digest announcements are synthetic examples.`);
        setError("");
      }
    }).catch((reason) => { if (active) setError(reason instanceof Error ? reason.message : "Could not load feed."); });
    return () => { active = false; };
  }, [ticker, windowSize]);

  return <div className="screen">
    <div className="page-title-row"><div><p className="eyebrow">PORTFOLIO OVERVIEW · DEMO</p><h1>Your signal feed</h1><p className="muted">Noise filtered. Context included.</p></div><span className="live-pill"><i className="status-dot" /> Demo</span></div>
    <div className="demo-banner">{dataNotice}</div>
    <div className="toolbar">
      <select value={ticker} onChange={(event) => setTicker(event.target.value)} aria-label="Filter by company">
        <option value="ALL">All companies</option><option>TRENT</option><option>KAYNES</option><option>LT</option><option>ITC</option><option>INFY</option><option>SBIN</option>
      </select>
      <div className="segmented">
        {(["24h", "7d"] as const).map((value) => <button key={value} onClick={() => setWindowSize(value)} className={windowSize === value ? "selected" : ""}>{value}</button>)}
      </div>
    </div>
    <section className="section">
      <div className="section-heading"><div><p className="eyebrow">ANOMALIES</p><h2>Worth a look</h2></div><span className="count-pill">{alerts.length}</span></div>
      <div className="alert-list">{alerts.slice(0, 4).map((alert) => <article className="alert-card" key={alert.id}><span className={`alert-icon ${alert.severity === "HIGH" ? "alert-high" : ""}`}>↗</span><div><div className="item-meta">{alert.ticker} <span>·</span> {alert.trigger_value}</div><strong>{alert.headline}</strong></div><span className="chevron">›</span></article>)}</div>
    </section>
    {error && <div className="error-card">{error} <button onClick={() => setWindowSize(windowSize)}>Retry</button></div>}
    <section className="section">
      <div className="section-heading"><div><p className="eyebrow">PUSH INTELLIGENCE · {windowSize}</p><h2>Material updates</h2></div><span className="count-pill">{digest?.material_count ?? "—"}</span></div>
      <div className="feed-list">{digest?.material_announcements.map((item) => <article className="feed-card panel" key={item.id}>
        <div className="item-meta">{item.ticker} <span>·</span> {item.category.replaceAll("_", " ")} <span>·</span> {new Date(item.timestamp).toLocaleString()}</div>
        <h3>{item.title}</h3><p>{item.summary}</p>
        {item.metric_headline && <span className="metric-chip">{item.metric_headline}</span>}
        {item.network_context_text && <div className="network-note">◎ {item.network_context_text}</div>}
        <div className="synthetic-tag">SYNTHETIC SCENARIO</div>
      </article>)}</div>
      {digest && digest.routine_count > 0 && <section className="routine-tray panel">
        <button className="routine-toggle" onClick={() => setRoutineOpen(!routineOpen)}><span>Routine filings <small>{digest.routine_count} items collapsed</small></span><b>{routineOpen ? "−" : "+"}</b></button>
        {routineOpen && digest.routine_announcements.map((item) => <div className="routine-item" key={item.id}><strong>{item.ticker}</strong><span>{item.title}</span><small>{item.summary}</small></div>)}
      </section>}
    </section>
    <p className="footnote">No exchange feeds are connected in this build. All events and metrics shown are illustrative test records.</p>
  </div>;
}
