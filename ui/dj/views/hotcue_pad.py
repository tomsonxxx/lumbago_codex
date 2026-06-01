"""
ui/dj/views/hotcue_pad.py

Ulepszony HotcuePad w stylu Rekordbox.

- Zawsze używa 8 unikalnych kolorów z BOOTH_COLORS
- Duży rozmiar 82×62 (booth-friendly)
- Pełne wsparcie etykiet niestandardowych (przyszłe)
- Używa wyłącznie helperów z styles.py – zero inline
- Sygnały: activated, set_requested
- Obsługa prawego przycisku = set, Ctrl+klik = clear (w kontrolerze)

Cały kod i komentarze po polsku.
"""

from __future__ import annotations

from PyQt6 import QtCore, QtGui, QtWidgets

from ui.dj.styles import BOOTH_COLORS, BOOTH_SIZES, get_hotcue_pad_stylesheet


class HotcuePad(QtWidgets.QPushButton):
    """
    Profesjonalny pad hotcue (2×4 grid).

    Różnice vs stary HotcuePad:
    - Używa palety 8 kolorów z BOOTH_COLORS (zamiast 4)
    - Rozmiar zdefiniowany centralnie
    - Lepsze tooltipy + miejsce na custom label
    - Style wyłącznie przez get_hotcue_pad_stylesheet
    """

    activated = QtCore.pyqtSignal(int)           # lewy klik → skok lub clear
    set_requested = QtCore.pyqtSignal(int)       # szybkie ustawienie (z menu lub legacy)
    delete_requested = QtCore.pyqtSignal(int)    # usuń hotcue
    rename_requested = QtCore.pyqtSignal(int)    # poproś o zmianę nazwy
    color_change_requested = QtCore.pyqtSignal(int, str)  # index + nowy kolor hex

    def __init__(self, index: int, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.index = index
        self._has_cue: bool = False
        self._cue_time_ms: int | None = None
        self._custom_label: str | None = None

        # Rozmiar z centralnej definicji (booth 82×62)
        size = BOOTH_SIZES.get("hotcue_pad", (82, 62))
        self.setFixedSize(*size)

        self.setText(str(index + 1))
        self._update_tooltip()
        self._apply_style()

        self.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)

    def _apply_style(self) -> None:
        """Zawsze deleguje do helpera – nigdy inline."""
        stylesheet = get_hotcue_pad_stylesheet(self.index, has_cue=self._has_cue)
        self.setStyleSheet(stylesheet)

    def _update_tooltip(self) -> None:
        base = f"Hotcue {self.index + 1}"
        if self._has_cue and self._cue_time_ms is not None:
            total_sec = max(0, self._cue_time_ms) // 1000
            m, s = divmod(total_sec, 60)
            tstr = f"{m}:{s:02d}"
            label_part = f" • {self._custom_label}" if self._custom_label else ""
            self.setToolTip(
                f"{base}{label_part}  •  {tstr}\n"
                f"Klik: skocz  •  Ctrl+Klik: usuń  •  Prawy: nadpisz"
            )
        else:
            self.setToolTip(
                f"{base}\nKlik: skocz (po ustawieniu)  •  Prawy przycisk: ustaw w playhead"
            )

    def set_cue_time(self, time_ms: int | None, label: str | None = None) -> None:
        """Ustawia czas + opcjonalną etykietę (przygotowanie na przyszłość)."""
        self._cue_time_ms = time_ms
        self._custom_label = label
        self._has_cue = time_ms is not None
        self._update_tooltip()
        self._apply_style()
        self.update()

    def clear_cue(self) -> None:
        """Czyści stan pada (wywoływane przez kontroler po usunięciu)."""
        self._has_cue = False
        self._cue_time_ms = None
        self._custom_label = None
        self._update_tooltip()
        self._apply_style()

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:  # type: ignore
        """Lewy = activated, Prawy = pełne menu kontekstowe."""
        if event.button() == QtCore.Qt.MouseButton.RightButton:
            self._show_context_menu(event.globalPosition().toPoint())
            event.accept()
            return

        # Lewy przycisk – normalna aktywacja (z Ctrl obsługuje kontroler)
        self.activated.emit(self.index)
        super().mouseReleaseEvent(event)

    # Dla kompatybilności z ewentualnym starym kodem (nie używane w nowych widokach)
    def _update_style(self) -> None:
        self._apply_style()

    def _show_context_menu(self, global_pos: QtCore.QPoint) -> None:
        """Profesjonalne menu kontekstowe w stylu Rekordbox."""
        menu = QtWidgets.QMenu(self)

        # Zawsze dostępna opcja szybkiego ustawienia
        if self._has_cue:
            menu.addAction("Nadpisz w aktualnym playhead", lambda: self.set_requested.emit(self.index))
            menu.addSeparator()
            menu.addAction("Usuń hotcue", lambda: self.delete_requested.emit(self.index))

            # Zmień nazwę
            menu.addAction("Zmień nazwę...", lambda: self.rename_requested.emit(self.index))

            # Zmień kolor – submenu
            color_menu = menu.addMenu("Zmień kolor")
            colors = BOOTH_COLORS.get("hotcue", [])
            for i, color in enumerate(colors):
                action = color_menu.addAction(f"Kolor {i+1}")
                action.setIcon(self._create_color_icon(color))
                action.triggered.connect(lambda checked=False, c=color: self.color_change_requested.emit(self.index, c))
        else:
            menu.addAction("Ustaw w aktualnym playhead", lambda: self.set_requested.emit(self.index))

        menu.exec(global_pos)

    def _create_color_icon(self, color_hex: str) -> QtGui.QIcon:
        """Prosta kolorowa ikonka do menu."""
        pixmap = QtGui.QPixmap(16, 16)
        pixmap.fill(QtGui.QColor(color_hex))
        return QtGui.QIcon(pixmap)

