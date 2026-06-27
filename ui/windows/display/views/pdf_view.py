"""
PDFView — renders a PDF page-by-page, auto-advancing on a timer.

Requires:
    pip install pypdf pillow          (for rendering pages to pixmaps)
    OR PySide6's built-in QPdfView    (PySide6 >= 6.4)

Strategy
────────
  1.  Try QPdfDocument / QPdfView (zero extra deps, PySide6 ≥ 6.4).
  2.  Fall back to pypdf + Pillow rendering if QPdfView is absent.
  3.  If neither works, show a placeholder label.
"""

from __future__ import annotations
import logging
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

log = logging.getLogger("mediabridge.display.pdf")

# ── Backend detection ─────────────────────────────────────────────────────────
try:
    from PySide6.QtPdf import QPdfDocument
    from PySide6.QtPdfWidgets import QPdfView
    _BACKEND = "qt"
except ImportError:
    _BACKEND = None

if _BACKEND is None:
    try:
        import pypdf          # noqa: F401
        from PIL import Image  # noqa: F401
        _BACKEND = "pillow"
    except ImportError:
        _BACKEND = None

log.info("PDF backend: %s", _BACKEND or "none (placeholder)")


class PDFView(QWidget):
    def __init__(
        self,
        pdf_path: str,
        page_interval_seconds: int = 5,
        loop: bool = True,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._path = pdf_path
        self._interval = page_interval_seconds
        self._loop = loop
        self._page = 0
        self._total_pages = 0
        self._timer: QTimer | None = None

        self.setStyleSheet("background: #1A1A1A;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        if _BACKEND == "qt":
            self._init_qt(layout)
        elif _BACKEND == "pillow":
            self._init_pillow(layout)
        else:
            self._init_placeholder(layout)

    # ── Qt backend ────────────────────────────────────────────────────────────
    def _init_qt(self, layout: QVBoxLayout) -> None:
        self._doc = QPdfDocument(self)
        self._pdf_view = QPdfView(self)
        self._pdf_view.setDocument(self._doc)
        self._pdf_view.setPageMode(QPdfView.PageMode.SinglePage)
        layout.addWidget(self._pdf_view)

    # ── Pillow / pypdf backend ────────────────────────────────────────────────
    def _init_pillow(self, layout: QVBoxLayout) -> None:
        self._img_label = QLabel(self)
        self._img_label.setAlignment(Qt.AlignCenter)
        self._img_label.setStyleSheet("background: #1A1A1A;")
        layout.addWidget(self._img_label)
        self._doc = None

    # ── Placeholder ───────────────────────────────────────────────────────────
    def _init_placeholder(self, layout: QVBoxLayout) -> None:
        lbl = QLabel(
            "⚠  PDF rendering unavailable\n\n"
            "Install PySide6-Addons or pypdf + Pillow",
            self,
        )
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("color: #8B90A8; font-size: 16px;")
        layout.addWidget(lbl)

    # ── Lifecycle ─────────────────────────────────────────────────────────────
    def start(self) -> None:
        if not Path(self._path).is_file():
            log.warning("PDF not found: %s", self._path)
            return

        if _BACKEND == "qt":
            self._doc.load(self._path)
            self._total_pages = self._doc.pageCount()
            self._go_to(0)
        elif _BACKEND == "pillow":
            self._render_page_pillow(0)

        if self._total_pages > 1 or _BACKEND == "pillow":
            self._timer = QTimer(self)
            self._timer.setInterval(self._interval * 1000)
            self._timer.timeout.connect(self._advance)
            self._timer.start()
            log.info("PDF viewer started — %d pages, %ds interval",
                     self._total_pages, self._interval)

    def stop(self) -> None:
        if self._timer:
            self._timer.stop()

    # ── Navigation ────────────────────────────────────────────────────────────
    def _advance(self) -> None:
        next_page = self._page + 1
        if next_page >= self._total_pages:
            if self._loop:
                next_page = 0
            else:
                self._timer and self._timer.stop()
                return
        if _BACKEND == "qt":
            self._go_to(next_page)
        elif _BACKEND == "pillow":
            self._render_page_pillow(next_page)

    def _go_to(self, page: int) -> None:
        self._page = page
        if _BACKEND == "qt":
            nav = self._pdf_view.pageNavigator()
            nav.jump(page, nav.currentLocation(), nav.currentZoom())

    def _render_page_pillow(self, page_idx: int) -> None:
        """Render via pypdf → PIL → QPixmap (software fallback)."""
        try:
            import pypdf
            from PIL import Image
            import io

            reader = pypdf.PdfReader(self._path)
            self._total_pages = len(reader.pages)
            self._page = page_idx % self._total_pages

            # pypdf can't rasterize — use pypdf for page count, pillow for image
            # Try pdf2image if available, otherwise show page number overlay
            try:
                from pdf2image import convert_from_path
                images = convert_from_path(
                    self._path, first_page=self._page + 1,
                    last_page=self._page + 1, dpi=150
                )
                if images:
                    img = images[0]
                    buf = io.BytesIO()
                    img.save(buf, format="PNG")
                    qpx = QPixmap()
                    qpx.loadFromData(buf.getvalue())
                    w, h = self.width() or 1920, self.height() or 1080
                    self._img_label.setPixmap(
                        qpx.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    )
            except ImportError:
                # Neither pdf2image available — show page counter
                self._img_label.setText(
                    f"PDF: {Path(self._path).name}\n"
                    f"Page {self._page + 1} / {self._total_pages}\n\n"
                    "(Install pdf2image + poppler for rendering)"
                )
                self._img_label.setStyleSheet(
                    "color: #8B90A8; font-size: 18px; background: #1A1A1A;"
                )
        except Exception as exc:
            log.exception("PDF render error: %s", exc)
