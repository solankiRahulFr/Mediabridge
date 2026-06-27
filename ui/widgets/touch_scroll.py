from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, QPoint, Qt, QTimer
from PySide6.QtWidgets import QAbstractScrollArea, QScrollArea, QScrollBar


# ── tunables ─────────────────────────────────────────────────────────────────
FLICK_FRICTION        = 0.92   # velocity decay per tick (0–1; lower = more friction)
FLICK_TICK_MS         = 16     # ~60 fps
FLICK_MIN_SPEED       = 2      # px/tick below which we stop
SWIPE_THRESHOLD_PX    = 8      # minimum drag before we treat it as a scroll


class _FlickEngine(QObject):

    def __init__(self, scroll_area: QAbstractScrollArea):
        super().__init__(scroll_area)
        self._sa   = scroll_area
        self._vx   = 0.0
        self._vy   = 0.0
        self._timer = QTimer(self)
        self._timer.setInterval(FLICK_TICK_MS)
        self._timer.timeout.connect(self._tick)

    # public ──────────────────────────────────────────────────────────────────

    def kick(self, vx: float, vy: float):
        self._vx = vx
        self._vy = vy
        if not self._timer.isActive():
            self._timer.start()

    def stop(self):
        self._timer.stop()
        self._vx = self._vy = 0.0

    # internal ────────────────────────────────────────────────────────────────

    def _tick(self):
        if abs(self._vx) < FLICK_MIN_SPEED and abs(self._vy) < FLICK_MIN_SPEED:
            self._timer.stop()
            return

        hbar: QScrollBar = self._sa.horizontalScrollBar()
        vbar: QScrollBar = self._sa.verticalScrollBar()

        if hbar:
            hbar.setValue(int(hbar.value() - self._vx))
        if vbar:
            vbar.setValue(int(vbar.value() - self._vy))

        self._vx *= FLICK_FRICTION
        self._vy *= FLICK_FRICTION


class TouchScrollFilter(QObject):

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        # keyed by scroll-area id() so we don't keep hard refs
        self._engines:    dict[int, _FlickEngine]  = {}
        self._pressing:   dict[int, bool]          = {}
        self._last_pos:   dict[int, QPoint]        = {}
        self._start_pos:  dict[int, QPoint]        = {}
        self._velocity:   dict[int, tuple[float, float]] = {}

    # ── event filter ─────────────────────────────────────────────────────────

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if not isinstance(obj, QAbstractScrollArea):
            return super().eventFilter(obj, event)

        vp = obj.viewport()          # events come from the viewport
        if obj is not vp:
            # re-check: PySide6 routes viewport events through the SA too
            pass

        t = event.type()

        if t in (QEvent.Type.MouseButtonPress, QEvent.Type.TouchBegin):
            self._on_press(obj, event)
        elif t in (QEvent.Type.MouseMove, QEvent.Type.TouchUpdate):
            return self._on_move(obj, event)
        elif t in (QEvent.Type.MouseButtonRelease, QEvent.Type.TouchEnd):
            self._on_release(obj, event)

        return super().eventFilter(obj, event)

    # ── helpers ───────────────────────────────────────────────────────────────

    def _engine(self, sa: QAbstractScrollArea) -> _FlickEngine:
        k = id(sa)
        if k not in self._engines:
            self._engines[k] = _FlickEngine(sa)
        return self._engines[k]

    def _global_pos(self, event: QEvent) -> QPoint | None:
        if hasattr(event, "globalPosition"):          # MouseEvent
            return event.globalPosition().toPoint()
        if hasattr(event, "touchPoints"):             # TouchEvent
            pts = event.touchPoints()
            if pts:
                return pts[0].globalPosition().toPoint()
        return None

    def _on_press(self, sa: QAbstractScrollArea, event: QEvent):
        k = id(sa)
        pos = self._global_pos(event)
        if pos is None:
            return
        self._engine(sa).stop()
        self._pressing[k]  = True
        self._last_pos[k]  = pos
        self._start_pos[k] = pos
        self._velocity[k]  = (0.0, 0.0)

    def _on_move(self, sa: QAbstractScrollArea, event: QEvent) -> bool:
        k = id(sa)
        if not self._pressing.get(k):
            return False

        pos = self._global_pos(event)
        if pos is None:
            return False

        last = self._last_pos[k]
        start = self._start_pos[k]
        dx = pos.x() - last.x()
        dy = pos.y() - last.y()

        # Only steal the event once the drag exceeds the threshold
        dist = ((pos.x() - start.x())**2 + (pos.y() - start.y())**2) ** 0.5
        if dist < SWIPE_THRESHOLD_PX:
            return False

        # Scroll
        hbar = sa.horizontalScrollBar()
        vbar = sa.verticalScrollBar()
        if hbar:
            hbar.setValue(hbar.value() - dx)
        if vbar:
            vbar.setValue(vbar.value() - dy)

        self._velocity[k] = (dx * 0.6 + self._velocity[k][0] * 0.4,
                              dy * 0.6 + self._velocity[k][1] * 0.4)
        self._last_pos[k] = pos
        return True   # consume event so the view doesn't also select/drag

    def _on_release(self, sa: QAbstractScrollArea, event: QEvent):
        k = id(sa)
        if not self._pressing.pop(k, False):
            return
        vx, vy = self._velocity.get(k, (0.0, 0.0))
        if abs(vx) > FLICK_MIN_SPEED or abs(vy) > FLICK_MIN_SPEED:
            self._engine(sa).kick(vx, vy)


# ── convenience subclass ──────────────────────────────────────────────────────

class TouchScrollArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._engine  = _FlickEngine(self)
        self._pressing = False
        self._last_pos: QPoint | None = None
        self._start_pos: QPoint | None = None
        self._velocity = (0.0, 0.0)
        self.viewport().setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, True)
        self.grabGesture(Qt.GestureType.PanGesture)

    def mousePressEvent(self, event):
        self._engine.stop()
        self._pressing  = True
        self._last_pos  = event.globalPosition().toPoint()
        self._start_pos = self._last_pos
        self._velocity  = (0.0, 0.0)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not self._pressing or self._last_pos is None:
            return super().mouseMoveEvent(event)
        pos = event.globalPosition().toPoint()
        dx  = pos.x() - self._last_pos.x()
        dy  = pos.y() - self._last_pos.y()
        dist = ((pos.x() - self._start_pos.x())**2 +
                (pos.y() - self._start_pos.y())**2) ** 0.5
        if dist >= SWIPE_THRESHOLD_PX:
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - dx)
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - dy)
            self._velocity = (dx * 0.6 + self._velocity[0] * 0.4,
                              dy * 0.6 + self._velocity[1] * 0.4)
        self._last_pos = pos

    def mouseReleaseEvent(self, event):
        self._pressing = False
        vx, vy = self._velocity
        if abs(vx) > FLICK_MIN_SPEED or abs(vy) > FLICK_MIN_SPEED:
            self._engine.kick(vx, vy)
        super().mouseReleaseEvent(event)