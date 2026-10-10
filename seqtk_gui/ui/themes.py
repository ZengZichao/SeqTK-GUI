"""Light and dark themes.

Both are expressed as a QPalette plus a small QSS layer, so the app looks
correct on Windows (Fusion style) and will keep working on macOS where the
native style ignores parts of the palette.
"""

from __future__ import annotations

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

THEMES = ("light", "dark")

_LIGHT = {
    "window": "#f3f4f6",
    "base": "#ffffff",
    "text": "#1c1f23",
    "muted": "#5b6470",
    "accent": "#1f6feb",
    "accent_hover": "#3483f0",
    "accent_pressed": "#1a5fd0",
    "accent_text": "#ffffff",
    "border": "#d6dae0",
    "alt": "#eaeef3",
    "ok": "#1a7f37",
    "err": "#b3261e",
    "err_soft": "#fbeaec",
    "err_text": "#ffffff",
}

_DARK = {
    "window": "#1e2124",
    "base": "#25292e",
    "text": "#e6e8ea",
    "muted": "#9aa4b0",
    "accent": "#3b82f6",
    "accent_hover": "#5a97f8",
    "accent_pressed": "#2f6fd6",
    "accent_text": "#ffffff",
    "border": "#3a4046",
    "alt": "#2b3036",
    "ok": "#4ec98b",
    "err": "#c4473c",
    "err_soft": "#4a2a27",
    "err_text": "#ffffff",
}

MONO_STACK = "Consolas, 'Cascadia Mono', 'SF Mono', Menlo, monospace"


def colors(theme: str) -> dict[str, str]:
    return _DARK if theme == "dark" else _LIGHT


def build_palette(theme: str) -> QPalette:
    c = colors(theme)
    palette = QPalette()
    window = QColor(c["window"])
    base = QColor(c["base"])
    text = QColor(c["text"])
    accent = QColor(c["accent"])
    palette.setColor(QPalette.Window, window)
    palette.setColor(QPalette.WindowText, text)
    palette.setColor(QPalette.Base, base)
    palette.setColor(QPalette.AlternateBase, QColor(c["alt"]))
    palette.setColor(QPalette.Text, text)
    palette.setColor(QPalette.Button, QColor(c["alt"]))
    palette.setColor(QPalette.ButtonText, text)
    palette.setColor(QPalette.ToolTipBase, base)
    palette.setColor(QPalette.ToolTipText, text)
    palette.setColor(QPalette.BrightText, text)
    palette.setColor(QPalette.Highlight, accent)
    palette.setColor(QPalette.HighlightedText, QColor(c["accent_text"]))
    palette.setColor(QPalette.Link, accent)
    disabled = QColor(c["muted"])
    palette.setColor(QPalette.Disabled, QPalette.Text, disabled)
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, disabled)
    palette.setColor(QPalette.Disabled, QPalette.WindowText, disabled)
    return palette


def build_qss(theme: str) -> str:
    c = colors(theme)
    return f"""
* {{ outline: 0; }}
QWidget {{ background: {c['window']}; color: {c['text']}; }}
QMainWindow::separator {{ background: {c['border']}; width: 1px; height: 1px; }}
QGroupBox {{
    border: 1px solid {c['border']}; border-radius: 7px; margin-top: 14px;
    padding: 8px 8px 8px 8px; font-weight: 600;
}}
QGroupBox::title {{ subcontrol-origin: margin; left: 8px; padding: 0 4px; color: {c['muted']}; }}
QPushButton {{
    background: {c['base']}; border: 1px solid {c['border']}; border-radius: 5px;
    padding: 5px 12px;
}}
QPushButton:hover {{ border-color: {c['accent']}; background: {c['alt']}; }}
QPushButton:focus {{ border-color: {c['accent']}; }}
QPushButton:default, QPushButton[accent="true"] {{
    background: {c['accent']}; color: {c['accent_text']}; border-color: {c['accent']};
}}
QPushButton[accent="true"]:hover {{ background: {c['accent_hover']}; border-color: {c['accent_hover']}; }}
QPushButton[accent="true"]:focus {{ border-color: {c['accent_pressed']}; }}
QPushButton[accent="true"]:pressed, QPushButton[accent="true"]:default:hover {{
    background: {c['accent_pressed']}; border-color: {c['accent_pressed']};
}}
QPushButton[danger="true"] {{
    background: {c['base']}; color: {c['err']}; border-color: {c['err']};
}}
QPushButton[danger="true"]:enabled:hover {{ background: {c['err_soft']}; border-color: {c['err']}; }}
QPushButton[danger="true"]:enabled:pressed {{ background: {c['err']}; color: {c['err_text']}; }}
QPushButton[danger="true"]:disabled {{ color: {c['muted']}; background: {c['alt']}; border-color: {c['border']}; }}
QPushButton:disabled {{ color: {c['muted']}; background: {c['alt']}; }}
QLineEdit, QPlainTextEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
    background: {c['base']}; border: 1px solid {c['border']}; border-radius: 5px;
    padding: 3px 6px; selection-background-color: {c['accent']};
    selection-color: {c['accent_text']};
}}
QLineEdit:hover:!focus, QPlainTextEdit:hover:!focus, QTextEdit:hover:!focus,
QSpinBox:hover:!focus, QDoubleSpinBox:hover:!focus, QComboBox:hover:!focus {{
    border-color: {c['muted']};
}}
QLineEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
    border-color: {c['accent']};
}}
QLineEdit:read-only, QPlainTextEdit:read-only {{ background: {c['alt']}; }}
QSpinBox, QDoubleSpinBox {{ padding-right: 18px; }}
QSpinBox::up-button, QDoubleSpinBox::up-button {{
    subcontrol-origin: border; subcontrol-position: top right;
    width: 16px; border-left: 1px solid {c['border']}; background: {c['alt']};
}}
QSpinBox::down-button, QDoubleSpinBox::down-button {{
    subcontrol-origin: border; subcontrol-position: bottom right;
    width: 16px; border-left: 1px solid {c['border']}; background: {c['alt']};
}}
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow,
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
    width: 0; height: 0; border-left: 3px solid transparent; border-right: 3px solid transparent;
}}
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{ border-bottom: 4px solid {c['text']}; }}
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{ border-top: 4px solid {c['text']}; }}
QComboBox::drop-down {{ border: 0; width: 18px; }}
QComboBox::down-arrow {{
    width: 0; height: 0; border-left: 3px solid transparent; border-right: 3px solid transparent;
    border-top: 4px solid {c['text']};
}}
QComboBox QAbstractItemView {{
    background: {c['base']}; border: 1px solid {c['border']};
    selection-background-color: {c['accent']}; selection-color: {c['accent_text']};
}}
QTreeWidget, QListWidget, QTreeView, QListView {{
    background: {c['base']}; border: 1px solid {c['border']}; border-radius: 6px;
    outline: 0;
}}
QTreeWidget::item, QListWidget::item {{ padding: 3px 2px; border: 0; }}
QTreeWidget::item:hover, QListWidget::item:hover {{ background: {c['alt']}; }}
QTreeWidget::item:selected, QListWidget::item:selected {{
    background: {c['accent']}; color: {c['accent_text']};
}}
QHeaderView::section {{
    background: {c['alt']}; border: 0; border-bottom: 1px solid {c['border']};
    padding: 4px; color: {c['muted']};
}}
QTabWidget::pane {{ border: 1px solid {c['border']}; border-radius: 6px; top: -1px; }}
QTabBar::tab {{
    background: {c['alt']}; border: 1px solid {c['border']};
    border-bottom: 0; border-top-left-radius: 5px; border-top-right-radius: 5px;
    padding: 5px 16px; color: {c['muted']};
}}
QTabBar::tab:hover {{ color: {c['text']}; }}
QTabBar::tab:selected {{ background: {c['base']}; color: {c['text']}; }}
QToolTip {{
    background: {c['base']}; color: {c['text']};
    border: 1px solid {c['border']}; border-radius: 4px; padding: 4px 8px;
}}
QScrollBar:vertical {{ background: transparent; width: 11px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {c['border']}; border-radius: 5px; min-height: 28px; }}
QScrollBar::handle:vertical:hover {{ background: {c['muted']}; }}
QScrollBar:horizontal {{ background: transparent; height: 11px; margin: 0; }}
QScrollBar::handle:horizontal {{ background: {c['border']}; border-radius: 5px; min-width: 28px; }}
QScrollBar::handle:horizontal:hover {{ background: {c['muted']}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
QStatusBar {{ background: {c['alt']}; border-top: 1px solid {c['border']}; }}
QStatusBar::item {{ border: 0; }}
QMenuBar {{ background: {c['window']}; border-bottom: 1px solid {c['border']}; }}
QMenuBar::item {{ background: transparent; padding: 4px 10px; border-radius: 4px; }}
QMenuBar::item:selected {{ background: {c['accent']}; color: {c['accent_text']}; }}
QMenu {{ background: {c['base']}; border: 1px solid {c['border']}; }}
QMenu::item {{ padding: 5px 28px 5px 14px; }}
QMenu::item:selected {{ background: {c['accent']}; color: {c['accent_text']}; }}
QMenu::item:disabled {{ color: {c['muted']}; }}
QMenu::separator {{ height: 1px; background: {c['border']}; margin: 4px 8px; }}
QToolBar {{
    background: {c['window']}; border-bottom: 1px solid {c['border']};
    padding: 4px 6px; spacing: 6px;
}}
QToolBar::separator {{ background: {c['border']}; width: 1px; margin: 4px 4px; }}
QCheckBox::indicator {{ width: 15px; height: 15px; }}
QLabel[muted="true"] {{ color: {c['muted']}; }}
QLabel[flag="true"] {{ font-family: {MONO_STACK}; font-weight: 600; }}
QLabel[error="true"] {{ color: {c['err']}; }}
QLabel[help="true"] {{ color: {c['muted']}; }}
QToolButton {{
    background: {c['base']}; border: 1px solid {c['border']}; border-radius: 5px;
    padding: 4px 10px;
}}
QToolButton:hover {{ border-color: {c['accent']}; }}
QToolButton:disabled {{ color: {c['muted']}; }}
QSplitter::handle {{ background: {c['border']}; }}
"""


def apply_theme(app: QApplication, theme: str) -> None:
    app.setStyle("Fusion")
    app.setPalette(build_palette(theme))
    app.setStyleSheet(build_qss(theme))
