"use client";

import { useState } from "react";
import { api } from "@/lib/api";

type Reply = { response: { content: string }; referenced_sources: string[] };

export default function Copilot() {
  const [open, setOpen] = useState(false);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function ask(event: React.FormEvent) {
    event.preventDefault();
    if (!question.trim() || busy) return;
    setBusy(true);
    setError("");
    try {
      const result = await api<Reply>("/copilot/chat", {
        method: "POST",
        body: JSON.stringify({ messages: [{ role: "user", content: question }] })
      });
      setAnswer(result.response.content);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not reach FINN.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <button className="copilot-launch" onClick={() => setOpen(!open)} aria-expanded={open}>
        {open ? "×" : "✳"} <span>{open ? "Close" : "Ask FINN"}</span>
      </button>
      {open && <section className="copilot-panel panel">
        <div className="panel-heading"><div><p className="eyebrow">FINN COPILOT</p><h2>Ask with context</h2></div><button className="icon-button" onClick={() => setOpen(false)} aria-label="Close">×</button></div>
        <p className="muted small">Demo assistant only. It does not provide verified financial research or investment advice.</p>
        {answer && <div className="copilot-answer">{answer}</div>}
        {error && <p className="error-text">{error}</p>}
        <form className="ask-form" onSubmit={ask}>
          <input value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Who can I ask about retail?" aria-label="Ask FINN" />
          <button className="button button-dark" disabled={busy}>{busy ? "…" : "Ask"}</button>
        </form>
      </section>}
    </>
  );
}
