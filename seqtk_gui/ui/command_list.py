"""Grouped, filterable list of every seqtk subcommand."""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QLabel, QLineEdit, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

from ..core.spec import COMMANDS, GROUP_LABELS_EN, GROUP_LABELS_ZH, GROUPS
from ..i18n.catalog import Language


class CommandList(QWidget):
    selected = Signal(str)

    def __init__(self, lang: Language, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._lang = lang
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self._title = QLabel("")
        self._title.setFont(QFont(self._title.font().family(), 11, QFont.Bold))
        layout.addWidget(self._title)

        self.filter_edit = QLineEdit()
        self.filter_edit.setClearButtonEnabled(True)
        self.filter_edit.textChanged.connect(self._apply_filter)
        layout.addWidget(self.filter_edit)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setRootIsDecorated(True)
        self.tree.setIndentation(14)
        self.tree.setUniformRowHeights(True)
        self.tree.itemSelectionChanged.connect(self._emit_selection)
        layout.addWidget(self.tree, 1)

        self._items: list[tuple[str, str, str, QTreeWidgetItem]] = []
        self._groups: list[tuple[str, QTreeWidgetItem]] = []
        self._build()
        self.retranslate()

    def _build(self) -> None:
        for group in GROUPS:
            top = QTreeWidgetItem([self._group_label(group)])
            # Headers stay enabled (so children remain selectable) but are not
            # themselves selectable.
            top.setFlags(top.flags() & ~Qt.ItemIsSelectable)
            font = top.font(0)
            font.setBold(True)
            top.setFont(0, font)
            self.tree.addTopLevelItem(top)
            self._groups.append((group, top))
            for command in COMMANDS:
                if command.group != group:
                    continue
                item = QTreeWidgetItem([command.name])
                item.setData(0, Qt.UserRole, command.name)
                item.setToolTip(0, self._lang.pick(command.summary_en, command.summary_zh))
                top.addChild(item)
                self._items.append((command.name, command.summary_en, command.summary_zh, item))

    def _group_label(self, group: str) -> str:
        return self._lang.pick(GROUP_LABELS_EN[group], GROUP_LABELS_ZH[group])

    def _emit_selection(self) -> None:
        items = self.tree.selectedItems()
        if not items:
            return
        name = items[0].data(0, Qt.UserRole)
        if name:
            self.selected.emit(str(name))

    def select(self, name: str) -> None:
        for command_name, _, _, item in self._items:
            if command_name == name:
                self.tree.setCurrentItem(item)
                return

    def current(self) -> Optional[str]:
        items = self.tree.selectedItems()
        if not items:
            return None
        name = items[0].data(0, Qt.UserRole)
        return str(name) if name else None

    def _apply_filter(self, text: str) -> None:
        needle = text.strip().lower()
        for group, top in self._groups:
            visible_children = 0
            for index in range(top.childCount()):
                child = top.child(index)
                name = str(child.data(0, Qt.UserRole))
                summary = child.toolTip(0).lower()
                match = not needle or needle in name or needle in summary
                child.setHidden(not match)
                visible_children += 1 if match else 0
            top.setHidden(visible_children == 0)
            top.setExpanded(True)

    def retranslate(self) -> None:
        self._title.setText(self._lang.tr("panel.commands"))
        self.filter_edit.setPlaceholderText(self._lang.tr("panel.filter"))
        for group, top in self._groups:
            top.setText(0, self._group_label(group))
        for name, summary_en, summary_zh, item in self._items:
            item.setToolTip(0, self._lang.pick(summary_en, summary_zh))
            item.setText(0, name)
        for _, top in self._groups:
            top.setExpanded(True)
