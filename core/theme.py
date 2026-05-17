"""
core/theme.py
─────────────────────────────────────────────────────────────────────────────
Re‑export convenience — lets any module write::

    from core.theme import ThemeManager, ThemeToggle, THEMES, apply_theme

The canonical implementation lives in ``ui/themes/theme.py``.
"""

from ui.themes.theme import THEMES, ThemeManager, ThemeToggle, apply_theme  # noqa: F401
