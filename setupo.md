# MediaBridge

A professional multi-screen kiosk platform built with **PySide6** and **Python 3.11+**.  
Supports PDF, images, video, and web pages across configurable display modes.

---

## Project Structure

```
MediaBridge/
├── main.py                          # Entry point — bootstraps managers & launches UI
├── core/                            # Pure-Python application logic (no Qt where possible)
│   ├── app_state.py                 # Singleton state container + get_state()
│   ├── base.py                      # BasePanel — base class for config panels
│   ├── configio.py                  # JSON config save / load / merge / defaults
│   ├── language_manager.py          # Singleton i18n manager with dot-key lookup
│   ├── resolver.py                  # Runtime field resolver (API mapping → UI values)
│   ├── theme.py                     # Re-export convenience from ui/themes/theme.py
│   ├── languages.json               # Available language definitions
│   ├── modes.json                   # Kiosk mode definitions (dual / display / control)
│   └── locales/
│       ├── en.json                  # English translations (nested JSON)
│       └── fr.json                  # French translations
├── ui/
│   ├── themes/
│   │   ├── theme.py                 # THEMES dict, QSS template, ThemeManager, ThemeToggle
│   │   └── theme.json               # Colour tokens (read by theme.py at import time)
│   ├── widgets/
│   │   └── language_switcher.py     # Drop-in language picker combo box
│   ├── assets/
│   │   ├── icons/
│   │   └── images/
│   │       ├── mediabridge.png
│   │       └── flags/               # Flag PNGs for language switcher
│   └── windows/
│       ├── display_window.py        # Media display (PDF / video viewer stack)
│       ├── control_window.py        # Media control panel
│       ├── launch/
│       │   ├── launcher_window.py   # Mode-selection launcher screen
│       │   ├── modeCard.py          # Individual mode card widget
│       │   ├── styledDialog.py      # Themed modal dialog (Help / About)
│       │   └── togglebutton.py      # Compact theme toggle for launcher header
│       └── config/
│           ├── config_window.py     # Main config page (assembles all panels)
│           ├── display_panel.py     # Display settings panel
│           ├── behavior_panel.py    # Behavior settings panel
│           ├── header_panel.py      # Header settings panel
│           └── mapping_panel.py     # Field mapping panel
└── media/
    └── viewers/
        ├── pdf_viewer.py            # PyMuPDF-based PDF renderer
        └── video_viewer.py          # VLC-based video player
```

---

## Core Modules — Detailed Reference

### `core/app_state.py` — AppState (Singleton)

**The single source of truth** for all shared runtime data.

| Attribute       | Type              | Description                                      |
|-----------------|-------------------|--------------------------------------------------|
| `theme`         | `ThemeManager`    | The shared theme manager (dark/light switching)  |
| `lang`          | `LanguageManager` | The shared i18n manager                          |
| `is_dark`       | `bool`            | Current theme mode                               |
| `language`      | `str`             | Current language code                            |
| `kiosk_mode`    | `str`             | Selected kiosk mode ID                           |
| `kiosk_config`  | `dict`            | Full config dict from ConfigIO                   |

**Key methods:**

```python
from core.app_state import get_state

state = get_state()                      # get the singleton
state.t("launch.select_mode")            # shorthand for state.lang.t(…)
state.subscribe("is_dark", callback)     # observe changes
state.set("is_dark", False)              # set + notify observers
state.section("display")                 # get a config section dict
state.apply_config(cfg_dict)             # merge config into state
```

**Lifecycle:**  
Created lazily on first `get_state()` call. Managers are wired in `main.py`:

```python
state = get_state()
state.theme = ThemeManager(is_dark=True)
state.lang  = LanguageManager.instance()
```

---

### `core/language_manager.py` — LanguageManager (Singleton)

Loads nested JSON locale files from `core/locales/` and resolves translations
using **dot-notation deep key lookup**.

```python
lm = LanguageManager.instance()
lm.set_language("fr")
lm.t("config.display.title")             # → "Paramètres d'affichage"
lm.t("modes.dual.tags")                  # → ["Contrôle tactile", "Sortie 4K", "2 écrans"]
lm.t("modes.dual.tags.0")                # → "Contrôle tactile"
lm.t("status.saved", path="/tmp/x.json") # → "Enregistré → /tmp/x.json"
```

**Observer pattern:**

```python
lm.on_change(lambda lang_code: self._retranslate())
```

Callbacks fire on every `set_language()` call. No Qt signals — works in non-Qt contexts.

---

### `ui/themes/theme.py` — ThemeManager + THEMES + QSS

| Export          | Type         | Description                                       |
|-----------------|--------------|---------------------------------------------------|
| `THEMES`        | `dict`       | `{"dark": {…}, "light": {…}}` colour token dicts |
| `ThemeManager`  | class        | Manages is_dark state, applies QSS to widgets     |
| `ThemeToggle`   | QWidget      | Animated pill toggle (config header variant)       |
| `apply_theme()` | function     | Standalone: `apply_theme(widget, is_dark=True)`    |

**ThemeManager usage:**

```python
tm = get_state().theme

# Apply global QSS to a widget tree
tm.apply(self)

# Read a single colour token
accent = tm.color("accent")

# Get the full colour dict
colors = tm.colors

# Switch theme
tm.set_dark(False)
tm.toggle()

# Subscribe to changes
tm.on_change(lambda is_dark: self._refresh())
```

**Style override pattern:**  
The global QSS uses `objectName` selectors (`#Card`, `#NavBtn`, etc.).
Widgets can layer overrides on top:

```python
tm.apply(self)  # base styles
self.my_btn.setStyleSheet(f"QPushButton {{ color: {tm.color('accent')}; }}")
```

---

### `core/base.py` — BasePanel

Abstract base class for config panels. Provides layout helpers:

```python
class MyPanel(BasePanel):
    def __init__(self, tm, parent=None):
        super().__init__(tm, parent)
        sec = self._section("Title", "Description")     # creates a Card frame
        sec.addLayout(self._row("Label", widget, "hint")[0])
        self._root.addStretch()
```

---

### `core/resolver.py` — FieldResolver

Maps UI semantic keys to actual backend field values using the mapping config
produced by MappingPanel.

```python
resolver = FieldResolver(config["mapping"])

title  = resolver.get(record, "title")
image  = resolver.image_url(record, base_url="https://cdn.example.com")
authors = resolver.authors(record)
tags   = resolver.tags(record)
bound  = resolver.bind_all(record)  # {semantic_key: resolved_value}
```

- **Dot-notation paths**: `"author.avatar.url"` → walks nested dicts
- **List indexing**: `"items.0.title"` → walks into lists
- **Multi-candidate**: tries candidates in priority order, returns first non-null

---

### `core/configio.py` — ConfigIO

Static helpers for JSON config persistence:

```python
ConfigIO.save("config.json", config_dict)   # → bool
ConfigIO.load("config.json")                 # → dict | None
ConfigIO.validate(config_dict)               # → list[str] warnings
ConfigIO.merge(base_dict, override_dict)     # → merged dict
ConfigIO.defaults()                          # → minimal valid config
```

---

## How to Add a New Widget

1. **Import `get_state`:**
   ```python
   from core.app_state import get_state
   ```

2. **In `__init__`, grab state and apply theme:**
   ```python
   self._state = get_state()
   self._state.theme.apply(self)
   ```

3. **For theme-aware custom styles**, read tokens from the manager:
   ```python
   t = self._state.theme.colors
   self.setStyleSheet(f"background: {t['surface']};")
   ```

4. **For translations**, use `state.t()`:
   ```python
   self.label.setText(self._state.t("my_widget.title"))
   ```

5. **Subscribe to changes** for runtime switching:
   ```python
   self._state.lang.on_change(lambda _: self._retranslate())
   self._state.theme.on_change(lambda is_dark: self._refresh_theme())
   ```

---

## Running

```bash
python main.py
```

Requires: `PySide6`, `PyMuPDF` (fitz), `python-vlc`

---

## License

© 2026 — All rights reserved.
