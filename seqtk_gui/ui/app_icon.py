"""The application icon, drawn at every needed size with QPainter.

A black rounded tile carrying two intertwined white strands - the double
helix of seqtk's subject matter reduced to pure line, no literal rungs.
Title bar, taskbar and About dialog share one source and the repository
stays free of binary assets; scripts/make_logo.py rasterises the same code
into app.ico and logo.png.
"""

from __future__ import annotations

import math

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QIcon, QImage, QPainter, QPainterPath, QPen, QPixmap

_SIZES = (16, 24, 32, 48, 64, 128, 256)
_TILE = QColor("#000000")
_STRAND = QColor("#ffffff")


def application_icon() -> QIcon:
    icon = QIcon()
    for size in _SIZES:
        icon.addPixmap(render_pixmap(size))
    return icon


def render_pixmap(size: int) -> QPixmap:
    return QPixmap.fromImage(render_image(size))


def render_image(size: int) -> QImage:
    """The logo rasterised at ``size`` on a transparent canvas.

    Painting goes onto a QImage rather than a QPixmap so headless scripts
    (make_screenshots, make_logo) can call it without a QGuiApplication.
    """
    image = QImage(size, size, QImage.Format_ARGB32)
    image.fill(Qt.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing, True)

    margin = size * 0.04
    tile = QRectF(margin, margin, size - 2 * margin, size - 2 * margin)
    painter.setPen(Qt.NoPen)
    painter.setBrush(QBrush(_TILE))
    painter.drawRoundedRect(tile, tile.width() * 0.22, tile.height() * 0.22)

    # One continuous ribbon folded into a figure-eight: two loops meeting at
    # a single crossing, where the right loop passes OVER the left one (the
    # tile-coloured halo cuts a gap). Two strands, one knot - the double
    # helix reduced to pure line, abstract on purpose.
    width = max(1.2, size * 0.048)
    gap = max(1.0, size * 0.020)

    def arc(u0: float, u1: float) -> QPainterPath:
        path = QPainterPath()
        steps = max(120, size // 3)
        for step in range(steps + 1):
            u = u0 + (u1 - u0) * step / steps
            x = tile.center().x() + tile.width() * 0.36 * math.sin(u)
            y = tile.center().y() + tile.height() * 0.33 * math.sin(u) * math.cos(u)
            if step == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)
        return path

    def stroke(path: QPainterPath, pen_width: int, color: QColor) -> None:
        pen = QPen(color, pen_width)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawPath(path)

    left = arc(math.pi, 2 * math.pi)
    right = arc(0.0, math.pi)

    stroke(left, round(width), _STRAND)
    stroke(right, round(width + 2 * gap), _TILE)   # right loop passes over:
    stroke(right, round(width), _STRAND)           # the halo cuts the left one

    painter.end()
    return image
