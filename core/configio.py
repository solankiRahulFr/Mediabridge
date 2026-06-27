"""
JSON persistence for the kiosk configuration.
"""

from __future__ import annotations

import json
import logging
import pathlib
from datetime import datetime
from typing import Any

log = logging.getLogger(__name__)

CONFIG_VERSION = "1.0.0"

# Keys that ConfigIO injects / strips automatically so panels never see them.
_META_KEYS = {"_version", "_saved_at"}


class ConfigIO:

    # ── Save ─────────────────────────────────────────────────────────────────
    @staticmethod
    def save(path: str | pathlib.Path, config: dict[str, Any]) -> bool:
        try:
            payload: dict[str, Any] = {
                "_version":  CONFIG_VERSION,
                "_saved_at": datetime.now().isoformat(timespec="seconds"),
                **config,
            }
            pathlib.Path(path).write_text(
                json.dumps(payload, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            log.info("Config saved → %s", path)
            return True
        except Exception as exc:  # noqa: BLE001
            log.error("Config save error: %s", exc)
            return False

    # ── Load ─────────────────────────────────────────────────────────────────
    @staticmethod
    def load(path: str | pathlib.Path) -> dict[str, Any] | None:
        try:
            raw = pathlib.Path(path).read_text(encoding="utf-8")
            data: dict[str, Any] = json.loads(raw)
            for k in _META_KEYS:
                data.pop(k, None)
            log.info("Config loaded ← %s", path)
            return data
        except Exception as exc:  # noqa: BLE001
            log.error("Config load error: %s", exc)
            return None

    # ── Validate ─────────────────────────────────────────────────────────────
    @staticmethod
    def validate(config: dict[str, Any]) -> list[str]:
        warnings: list[str] = []
        expected_sections = {"display", "behavior", "header", "mapping"}
        for section in expected_sections:
            if section not in config:
                warnings.append(f"Missing section: '{section}'")
        return warnings

    # ── Merge ────────────────────────────────────────────────────────────────
    @staticmethod
    def merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        result = base.copy()
        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = ConfigIO.merge(result[key], value)
            else:
                result[key] = value
        return result

    # ── Default config skeleton ───────────────────────────────────────────────
    @staticmethod
    def defaults() -> dict[str, Any]:
        return {
            "display": {
                "fullscreen":    True,
                "resolution":    "Auto-detect",
                "orientation":   "Landscape",
                "monitor_index": 0,
                "bg_color":      "#0D0F14",
                "text_color":    "#EEF0F8",
                "accent_color":  "#4F8EF7",
                "hide_cursor":   True,
                "touch_ripple":  True,
                "dpi_scale":     "Auto",
            },
            "behavior": {
                "autostart":          False,
                "startup_delay":      3,
                "start_page":         "Home / Landing",
                "start_content_id":   "",
                "kiosk_mode":         True,
                "disable_rightclick": True,
                "disable_keyboard":   False,
                "exit_method":        "Corner tap  (N taps on any corner)",
                "exit_taps":          7,
                "exit_timeout_sec":   5,
                "exit_corner":        "Bottom-right",
                "exit_pin":           "",
                "idle_timeout_sec":   120,
                "idle_action":        "Return to home page",
                "attract_loop_path":  "",
            },
            "header": {
                "show_header":       True,
                "header_height":     64,
                "header_bg":         "#13161E",
                "header_text_color": "#EEF0F8",
                "show_title":        True,
                "title_text":        "",
                "title_font_size":   18,
                "title_position":    "Left",
                "show_logo":         True,
                "logo_url":          "",
                "logo_position":     "Left",
                "logo_height":       40,
                "logo_clickable":    False,
                "show_clock":        False,
                "clock_format":      "HH:MM",
                "show_lang":         True,
                "show_theme_toggle": False,
            },
            "mapping": {},
        }
