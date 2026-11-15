"""
FINN Database Setup
File: backend/database.py
SQLite with aiosqlite, WAL mode, no FK constraints on cache tables
"""
from __future__ import annotations
import aiosqlite
import json
import os
from contextlib import asynccontextmanager
from backend.config import settings


@asynccontextmanager
async def get_db():
    """Async context manager for database connections."""
    async with aiosqlite.connect(settings.DATABASE_URL) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA foreign_keys=OFF")
        yield db


async def init_db() -> None:
    """Create all tables on startup."""
    # Ensure storage directory exists
    db_dir = os.path.dirname(settings.DATABASE_URL)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    async with aiosqlite.connect(settings.DATABASE_URL) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA foreign_keys=OFF")

        # 1. Companies / Portfolio Table (is_portfolio_holding flag)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS companies (
                ticker TEXT PRIMARY KEY,
                company_name TEXT NOT NULL,
                sector TEXT NOT NULL,
                market_cap_category TEXT NOT NULL,
                is_portfolio_holding INTEGER DEFAULT 1,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 2. Market Data Cache (NO foreign keys — works for any ticker)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS market_data_cache (
                ticker TEXT PRIMARY KEY,
                current_price REAL NOT NULL,
                change_absolute REAL NOT NULL,
                change_percent REAL NOT NULL,
                day_volume INTEGER NOT NULL,
                volume_20d_avg REAL NOT NULL,
                volume_multiple REAL NOT NULL,
                pe_ratio REAL,
                market_cap_cr REAL NOT NULL,
                high_52w REAL NOT NULL,
                low_52w REAL NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 3. Announcements (NO foreign keys)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS announcements (
                id TEXT PRIMARY KEY,
                ticker TEXT NOT NULL,
                company_name TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                is_material INTEGER NOT NULL,
                materiality_score REAL NOT NULL,
                summary TEXT NOT NULL,
                source_url TEXT,
                network_connection_id TEXT,
                network_context_text TEXT,
                metric_headline TEXT,
                is_classified INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 4. Alerts (NO foreign keys)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id TEXT PRIMARY KEY,
                ticker TEXT NOT NULL,
                company_name TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                headline TEXT NOT NULL,
                trigger_value TEXT NOT NULL,
                network_context TEXT,
                is_dismissed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 5. Network Nodes
        await db.execute("""
            CREATE TABLE IF NOT EXISTS network_nodes (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                current_role TEXT NOT NULL,
                current_company TEXT NOT NULL,
                closeness_score INTEGER NOT NULL CHECK(closeness_score BETWEEN 1 AND 5),
                role_type TEXT NOT NULL,
                past_companies_json TEXT NOT NULL,
                alma_maters_json TEXT NOT NULL,
                expertise_tags_json TEXT NOT NULL,
                last_interaction_date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 6. Network Edges (with target_type column)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS network_edges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                target_type TEXT DEFAULT 'person',
                relationship_type TEXT NOT NULL,
                weight REAL DEFAULT 1.0,
                context_notes TEXT,
                UNIQUE(source_id, target_id, relationship_type)
            )
        """)

        # 7. Network Cache
        await db.execute("""
            CREATE TABLE IF NOT EXISTS network_cache (
                cache_key TEXT PRIMARY KEY,
                result_json TEXT NOT NULL,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL
            )
        """)

        # 8. Research Cache
        await db.execute("""
            CREATE TABLE IF NOT EXISTS research_cache (
                ticker TEXT PRIMARY KEY,
                report_json TEXT NOT NULL,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL
            )
        """)

        # 9. Narrative Cache
        await db.execute("""
            CREATE TABLE IF NOT EXISTS narrative_cache (
                ticker TEXT PRIMARY KEY,
                credibility_score REAL NOT NULL,
                credibility_summary TEXT NOT NULL,
                audit_entries_json TEXT NOT NULL,
                forward_guidance_json TEXT NOT NULL,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL
            )
        """)

        # 10. Digest Cache
        await db.execute("""
            CREATE TABLE IF NOT EXISTS digest_cache (
                cache_key TEXT PRIMARY KEY,
                digest_json TEXT NOT NULL,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS local_response_cache (
                cache_key TEXT PRIMARY KEY,
                payload_json TEXT NOT NULL,
                cached_at REAL NOT NULL,
                expires_at REAL NOT NULL
            )
        """)

        # Indexes
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_announcements_ticker_time ON announcements(ticker, timestamp DESC)"
        )
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_announcements_material ON announcements(is_material, timestamp DESC)"
        )
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_alerts_active ON alerts(is_dismissed, created_at DESC)"
        )
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_edges_source ON network_edges(source_id)"
        )
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_edges_target ON network_edges(target_id)"
        )

        await db.commit()


async def load_portfolio_seed(db_path: str, seed_file: str = "storage/portfolio_seed.json") -> None:
    """Load portfolio seed data into companies table on startup."""
    if not os.path.exists(seed_file):
        print(f"[WARN] Seed file not found: {seed_file}")
        return

    with open(seed_file, "r") as f:
        seed_data = json.load(f)

    async with aiosqlite.connect(db_path) as db:
        await db.execute("PRAGMA foreign_keys=OFF")
        for stock in seed_data:
            await db.execute(
                """
                INSERT OR REPLACE INTO companies
                    (ticker, company_name, sector, market_cap_category, is_portfolio_holding)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    stock["ticker"],
                    stock["company_name"],
                    stock["sector"],
                    stock["market_cap_category"],
                    stock.get("is_portfolio_holding", 1),
                ),
            )
        await db.commit()
    print(f"[INFO] Portfolio seed loaded: {len(seed_data)} stocks")
