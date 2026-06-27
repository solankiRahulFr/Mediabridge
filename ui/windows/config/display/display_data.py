from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal


@dataclass
class DisplayModeConfig:
    # ── Window ──────────────────────────────────────────────────────────────
    fullscreen: bool = True
    target_screen_index: int = 1
    controllable: bool = False

    # ── Content ─────────────────────────────────────────────────────────────
    content_type: Literal["url", "image", "pdf", "video", "stream"] = "url"

    # ── URL ─────────────────────────────────────────────────────────────────
    url: str = "https://www.example.com"
    url_refresh_minutes: float = 0.0

    # ── Image carousel ──────────────────────────────────────────────────────
    image_paths: list[str] = field(default_factory=list)
    image_interval_seconds: int = 10
    image_screensaver_mode: bool = False
    image_fit: Literal["fill", "contain", "stretch"] = "contain"

    # ── PDF ─────────────────────────────────────────────────────────────────
    pdf_path: str = ""
    pdf_page_interval_seconds: int = 5
    pdf_loop: bool = True

    # ── Video (local file OR direct http/https stream URL) ───────────────────
    video_path: str = ""     
    video_loop: bool = True
    video_muted: bool = False

    # ── Stream (YouTube / Vimeo / embed URL rendered in WebEngine) ───────────
    stream_url: str = ""
    stream_autoplay: bool = True
    stream_loop: bool = True
    stream_muted: bool = True    

    # ── Exit / escape hatch ──────────────────────────────────────────────────
    exit_hotkey: str = "Ctrl+Shift+Q"  
    show_exit_badge: bool = True
    exit_badge_position: Literal[
        "top-left", "top-right", "bottom-left", "bottom-right"
    ] = "bottom-right"
    system_tray_exit: bool = False