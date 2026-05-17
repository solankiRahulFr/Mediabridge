"""
Centralised application state — **single source of truth** shared across
every window, panel, widget, and worker in the project.

Design goals
────────────
• Pure-Python singleton — no QObject, no Qt signals.  This keeps AppState
  importable in non-Qt contexts (CLI scripts, unit tests, background threads).
• Holds references to the two shared managers:
      .theme   →  ThemeManager   (colour palette + QSS application)
      .lang    →  LanguageManager (i18n translations + language switching)
• Lightweight observer pattern for reactive updates:
      state.subscribe("is_dark", my_callback)
      state.set("is_dark", False)  # fires my_callback(False)

Quick-start
───────────
    from core.app_state import get_state

    state = get_state()

    # Theme
    state.theme.apply(some_widget)        # apply current QSS
    state.theme.set_dark(False)           # switch palette

    # Language
    state.lang.set_language("fr")         # loads fr.json, notifies observers
    label = state.t("launch.select_mode") # → "Sélectionnez un mode"

    # Kiosk config
    state.kiosk_config                    # full config dict
    state.section("display")              # one section dict

Integration checklist (new widget)
──────────────────────────────────
1.  ``from core.app_state import get_state``
2.  In ``__init__``: ``self._state = get_state()``
3.  Apply theme:  ``self._state.theme.apply(self)``
4.  Subscribe to language changes:
        ``self._state.lang.on_change(self._retranslate)``
5.  Implement ``_retranslate(self, lang_code)`` to update labels.
"""

from __future__ import annotations
from .language_manager import LanguageManager
from .theme import ThemeManager
import logging
from typing import Any, Callable

log = logging.getLogger(__name__)


class AppState:
    """
    Singleton state container.

    Access the shared instance via ``AppState.instance()`` or the module-level
    convenience function ``get_state()``.
    """

    _instance: "AppState | None" = None

    # ── Singleton access ──────────────────────────────────────────────────────

    @classmethod
    def instance(cls) -> "AppState":
        """Return (and lazily create) the global AppState singleton."""
        if cls._instance is None:
            cls._instance = cls()
            log.info("AppState singleton created")
        return cls._instance

    # ── Initialisation ────────────────────────────────────────────────────────

    def __init__(self) -> None:
        # Managers — assigned once during bootstrap (main.py)
        self.theme: ThemeManager | None = None        # will be ThemeManager
        self.lang: LanguageManager | None = None         # will be LanguageManager

        # Convenience flags
        self.is_dark: bool = True
        self.language: str = "en"
        self.kiosk_mode: str = "dual"
        self.kiosk_config: dict[str, Any] = {}

        # Observer registry  {key: [callback, …]}
        self._observers: dict[str, list[Callable]] = {}

    # ── Observer pattern ──────────────────────────────────────────────────────

    def subscribe(self, key: str, callback: Callable[[Any], None]) -> None:
        """Register *callback* to fire whenever *key* changes via ``set()``."""
        self._observers.setdefault(key, []).append(callback)

    def unsubscribe(self, key: str, callback: Callable) -> None:
        if key in self._observers:
            try:
                self._observers[key].remove(callback)
            except ValueError:
                pass

    def set(self, key: str, value: Any) -> None:
        """Set *key* on this object and notify all subscribed observers."""
        setattr(self, key, value)
        for cb in self._observers.get(key, []):
            try:
                cb(value)
            except Exception as exc:  # noqa: BLE001
                log.warning("Observer error for '%s': %s", key, exc)

    # ── Translation shorthand ─────────────────────────────────────────────────

    def t(self, key: str, **kwargs: str) -> Any:
        """
        Shorthand for ``state.lang.t(key)``.

        Returns the translated value (string, list, or dict) for *key* in the
        current language, falling back to English, then the raw key string.
        """
        if self.lang is None:
            return key
        return self.lang.t(key, **kwargs)

    # ── Config helpers ────────────────────────────────────────────────────────

    def apply_config(self, cfg: dict[str, Any]) -> None:
        """Merge a loaded config dict into state and notify 'kiosk_config'."""
        self.kiosk_config.update(cfg)
        self.set("kiosk_config", self.kiosk_config)
        log.info("Config applied (%d top-level keys)", len(cfg))

    def section(self, name: str) -> dict[str, Any]:
        """Return a config section dict, empty dict if not present."""
        return self.kiosk_config.get(name, {})


# ── Module-level convenience ──────────────────────────────────────────────────

def get_state() -> AppState:
    """
    Return the global AppState singleton.

    This is the **recommended** way to access state throughout the codebase::

        from core.app_state import get_state
        state = get_state()
    """
    return AppState.instance()
