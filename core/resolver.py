"""
Runtime Field Resolver — pure Python, zero Qt dependency.

Maps UI semantic keys → backend record values using the mapping section of
the saved kiosk config.  Supports dot-notation paths, list indexing, multi-
candidate priority resolution, and convenience helpers for images / authors.

Architecture
────────────
The MappingPanel (UI) lets the user configure which backend field names
correspond to which UI concepts.  That mapping is persisted as JSON via
ConfigIO.  At runtime, FieldResolver reads that mapping and resolves each
semantic key against an actual data record from the customer's API.

Mapping config format (as produced by the MappingPanel)::

    {
        "title":         {"enabled": true,  "candidates": ["title", "name"]},
        "primary_image": {"enabled": true,  "candidates": ["thumbnail", "cover"]},
        ...
    }

Usage
─────
    from core.resolver import FieldResolver
    from core.configio import ConfigIO

    cfg      = ConfigIO.load("kiosk_config.json")
    resolver = FieldResolver(cfg["mapping"])

    record = {
        "id": "abc-123",
        "title": "Annual Conference Keynote",
        "thumbnail": "https://cdn.example.com/thumb.jpg",
        "author": {"name": "Alice Martin"},
        "tags": ["keynote", "AI", "design"],
    }

    title   = resolver.get(record, "title")       # "Annual Conference Keynote"
    authors = resolver.authors(record)             # ["Alice Martin"]
    image   = resolver.image_url(record)           # "https://cdn.example.com/thumb.jpg"
    bound   = resolver.bind_all(record)            # {semantic_key: value, …}
"""

from __future__ import annotations

import re
from typing import Any


class FieldResolver:
    """
    Resolves semantic keys to backend values using the persisted mapping config.
    """

    def __init__(self, mapping_cfg: dict[str, dict]) -> None:
        self._cfg = mapping_cfg or {}

    # ── Core resolution ───────────────────────────────────────────────────────

    def get(self, record: dict[str, Any], semantic_key: str,
            fallback: Any = None) -> Any:
        """
        Return the first non-null, non-empty candidate value for *semantic_key*
        found inside *record*.

        Supports:
        • Dot-notation  →  ``"author.avatar.url"``
        • List indexing →  ``"items.0.title"``
        • Multiple candidates tried in priority order
        """
        entry = self._cfg.get(semantic_key)
        if not entry or not entry.get("enabled", True):
            return fallback

        for candidate in entry.get("candidates", []):
            value = self._deep_get(record, candidate)
            if value is not None and value != "" and value != [] and value != {}:
                return value

        return fallback

    def bind_all(self, record: dict[str, Any]) -> dict[str, Any]:
        """
        Resolve all enabled semantic keys against *record*.
        Returns ``{semantic_key: resolved_value}`` — only keys with a hit.
        """
        result: dict[str, Any] = {}
        for key, entry in self._cfg.items():
            if not entry.get("enabled", True):
                continue
            value = self.get(record, key)
            if value is not None:
                result[key] = value
        return result

    # ── Convenience helpers ───────────────────────────────────────────────────

    def image_url(self, record: dict[str, Any],
                  base_url: str = "") -> str | None:
        """Resolve *primary_image*; handles Strapi-style ``{"url": "…"}``."""
        raw = self.get(record, "primary_image")
        if raw is None:
            return None
        if isinstance(raw, dict):
            raw = raw.get("url") or raw.get("src") or raw.get("href") or ""
        raw = str(raw).strip()
        if not raw:
            return None
        if base_url and not re.match(r"^https?://", raw):
            return base_url.rstrip("/") + "/" + raw.lstrip("/")
        return raw

    def authors(self, record: dict[str, Any]) -> list[str]:
        """Flat list of author name strings, regardless of backend schema."""
        raw = self.get(record, "authors")
        return self._flatten_authors(raw)

    def tags(self, record: dict[str, Any]) -> list[str]:
        """Return tags as a flat list of strings."""
        raw = self.get(record, "tags")
        if raw is None:
            return []
        if isinstance(raw, str):
            return [t.strip() for t in raw.split(",") if t.strip()]
        if isinstance(raw, list):
            flat = []
            for item in raw:
                if isinstance(item, str):
                    flat.append(item)
                elif isinstance(item, dict):
                    flat.append(item.get("name") or item.get("label") or str(item))
            return flat
        return [str(raw)]

    def qr_url(self, record: dict[str, Any]) -> str | None:
        raw = self.get(record, "qr_target")
        return str(raw).strip() if raw else None

    def content_type(self, record: dict[str, Any]) -> str:
        return str(self.get(record, "content_type") or "unknown").lower()

    # ── Internal helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _deep_get(obj: Any, path: str) -> Any:
        """Walk a dot-notation *path* through nested dicts/lists."""
        parts = path.split(".")
        current = obj
        for part in parts:
            if current is None:
                return None
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list):
                try:
                    current = current[int(part)]
                except (ValueError, IndexError):
                    return None
            else:
                return None
        return current

    @staticmethod
    def _flatten_authors(raw: Any) -> list[str]:
        if raw is None:
            return []
        _NAME_KEYS = ("name", "display_name", "full_name", "username", "title")
        if isinstance(raw, str):
            return [raw] if raw.strip() else []
        if isinstance(raw, list):
            names: list[str] = []
            for item in raw:
                if isinstance(item, str) and item.strip():
                    names.append(item.strip())
                elif isinstance(item, dict):
                    for k in _NAME_KEYS:
                        if item.get(k):
                            names.append(str(item[k]))
                            break
            return names
        if isinstance(raw, dict):
            for k in _NAME_KEYS:
                if raw.get(k):
                    return [str(raw[k])]
        return [str(raw)] if raw else []
