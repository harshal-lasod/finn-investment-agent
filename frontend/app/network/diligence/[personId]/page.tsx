"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api, demoNotice, Person } from "@/lib/api";

type Dossier = { person: Person; shortest_path_from_investor: string[]; degrees_of_separation: number; common_alumni: string[]; common_past_employers: string[]; talking_points: string[] };

export default function DiligencePage() {
  const { personId } = useParams<{ personId: string }>();
  const [data, setData] = useState<Dossier | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    api<Dossier>(`/network/diligence/${encodeURIComponent(personId)}`).then(setData)
      .catch((reason) => setError(reason instanceof Error ? reason.message : "Could not load contact."));
  }, [personId]);
  return <div className="screen">
    <Link href="/network" className="back-link">← Network explorer</Link>
    {error ? <div className="error-card">{error}</div> : !data ? <div className="loading-state">Opening synthetic dossier…</div> : <>
      <div className="demo-banner">{demoNotice} This contact profile is fictional and must not be used for diligence.</div>
      <section className="dossier-hero panel"><span className="dossier-avatar">{data.person.name.split(" ").map((part) => part[0]).join("")}</span><p className="eyebrow">SYNTHETIC CONTACT · {data.degrees_of_separation}° SEPARATION</p><h1>{data.person.name}</h1><p>{data.person.current_role} · {data.person.current_company}</p><div className="closeness">{Array.from({ length: 5 }, (_, i) => <span className={i < data.person.closeness_score ? "filled" : ""} key={i}>●</span>)} <small>Connection strength (demo)</small></div></section>
      <section className="section"><p className="eyebrow">SHORTEST PATH</p><div className="path-breadcrumb panel">{data.shortest_path_from_investor.map((name, index) => <span key={`${name}-${index}`}>{index > 0 && <b>→</b>}{name}</span>)}</div></section>
      <div className="metrics-grid two">
        <article className="metric-card panel"><p className="eyebrow">SHARED EDUCATION</p>{data.common_alumni.map((item) => <div className="metric-row" key={item}><span>{item}</span><strong>Shared</strong></div>)}</article>
        <article className="metric-card panel"><p className="eyebrow">SHARED EMPLOYERS</p>{data.common_past_employers.map((item) => <div className="metric-row" key={item}><span>{item}</span><strong>Shared</strong></div>)}</article>
      </div>
      <section className="section"><div className="section-heading"><div><p className="eyebrow">CONVERSATION STARTERS</p><h2>Talking points</h2></div></div><div className="feed-list">{data.talking_points.map((point, index) => <div className="talking-point panel" key={point}><span>0{index + 1}</span>{point}</div>)}</div></section>
    </>}
  </div>;
}
