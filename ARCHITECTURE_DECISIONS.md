# FINN — Architecture Decisions & Context Record

> **Purpose**: Persistent, single-source-of-truth document capturing every architectural decision, design rationale, constraint, and contextual assumption made during the FINN build. This is the document you pull up when someone asks *"Why did you do it this way?"*

---

## Table of Contents
1. [Project Context & Constraints](#1-project-context--constraints)
2. [Architectural Decision Records (ADRs)](#2-architectural-decision-records-adrs)
3. [Technology Stack Summary](#3-technology-stack-summary)
4. [Data Source Decisions](#4-data-source-decisions)
5. [AI/LLM Strategy](#5-aillm-strategy)
6. [Security & Privacy Posture](#6-security--privacy-posture)
7. [Open Items & Future Considerations](#7-open-items--future-considerations)

---

## 1. Project Context & Constraints

### What Is FINN?
FINN is a mobile-first AI-powered financial investment agent built for the **ENAM Holdings Founding AI Engineer Build Challenge**. It operates across three tightly integrated pillars:
- **Push**: Proactive intelligence — windowed digest, anomaly alerts, noise filtering
- **Pull**: On-demand primary-source-grounded research — 8 fundamental modules, Narrative vs Numbers engine
- **The Network**: Investor's personal/professional connection graph woven into Push and Pull

### Challenge Constraints
| Constraint | Implication |
|---|---|
| **Mobile-first delivery** | Must run on an evaluator's phone with zero friction. "A demo that doesn't run is the worst outcome." |
| **Primary source grounding** | No broker notes, no financial news aggregators. Only annual reports, concall transcripts, audited financial statements. |
| **15–20 stock portfolio** | Must handle a curated portfolio deeply, plus generalize to any NSE ticker on demand. |
| **Realistic synthetic network** | Network contacts must be realistic but synthetic (no real PII). Must overlap with portfolio companies to demonstrate value. |
| **AI build history required** | Must submit a log of how AI was used, prompt strategies, course corrections — tracked in `BUILD_LOG.md`. |
| **Solo builder** | This is a founding engineer challenge — the entire system is built by one person with AI assistance. |

### Non-Functional Requirements
- **Latency**: Push digest generation < 5s. Pull research modules < 15s per module. Network queries < 1s.
- **Reliability**: Demo must work 100% of the time. No live-scraping single points of failure during evaluation.
- **Cost**: Must operate within free/low-cost API tiers (Gemini free tier, yfinance free, Screener.in public pages).

---

## 2. Architectural Decision Records (ADRs)

### ADR-001: Mobile Client — Next.js 14+ PWA over React Native Expo
- **Status**: ✅ Decided (User Confirmed)
- **Date**: 2026-11-13
- **Context**: The challenge explicitly warns that a demo that doesn't run is the worst outcome. Evaluators need to test on their phones.
- **Options Considered**:
  - **Option A: Next.js 14+ Mobile-First Responsive Web App (PWA)**: Deploy to Vercel, evaluators open URL or scan QR code, works instantly on any phone browser.
  - **Option B: React Native with Expo**: True native app feel, but requires evaluators to have Expo Go installed or deal with potential SDK version mismatches.
- **Decision**: Option A — Next.js PWA
- **Rationale**: Zero-friction access is the single most important demo quality. PWA guarantees any evaluator on any phone can test immediately. The mobile viewport shell (centered frame on desktop, full-bleed on phone) provides a convincing mobile experience. Web push limitations are irrelevant since we use an in-app alert feed.
- **Trade-offs Accepted**: No native haptics, no native bottom sheets (replaced with Framer Motion drawers), no system-level push notifications.

---

### ADR-002: Graph Engine — In-Memory NetworkX + SQLite over Neo4j
- **Status**: ✅ Decided (Auto — clearly superior)
- **Date**: 2026-11-13
- **Context**: An investor's personal network is ~100–1,000 nodes and ~5,000 edges. We need BFS shortest-path, expertise clustering, and 2nd-degree reach queries.
- **Options Considered**:
  - **Option A: NetworkX (in-memory) + SQLite for persistence**: Zero infrastructure, microsecond query times, single-file persistence, Python-native.
  - **Option B: Neo4j / Memgraph**: Full graph database with Cypher queries, built for massive graph traversal.
- **Decision**: Option A — NetworkX + SQLite
- **Rationale**: Neo4j is designed for millions of nodes. An investor's personal network is 3–4 orders of magnitude smaller. Neo4j would introduce JVM overhead, Docker dependency, network latency, cloud hosting costs, and operational complexity — all for zero benefit at this scale. NetworkX executes BFS in microseconds with a few lines of Python.
- **When This Would Change**: If FINN scaled to a multi-tenant platform with thousands of investors and cross-network intelligence, Neo4j would become the right choice.

---

### ADR-003: Financial Calculations — Deterministic Code over LLM Computation
- **Status**: ✅ Decided (Auto — clearly superior)
- **Date**: 2026-11-13
- **Context**: FINN computes QoQ/YoY revenue growth, EBITDA margins, volume spike multiples, P/E ratios, and other financial metrics.
- **Options Considered**:
  - **Option A: Pure Python/Pandas code**: Deterministic, 100% accurate, zero-cost, instant.
  - **Option B: Ask the LLM to compute**: Convenient but prone to arithmetic hallucination.
- **Decision**: Option A — Deterministic code
- **Rationale**: LLMs routinely hallucinate basic arithmetic, especially in multi-row table contexts. Financial calculations must be 100% accurate. There is zero upside to using an LLM for math when `pandas` computes it perfectly in milliseconds. This is the "Zero-Arithmetic Policy for LLMs" — LLMs synthesize and reason; code computes.
- **When This Would Change**: Never for arithmetic. LLMs may be used for *interpreting* computed numbers (e.g., "Is 15% ROCE good for this sector?"), but never for the computation itself.

---

### ADR-004: Agent Architecture — Direct Modular Pipeline over Multi-Agent Frameworks
- **Status**: ✅ Decided (Auto — clearly superior)
- **Date**: 2026-11-13
- **Context**: FINN orchestrates multiple AI tasks: classification, extraction, synthesis, graph traversal. The question is how to wire them together.
- **Options Considered**:
  - **Option A: Direct Pipeline with Pydantic schemas**: Each step is a Python function with typed inputs/outputs. Orchestration is explicit Python code. LLM calls are direct API calls with structured output schemas.
  - **Option B: Multi-Agent Frameworks (CrewAI, AutoGen, LangGraph)**: Agents with roles, tools, and conversation loops.
- **Decision**: Option A — Direct Pipeline
- **Rationale**: Heavy agent frameworks introduce: (1) unpredictable token loops where agents talk to each other burning tokens, (2) fragile tool-calling chains that break when an LLM generates malformed tool calls, (3) high latency from sequential agent conversations, (4) opaque debugging. A direct pipeline is deterministic, fast, and fully debuggable. Every LLM call has a Pydantic response schema enforcing structured output.
- **When This Would Change**: If FINN needed truly open-ended multi-step reasoning with dynamic tool selection (e.g., a general-purpose research assistant), an agent framework might add value. For FINN's well-defined modules, it adds only overhead.

---

### ADR-005: Demo Data Strategy — Pre-Seeded Hybrid Cache + Live Crawler
- **Status**: ✅ Decided (Auto — clearly superior)
- **Date**: 2026-11-13
- **Context**: FINN needs financial data, corporate announcements, and concall transcripts for 15–20 portfolio stocks, plus the ability to generalize to any NSE ticker.
- **Options Considered**:
  - **Option A: Pre-seeded cache for portfolio + live crawler for ad-hoc tickers**: Portfolio data is fetched, processed, and cached before the demo. New tickers trigger live fetching.
  - **Option B: Pure live scraping**: Everything is fetched in real-time during the demo.
- **Decision**: Option A — Hybrid Cache
- **Rationale**: Live scraping NSE/BSE/Screener during a demo is vulnerable to: IP rate limiting, CAPTCHAs, temporary site downtime, and slow response times. Pre-seeding the portfolio guarantees the demo works 100% of the time regardless of external service availability. The live crawler for ad-hoc tickers proves generalization without betting the demo on third-party uptime.
- **Fallback**: If a live crawler fails for an ad-hoc ticker, FINN displays a graceful "data loading" state rather than crashing.

---

### ADR-006: LLM Model Routing — Three-Tier Strategy
- **Status**: ✅ Decided
- **Date**: 2026-11-13
- **Context**: Different tasks have vastly different complexity, latency, and cost profiles. Using a single model for everything is wasteful and slow.
- **Tiers**:
  - **Tier 3 (Deterministic Code)**: All math, threshold checks, volume multiples. Cost: $0. Latency: <1ms.
  - **Tier 1 (Fast LLM — Gemini 2.5 Flash / GPT-4o-mini)**: Announcement classification (material vs routine), table extraction, NER. Cost: minimal. Latency: ~400ms.
  - **Tier 2 (Reasoning LLM — Gemini 2.5 Pro / Claude 3.5 Sonnet)**: Narrative vs Numbers synthesis, Bull vs Bear thesis, explaining network relevance. Cost: moderate. Latency: 2–5s.
- **Rationale**: This routing ensures: (1) financial accuracy via code, (2) fast classification via lightweight models, (3) deep synthesis via frontier models only when needed. Prompt caching (Gemini/Anthropic) reduces cost by 75% for repeated concall transcript analysis.

---

### ADR-007: Primary Source Discipline — No Broker Notes, No Financial News
- **Status**: ✅ Decided (Challenge Requirement)
- **Date**: 2026-11-13
- **Context**: The ENAM challenge explicitly values primary source grounding over aggregated financial news.
- **Decision**: All research modules are grounded exclusively in:
  - Annual reports and 10-K filings
  - Quarterly earnings concall transcripts
  - Audited financial statements (balance sheet, P&L, cash flow)
  - Official corporate announcements (NSE/BSE filings)
- **What Is Explicitly Excluded**: MoneyControl articles, Economic Times summaries, broker research reports, Twitter/X sentiment, YouTube analysis.
- **Rationale**: Primary sources are the only materials where information is legally attributable and verifiable. Third-party summaries introduce interpretation bias, factual errors, and speculative framing. The "Narrative vs Numbers" engine *requires* primary transcripts to audit management's own words against actual results.

---

## 3. Technology Stack Summary

| Layer | Technology | Why This Choice |
|---|---|---|
| **Frontend** | Next.js 14+ (App Router), Tailwind CSS, Framer Motion, Lucide Icons | Mobile-first PWA, server components for data fetching, instant Vercel deployment |
| **Backend** | FastAPI (Python 3.11+) | Async-native, Pydantic-first, fast serialization, excellent LLM SDK ecosystem |
| **Graph Engine** | NetworkX + SQLite | Perfect for personal-scale graphs (~1K nodes), zero infrastructure |
| **Market Data** | yfinance | Free, reliable EOD price/volume/fundamentals for NSE/BSE stocks |
| **Fundamentals** | Screener.in (scraper) + BSE corporate filings | Primary source financial statements and concall transcripts |
| **LLM Gateway** | Google Gemini API (primary), OpenAI/Anthropic (fallback) | Gemini 2.5 Flash has generous free tier; Pro has 1M+ token context for concalls |
| **Entity Resolution** | RapidFuzz (Jaro-Winkler) + LLM disambiguation | Fast fuzzy matching for 95% of cases, LLM fallback for ambiguous names |
| **Deployment** | Vercel (frontend) + Railway/Render (backend) | Free tier hosting, instant deployment, zero DevOps |
| **Database** | SQLite (file-based) | Zero-config persistence for cached data, portfolio state, and graph adjacency |

---

## 4. Data Source Decisions

### Portfolio Data Sources
| Data Need | Source | Reliability | Caching Strategy |
|---|---|---|---|
| EOD Price, Volume, 20d MA | yfinance API | High (Yahoo Finance backend) | Cache daily, refresh on market open |
| P/E, EV/EBITDA, Market Cap | yfinance API | High | Cache with 24h TTL |
| Balance Sheet, P&L, Cash Flow | Screener.in (scraper) | Medium (website scraping) | Pre-seeded for portfolio, live for ad-hoc |
| Concall Transcripts | Screener.in / BSE filings | Medium | Pre-seeded for last 4 quarters of portfolio stocks |
| Corporate Announcements | NSE/BSE RSS + scraper | Medium | Pre-seeded recent filings, simulated feed for demo |
| Network Contacts | Synthetic dataset | N/A (mock) | Loaded from `network_seed.json` at startup |

### Why Not Bloomberg/Reuters/FactSet?
- Cost: Enterprise terminals cost $20K+/year. This challenge targets a prototype, not a production trading desk.
- yfinance + Screener.in provide sufficient coverage for Indian NSE/BSE listed stocks at zero cost.
- The architecture is designed with a clean data abstraction layer — swapping to Bloomberg/FactSet APIs in production requires only changing the data provider implementation, not the analysis engines.

---

## 5. AI/LLM Strategy

### Prompt Design Principles
1. **Structured Output Always**: Every LLM call returns JSON conforming to a Pydantic schema. No free-text parsing.
2. **Context Window Discipline**: Concall transcripts can be 30–80 pages. We use Gemini's 1M+ token context window with prompt caching to avoid chunking artifacts.
3. **Grounding Instructions**: Every synthesis prompt includes explicit instructions: "Base your analysis ONLY on the provided document. Do not use external knowledge. If information is not present in the document, state 'Not mentioned in the provided filing.'"
4. **Zero-Arithmetic Policy**: Prompts never ask the LLM to compute percentages, ratios, or growth rates. These are pre-computed in Python and injected into the prompt as facts.

### LLM Failure Modes & Mitigations
| Failure Mode | Mitigation |
|---|---|
| Hallucinated financial numbers | Zero-Arithmetic Policy — all numbers computed in code |
| Fabricated sources/citations | Grounding instructions + only primary docs in context |
| Malformed JSON output | Pydantic validation with retry (max 2 retries) |
| API rate limit / downtime | Tiered fallback: Gemini → OpenAI → cached response |
| Excessively long/verbose output | Max token limits + structured output schemas |

---

## 6. Security & Privacy Posture

### Data Classification
| Data Type | Classification | Handling |
|---|---|---|
| Market data (prices, volumes) | Public | No restrictions |
| Corporate filings | Public | No restrictions |
| Portfolio holdings | Private (investor) | Stored locally, not shared with LLM training |
| Network contacts (synthetic) | Sensitive (demo) | PII masked before LLM API calls |
| Network contacts (real, future) | Highly Sensitive | AES-256 at rest, tenant-isolated, PII masking gateway |

### PII Masking Gateway (Design Decision)
Before any network-related prompt is sent to external LLM APIs:
1. Personal contact details (phone, email, personal notes) are stripped.
2. Names can be pseudonymized if the query doesn't require name resolution.
3. Only role, company, sector, and relationship metadata are sent.

This ensures that even if an LLM provider logs prompts, no actionable PII is exposed.

---

## 7. Open Items & Future Considerations

### Decided But Not Yet Implemented
- [ ] Prompt caching configuration for Gemini API (concall transcripts)
- [ ] PII masking pipeline for network prompts
- [ ] Graceful degradation for live crawler failures

### Future Production Considerations (Out of Scope for Challenge)
- **Multi-Tenant Isolation**: If FINN becomes a SaaS product, each investor's network graph and portfolio must be fully isolated with row-level security.
- **Real-Time Streaming**: Replace EOD polling with WebSocket market data feeds for intraday alerts.
- **Bloomberg/FactSet Integration**: Swap yfinance data provider for institutional-grade data in production.
- **Native Mobile App**: If user base grows, consider React Native or Flutter for true native experience with background push notifications.
- **Compliance**: SEBI insider trading regulations may apply if FINN surfaces network intelligence that could constitute UPSI (Unpublished Price Sensitive Information). Legal review required before production deployment.

---

*This document is updated whenever a new architectural decision is made or an existing decision is revised. Last updated: 2026-11-13.*
