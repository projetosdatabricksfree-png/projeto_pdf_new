"""
Generate/update MANIFEST.json for tests/fixtures/real_batch/.

Usage (from projeto_validador/):
    python scripts/generate_manifest.py

Reads all *.pdf files in tests/fixtures/real_batch/, computes sha256 + dimensions,
and updates MANIFEST.json in-place preserving existing `expected_gwg_errors` and
`notes` fields.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent.parent / "tests" / "fixtures" / "real_batch"
MANIFEST_PATH = FIXTURES_DIR / "MANIFEST.json"
MM_PER_PT = 25.4 / 72.0


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def get_pdf_dimensions_mm(path: Path) -> dict:
    try:
        import pymupdf

        with pymupdf.open(str(path)) as doc:
            page = doc[0]
            r = page.rect
            return {
                "width": round(r.width * MM_PER_PT, 2),
                "height": round(r.height * MM_PER_PT, 2),
            }
    except Exception as exc:
        print(f"  [WARN] Could not read dimensions for {path.name}: {exc}")
        return {"width": None, "height": None}


def main() -> None:
    if not FIXTURES_DIR.exists():
        print(f"Directory not found: {FIXTURES_DIR}")
        return

    pdfs = sorted(FIXTURES_DIR.glob("*.pdf"))
    if not pdfs:
        print("No PDFs found in real_batch/. Copy the production files first.")
        return

    existing: dict = {}
    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH) as f:
            data = json.load(f)
        for entry in data.get("files", []):
            existing[entry["normalized_name"]] = entry

    entries = []
    for pdf in pdfs:
        print(f"Processing {pdf.name}…")
        sha = sha256_file(pdf)
        dims = get_pdf_dimensions_mm(pdf)
        prev = existing.get(pdf.name, {})
        entries.append({
            "normalized_name": pdf.name,
            "sha256": sha,
            "dimensions_mm": dims,
            "expected_gwg_errors": prev.get("expected_gwg_errors", []),
            "notes": prev.get("notes", ""),
        })

    manifest = {
        "_comment": "Batch de referência de produção — gerado automaticamente por generate_manifest.py.",
        "baseline_date": "2026-04-15",
        "baseline_result": "0/10 entregues (todos GOLD_REJECTED antes do Sprint A)",
        "sprint_a_target": "≥8/10 entregues como GOLD_DELIVERED ou GOLD_DELIVERED_WITH_WARNINGS",
        "files": entries,
    }

    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"\nMANIFEST.json updated — {len(entries)} file(s) indexed.")


if __name__ == "__main__":
    main()
