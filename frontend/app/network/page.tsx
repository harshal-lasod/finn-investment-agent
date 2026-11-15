"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, demoNotice, Person } from "@/lib/api";

type NetworkResult = { person: Person; relevance_reason: string; path_from_investor: string[]; degree: number; suggested_icebreaker: string };
type Graph = { nodes: Person[]; edges: { source_id: string; target_id: string; relationship_type: string }[]; total_nodes: number; total_edges: number };

export default function NetworkPage() {
  const [graph, setGraph] = useState<Graph | null>(null);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<NetworkResult[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    api<Graph>("/network/graph").then(setGraph).catch((reason) => setError(reason instanceof Error ? reason.message : "Could not load graph."));
  }, []);
  async function search(event: React.FormEvent) {
    event.preventDefault();
    if (!query.trim()) return;
    setBusy(true);
    setError("");
    try {
      const response = await api<{ results: NetworkResult[] }>("/network/query", {
        method: "POST", body: JSON.stringify({ query, max_results: 8 })
      });
      setResults(response.results);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Search failed.");
    } finally { setBusy(false); }
  }
  const people = graph?.nodes.filter((node) => node.id !== "INVESTOR_ROOT") ?? [];
  return <div className="screen">
    <div className="page-title-row"><div><p className="eyebrow">THE NETWORK · SECOND-DEGREE REACH</p><h1>People behind the signal</h1><p className="muted">Expertise, shared context, and warm paths.</p></div><span className="page-icon">◎</span></div>
    <div className="demo-banner">{demoNotice} These profiles and relationships are computer-generated synthetic examples.</div>
    <form className="network-search panel" onSubmit={search}><div><p className="eyebrow">WHO SHOULD I CALL?</p><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Try: specialty chemicals or retail…" aria-label="Search network" /></div><button className="button button-dark" disabled={busy}>{busy ? "Searching…" : "Find people ↗"}</button></form>
    {error && <div className="error-card">{error}</div>}
    {results.length > 0 && <section className="section"><div className="section-heading"><div><p className="eyebrow">MATCHED EXPERTISE</p><h2>Possible paths</h2></div><button className="text-button" onClick={() => setResults([])}>Clear</button></div>
      <div className="result-list">{results.map((result) => <article className="result-card panel" key={result.person.id}>
        <div className="contact-avatar">{result.person.name.split(" ").map((part) => part[0]).join("")}</div>
        <div className="result-main"><div className="result-title"><strong>{result.person.name}</strong><span className="degree-pill">{result.degree}°</span></div><p>{result.person.current_role} · {result.person.current_company}</p><p className="muted small">{result.relevance_reason}</p><div className="path-line">{result.path_from_investor.join(" → ")}</div><Link href={`/network/diligence/${result.person.id}`} className="text-link">Open synthetic dossier →</Link></div>
      </article>)}</div>
      {results.length === 0 && <div className="empty-state panel">No matching demo contacts. Try a sector or expertise keyword.</div>}
    </section>}
    <section className="section">
      <div className="section-heading"><div><p className="eyebrow">YOUR GRAPH</p><h2>Expertise map</h2></div><span className="count-pill">{graph?.total_nodes ?? "—"} nodes</span></div>
      <div className="network-summary panel"><div className="network-orbit"><span className="orbit-center">You</span><span className="orbit-dot orbit-one">✦</span><span className="orbit-dot orbit-two">✦</span><span className="orbit-dot orbit-three">✦</span><span className="orbit-ring" /></div><div><h3>{graph?.total_edges ?? 0} overlapping paths</h3><p>First-degree contacts connect into shared employer and alumni clusters.</p><div className="tag-row"><span>Retail</span><span>EMS</span><span>Chemicals</span><span>Finance</span></div><small>Synthetic demo topology, not a real contact graph.</small></div></div>
    </section>
    <section className="section"><div className="section-heading"><div><p className="eyebrow">SAMPLE CONTACTS</p><h2>Warm reach</h2></div><span className="muted small">{people.length} synthetic</span></div>
      <div className="contact-grid">{people.slice(0, 8).map((person) => <Link href={`/network/diligence/${person.id}`} className="contact-card panel" key={person.id}><span className="avatar">{person.name.split(" ").map((part) => part[0]).join("")}</span><strong>{person.name}</strong><span>{person.current_company}</span><div className="tag-row">{person.expertise_tags.slice(0, 2).map((tag) => <i key={tag}>{tag}</i>)}</div><small>{person.closeness_score}/5 connection · Synthetic</small></Link>)}</div>
    </section>
  </div>;
}
