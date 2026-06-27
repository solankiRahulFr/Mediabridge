"""
Field Mapping Panel — maps every UI semantic key to the actual key(s)
in the customer's backend API / data source.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from PySide6.QtWidgets import (
    QCheckBox, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve

from core.theme import ThemeManager
from core.i18n_mixin import I18nMixin
from .base_panel import BasePanel


# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class SemanticField:
    """Definition of one semantic UI field."""
    key: str
    label: str
    defaults: list[str]
    hint: str = ""
    category: str = ""
    enabled: bool = True


# ─────────────────────────────────────────────────────────────────────────────
FIELD_DEFINITIONS: list[SemanticField] = [
    # ── Identity
    SemanticField("primary_id", "Primary ID",
                  ["id", "uuid", "_id", "objectId"],
                  "Unique record identifier — used for deep-linking and caching.",
                  "Identity"),
    SemanticField("slug", "Slug / Permalink",
                  ["slug", "handle", "permalink", "url_key"],
                  "Human-readable URL segment.",
                  "Identity"),
    SemanticField("content_type", "Content Type",
                  ["content_type", "type", "kind", "format", "media_type"],
                  "Discriminates between video, pdf, article, event …",
                  "Identity"),

    # ── Taxonomy
    SemanticField("group", "Group / Category",
                  ["category", "group", "type", "genre", "section", "collection"],
                  "Primary classification bucket.",
                  "Taxonomy"),
    SemanticField("tags", "Tags / Keywords",
                  ["tags", "keywords", "labels", "topics", "interests"],
                  "Array of strings used for filtering and search.",
                  "Taxonomy"),

    # ── Content
    SemanticField("title", "Title",
                  ["title", "name", "headline", "subject"],
                  "Main display title.",
                  "Content"),
    SemanticField("subtitle", "Subtitle",
                  ["subtitle", "subheading", "tagline", "short_title"],
                  "Secondary title shown below the main title.",
                  "Content"),
    SemanticField("description", "Description / Body",
                  ["description", "body", "content", "summary", "excerpt", "overview"],
                  "Long-form text shown in detail views.",
                  "Content"),

    # ── Media
    SemanticField("primary_image", "Primary Image",
                  ["thumbnail", "cover", "image", "poster", "banner",
                   "cover_image", "featured_image", "photo"],
                  "Main visual shown on cards and detail pages.",
                  "Media"),
    SemanticField("video", "Video Source",
                  ["video", "video_url", "stream_url", "hls_url", "mp4_url", "media_url"],
                  "Direct URL or embed URL of the video asset.",
                  "Media"),
    SemanticField("pdf", "PDF Source",
                  ["pdf", "pdf_url", "document", "document_url", "file_url"],
                  "URL of the PDF asset.",
                  "Media"),
    SemanticField("image", "Standalone Image",
                  ["image", "image_url", "photo_url", "asset_url"],
                  "Image-only content (not the thumbnail).",
                  "Media"),
    SemanticField("qr_target", "QR Code Target URL",
                  ["url", "link", "canonical_url", "website", "external_url", "href"],
                  "URL encoded into a QR code widget on the detail screen.",
                  "Media"),

    # ── People
    SemanticField("authors", "Author(s)",
                  ["author", "authors", "creator", "contributors",
                   "presenter", "speaker", "instructor"],
                  "Person or persons responsible for the content.",
                  "People"),
    SemanticField("author_avatar", "Author Avatar",
                  ["author.avatar", "author.photo", "creator.photo",
                   "presenter.image", "speaker.avatar"],
                  "Dot-notation path or flat key for author profile image.",
                  "People"),
    SemanticField("organization", "Organization",
                  ["org", "organization", "company", "department",
                   "publisher", "brand", "institution"],
                  "Affiliated organisation shown alongside the author.",
                  "People"),

    # ── Dates
    SemanticField("publish_date", "Publish Date",
                  ["published_at", "date", "created_at", "release_date", "publish_date"],
                  "ISO-8601 date/datetime string.",
                  "Dates & Schedule"),
    SemanticField("updated_date", "Updated Date",
                  ["updated_at", "modified_at", "last_edited", "last_modified"],
                  "Date the record was last changed.",
                  "Dates & Schedule"),
    SemanticField("schedule", "Scheduled / Air Time",
                  ["schedule", "air_time", "event_date", "start_time", "event_start"],
                  "For live events or timed broadcasts.",
                  "Dates & Schedule"),

    # ── Stats
    SemanticField("duration", "Duration / Read Time",
                  ["duration", "length", "runtime", "read_time", "watch_time"],
                  "Numeric value in seconds, or a pre-formatted string.",
                  "Stats & Engagement"),
    SemanticField("likes", "Likes / Reactions",
                  ["likes", "reactions", "thumbs_up", "upvotes", "hearts", "love_count"],
                  "Engagement counter shown on cards.",
                  "Stats & Engagement"),
    SemanticField("views", "Views / Plays",
                  ["views", "view_count", "impressions", "plays", "watch_count"],
                  "Reach counter shown on cards.",
                  "Stats & Engagement"),
    SemanticField("rating", "Rating / Score",
                  ["rating", "score", "stars", "grade", "quality_score"],
                  "Numeric or string rating (0-5, A-F, etc.).",
                  "Stats & Engagement"),
]


# ─────────────────────────────────────────────────────────────────────────────
class MappingRow(QFrame):
    """One row in the mapping table."""

    def __init__(self, sf: SemanticField, parent: QWidget | None = None):
        super().__init__(parent)
        self._sf = sf
        self._defaults = sf.defaults.copy()
        self.setObjectName("MappingRow")
        self._build()
        

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(14, 10, 14, 10)
        outer.setSpacing(6)
        

        row = QHBoxLayout()
        row.setSpacing(10)

        self._enabled = QCheckBox()
        self._enabled.setChecked(self._sf.enabled)
        self._enabled.setFixedWidth(20)
        row.addWidget(self._enabled)

        key_col = QVBoxLayout()
        key_col.setSpacing(1)
        key_lbl = QLabel(self._sf.key)
        key_lbl.setObjectName("SemanticKey")
        key_lbl.setFixedWidth(170)
        key_col.addWidget(key_lbl)
        human_lbl = QLabel(self._sf.label)
        human_lbl.setObjectName("SemanticCategory")
        key_col.addWidget(human_lbl)
        row.addLayout(key_col)

        self._input = QLineEdit()
        self._input.setText(",  ".join(self._defaults))
        self._input.setPlaceholderText("field1,  field2,  …")
        self._input.setToolTip(self._sf.hint)
        row.addWidget(self._input, 1)

        reset_btn = QPushButton("↩")
        reset_btn.setObjectName("SmallBtn")
        reset_btn.setFixedSize(32, 32)
        reset_btn.setToolTip("Reset to defaults")
        reset_btn.setCursor(Qt.PointingHandCursor)
        reset_btn.setStyleSheet("font-size: 18px;")
        reset_btn.clicked.connect(self._reset)
        row.addWidget(reset_btn)

        outer.addLayout(row)

        if self._sf.hint:
            hint = QLabel(self._sf.hint)
            hint.setObjectName("HintLabel")
            hint.setContentsMargins(34, 0, 0, 0)
            hint.setWordWrap(True)
            outer.addWidget(hint)

    def _reset(self):
        self._input.setText(",  ".join(self._defaults))

    def get_value(self) -> dict:
        raw = self._input.text()
        candidates = [c.strip() for c in raw.split(",") if c.strip()]
        return {
            "enabled":    self._enabled.isChecked(),
            "candidates": candidates,
        }

    def set_value(self, d: dict):
        if "enabled"    in d: self._enabled.setChecked(d["enabled"])
        if "candidates" in d: self._input.setText(",  ".join(d["candidates"]))


# ─────────────────────────────────────────────────────────────────────────────
class CollapsibleGroup(QWidget):
    """Collapsible section header + content area."""

    def __init__(self, title: str, parent: QWidget | None = None):
        super().__init__(parent)
        self._collapsed = False
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._toggle = QPushButton(f"▾  {title}")
        self._toggle.setObjectName("NavBtn")
        self._toggle.setCheckable(False)
        self._toggle.setCursor(Qt.PointingHandCursor)
        self._toggle.setFixedHeight(38)
        self._toggle.setStyleSheet(
            "QPushButton { text-align:left; padding:0 12px; font-weight:700; }"
        )
        self._toggle.clicked.connect(self._toggle_collapse)
        outer.addWidget(self._toggle)

        self._body = QWidget()
        self._body_lay = QVBoxLayout(self._body)
        self._body_lay.setContentsMargins(0, 6, 0, 6)
        self._body_lay.setSpacing(6)
        outer.addWidget(self._body)

    def add_row(self, row: MappingRow):
        self._body_lay.addWidget(row)

    def _toggle_collapse(self):
        self._collapsed = not self._collapsed
        self._body.setVisible(not self._collapsed)
        label = self._toggle.text()
        self._toggle.setText(
            label.replace("▾", "▸") if self._collapsed else label.replace("▸", "▾")
        )


# ─────────────────────────────────────────────────────────────────────────────
class MappingPanel(BasePanel):
    def __init__(self, tm: ThemeManager, parent: QWidget | None = None):
        super().__init__(tm, parent)
        self._rows: dict[str, MappingRow] = {}
        self._build()

    def _build(self):
        intro = self._section(
            "Backend Field Mapping",
            (
                "Map each UI concept to the actual field name(s) in your API / data source. "
                "Enter multiple candidates separated by commas — the kiosk will try them in order "
                "and use the first non-null value found at runtime.  "
                "Dot-notation is supported for nested objects  (e.g.  author.avatar)."
            ),
            title_key="config_dual_mode.mapping.title",
            desc_key="config_dual_mode.mapping.desc",
        )
        self.setStyleSheet("background-color: transparent;")

        groups: dict[str, list[SemanticField]] = {}
        for sf in FIELD_DEFINITIONS:
            groups.setdefault(sf.category, []).append(sf)

        for group_title, fields in groups.items():
            grp = CollapsibleGroup(group_title)
            for sf in fields:
                row = MappingRow(sf)
                self._rows[sf.key] = row
                grp.add_row(row)
            intro.addWidget(grp)

        # ── Preset loader ─────────────────────────────────────────────────────
        preset_sec = self._section(
            "Quick Presets",
            "Apply a field-name convention common to popular CMS / API platforms. "
            "Presets only fill in defaults — your custom edits above take priority.",
            title_key="config_dual_mode.mapping.presets",
            desc_key="config_dual_mode.mapping.presets.desc",
        )
        btn_row = QHBoxLayout()
        presets = [
            ("Contentful",  self._preset_contentful),
            ("Strapi",      self._preset_strapi),
            ("Sanity",      self._preset_sanity),
            ("WordPress",   self._preset_wordpress),
            ("Custom REST", self._preset_rest),
        ]
        for label, fn in presets:
            btn = QPushButton(label)
            btn.setObjectName("SmallBtn")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(fn)
            btn_row.addWidget(btn)
        btn_row.addStretch()
        preset_sec.addLayout(btn_row)

        self._root.addStretch()
        
        # Apply initial translations
        self.retranslate_ui()

    # ── Preset definitions ────────────────────────────────────────────────────
    def _apply_preset(self, mapping: dict[str, list[str]]):
        for key, candidates in mapping.items():
            if key in self._rows:
                self._rows[key].set_value({"candidates": candidates})

    def _preset_contentful(self):
        self._apply_preset({
            "primary_id":    ["sys.id"],
            "title":         ["fields.title"],
            "subtitle":      ["fields.subtitle"],
            "description":   ["fields.description", "fields.body"],
            "primary_image": ["fields.thumbnail.fields.file.url", "fields.image.fields.file.url"],
            "video":         ["fields.videoUrl", "fields.video.fields.file.url"],
            "tags":          ["metadata.tags", "fields.tags"],
            "publish_date":  ["sys.createdAt"],
            "updated_date":  ["sys.updatedAt"],
            "authors":       ["fields.author.fields.name", "fields.author"],
            "author_avatar": ["fields.author.fields.photo.fields.file.url"],
        })

    def _preset_strapi(self):
        self._apply_preset({
            "primary_id":    ["id", "documentId"],
            "title":         ["title", "name"],
            "subtitle":      ["subtitle"],
            "description":   ["description", "content", "body"],
            "primary_image": ["thumbnail.url", "cover.url", "image.url"],
            "video":         ["video.url", "videoUrl"],
            "tags":          ["tags", "categories"],
            "publish_date":  ["publishedAt", "createdAt"],
            "updated_date":  ["updatedAt"],
            "authors":       ["author.name", "authors"],
            "author_avatar": ["author.avatar.url"],
            "slug":          ["slug"],
        })

    def _preset_sanity(self):
        self._apply_preset({
            "primary_id":    ["_id"],
            "title":         ["title"],
            "description":   ["body", "description", "excerpt"],
            "primary_image": ["mainImage.asset.url", "image.asset.url"],
            "video":         ["video.asset.url", "videoUrl"],
            "tags":          ["tags", "categories"],
            "publish_date":  ["publishedAt", "_createdAt"],
            "updated_date":  ["_updatedAt"],
            "authors":       ["author.name", "authors"],
            "slug":          ["slug.current"],
        })

    def _preset_wordpress(self):
        self._apply_preset({
            "primary_id":    ["id"],
            "title":         ["title.rendered", "title"],
            "description":   ["content.rendered", "excerpt.rendered"],
            "primary_image": ["_embedded.wp:featuredmedia.0.source_url",
                              "featured_media_url"],
            "tags":          ["tags", "_embedded.wp:term"],
            "publish_date":  ["date", "date_gmt"],
            "updated_date":  ["modified", "modified_gmt"],
            "authors":       ["_embedded.author.0.name"],
            "author_avatar": ["_embedded.author.0.avatar_urls.96"],
            "slug":          ["slug", "link"],
        })

    def _preset_rest(self):
        """Generic REST convention (snake_case)."""
        self._apply_preset({
            "primary_id":    ["id", "uuid"],
            "title":         ["title", "name"],
            "subtitle":      ["subtitle", "tagline"],
            "description":   ["description", "body", "summary"],
            "primary_image": ["thumbnail", "image", "cover"],
            "video":         ["video_url", "video"],
            "pdf":           ["pdf_url", "document_url"],
            "tags":          ["tags", "keywords"],
            "publish_date":  ["published_at", "created_at"],
            "updated_date":  ["updated_at"],
            "authors":       ["author", "authors"],
            "author_avatar": ["author_avatar", "author.avatar"],
            "slug":          ["slug", "handle"],
            "qr_target":     ["url", "external_url", "link"],
        })

    # ── serialisation ─────────────────────────────────────────────────────────
    def get_values(self) -> dict:
        return {key: row.get_value() for key, row in self._rows.items()}

    def set_values(self, d: dict):
        for key, row in self._rows.items():
            if key in d:
                row.set_value(d[key])

    def retranslate_ui(self) -> None:
        """Update translatable strings."""
        super().retranslate_ui()  # Call parent to update all bound labels