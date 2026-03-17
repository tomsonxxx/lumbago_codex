from __future__ import annotations

from PyQt6 import QtCore, QtWidgets
from lumbago_app.ui.widgets import apply_dialog_fade, dialog_icon_pixmap
from lumbago_app.core.models import Track
from lumbago_app.data.repository import update_track


class ManualSearchDialog(QtWidgets.QDialog):
    """Dialog ręcznego wyszukiwania metadanych przez MusicBrainz dla jednego tracku."""

    def __init__(self, track: Track, musicbrainz_app: str | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ręczne wyszukiwanie metadanych")
        self.setMinimumSize(820, 500)
        apply_dialog_fade(self)
        self._track = track
        self._mb_app = musicbrainz_app or "LumbagoMusicAI"
        self._results: list[dict] = []
        self._build_ui()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        card = QtWidgets.QFrame()
        card.setObjectName("DialogCard")
        card_layout = QtWidgets.QVBoxLayout(card)
        card_layout.setContentsMargins(16, 14, 16, 16)
        card_layout.setSpacing(10)
        layout.addWidget(card)
        layout = card_layout

        title_row = QtWidgets.QHBoxLayout()
        title_icon = QtWidgets.QLabel()
        title_icon.setPixmap(dialog_icon_pixmap(18))
        title_icon.setFixedSize(20, 20)
        title_lbl = QtWidgets.QLabel(self.windowTitle())
        title_lbl.setObjectName("DialogTitle")
        title_row.addWidget(title_icon)
        title_row.addWidget(title_lbl)
        title_row.addStretch(1)
        layout.addLayout(title_row)

        track_info = QtWidgets.QLabel(
            f"Utwór: {self._track.title or '—'}  |  Artysta: {self._track.artist or '—'}  |  {self._track.path}"
        )
        track_info.setObjectName("DialogHint")
        track_info.setWordWrap(True)
        layout.addWidget(track_info)

        # Pole wyszukiwania
        search_row = QtWidgets.QHBoxLayout()
        search_row.addWidget(QtWidgets.QLabel("Szukaj:"))
        self.search_input = QtWidgets.QLineEdit()
        default_query = " ".join(filter(None, [self._track.artist, self._track.title]))
        self.search_input.setText(default_query)
        self.search_input.setPlaceholderText("np. Daft Punk Around the World")
        self.search_input.returnPressed.connect(self._run_search)
        search_row.addWidget(self.search_input, 1)
        self.search_btn = QtWidgets.QPushButton("Szukaj")
        self.search_btn.setFixedWidth(80)
        self.search_btn.clicked.connect(self._run_search)
        search_row.addWidget(self.search_btn)
        layout.addLayout(search_row)

        self.status_label = QtWidgets.QLabel("")
        self.status_label.setObjectName("DialogHint")
        layout.addWidget(self.status_label)

        # Tabela wyników
        self.results_table = QtWidgets.QTableWidget(0, 5)
        self.results_table.setHorizontalHeaderLabels(["Tytuł", "Artysta", "Album", "Rok", "Wynik"])
        header = self.results_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Interactive)
        self.results_table.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.results_table.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.results_table.doubleClicked.connect(self._apply_selected)
        layout.addWidget(self.results_table, 1)

        hint = QtWidgets.QLabel("Kliknij dwukrotnie wynik lub zaznacz i naciśnij Zastosuj.")
        hint.setObjectName("DialogHint")
        layout.addWidget(hint)

        btn_row = QtWidgets.QHBoxLayout()
        self.apply_btn = QtWidgets.QPushButton("Zastosuj wybrany")
        self.apply_btn.setEnabled(False)
        self.apply_btn.clicked.connect(self._apply_selected)
        self.results_table.selectionModel().selectionChanged.connect(
            lambda: self.apply_btn.setEnabled(bool(self.results_table.selectedItems()))
        )
        close_btn = QtWidgets.QPushButton("Zamknij")
        close_btn.clicked.connect(self.reject)
        btn_row.addStretch(1)
        btn_row.addWidget(self.apply_btn)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def _run_search(self):
        query = self.search_input.text().strip()
        if not query:
            return
        self.search_btn.setEnabled(False)
        self.status_label.setText("Wyszukiwanie…")
        QtWidgets.QApplication.processEvents()
        worker = _MBSearchWorker(query, self._mb_app)
        worker.signals.finished.connect(self._on_results)
        QtCore.QThreadPool.globalInstance().start(worker)

    def _on_results(self, results: list[dict]):
        self.search_btn.setEnabled(True)
        self._results = results
        self.results_table.setRowCount(0)
        if not results:
            self.status_label.setText("Brak wyników.")
            return
        self.status_label.setText(f"Znaleziono: {len(results)} nagrań")
        for rec in results:
            row = self.results_table.rowCount()
            self.results_table.insertRow(row)
            self.results_table.setItem(row, 0, QtWidgets.QTableWidgetItem(rec.get("title", "")))
            artists = ", ".join(
                a.get("name", "") for a in rec.get("artist-credit", [])
                if isinstance(a, dict) and "name" in a
            )
            self.results_table.setItem(row, 1, QtWidgets.QTableWidgetItem(artists))
            releases = rec.get("releases", [])
            album = releases[0].get("title", "") if releases else ""
            year = str(releases[0].get("date", "")[:4]) if releases else ""
            self.results_table.setItem(row, 2, QtWidgets.QTableWidgetItem(album))
            self.results_table.setItem(row, 3, QtWidgets.QTableWidgetItem(year))
            score = str(rec.get("score", ""))
            self.results_table.setItem(row, 4, QtWidgets.QTableWidgetItem(score))

    def _apply_selected(self):
        row = self.results_table.currentRow()
        if row < 0 or row >= len(self._results):
            return
        rec = self._results[row]
        title = rec.get("title", "")
        artists = [a.get("name", "") for a in rec.get("artist-credit", []) if isinstance(a, dict) and "name" in a]
        artist = " & ".join(filter(None, artists))
        releases = rec.get("releases", [])
        album = releases[0].get("title", "") if releases else ""
        year = str(releases[0].get("date", "")[:4]) if releases else ""
        if title:
            self._track.title = title
        if artist:
            self._track.artist = artist
        if album:
            self._track.album = album
        if year:
            self._track.year = year
        update_track(self._track)
        QtWidgets.QMessageBox.information(
            self,
            "Zastosowano",
            f"Metadane zaktualizowane:\n"
            f"Tytuł: {title}\nArtysta: {artist}\nAlbum: {album}\nRok: {year}"
        )
        self.accept()


class _MBSearchSignals(QtCore.QObject):
    finished = QtCore.pyqtSignal(list)


class _MBSearchWorker(QtCore.QRunnable):
    def __init__(self, query: str, app_name: str):
        super().__init__()
        self.query = query
        self.app_name = app_name
        self.signals = _MBSearchSignals()

    def run(self):
        from lumbago_app.services.metadata_providers import MusicBrainzProvider
        provider = MusicBrainzProvider(self.app_name)
        data = provider.search_recording(self.query)
        recordings: list[dict] = []
        if isinstance(data, dict):
            recordings = data.get("recordings", [])
        self.signals.finished.emit(recordings)
