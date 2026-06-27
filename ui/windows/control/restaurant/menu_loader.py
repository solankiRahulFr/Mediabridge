from __future__ import annotations

import csv
import json
import logging
import pathlib
from typing import Any

logger = logging.getLogger(__name__)


def load_menu(source: str) -> list[dict[str, Any]]:
    path = pathlib.Path(source)
    if not path.exists():
        logger.error("Menu file not found: %s", source)
        return []

    suffix = path.suffix.lower()
    if suffix == ".json":
        return _load_json(path)
    elif suffix == ".csv":
        return _load_csv(path)
    else:
        logger.error("Unsupported menu file format: %s", suffix)
        return []


def _load_json(path: pathlib.Path) -> list[dict]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        logger.error("Failed to load menu JSON: %s", exc)
        return []

    if isinstance(data, list):
        raw_items = data
    elif isinstance(data, dict):
        raw_items = (
            data.get("menu") or data.get("items")
            or data.get("data") or data.get("records") or []
        )
    else:
        return []

    return [_normalise(item) for item in raw_items if isinstance(item, dict)]


def _load_csv(path: pathlib.Path) -> list[dict]:
    items: list[dict] = []
    try:
        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                item: dict[str, Any] = {}
                item["id"] = row.get("id", "").strip()
                item["name"] = row.get("name", "").strip()
                item["category"] = row.get("category", "").strip()

                price_str = row.get("price", "0").strip()
                try:
                    item["price"] = float(price_str)
                except ValueError:
                    item["price"] = 0.0

                item["description"] = row.get("description", "").strip()
                item["image"] = row.get("image", "").strip()

                tags_raw = row.get("tags", "")
                item["tags"] = [t.strip() for t in tags_raw.split(",") if t.strip()]

                avail = row.get("available", "true").strip().lower()
                item["available"] = avail in ("true", "1", "yes", "")

                items.append(_normalise(item))
    except OSError as exc:
        logger.error("Failed to load menu CSV: %s", exc)

    return items


def _normalise(raw: dict) -> dict[str, Any]:
    return {
        "id": raw.get("id") or raw.get("_id") or raw.get("item_id", ""),
        "name": raw.get("name") or raw.get("title", "Unknown Item"),
        "category": raw.get("category") or raw.get("cat", "Other"),
        "price": float(raw.get("price", 0)),
        "description": raw.get("description") or raw.get("desc", ""),
        "image": raw.get("image") or raw.get("img") or raw.get("photo", ""),
        "tags": raw.get("tags", []) if isinstance(raw.get("tags"), list) else [],
        "available": raw.get("available", True),
        "_raw": raw,
    }


def get_categories(items: list[dict]) -> list[str]:
    seen: set[str] = set()
    cats: list[str] = []
    for item in items:
        cat = item.get("category", "Other")
        if cat not in seen:
            seen.add(cat)
            cats.append(cat)
    return cats


def get_tags(items: list[dict]) -> list[str]:
    seen: set[str] = set()
    for item in items:
        for tag in item.get("tags", []):
            seen.add(tag)
    return sorted(seen)
