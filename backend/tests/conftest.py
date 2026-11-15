import pytest

from backend.config import settings


@pytest.fixture(autouse=True)
def disable_external_market_requests(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(settings, "ENABLE_LIVE_DATA", False)
    monkeypatch.setattr(settings, "DATABASE_URL", str(tmp_path / "test-finn.db"))
