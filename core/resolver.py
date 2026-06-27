from __future__ import annotations

import re
from typing import Any


class FieldResolver:
    def __init__(self, mapping_cfg: dict[str, dict]) -> None:
        self._cfg = mapping_cfg or {}

    # ── Core resolution ───────────────────────────────────────────────────────

    def get(self, record: dict[str, Any], semantic_key: str,
            fallback: Any = None) -> Any:
        entry = self._cfg.get(semantic_key)
        if not entry or not entry.get("enabled", True):
            return fallback

        for candidate in entry.get("candidates", []):
            value = self._deep_get(record, candidate)
            if value is not None and value != "" and value != [] and value != {}:
                return value

        return fallback

    def bind_all(self, record: dict[str, Any]) -> dict[str, Any]:
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
        raw = self.get(record, "authors")
        return self._flatten_authors(raw)

    def tags(self, record: dict[str, Any]) -> list[str]:
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
