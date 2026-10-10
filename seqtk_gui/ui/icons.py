"""Theme-aware vector icons drawn with QPainter at load time.

The app ships no binary icon assets: every glyph is stroked from a small
path table in the current palette's colors, so light and dark themes both
get crisp icons and switching themes only means drawing them again.
"""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap

_ICON_SIZES = (16, 20, 24, 32, 48)

# name -> painter callback receiving (painter, unit square, color)
_GLYPHS: dict[str, Callable[[QPainter, QRectF, QColor], None]] = {}


def _pt(rect: QRectF, ux: float, uy: float) -> QPointF:
    return QPointF(rect.left() + rect.width() * ux,
                   rect.top() + rect.height() * uy)


def _register(name: str):
    def wrap(fn: Callable[[QPainter, QRectF, QColor], None]):
        _GLYPHS[name] = fn
        return fn
    return wrap


def _stroke_path(p: QPainter, rect: QRectF, points: list[tuple[float, float]],
                 color: QColor, close: bool = False) -> None:
    path = QPainterPath(_pt(rect, *points[0]))
    for ux, uy in points[1:]:
        path.lineTo(_pt(rect, ux, uy))
    if close:
        path.closeSubpath()
    p.drawPath(path)


@_register("play")
def _play(p: QPainter, rect: QRectF, color: QColor) -> None:
    p.setPen(Qt.NoPen)
    p.setBrush(color)
    path = QPainterPath(_pt(rect, 0.32, 0.20))
    path.lineTo(_pt(rect, 0.80, 0.50))
    path.lineTo(_pt(rect, 0.32, 0.80))
    path.closeSubpath()
    p.drawPath(path)


@_register("stop")
def _stop(p: QPainter, rect: QRectF, color: QColor) -> None:
    p.setPen(Qt.NoPen)
    p.setBrush(color)
    p.drawRoundedRect(QRectF(_pt(rect, 0.26, 0.26), _pt(rect, 0.74, 0.74)), 2, 2)


@_register("folder")
def _folder(p: QPainter, rect: QRectF, color: QColor) -> None:
    _stroke_path(p, rect, [(0.10, 0.72), (0.10, 0.28), (0.40, 0.28),
                           (0.47, 0.36), (0.90, 0.36), (0.90, 0.72)],
                 color, close=True)
    _stroke_path(p, rect, [(0.10, 0.46), (0.90, 0.46)], color)


@_register("trash")
def _trash(p: QPainter, rect: QRectF, color: QColor) -> None:
    _stroke_path(p, rect, [(0.16, 0.28), (0.84, 0.28)], color)
    _stroke_path(p, rect, [(0.40, 0.28), (0.40, 0.18), (0.60, 0.18), (0.60, 0.28)], color)
    _stroke_path(p, rect, [(0.26, 0.28), (0.31, 0.82), (0.69, 0.82), (0.74, 0.28)],
                 color, close=True)
    _stroke_path(p, rect, [(0.44, 0.44), (0.44, 0.66)], color)
    _stroke_path(p, rect, [(0.56, 0.44), (0.56, 0.66)], color)


@_register("copy")
def _copy(p: QPainter, rect: QRectF, color: QColor) -> None:
    path = QPainterPath(_pt(rect, 0.36, 0.18))
    path.lineTo(_pt(rect, 0.82, 0.18))
    path.lineTo(_pt(rect, 0.82, 0.64))
    p.drawPath(path)
    _stroke_path(p, rect, [(0.36, 0.18), (0.18, 0.18), (0.18, 0.64), (0.64, 0.64),
                           (0.64, 0.40), (0.36, 0.40)], color, close=True)


@_register("doc")
def _doc(p: QPainter, rect: QRectF, color: QColor) -> None:
    _stroke_path(p, rect, [(0.28, 0.12), (0.58, 0.12), (0.72, 0.26), (0.72, 0.88),
                           (0.28, 0.88)], color, close=True)
    _stroke_path(p, rect, [(0.58, 0.12), (0.58, 0.26), (0.72, 0.26)], color)
    _stroke_path(p, rect, [(0.38, 0.46), (0.62, 0.46)], color)
    _stroke_path(p, rect, [(0.38, 0.60), (0.62, 0.60)], color)
    _stroke_path(p, rect, [(0.38, 0.74), (0.62, 0.74)], color)


@_register("info")
def _info(p: QPainter, rect: QRectF, color: QColor) -> None:
    p.drawEllipse(QRectF(_pt(rect, 0.14, 0.14), _pt(rect, 0.86, 0.86)))
    p.setPen(Qt.NoPen)
    p.setBrush(color)
    p.drawEllipse(QRectF(_pt(rect, 0.455, 0.28), _pt(rect, 0.545, 0.37)))
    p.setPen(QPen(color, rect.width() / 12, Qt.SolidLine, Qt.RoundCap))
    _stroke_path(p, rect, [(0.50, 0.48), (0.50, 0.70)], color)


def line_icon(name: str, color: QColor) -> QIcon:
    """One named glyph rendered as a multi-size QIcon in ``color``."""
    icon = QIcon()
    for size in _ICON_SIZES:
        pixmap = _render(name, color, size)
        if pixmap is not None:
            icon.addPixmap(pixmap)
    return icon


def _render(name: str, color: QColor, size: int) -> QPixmap | None:
    glyph = _GLYPHS.get(name)
    if glyph is None:
        return None
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    pen = QPen(color, max(1.2, size / 13.0))
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)
    glyph(painter, QRectF(0, 0, size, size), color)
    painter.end()
    return pixmap
