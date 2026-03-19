"""Lumbago Music AI — Panel szczegółów aktywnego utworu."""

import logging
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout,
    QLabel, QScrollArea, QFrame,
)

logger = logging.getLogger(__name__)


class DetailsPanel(QWidget):
    """Panel boczny z detalami wybranego utworu."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumWidth(250)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        self._title_label = QLabel("— Brak wybranego utworu —")
        self._title_label.setWordWrap(True)
        self._title_label.setStyleSheet("color: #00f5ff; font-weight: bold; font-size: 13px;")
        layout.addWidget(self._title_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameStyle(QFrame.Shape.NoFrame)

        content = QWidget()
        self._form = QFormLayout(content)
        self._form.setSpacing(6)
        self._form.setContentsMargins(0, 4, 0, 4)

        self._fields: dict[str, QLabel] = {}
        for field, label in [
            ("artist",      "Artysta"),
            ("album",       "Album"),
            ("year",        "Rok"),
            ("genre",       "Gatunek"),
            ("bpm",         "BPM"),
            ("key_camelot", "Tonacja"),
            ("duration",    "Czas"),
            ("energy_level","Energia"),
            ("rating",      "Ocena"),
            ("label",       "Wytwórnia"),
            ("isrc",        "ISRC"),
            ("bit_rate",    "Bitrate"),
            ("sample_rate", "Sample Rate"),
        ]:
            val_label = QLabel("—")
            val_label.setStyleSheet("color: #c0c0c0;")
            val_label.setWordWrap(True)
            lbl = QLabel(f"{label}:")
            lbl.setStyleSheet("color: #606070; font-size: 11px;")
            self._form.addRow(lbl, val_label)
            self._fields[field] = val_label

        scroll.setWidget(content)
        layout.addWidget(scroll, stretch=1)

        # Tagi
        tags_lbl = QLabel("TAGI:")
        tags_lbl.setStyleSheet("color: #606070; font-size: 10px; letter-spacing: 1px; margin-top: 4px;")
        layout.addWidget(tags_lbl)

        from lumbago_app.ui.widgets.tag_cloud_widget import TagCloud
        self._tag_cloud = TagCloud()
        self._tag_cloud.setMaximumHeight(100)
        layout.addWidget(self._tag_cloud)

    def load_track(self, track_id: int) -> None:
        """Ładuje i wyświetla dane wybranego utworu."""
        try:
            from lumbago_app.data.database import session_scope
            from lumbago_app.data.models import TrackOrm

            with session_scope() as session:
                track = session.get(TrackOrm, track_id)
                if not track:
                    return
                self._update_display(track)
        except Exception as exc:
            logger.warning("Błąd ładowania szczegółów utworu %d: %s", track_id, exc)

    def _update_display(self, track: object) -> None:
        """Aktualizuje pola wyświetlane w panelu."""
        from lumbago_app.core.utils import format_duration

        title = getattr(track, "title", None) or "Nieznany tytuł"
        artist = getattr(track, "artist", None) or "Nieznany artysta"
        self._title_label.setText(f"{artist}\n{title}")

        for field, lbl in self._fields.items():
            value = getattr(track, field, None)
            if value is None:
                lbl.setText("—")
            elif field == "duration":
                lbl.setText(format_duration(float(value)))
            elif field == "bpm":
                lbl.setText(f"{value:.1f}")
            elif field == "rating":
                lbl.setText("★" * int(value) if value else "—")
            elif field == "bit_rate":
                lbl.setText(f"{value} kbps" if value else "—")
            elif field == "sample_rate":
                lbl.setText(f"{value} Hz" if value else "—")
            else:
                lbl.setText(str(value))

        # Tagi
        tags = [t.name for t in getattr(track, "tags", [])]
        self._tag_cloud.set_tags(tags, editable=False)
