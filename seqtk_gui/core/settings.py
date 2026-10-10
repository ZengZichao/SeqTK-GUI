"""QSettings-backed preferences: language, theme, binary path, per-command form state."""

from __future__ import annotations

from typing import Any, Optional

from PySide6.QtCore import QSettings, QCoreApplication

from .paths import APP_NAME, ORG_NAME

KEY_LANGUAGE = "general/language"
KEY_THEME = "general/theme"
KEY_BINARY = "seqtk/binary"
KEY_WORKING_DIR = "seqtk/working_dir"
KEY_LAST_COMMAND = "ui/last_command"
KEY_WINDOW_GEOMETRY = "ui/window_geometry"
KEY_WINDOW_STATE = "ui/window_state"
KEY_RECENT_FILES = "ui/recent_files"
MAX_RECENT_FILES = 10
FORM_SECTION = "form"


class SettingsStore:
    """Typed access wrapper so the UI never touches raw keys."""

    def __init__(self, qsettings: Optional[QSettings] = None) -> None:
        if qsettings is None:
            # An application instance is required for the org/app scope to apply.
            if QCoreApplication.instance() is not None:
                QCoreApplication.setOrganizationName(ORG_NAME)
                QCoreApplication.setApplicationName(APP_NAME)
            qsettings = QSettings(ORG_NAME, APP_NAME)
        self._s = qsettings

    def get(self, key: str, default: str = "") -> str:
        value = self._s.value(key, default)
        if value is None:
            return default
        return str(value)

    def set(self, key: str, value: Any) -> None:
        self._s.setValue(key, value)
        self._s.sync()

    @property
    def language(self) -> str:
        value = self.get(KEY_LANGUAGE, "zh")
        return value if value in ("zh", "en") else "zh"

    @language.setter
    def language(self, code: str) -> None:
        self.set(KEY_LANGUAGE, code)

    @property
    def theme(self) -> str:
        value = self.get(KEY_THEME, "light")
        return value if value in ("light", "dark") else "light"

    @theme.setter
    def theme(self, name: str) -> None:
        self.set(KEY_THEME, name)

    @property
    def binary_path(self) -> Optional[str]:
        return self.get(KEY_BINARY, "") or None

    @binary_path.setter
    def binary_path(self, path: str) -> None:
        self.set(KEY_BINARY, path)

    @property
    def working_dir(self) -> str:
        return self.get(KEY_WORKING_DIR, "")

    @working_dir.setter
    def working_dir(self, path: str) -> None:
        self.set(KEY_WORKING_DIR, path)

    @property
    def last_command(self) -> str:
        return self.get(KEY_LAST_COMMAND, "seq")

    @last_command.setter
    def last_command(self, name: str) -> None:
        self.set(KEY_LAST_COMMAND, name)

    @property
    def window_geometry(self):
        return self._s.value(KEY_WINDOW_GEOMETRY)

    @window_geometry.setter
    def window_geometry(self, value) -> None:
        self._s.setValue(KEY_WINDOW_GEOMETRY, value)

    @property
    def window_state(self):
        return self._s.value(KEY_WINDOW_STATE)

    @window_state.setter
    def window_state(self, value) -> None:
        self._s.setValue(KEY_WINDOW_STATE, value)

    @property
    def recent_files(self) -> list[str]:
        raw = self._s.value(KEY_RECENT_FILES, "")
        if isinstance(raw, list):
            return [str(item) for item in raw if item]
        return [item for item in str(raw).split("\n") if item]

    def push_recent_file(self, path: str) -> None:
        items = [path] + [item for item in self.recent_files if item != path]
        self.set(KEY_RECENT_FILES, "\n".join(items[:MAX_RECENT_FILES]))

    # -- per command form state -------------------------------------------
    def save_form(self, command: str, values: dict[str, Any]) -> None:
        group = f"{FORM_SECTION}/{command}"
        self._s.remove(group)
        for key, value in values.items():
            if isinstance(value, bool):
                value = "true" if value else "false"
            self._s.setValue(f"{group}/{key}", value)
        self._s.sync()

    def load_form(self, command: str) -> dict[str, Any]:
        group = f"{FORM_SECTION}/{command}"
        out: dict[str, Any] = {}
        self._s.beginGroup(group)
        for key in self._s.allKeys():
            raw = self._s.value(key)
            out[key] = raw if raw is not None else ""
        self._s.endGroup()
        return out
