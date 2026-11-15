"""Yahoo Finance adapter and deterministic technical indicators."""
from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from backend.config import settings
from backend.services.local_cache import get_local_cache, set_local_cache
from backend.models.market import MarketData

logger = logging.getLogger(__name__)
YAHOO_SOURCE = "Yahoo Finance via yfinance (unofficial; may be delayed or incomplete)"


class MarketDataService:
    """Fetch and cache market snapshots without blocking FastAPI's event loop."""

    def __init__(self) -> None:
        self._cache: dict[str, tuple[float, dict[str, Any]]] = {}
        self._errors: dict[str, str] = {}

    @staticmethod
    def compute_volume_multiple(day_volume: int, average_volume: float) -> float:
        return round(day_volume / max(average_volume, 1.0), 2)

    @staticmethod
    def compute_price_change_pct(current: float, previous_close: float) -> float:
        if previous_close == 0:
            return 0.0
        return round((current - previous_close) / previous_close * 100, 2)

    @staticmethod
    def build_market_data(
        current: float, previous_close: float, day_volume: int,
        average_volume: float, *, pe_ratio: float | None = None,
        market_cap_cr: float = 0.0,
    ) -> MarketData:
        average = max(average_volume, 1.0)
        return MarketData(
            current_price=current,
            change_absolute=round(current - previous_close, 2),
            change_percent=MarketDataService.compute_price_change_pct(current, previous_close),
            day_volume=day_volume,
            volume_20d_avg=average,
            volume_multiple=MarketDataService.compute_volume_multiple(day_volume, average),
            pe_ratio=pe_ratio,
            market_cap_cr=market_cap_cr,
            high_52w=current,
            low_52w=current,
        )

    @staticmethod
    def calculate_technicals(history: pd.DataFrame) -> dict[str, float | None]:
        """Calculate common indicators from daily OHLCV bars; no model-generated math."""
        close = history["Close"].dropna().astype(float)
        if close.empty:
            return {}
        latest = close.iloc[-1]
        result: dict[str, float | None] = {
            "sma_20": round(float(close.rolling(20).mean().iloc[-1]), 2) if len(close) >= 20 else None,
            "sma_50": round(float(close.rolling(50).mean().iloc[-1]), 2) if len(close) >= 50 else None,
            "sma_200": round(float(close.rolling(200).mean().iloc[-1]), 2) if len(close) >= 200 else None,
        }

        change = close.diff()
        gains = change.clip(lower=0).ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()
        losses = (-change.clip(upper=0)).ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()
        relative_strength = gains / losses.replace(0, float("nan"))
        rsi = 100 - 100 / (1 + relative_strength)
        if len(close) >= 15:
            result["rsi_14"] = round(float(rsi.iloc[-1]), 2) if pd.notna(rsi.iloc[-1]) else 100.0
        else:
            result["rsi_14"] = None

        macd = close.ewm(span=12, adjust=False).mean() - close.ewm(span=26, adjust=False).mean()
        signal = macd.ewm(span=9, adjust=False).mean()
        result["macd"] = round(float(macd.iloc[-1]), 3)
        result["macd_signal"] = round(float(signal.iloc[-1]), 3)
        if len(close) >= 20:
            average = close.rolling(20).mean().iloc[-1]
            deviation = close.rolling(20).std(ddof=0).iloc[-1]
            result["bollinger_upper_20"] = round(float(average + 2 * deviation), 2)
            result["bollinger_lower_20"] = round(float(average - 2 * deviation), 2)
        else:
            result["bollinger_upper_20"] = None
            result["bollinger_lower_20"] = None

        if {"High", "Low"}.issubset(history.columns) and len(history) >= 14:
            high = history["High"].astype(float)
            low = history["Low"].astype(float)
            previous = close.shift(1)
            true_range = pd.concat(
                [(high - low), (high - previous).abs(), (low - previous).abs()], axis=1
            ).max(axis=1)
            atr = true_range.rolling(14).mean().iloc[-1]
            result["atr_14"] = round(float(atr), 2) if pd.notna(atr) else None
        else:
            result["atr_14"] = None
        result["latest_close"] = round(float(latest), 2)
        return result

    @staticmethod
    def _latest_statement_values(statement: pd.DataFrame, fields: dict[str, str]) -> dict[str, Any]:
        output: dict[str, Any] = {}
        for key, row_name in fields.items():
            if row_name not in statement.index:
                continue
            values = statement.loc[row_name].dropna()
            if values.empty:
                continue
            value = values.iloc[0]
            output[key] = round(float(value), 2) if pd.notna(value) else None
        if len(statement.columns):
            output["period"] = str(statement.columns[0].date()) if hasattr(statement.columns[0], "date") else str(statement.columns[0])
        return output

    @classmethod
    def _fetch_snapshot(
        cls, ticker: str, cached_fundamentals: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        import yfinance as yf

        symbol = f"{ticker.upper().removesuffix('.NS')}.NS"
        company = yf.Ticker(symbol)
        history = company.history(period="1y", interval="1d", auto_adjust=False, timeout=10)
        if history.empty or "Close" not in history or len(history["Close"].dropna()) < 2:
            return None

        close = history["Close"].dropna().astype(float)
        current = float(close.iloc[-1])
        previous = float(close.iloc[-2])
        volume = history["Volume"].dropna() if "Volume" in history else pd.Series(dtype=float)
        current_volume = int(volume.iloc[-1]) if len(volume) else 0
        average_volume = float(volume.tail(20).mean()) if len(volume) else 0.0
        quote = cls.build_market_data(current, previous, current_volume, average_volume)
        quote_currency = None
        financial_currency = None
        market_cap = 0.0
        pe_ratio = None
        try:
            info = company.get_info()
            quote_currency = info.get("currency")
            financial_currency = info.get("financialCurrency")
            pe_ratio = info.get("trailingPE")
            raw_market_cap = info.get("marketCap")
            if raw_market_cap and quote_currency == "INR":
                market_cap = round(float(raw_market_cap) / 10_000_000, 2)
        except Exception:
            logger.info("Yahoo currency/valuation metadata unavailable for %s", symbol)
        quote = quote.model_copy(update={"pe_ratio": pe_ratio, "market_cap_cr": market_cap})
        quote = quote.model_copy(update={
            "high_52w": round(float(close.tail(252).max()), 2),
            "low_52w": round(float(close.tail(252).min()), 2),
            "last_updated": datetime.now(timezone.utc),
        })
        last_index = history.dropna(subset=["Close"]).index[-1]
        quote_date = last_index.date().isoformat() if hasattr(last_index, "date") else str(last_index)
        price_history = [
            {
                "date": index.date().isoformat() if hasattr(index, "date") else str(index),
                "close": round(float(row["Close"]), 2),
            }
            for index, row in history.dropna(subset=["Close"]).tail(260).iterrows()
        ]

        fundamentals: dict[str, Any] = cached_fundamentals or {}
        if cached_fundamentals is None:
            try:
                income = company.income_stmt
                balance = company.balance_sheet
                cashflow = company.cashflow
                fundamentals = {
                    "income_statement": cls._latest_statement_values(income, {
                        "revenue": "Total Revenue",
                        "operating_income": "Operating Income",
                        "ebitda": "EBITDA",
                        "net_income": "Net Income",
                    }),
                    "balance_sheet": cls._latest_statement_values(balance, {
                        "total_assets": "Total Assets",
                        "total_debt": "Total Debt",
                        "stockholders_equity": "Stockholders Equity",
                        "cash_and_equivalents": "Cash And Cash Equivalents",
                    }),
                    "cash_flow": cls._latest_statement_values(cashflow, {
                        "operating_cash_flow": "Operating Cash Flow",
                        "capital_expenditure": "Capital Expenditure",
                        "free_cash_flow": "Free Cash Flow",
                    }),
                }
                fundamentals = {name: values for name, values in fundamentals.items() if values}
            except Exception:
                logger.warning("Yahoo Finance statements unavailable for %s", symbol, exc_info=True)

        yahoo_base = f"https://finance.yahoo.com/quote/{symbol}/"

        return {
            "ticker": ticker.upper().removesuffix(".NS"),
            "quote": quote.model_dump(mode="json"),
            "quote_date": quote_date,
            "price_history": price_history,
            "technicals": cls.calculate_technicals(history),
            "fundamentals": fundamentals,
            "source_urls": {
                "quote": yahoo_base,
                "financials": f"{yahoo_base}financials/",
                "balance_sheet": f"{yahoo_base}balance-sheet/",
                "cash_flow": f"{yahoo_base}cash-flow/",
            },
            "currency": quote_currency,
            "financial_currency": financial_currency,
            "source": YAHOO_SOURCE,
        }

    async def get_live_snapshot(self, ticker: str) -> dict[str, Any] | None:
        key = ticker.upper().removesuffix(".NS")
        cached = self._cache.get(key)
        if cached and time.monotonic() - cached[0] < settings.YFINANCE_CACHE_TTL_SECONDS:
            return cached[1]
        persisted = await get_local_cache(f"yahoo_snapshot:{key}")
        if persisted is not None:
            self._cache[key] = (time.monotonic(), persisted)
            self._errors.pop(key, None)
            return persisted
        cached_fundamentals = await get_local_cache(f"yahoo_fundamentals:{key}")
        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(self._fetch_snapshot, key, cached_fundamentals),
                timeout=20,
            )
        except asyncio.TimeoutError:
            self._errors[key] = "Yahoo Finance request timed out."
            logger.warning("Yahoo Finance request timed out for %s", key)
            return None
        except Exception:
            self._errors[key] = "Yahoo Finance could not return a usable snapshot."
            logger.warning("Yahoo Finance request failed for %s", key, exc_info=True)
            return None
        if result is None:
            self._errors[key] = "Yahoo Finance returned no recent daily history."
            return None
        self._errors.pop(key, None)
        self._cache[key] = (time.monotonic(), result)
        await set_local_cache(
            f"yahoo_snapshot:{key}", result, settings.YFINANCE_CACHE_TTL_SECONDS
        )
        if cached_fundamentals is None and result.get("fundamentals"):
            await set_local_cache(
                f"yahoo_fundamentals:{key}",
                result["fundamentals"],
                settings.FINANCIAL_STATEMENTS_CACHE_TTL_SECONDS,
            )
        return result

    def last_error(self, ticker: str) -> str | None:
        return self._errors.get(ticker.upper().removesuffix(".NS"))


market_data_service = MarketDataService()
