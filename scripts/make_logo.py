"""Render the SeqTK-GUI logo into the files the project ships.

    python scripts/make_logo.py

Produces, from the same QPainter artwork the running app draws at runtime
(seqtk_gui/ui/app_icon.py):

* ``resources/app.ico``  - multi-size Windows icon (16-256 px) that PyInstaller
  embeds into ``dist/SeqTK-GUI.exe``, so Explorer, shortcuts and the taskbar
  show the logo without any runtime code. Sizes up to 64 px are stored as
  classic BMP/DIB entries and the larger two as PNG entries, which is the
  layout Windows itself expects.
* ``docs/logo.png``      - a 512 px PNG for the README headers.

Both outputs are committed; rerun this script only after changing the artwork.
No Qt application object is needed - the artwork paints onto plain QImages.
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QBuffer  # noqa: E402
from PySide6.QtGui import QImage  # noqa: E402

from seqtk_gui.ui.app_icon import render_image  # noqa: E402

ICO_SIZES = (16, 24, 32, 48, 64, 128, 256)
LOGO_PNG_SIZE = 512


def _png_bytes(image: QImage) -> bytes:
    buffer = QBuffer()
    buffer.open(QBuffer.OpenModeFlag.WriteOnly)
    image.save(buffer, "PNG")
    return bytes(buffer.data())


def _bmp_dib_bytes(image: QImage) -> bytes:
    """One ICO entry as a 32-bit BGRA bitmap with the AND mask appended.

    Every pixel carries its own alpha, so the 1-bit AND mask underneath is
    written as all-opaque zeros - that is exactly what Windows itself stores
    for alpha icons.
    """
    argb = image.convertToFormat(QImage.Format_ARGB32)
    width, height = argb.width(), argb.height()
    raw = bytes(argb.constBits())[: width * height * 4]
    stride = width * 4
    rows = [raw[y * stride:(y + 1) * stride] for y in range(height)]
    xor = b"".join(reversed(rows))
    mask_stride = ((width + 31) // 32) * 4
    AND = b"\x00" * (mask_stride * height)
    header = struct.pack("<IiiHHIIiiII", 40, width, height * 2, 1, 32, 0,
                         len(xor) + len(AND), 0, 0, 0, 0)
    return header + xor + AND


def _write_ico(path: Path) -> None:
    entries = []
    for size in ICO_SIZES:
        image = render_image(size)
        entries.append((size, _bmp_dib_bytes(image) if size <= 64 else _png_bytes(image)))
    header = struct.pack("<HHH", 0, 1, len(entries))
    offset = len(header) + 16 * len(entries)
    directory = b""
    body = b""
    for size, blob in entries:
        side = 0 if size >= 256 else size  # 0 is the ICO encoding for 256
        directory += struct.pack("<BBBBHHII", side, side, 0, 0, 1, 32,
                                 len(blob), offset + len(body))
        body += blob
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(header + directory + body)
    print("wrote", path)


def _write_logo_png(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    render_image(LOGO_PNG_SIZE).save(str(path), "PNG")
    print("wrote", path)


def main() -> int:
    _write_ico(ROOT / "resources" / "app.ico")
    _write_logo_png(ROOT / "docs" / "logo.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
