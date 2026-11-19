"""Validate Archive Signal catalog/archives.json Digital Museum schema and integrity."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REQUIRED_ENTRY_FIELDS = (
    "id",
    "catalog_ref",
    "title",
    "date",
    "year",
    "era",
    "category",
    "source",
    "original_format",
    "transfer_chain",
    "technical_metadata",
    "restoration_notes",
    "why_it_matters",
    "historical_context",
    "related_media",
    "references",
    "tags",
    "status",
)

REQUIRED_TECH_FIELDS = (
    "duration",
    "format_spec",
    "preservation_grade",
    "checksum_sha256",
    "version_history",
)

VALID_CATEGORIES = {
    "Television Broadcasts",
    "Radio Archives",
    "Documentary Archives",
    "Live Performance Archives",
    "Interview Archives",
}

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def validate_catalog(path: Path) -> int:
    data = json.loads(path.read_text(encoding="utf-8"))
    entries = data.get("entries")
    if not isinstance(entries, list) or not entries:
        print("ERROR: catalog must contain a non-empty 'entries' list")
        return 1

    seen_ids = set()
    seen_refs = set()
    errors = []

    for idx, item in enumerate(entries):
        for field in REQUIRED_ENTRY_FIELDS:
            if field not in item or item[field] in (None, ""):
                errors.append(f"Entry #{idx} missing required field '{field}'")

        eid = item.get("id")
        ref = item.get("catalog_ref")
        if eid in seen_ids:
            errors.append(f"Duplicate entry id: {eid}")
        seen_ids.add(eid)
        if ref in seen_refs:
            errors.append(f"Duplicate catalog_ref: {ref}")
        seen_refs.add(ref)

        cat = item.get("category")
        if cat not in VALID_CATEGORIES:
            errors.append(f"Entry {eid}: invalid category '{cat}'")

        year = item.get("year")
        if not isinstance(year, int) or year < 1920 or year > 2100:
            errors.append(f"Entry {eid}: invalid year '{year}'")

        date_str = item.get("date", "")
        if not isinstance(date_str, str) or not DATE_RE.match(date_str):
            errors.append(f"Entry {eid}: 'date' must be YYYY-MM-DD (got '{date_str}')")
        elif isinstance(year, int) and not date_str.startswith(str(year)):
            errors.append(f"Entry {eid}: date '{date_str}' does not match year {year}")

        tech = item.get("technical_metadata")
        if not isinstance(tech, dict):
            errors.append(f"Entry {eid}: 'technical_metadata' must be an object")
        else:
            for tf in REQUIRED_TECH_FIELDS:
                if not tech.get(tf):
                    errors.append(f"Entry {eid}: technical_metadata missing '{tf}'")

        if not isinstance(item.get("related_media"), list):
            errors.append(f"Entry {eid}: 'related_media' must be a list")

        if not isinstance(item.get("references"), list) or not item["references"]:
            errors.append(f"Entry {eid}: 'references' must be a non-empty list")

        if not isinstance(item.get("tags"), list) or not item["tags"]:
            errors.append(f"Entry {eid}: 'tags' must be a non-empty list")

    if errors:
        for err in errors:
            print("FAIL:", err)
        return 1

    print(f"OK: Validated {len(entries)} archive entries in {path.name}")
    return 0


if __name__ == "__main__":
    target = Path(__file__).resolve().parents[1] / "catalog" / "archives.json"
    sys.exit(validate_catalog(target))
