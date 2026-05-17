"""
core/language_manager.py
─────────────────────────────────────────────────────────────────────────────
Loads localisation JSON files from core/lang/ and provides a simple t()
lookup.  No Qt dependency.

File structure expected:
    core/lang/en.json   →  {"config.display.title": "Display Settings", …}
    core/lang/fr.json   →  {"config.display.title": "Paramètres d'affichage", …}
    core/languages.json →  [{"code": "en", "label": "English", "flag": "🇬🇧"}, …]

Usage:
    from core.language_manager import LanguageManager
    lm = LanguageManager.instance()
    lm.set_language("fr")
    lm.t("config.display.title")   # → "Paramètres d'affichage"
"""

from __future__ import annotations

import json
import pathlib
from typing import Callable

_LANG_DIR = pathlib.Path(__file__).parent / "locales"
_LANGUAGES_FILE = pathlib.Path(__file__).parent / "languages.json"


class LanguageManager:
    _instance: "LanguageManager | None" = None

    @classmethod
    def instance(cls) -> "LanguageManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self) -> None:
        self._language: str = "en"
        self._strings: dict[str, str] = {}
        self._fallback: dict[str, str] = {}
        self._observers: list[Callable[[str], None]] = []
        self._load("en")  # always load English as fallback

    # ── Language switching ────────────────────────────────────────────────────

    def set_language(self, code: str) -> None:
        if code == self._language:
            return
        self._language = code
        self._load(code)
        for cb in self._observers:
            try:
                cb(code)
            except Exception as exc:  # noqa: BLE001
                print(f"[LanguageManager] observer error: {exc}")

    @property
    def current(self) -> str:
        return self._language

    # ── Translation ───────────────────────────────────────────────────────────

    def t(self, key: str, **kwargs: str) -> str:
        """
        Look up *key* in the current language, fall back to English, then the key itself.
        Supports simple {variable} substitution via kwargs.
        """
        def _lookup(mapping: dict[str, object], path: list[str]) -> object | None:
            value: object | None = mapping
            for part in path:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return None
            return value

        path = key.split(".")
        text = _lookup(self._strings, path)
        if text is None:
            text = _lookup(self._fallback, path)
        if text is None:
            return key

        if isinstance(text, str) and kwargs:
            try:
                return text.format(**kwargs)
            except KeyError:
                return text

        return text

    # ── Available languages ───────────────────────────────────────────────────

    def available(self) -> list[dict]:
        """
        Return list of {"code": "en", "label": "English", "flag": "🇬🇧"} dicts
        from core/languages.json.  Falls back to a minimal built-in list.
        """
        try:
            return json.loads(_LANGUAGES_FILE.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return [
                {"code": "en", "label": "English",  "flag": "🇬🇧"},
                {"code": "fr", "label": "Français",  "flag": "🇫🇷"},
                {"code": "de", "label": "Deutsch",   "flag": "🇩🇪"},
                {"code": "es", "label": "Español",   "flag": "🇪🇸"},
                {"code": "ar", "label": "العربية",   "flag": "🇸🇦"},
                {"code": "zh", "label": "中文",       "flag": "🇨🇳"},
                {"code": "ja", "label": "日本語",      "flag": "🇯🇵"},
            ]

    # ── Observer ──────────────────────────────────────────────────────────────

    def on_change(self, callback: Callable[[str], None]) -> None:
        self._observers.append(callback)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _load(self, code: str) -> None:
        path = _LANG_DIR / f"{code}.json"
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            data = {}
        if code == "en":
            self._fallback = data
        self._strings = data