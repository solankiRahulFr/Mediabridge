"""
Re‑export convenience symbols from the UI theme system.
This allows the core to use the theme system without importing from the UI package ui/themes/theme.py.
"""

from ui.themes.theme import THEMES, ThemeManager, apply_theme  # noqa: F401
