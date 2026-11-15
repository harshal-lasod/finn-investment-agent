"""Create a source-only submission archive without local secrets or build output."""
from __future__ import annotations

import argparse
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "FINN_submission_2026-11-15.zip"
EXCLUDED_DIRS = {
    ".git",
    ".next",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "node_modules",
}
EXCLUDED_FILES = {
    ".DS_Store",
    "ENAM_Founding AI Engineer Build Challenge_Main.pdf",
    "FINN_LLD_REVIEW.md",
    "SUBMISSION_COVERING_NOTE.md",
    "SUBMISSION_EMAIL_DRAFT.md",
    "plan.md",
    "next-env.d.ts",
}
EXCLUDED_SUFFIXES = {".db", ".sqlite", ".sqlite3", ".pyc", ".pyo", ".zip"}


def should_include(path: Path, output: Path) -> bool:
    if not path.is_file() or path.resolve() == output.resolve():
        return False
    if any(part in EXCLUDED_DIRS for part in path.relative_to(ROOT).parts):
        return False
    if path.name in EXCLUDED_FILES or path.suffix in EXCLUDED_SUFFIXES:
        return False
    if path.name.endswith((".db-wal", ".db-shm")):
        return False
    if path.name == ".env" or (path.name.startswith(".env.") and path.name != ".env.example"):
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    files = sorted(path for path in ROOT.rglob("*") if should_include(path, output))
    if not files:
        parser.error("No project files found to package.")

    with ZipFile(output, "w", compression=ZIP_DEFLATED, compresslevel=8) as archive:
        for path in files:
            archive.write(path, Path("FINN") / path.relative_to(ROOT))

    print(f"Created {output} ({len(files)} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
