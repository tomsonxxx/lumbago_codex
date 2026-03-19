"""
Lumbago Music AI — Dialog AI Taggera
======================================
Wybór kryterium, szacowanie kosztów, uruchomienie tagowania.
"""

import logging
from typing import Optional

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QProgressBar, QRadioButton, QButtonGroup,
    QCheckBox, QDialogButtonBox, QGroupBox, QTextEdit,
)

logger = logging.getLogger(__name__)


class _TagWorker(QThread):
    """Worker thread dla tagowania AI."""
    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(int, int)  # (success, failed)
    error = pyqtSignal(str)

    def __init__(self, track_ids: list[int]) -> None:
        super().__init__()
        self._track_ids = track_ids
        self._cancelled = False

    def run(self) -> None:
        try:
            from lumbago_app.services.ai.tagger_service import TaggerService

            service = TaggerService()
            results = service.tag_tracks(
                self._track_ids,
                progress_callback=lambda c, t, title: self.progress.emit(c, t, title),
            )
            success = sum(1 for v in results.values() if v)
            failed = len(results) - success
            self.finished.emit(success, failed)
        except Exception as exc:
            self.error.emit(str(exc))

    def cancel(self) -> None:
        self._cancelled = True


class TaggerDialog(QDialog):
    """Dialog uruchamiający AI tagowanie biblioteki."""

    def __init__(self, track_ids: Optional[list[int]] = None, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("✦ AI Tagger — Tagowanie AI")
        self.setMinimumWidth(500)
        self.setMinimumHeight(380)
        self._track_ids = track_ids
        self._worker: Optional[_TagWorker] = None
        self._build_ui()
        self._load_info()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Opis
        info = QLabel(
            "AI Tagger analizuje metadane utworów i automatycznie przypisuje:\n"
            "gatunek, nastrój, styl, poziom energii i tagi słów kluczowych."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #909090; font-size: 11px;")
        layout.addWidget(info)

        # Wybór zakresu
        scope_group = QGroupBox("Zakres tagowania")
        scope_layout = QVBoxLayout(scope_group)

        self._rb_all = QRadioButton("Wszystkie utwory w bibliotece")
        self._rb_untagged = QRadioButton("Tylko nieoznakowane (bez gatunku)")
        self._rb_selected = QRadioButton("Zaznaczone w tabeli")
        self._rb_untagged.setChecked(True)

        if not self._track_ids:
            self._rb_selected.setEnabled(False)

        scope_layout.addWidget(self._rb_all)
        scope_layout.addWidget(self._rb_untagged)
        scope_layout.addWidget(self._rb_selected)
        layout.addWidget(scope_group)

        # Opcje
        self._cb_overwrite = QCheckBox("Nadpisuj istniejące tagi AI")
        self._cb_cache = QCheckBox("Używaj cache (pomijaj wcześniej otagowane)")
        self._cb_cache.setChecked(True)
        layout.addWidget(self._cb_overwrite)
        layout.addWidget(self._cb_cache)

        # Szacowanie kosztów
        self._cost_label = QLabel("Szacowany koszt: obliczanie...")
        self._cost_label.setStyleSheet("color: #80c080; font-size: 11px;")
        layout.addWidget(self._cost_label)

        # Progress
        self._progress = QProgressBar()
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setMaximumHeight(80)
        self._log.setVisible(False)
        layout.addWidget(self._log)

        # Przyciski
        self._btn_start = QPushButton("▶  Uruchom tagowanie")
        self._btn_start.setProperty("accent", True)
        self._btn_start.clicked.connect(self._on_start)

        self._btn_cancel = QPushButton("Anuluj")
        self._btn_cancel.clicked.connect(self.reject)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self._btn_cancel)
        btn_layout.addWidget(self._btn_start)
        layout.addLayout(btn_layout)

    def _load_info(self) -> None:
        """Ładuje informacje o dostępnych providerach i szacunku kosztów."""
        try:
            from lumbago_app.services.ai.llm_router import get_router
            from lumbago_app.data.database import session_scope
            from lumbago_app.data.repository import TrackRepository

            router = get_router()
            if not router.has_providers:
                self._cost_label.setText(
                    "Brak skonfigurowanych kluczy API.\nDodaj klucz w Ustawienia → AI/LLM."
                )
                self._cost_label.setStyleSheet("color: #ff6060; font-size: 11px;")
                self._btn_start.setEnabled(False)
                return

            with session_scope() as session:
                count = TrackRepository(session).count()

            estimates = router.estimate_cost(count)
            if estimates:
                cheapest = min(estimates, key=estimates.get)  # type: ignore[arg-type]
                self._cost_label.setText(
                    f"Biblioteka: {count:,} utworów | "
                    f"Najtańszy provider: {cheapest} "
                    f"(~${estimates[cheapest]:.4f})"
                )
        except Exception as exc:
            self._cost_label.setText(f"Błąd ładowania info: {exc}")

    def _on_start(self) -> None:
        """Uruchamia tagowanie."""
        try:
            track_ids = self._get_track_ids()
            if not track_ids:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(
                    self, "Brak utworów", "Nie znaleziono utworów do tagowania."
                )
                return

            self._progress.setVisible(True)
            self._progress.setRange(0, len(track_ids))
            self._progress.setValue(0)
            self._log.setVisible(True)
            self._btn_start.setEnabled(False)

            self._worker = _TagWorker(track_ids)
            self._worker.progress.connect(self._on_progress)
            self._worker.finished.connect(self._on_finished)
            self._worker.error.connect(self._on_error)
            self._worker.start()

        except Exception as exc:
            logger.error("Błąd uruchamiania taggera: %s", exc)

    def _get_track_ids(self) -> list[int]:
        """Zwraca listę ID do tagowania wg wybranego zakresu."""
        from lumbago_app.data.database import session_scope
        from lumbago_app.data.repository import TrackRepository
        from sqlalchemy import select
        from lumbago_app.data.models import TrackOrm

        with session_scope() as session:
            repo = TrackRepository(session)
            if self._rb_all.isChecked():
                return [t.id for t in repo.get_all(limit=10000)]
            elif self._rb_untagged.isChecked():
                tracks = session.execute(
                    select(TrackOrm).where(TrackOrm.genre.is_(None))
                ).scalars().all()
                return [t.id for t in tracks]
            else:
                return self._track_ids or []

    def _on_progress(self, current: int, total: int, title: str) -> None:
        self._progress.setValue(current)
        self._log.append(f"[{current}/{total}] {title}")

    def _on_finished(self, success: int, failed: int) -> None:
        self._btn_start.setEnabled(True)
        self._log.append(f"\nGotowe: {success} otagowano, {failed} błędów.")
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(
            self, "Tagowanie zakończone",
            f"Otagowano: {success} utworów\nBłędy: {failed}"
        )

    def _on_error(self, msg: str) -> None:
        self._btn_start.setEnabled(True)
        self._log.append(f"\nBŁĄD: {msg}")
        logger.error("Błąd taggera: %s", msg)
