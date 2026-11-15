"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { api, demoNotice, Stock } from "@/lib/api";

type SymbolSuggestion = { symbol: string; name: string; exchange: string; series: string };

export default function ResearchHub() {
  const router = useRouter();
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [suggestions, setSuggestions] = useState<SymbolSuggestion[]>([]);
  const [query, setQuery] = useState("");
  const [error, setError] = useState("");
  const [dataNotice, setDataNotice] = useState(demoNotice);
  useEffect(() => {
    api<{ stocks: Stock[]; data_notice?: string }>("/portfolio").then((result) => {
      setStocks(result.stocks);
      setDataNotice(result.data_notice ?? demoNotice);
    })
      .catch((reason) => setError(reason instanceof Error ? reason.message : "Could not load portfolio."));
  }, []);
  useEffect(() => {
    const value = query.trim();
    if (!value) return;
    let active = true;
    const timer = window.setTimeout(() => {
      api<{ symbols: SymbolSuggestion[] }>(`/symbols/search?q=${encodeURIComponent(value)}&limit=8`)
        .then((result) => { if (active) setSuggestions(result.symbols); })
        .catch((reason) => {
          if (active) {
            setSuggestions([]);
            setError(reason instanceof Error ? reason.message : "Could not search exchange symbols.");
          }
        });
    }, 160);
    return () => {
      active = false;
      window.clearTimeout(timer);
    };
  }, [query]);
  const filtered = useMemo(() => stocks.filter((stock) =>
    `${stock.ticker} ${stock.company_name} ${stock.sector}`.toLowerCase().includes(query.toLowerCase())
  ), [stocks, query]);
  function submitTicker(event: React.FormEvent) {
    event.preventDefault();
    const value = query.trim().toUpperCase().replace(/\.NS$/, "");
    if (value) router.push(`/research/${encodeURIComponent(value)}`);
  }
  function chooseSuggestion(symbol: string) {
    setQuery(symbol);
    router.push(`/research/${encodeURIComponent(symbol)}`);
  }
  return <div className="screen">
    <div className="page-title-row"><div><p className="eyebrow">PULL · PRIMARY-SOURCE RESEARCH</p><h1>Company explorer</h1><p className="muted">Build a view, then verify it at the source.</p></div><span className="page-icon">⌕</span></div>
    <div className="demo-banner">{dataNotice}</div>
    <form className="search-box" onSubmit={submitTicker}><span>⌕</span><input value={query} onChange={(event) => { setQuery(event.target.value); if (!event.target.value.trim()) setSuggestions([]); }} placeholder="Search a company or exchange symbol…" aria-label="Search company or ticker" autoComplete="off" /><button className="button button-dark">Research</button></form>
    {suggestions.length > 0 && <div className="symbol-suggestions" role="listbox" aria-label="Exchange symbol suggestions">
      {suggestions.map((item) => <button type="button" className="symbol-suggestion" key={`${item.exchange}:${item.symbol}`} onClick={() => chooseSuggestion(item.symbol)} role="option" aria-selected={false}>
        <strong>{item.symbol}</strong><span>{item.name}</span><small>{item.exchange}{item.series ? ` · ${item.series}` : ""}</small>
      </button>)}
    </div>}
    <div className="section-heading portfolio-heading"><div><p className="eyebrow">YOUR WATCHLIST</p><h2>{filtered.length} companies</h2></div><span className="muted small">Illustrative quotes</span></div>
    {error && <div className="error-card">{error}</div>}
    <div className="stock-grid">{filtered.map((stock) => <Link className="stock-card panel" href={`/research/${stock.ticker}`} key={stock.ticker}>
      <div className="stock-card-head"><span className="ticker-badge">{stock.ticker.slice(0, 2)}</span><span className={`change ${stock.market_data.change_percent >= 0 ? "positive" : "negative"}`}>{stock.market_data.change_percent > 0 ? "+" : ""}{stock.market_data.change_percent}%</span></div>
      <h3>{stock.ticker}</h3><p className="muted stock-name">{stock.company_name}</p>
      <div className="stock-price">₹{stock.market_data.current_price.toLocaleString("en-IN")}</div>
      <div className="item-meta">{stock.sector} <span>·</span> P/E {stock.market_data.pe_ratio ?? "—"}</div>
      <div className="source-note">{stock.market_data_source ?? "Demo seed"}{stock.quote_date ? ` · ${stock.quote_date}` : ""}</div>
    </Link>)}</div>
    {filtered.length === 0 && <div className="empty-state panel"><span>⌕</span><h3>No watchlist match</h3><p>Submit the search above to open an unverified NSE ticker.</p></div>}
    <p className="footnote">Ad-hoc ticker entry creates a clearly marked unverified placeholder; it does not fetch or validate exchange data.</p>
  </div>;
}
