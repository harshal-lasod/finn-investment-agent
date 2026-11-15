"""Download public exchange equity lists and save a local symbol catalog."""
from __future__ import annotations

import argparse
import csv
import io
import json
import ssl
import sys
from pathlib import Path
from urllib.request import urlopen

NSE_EQUITY_CSV = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
OUTPUT = Path(__file__).resolve().parents[1] / "backend" / "data" / "exchange_symbols.json"


def read_csv(source: str) -> list[dict[str, str]]:
    if source.startswith(("https://", "http://")):
        import certifi

        context = ssl.create_default_context(cafile=certifi.where())
        with urlopen(source, timeout=20, context=context) as response:
            if response.status != 200:
                raise RuntimeError(f"Symbol source returned HTTP {response.status}: {source}")
            content = response.read().decode("utf-8-sig")
    else:
        content = Path(source).read_text(encoding="utf-8-sig")
    return list(csv.DictReader(io.StringIO(content)))


def normalize_headers(row: dict[str, str]) -> dict[str, str]:
    return {
        "".join(character for character in key.casefold() if character.isalnum()): (value or "").strip()
        for key, value in row.items()
        if key
    }


def first_value(row: dict[str, str], *names: str) -> str:
    for name in names:
        value = row.get(name)
        if value:
            return value
    return ""


def load_nse() -> list[dict[str, str]]:
    result = []
    for raw in read_csv(NSE_EQUITY_CSV):
        row = normalize_headers(raw)
        symbol = first_value(row, "symbol")
        name = first_value(row, "nameofcompany", "companyname")
        if not symbol or not name:
            continue
        result.append({
            "symbol": symbol.upper(),
            "name": name,
            "exchange": "NSE",
            "isin": first_value(row, "isinnumber", "isin"),
            "series": first_value(row, "series").upper(),
        })
    if not result:
        raise RuntimeError("NSE CSV contained no recognizable equity symbols.")
    return result


def load_bse(source: str) -> list[dict[str, str]]:
    result = []
    for raw in read_csv(source):
        row = normalize_headers(raw)
        symbol = first_value(row, "securityid", "securitysymbol", "symbol", "scripid")
        name = first_value(row, "securityname", "nameofcompany", "companyname", "issuername")
        if not symbol or not name:
            continue
        result.append({
            "symbol": symbol.upper(),
            "name": name,
            "exchange": "BSE",
            "isin": first_value(row, "isin", "isinno", "isinnumber"),
            "series": first_value(row, "group", "series"),
        })
    if not result:
        raise RuntimeError("BSE CSV contained no recognizable equity symbols.")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--bse-csv",
        help="Path or public URL of a BSE equity-list CSV (optional; uses only directly accessible downloads).",
    )
    args = parser.parse_args()

    try:
        symbols = load_nse()
        if args.bse_csv:
            symbols.extend(load_bse(args.bse_csv))
        # A symbol may appear on both exchanges; keep each exchange listing.
        unique = {(row["exchange"], row["symbol"]): row for row in symbols}
        ordered = sorted(unique.values(), key=lambda row: (row["symbol"], row["exchange"]))
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(json.dumps(ordered, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    except Exception as error:
        print(f"Could not update symbol catalog: {error}", file=sys.stderr)
        return 1

    print(f"Saved {len(ordered)} exchange listings to {OUTPUT}")
    print(f"NSE: {sum(row['exchange'] == 'NSE' for row in ordered)}")
    print(f"BSE: {sum(row['exchange'] == 'BSE' for row in ordered)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
