"""
[
  {
    "title":        "Sunset Photo",
    "content_type": "image",                   # image | video | pdf
    "image":        "sunset.jpg",              # relative to folder
    "thumbnail":    "thumbs/sunset_thumb.jpg", # optional, relative
    "tags":         ["nature", "landscape"],    # optional
    "description":  "A beautiful sunset",       # optional
    "size_bytes":   1048576,                    # optional
    "date":         "2026-01-15"               # optional
  },
  ...
]

"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Callable

from PySide6.QtCore import QObject, QThread, Signal, QUrl
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

log = logging.getLogger(__name__)

_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", ".svg"}
_VIDEO_EXT = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".m4v"}
_PDF_EXT   = {".pdf"}


def _content_type_for(ext: str) -> str | None:
    ext = ext.lower()
    if ext in _IMAGE_EXT:
        return "image"
    if ext in _VIDEO_EXT:
        return "video"
    if ext in _PDF_EXT:
        return "pdf"
    return None


def _resolve_path(base: str, p: str) -> str:
    if not p:
        return p
    if os.path.isabs(p) or p.startswith("http://") or p.startswith("https://"):
        return p
    return str(Path(base) / p)


def _file_path_for(record: dict) -> str:
    ct = record.get("content_type", "")
    return record.get(ct, "") or record.get("image", "") or record.get("video", "") or record.get("pdf", "")


class MediaLoader(QObject):
    loaded = Signal(list)
    error  = Signal(str)

    def __init__(
        self,
        local_dir: str | None = None,
        remote_url: str | None = None,
        remote_headers: dict | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._local_dir = local_dir
        self._remote_url = remote_url
        self._remote_headers = remote_headers or {}
        self._nam: QNetworkAccessManager | None = None

    def load(self) -> None:
        # 1. Try media.json in local folder
        if self._local_dir:
            json_path = Path(self._local_dir) / "media.json"
            if json_path.is_file():
                try:
                    records = self._load_json(json_path)
                    log.info("Loaded %d records from %s", len(records), json_path)
                    self.loaded.emit(records)
                    return
                except Exception as exc:
                    log.warning("Failed to parse media.json: %s", exc)

        # 2. Try remote API
        if self._remote_url:
            self._load_from_api()
            return

        # 3. Fallback — filesystem scan
        if self._local_dir and os.path.isdir(self._local_dir):
            records = self._scan_folder()
            log.info("Scanned %d records from %s", len(records), self._local_dir)
            self.loaded.emit(records)
            return

        self.error.emit("No media source configured")

    # ── JSON loader ───────────────────────────────────────────────

    def _load_json(self, path: Path) -> list[dict]:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        if not isinstance(raw, list):
            raise ValueError("media.json root must be a JSON array")

        base = str(path.parent)
        records: list[dict] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            ct = item.get("content_type", "")
            # Resolve relative paths
            for key in ("image", "video", "pdf", "thumbnail"):
                if key in item:
                    item[key] = _resolve_path(base, item[key])
            # Auto-detect content_type from file if missing
            if not ct:
                fp = _file_path_for(item)
                if fp:
                    ct = _content_type_for(Path(fp).suffix) or "unknown"
                    item["content_type"] = ct
            # Generate title from filename if missing
            if not item.get("title"):
                fp = _file_path_for(item)
                if fp:
                    item["title"] = Path(fp).stem.replace("_", " ").replace("-", " ").title()
            records.append(item)
        return records

    # ── API loader ────────────────────────────────────────────────

    def _load_from_api(self) -> None:
        if not self._nam:
            self._nam = QNetworkAccessManager(self)
        req = QNetworkRequest(QUrl(self._remote_url))
        for k, v in self._remote_headers.items():
            req.setRawHeader(k.encode(), v.encode())
        reply = self._nam.get(req)
        reply.finished.connect(lambda: self._on_api_response(reply))

    def _on_api_response(self, reply: QNetworkReply) -> None:
        if reply.error() != QNetworkReply.NetworkError.NoError:
            self.error.emit(f"API error: {reply.errorString()}")
            reply.deleteLater()
            return
        try:
            data = json.loads(bytes(reply.readAll()).decode("utf-8"))
            if isinstance(data, dict) and "records" in data:
                data = data["records"]
            if not isinstance(data, list):
                self.error.emit("API response root must be a JSON array")
                return
            # Resolve paths against local_dir if available
            base = self._local_dir or ""
            for item in data:
                for key in ("image", "video", "pdf", "thumbnail"):
                    if key in item and base:
                        item[key] = _resolve_path(base, item[key])
                if not item.get("title"):
                    fp = _file_path_for(item)
                    if fp:
                        item["title"] = Path(fp).stem.replace("_", " ").replace("-", " ").title()
            log.info("Loaded %d records from API", len(data))
            self.loaded.emit(data)
        except Exception as exc:
            self.error.emit(f"API parse error: {exc}")
        finally:
            reply.deleteLater()

    # ── Filesystem scan ───────────────────────────────────────────

    def _scan_folder(self) -> list[dict]:
        records: list[dict] = []
        base = self._local_dir
        for entry in sorted(Path(base).iterdir()):
            if not entry.is_file():
                continue
            ct = _content_type_for(entry.suffix)
            if ct is None:
                continue
            path_str = str(entry)
            record = {
                "content_type": ct,
                ct: path_str,
                "title": entry.stem.replace("_", " ").replace("-", " ").title(),
                "size_bytes": entry.stat().st_size,
            }
            # Use image file itself as thumbnail for images
            if ct == "image":
                record["thumbnail"] = path_str
            records.append(record)
        return records
