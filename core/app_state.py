"""Centralised application state — singleton shared across all windows, panels, and widgets."""

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
        self.theme: ThemeManager | None = None          # will be ThemeManager
        self.theme_manager: ThemeManager | None = None  # legacy alias used by dual mode -------------------------------
        self.lang: LanguageManager | None = None        # will be LanguageManager

        # Convenience flags
        self.is_dark: bool = True
        self.language: str = "en"
        self.kiosk_mode: str = "dual"
        self.kiosk_config: dict[str, Any] = {}
        self.selected_mode: str | None = None 

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

        Returns the translated value for *key* in the current language,
        falling back to English, then the raw key string.
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
    
    def set_mode(self, mode: str) -> None:
        """Set the current kiosk mode and notify 'selected_mode'."""
        print("""Setting mode to: %s""" % mode)
        self.set("selected_mode", mode)


# ── Module-level convenience ──────────────────────────────────────────────────

def get_state() -> AppState:
    """Return the global AppState singleton."""
    return AppState.instance()