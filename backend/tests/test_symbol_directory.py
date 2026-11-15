import json

from fastapi.testclient import TestClient

from backend.main import app
from backend.services import symbol_directory
from scripts.update_symbols import load_bse


def test_symbol_search_prioritizes_symbol_prefixes(tmp_path, monkeypatch) -> None:
    path = tmp_path / "symbols.json"
    path.write_text(json.dumps([
        {"symbol": "RELIANCE", "name": "Reliance Industries Limited", "exchange": "NSE"},
        {"symbol": "RPOWER", "name": "Reliance Power Limited", "exchange": "NSE"},
        {"symbol": "ABC", "name": "Reliance Capital Limited", "exchange": "BSE"},
    ]), encoding="utf-8")
    monkeypatch.setattr(symbol_directory, "SYMBOLS_PATH", path)
    symbol_directory.load_symbols.cache_clear()
    try:
        results = symbol_directory.search_symbols("rel", limit=3)
        assert [row["symbol"] for row in results] == ["RELIANCE", "ABC", "RPOWER"]
        assert results[1]["exchange"] == "BSE"
        assert symbol_directory.search_symbols("   ") == []
    finally:
        symbol_directory.load_symbols.cache_clear()


def test_exchange_symbol_search_endpoint() -> None:
    with TestClient(app) as client:
        response = client.get("/api/symbols/search?q=RELIANCE&limit=5")
    assert response.status_code == 200
    results = response.json()["symbols"]
    assert results
    assert results[0]["symbol"] == "RELIANCE"
    assert results[0]["exchange"] == "NSE"


def test_bse_csv_parser_maps_exchange_fields(tmp_path) -> None:
    path = tmp_path / "bse.csv"
    path.write_text(
        "Security Code,Security Id,Security Name,ISIN No\n"
        "500325,RELIANCE,Reliance Industries Limited,INE002A01018\n",
        encoding="utf-8",
    )
    assert load_bse(str(path)) == [{
        "symbol": "RELIANCE",
        "name": "Reliance Industries Limited",
        "exchange": "BSE",
        "isin": "INE002A01018",
        "series": "",
    }]
