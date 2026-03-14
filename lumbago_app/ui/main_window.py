from __future__ import annotations

from pathlib import Path
import json

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer

from lumbago_app.core.audio import apply_local_metadata, clear_tags, extract_metadata, iter_audio_files, write_tags
import shutil
from lumbago_app.core.config import cache_dir, load_settings
from lumbago_app.core.models import Track
from lumbago_app.core.services import heuristic_analysis
from lumbago_app.core.waveform import generate_waveform
from lumbago_app.data.repository import (
    add_track_to_playlist,
    add_change_log,
    create_playlist,
    delete_playlist,
    init_db,
    list_playlist_tracks,
    list_playlists,
    list_playlists_full,
    list_tracks,
    set_playlist_track_order,
    update_playlist,
    update_tracks,
    update_track,
    upsert_tracks,
)
from lumbago_app.ui.ai_tagger_dialog import AiTaggerDialog
from lumbago_app.ui.bulk_edit_dialog import BulkEditDialog
from lumbago_app.ui.change_history_dialog import ChangeHistoryDialog
from lumbago_app.ui.duplicates_dialog import DuplicatesDialog
from lumbago_app.ui.import_wizard import ImportWizard
from lumbago_app.ui.models import TrackGridDelegate, TrackTableModel
from lumbago_app.ui.playlist_dialog import PlaylistEditorDialog
from lumbago_app.ui.playlist_order_dialog import PlaylistOrderDialog
from lumbago_app.ui.recognition_queue import RecognitionBatchWorker
from lumbago_app.ui.renamer_dialog import RenamerDialog
from lumbago_app.ui.settings_dialog import SettingsDialog
from lumbago_app.ui.tag_compare_dialog import TagCompareDialog
from lumbago_app.ui.widgets import AnimatedButton
from lumbago_app.ui.xml_converter_dialog import XmlConverterDialog
from lumbago_app.ui.xml_import_dialog import XmlImportDialog


class TrackFilterProxy(QtCore.QSortFilterProxyModel):
    def __init__(self):
        super().__init__()
        self.search_text = ""
        self.bpm_min = None
        self.bpm_max = None
        self.key = ""
        self.genre = ""

    def filterAcceptsRow(self, source_row: int, source_parent: QtCore.QModelIndex) -> bool:
        model = self.sourceModel()
        if model is None:
            return True
        title = model.index(source_row, 0, source_parent).data() or ""
        artist = model.index(source_row, 1, source_parent).data() or ""
        album = model.index(source_row, 2, source_parent).data() or ""
        genre = model.index(source_row, 3, source_parent).data() or ""
        bpm_text = model.index(source_row, 4, source_parent).data() or ""
        key = model.index(source_row, 5, source_parent).data() or ""

        search_blob = f"{title} {artist} {album}".lower()
        if self.search_text and self.search_text not in search_blob:
            return False

        if self.genre and self.genre.lower() not in genre.lower():
            return False

        if self.key and self.key.lower() not in key.lower():
            return False

        if bpm_text:
            try:
                bpm = float(bpm_text)
            except ValueError:
                bpm = None
        else:
            bpm = None

        if self.bpm_min is not None and bpm is not None and bpm < self.bpm_min:
            return False
        if self.bpm_max is not None and bpm is not None and bpm > self.bpm_max:
            return False

        return True


class ScanWorkerSignals(QtCore.QObject):
    progress = QtCore.pyqtSignal(int, int)
    finished = QtCore.pyqtSignal(list)


class ScanWorker(QtCore.QRunnable):
    def __init__(self, folder: Path):
        super().__init__()
        self.folder = folder
        self.signals = ScanWorkerSignals()

    def run(self):
        tracks: list[Track] = []
        files = list(iter_audio_files(self.folder))
        total = len(files)
        for idx, path in enumerate(files, 1):
            track = extract_metadata(path)
            analysis = heuristic_analysis(track)
            track.bpm = analysis.bpm
            track.key = analysis.key
            track.energy = analysis.energy
            track.mood = analysis.mood
            tracks.append(track)
            self.signals.progress.emit(idx, total)
        self.signals.finished.emit(tracks)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        init_db()
        self.setWindowTitle("Lumbago Music AI")
        self.setMinimumSize(1200, 720)
        self.thread_pool = QtCore.QThreadPool.globalInstance()
        self._apply_app_icon()

        self._build_ui()
        self._load_tracks()
        self._load_settings()

    def _build_ui(self):
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        self.sidebar = self._build_sidebar()
        layout.addWidget(self.sidebar, 0)

        main_column = QtWidgets.QVBoxLayout()
        layout.addLayout(main_column, 1)

        toolbar = self._build_toolbar()
        main_column.addWidget(toolbar)

        content = QtWidgets.QHBoxLayout()
        main_column.addLayout(content, 1)

        self.table_model = TrackTableModel([])
        self.filter_proxy = TrackFilterProxy()
        self.filter_proxy.setSourceModel(self.table_model)

        self.table_view = QtWidgets.QTableView()
        self.table_view.setModel(self.filter_proxy)
        self.table_view.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table_view.doubleClicked.connect(self._play_selected)
        self.table_view.selectionModel().selectionChanged.connect(self._update_detail_panel)
        self.table_view.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(self._table_context_menu)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSortingEnabled(True)
        self.filter_proxy.setSortCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        header = self.table_view.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Interactive)
        header.setSectionsMovable(True)

        self.grid_view = QtWidgets.QListView()
        self.grid_view.setViewMode(QtWidgets.QListView.ViewMode.IconMode)
        self.grid_view.setIconSize(QtCore.QSize(96, 96))
        self.grid_view.setSpacing(8)
        self.grid_view.setResizeMode(QtWidgets.QListView.ResizeMode.Adjust)
        self.grid_view.setUniformItemSizes(True)
        self.grid_view.setModel(self.filter_proxy)
        self.grid_view.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.grid_view.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.grid_view.customContextMenuRequested.connect(self._grid_context_menu)
        self.grid_view.setDragEnabled(True)
        self.grid_view.setDragDropMode(QtWidgets.QAbstractItemView.DragDropMode.DragOnly)
        placeholder = self._build_placeholder_pixmap(96, 96)
        self.grid_view.setItemDelegate(TrackGridDelegate(placeholder))
        self.grid_view.selectionModel().selectionChanged.connect(self._update_detail_panel_from_grid)

        self.view_stack = QtWidgets.QStackedWidget()
        self.view_stack.addWidget(self.table_view)
        self.view_stack.addWidget(self.grid_view)

        header = self._build_header()
        main_column.addWidget(header)

        content.addWidget(self.view_stack, 3)

        self.detail_panel = self._build_detail_panel()
        content.addWidget(self.detail_panel, 1)

        player = self._build_player()
        main_column.addWidget(player)

        self.status = QtWidgets.QStatusBar()
        self.setStatusBar(self.status)
        self._apply_icons()
        self._setup_shortcuts()
        self._build_menu()

    def _apply_app_icon(self):
        icon_path = Path(__file__).resolve().parents[2] / "assets" / "icon.svg"
        if icon_path.exists():
            self.setWindowIcon(QtGui.QIcon(str(icon_path)))

    def _build_sidebar(self) -> QtWidgets.QFrame:
        frame = QtWidgets.QFrame()
        frame.setObjectName("Sidebar")
        layout = QtWidgets.QVBoxLayout(frame)
        layout.setContentsMargins(12, 12, 12, 12)
        title = QtWidgets.QLabel("Tools")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        self.btn_scan = AnimatedButton("Importuj / Skanuj")
        self.btn_scan.setObjectName("PrimaryAction")
        self.btn_scan.setToolTip("Importuj pliki audio z wybranego folderu")
        self.btn_scan.clicked.connect(self._open_import_wizard)
        layout.addWidget(self.btn_scan)

        self.btn_recognition = AnimatedButton("Rozpoznaj metadane (wsadowo)")
        self.btn_recognition.setToolTip("Rozpoznaj i uzupełnij metadane dla zaznaczonych utworów")
        self.btn_recognition.clicked.connect(self._run_recognition_queue)
        layout.addWidget(self.btn_recognition)

        self.btn_ai = AnimatedButton("Tagger AI (lokalny)")
        self.btn_ai.setToolTip("Analizuj i uzupełnij tagi dla zaznaczonych utworów")
        self.btn_ai.clicked.connect(self._run_ai_tagger)
        layout.addWidget(self.btn_ai)

        self.btn_local_meta = AnimatedButton("Metadane lokalne")
        self.btn_local_meta.setToolTip("UzupeĹ‚nij metadane z nazwy pliku i folderu")
        self.btn_local_meta.clicked.connect(self._apply_local_metadata_selected)
        layout.addWidget(self.btn_local_meta)

        self.btn_duplicates = AnimatedButton("Wyszukaj duplikaty")
        self.btn_duplicates.setToolTip("Znajdź duplikaty w bibliotece")
        self.btn_duplicates.clicked.connect(self._open_duplicates)
        layout.addWidget(self.btn_duplicates)

        self.btn_renamer = AnimatedButton("Zmiana nazw")
        self.btn_renamer.setToolTip("Zmień nazwy plików według wzorca")
        self.btn_renamer.clicked.connect(self._open_renamer)
        layout.addWidget(self.btn_renamer)

        self.btn_xml = AnimatedButton("Konwerter XML")
        self.btn_xml.setToolTip("Konwersja Rekordbox ↔ VirtualDJ")
        self.btn_xml.clicked.connect(self._open_xml_converter)
        layout.addWidget(self.btn_xml)

        self.btn_xml_import = AnimatedButton("Import XML")
        self.btn_xml_import.setToolTip("Importuj metadane z Rekordbox/VirtualDJ XML")
        self.btn_xml_import.clicked.connect(self._open_xml_import)
        layout.addWidget(self.btn_xml_import)

        self.btn_settings = AnimatedButton("Ustawienia / API")
        self.btn_settings.setToolTip("Ustaw klucze API i konfigurację")
        self.btn_settings.clicked.connect(self._open_settings)
        layout.addWidget(self.btn_settings)

        playlists_title = QtWidgets.QLabel("Playlisty")
        playlists_title.setObjectName("SectionTitle")
        layout.addWidget(playlists_title)
        self.playlist_list = QtWidgets.QListWidget()
        self.playlist_list.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.playlist_list.customContextMenuRequested.connect(self._playlist_context_menu)
        self.playlist_list.itemClicked.connect(self._select_playlist)
        self._load_playlists()
        self.playlist_list.setAcceptDrops(True)
        self.playlist_list.setDropIndicatorShown(True)
        self.playlist_list.setDefaultDropAction(QtCore.Qt.DropAction.CopyAction)
        self.playlist_list.installEventFilter(self)
        layout.addWidget(self.playlist_list, 1)

        layout.addStretch(0)
        return frame

    def _build_header(self) -> QtWidgets.QFrame:
        frame = QtWidgets.QFrame()
        row = QtWidgets.QHBoxLayout(frame)
        row.setContentsMargins(12, 12, 12, 12)
        row.addWidget(QtWidgets.QLabel("Przeglądarka biblioteki"))

        self.search_input = QtWidgets.QLineEdit()
        self.search_input.setPlaceholderText("Szukaj: tytuł / artysta / album")
        self.search_input.setToolTip("Wpisz frazę, aby filtrować listę")
        self.search_input.textChanged.connect(self._apply_filters)
        row.addWidget(self.search_input, 1)

        self.bpm_min = QtWidgets.QDoubleSpinBox()
        self.bpm_min.setPrefix("BPM min ")
        self.bpm_min.setToolTip("Minimalne BPM")
        self.bpm_min.setRange(0, 300)
        self.bpm_min.valueChanged.connect(self._apply_filters)
        row.addWidget(self.bpm_min)

        self.bpm_max = QtWidgets.QDoubleSpinBox()
        self.bpm_max.setPrefix("BPM max ")
        self.bpm_max.setToolTip("Maksymalne BPM")
        self.bpm_max.setRange(0, 300)
        self.bpm_max.valueChanged.connect(self._apply_filters)
        row.addWidget(self.bpm_max)

        self.key_input = QtWidgets.QLineEdit()
        self.key_input.setPlaceholderText("Tonacja")
        self.key_input.setToolTip("Filtrowanie po tonacji")
        self.key_input.textChanged.connect(self._apply_filters)
        row.addWidget(self.key_input)

        self.genre_input = QtWidgets.QLineEdit()
        self.genre_input.setPlaceholderText("Gatunek")
        self.genre_input.setToolTip("Filtrowanie po gatunku")
        self.genre_input.textChanged.connect(self._apply_filters)
        row.addWidget(self.genre_input)

        self.view_toggle = QtWidgets.QComboBox()
        self.view_toggle.addItems(["Lista", "Siatka"])
        self.view_toggle.setToolTip("Przełącz widok listy/siatki")
        self.view_toggle.currentIndexChanged.connect(self._on_view_toggle)
        row.addWidget(self.view_toggle)
        return frame

    def _build_detail_panel(self) -> QtWidgets.QFrame:
        frame = QtWidgets.QFrame()
        frame.setObjectName("DetailPanel")
        layout = QtWidgets.QVBoxLayout(frame)
        layout.setContentsMargins(12, 12, 12, 12)
        title = QtWidgets.QLabel("Szczegóły")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)
        self.detail_text = QtWidgets.QTextEdit()
        self.detail_text.setReadOnly(True)
        layout.addWidget(self.detail_text)

        self.cover_label = QtWidgets.QLabel()
        self.cover_label.setFixedSize(140, 140)
        self.cover_label.setScaledContents(True)
        layout.addWidget(self.cover_label)

        self.cover_btn = AnimatedButton("Zmień okładkę")
        self.cover_btn.setToolTip("Wybierz nową okładkę utworu")
        self.cover_btn.clicked.connect(self._change_cover)
        layout.addWidget(self.cover_btn)

        form = QtWidgets.QFormLayout()
        self.detail_title = QtWidgets.QLineEdit()
        self.detail_artist = QtWidgets.QLineEdit()
        self.detail_album = QtWidgets.QLineEdit()
        self.detail_genre = QtWidgets.QLineEdit()
        self.detail_bpm = QtWidgets.QLineEdit()
        self.detail_key = QtWidgets.QLineEdit()
        form.addRow("Tytuł", self.detail_title)
        form.addRow("Artysta", self.detail_artist)
        form.addRow("Album", self.detail_album)
        form.addRow("Gatunek", self.detail_genre)
        form.addRow("BPM", self.detail_bpm)
        form.addRow("Tonacja", self.detail_key)
        layout.addLayout(form)

        self.save_btn = AnimatedButton("Zapisz zmiany")
        self.save_btn.setToolTip("Zapisz zmiany w bazie")
        self.save_btn.clicked.connect(self._save_detail_changes)
        layout.addWidget(self.save_btn)

        self.save_file_btn = AnimatedButton("Zapisz do pliku")
        self.save_file_btn.setToolTip("Zapisz tagi bezpośrednio do pliku audio")
        self.save_file_btn.clicked.connect(self._save_tags_to_file)
        layout.addWidget(self.save_file_btn)

        self.reload_tags_btn = AnimatedButton("Odczytaj z pliku")
        self.reload_tags_btn.setToolTip("Wczytaj tagi z pliku audio")
        self.reload_tags_btn.clicked.connect(self._reload_tags_from_file)
        layout.addWidget(self.reload_tags_btn)

        self.clear_tags_btn = AnimatedButton("Wyczyść tagi")
        self.clear_tags_btn.setToolTip("Usuń tagi z pliku i bazy")
        self.clear_tags_btn.clicked.connect(self._clear_tags)
        layout.addWidget(self.clear_tags_btn)

        self.history_btn = AnimatedButton("Historia zmian")
        self.history_btn.setToolTip("Pokaż historię zmian tagów")
        self.history_btn.clicked.connect(self._open_change_history)
        layout.addWidget(self.history_btn)

        self.waveform_label = QtWidgets.QLabel()
        self.waveform_label.setFixedHeight(32)
        layout.addWidget(self.waveform_label)
        return frame

    def _build_player(self) -> QtWidgets.QFrame:
        frame = QtWidgets.QFrame()
        frame.setObjectName("PlayerDock")
        layout = QtWidgets.QVBoxLayout(frame)
        layout.setContentsMargins(12, 8, 12, 8)
        row = QtWidgets.QHBoxLayout()
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)

        self.play_btn = AnimatedButton("Odtwarzaj / Pauza")
        self.play_btn.setToolTip("Odtwarzaj lub wstrzymaj wybrany utwór")
        self.play_btn.clicked.connect(self._toggle_playback)
        row.addWidget(self.play_btn)

        self.stop_btn = AnimatedButton("Stop")
        self.stop_btn.setToolTip("Zatrzymaj odtwarzanie")
        self.stop_btn.clicked.connect(self.player.stop)
        row.addWidget(self.stop_btn)
        row.addStretch(1)
        layout.addLayout(row)

        timeline = QtWidgets.QHBoxLayout()
        self.position_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.position_slider.setRange(0, 1000)
        self.position_slider.sliderMoved.connect(self._seek_position)
        self.time_label = QtWidgets.QLabel("00:00 / 00:00")
        timeline.addWidget(self.position_slider, 1)
        timeline.addWidget(self.time_label)
        layout.addLayout(timeline)

        cues = QtWidgets.QHBoxLayout()
        self.cue_a_btn = AnimatedButton("Ustaw Cue A")
        self.cue_a_btn.setToolTip("Zapisz pozycję jako Cue A")
        self.cue_a_btn.clicked.connect(self._set_cue_a)
        self.cue_b_btn = AnimatedButton("Ustaw Cue B")
        self.cue_b_btn.setToolTip("Zapisz pozycję jako Cue B")
        self.cue_b_btn.clicked.connect(self._set_cue_b)
        self.jump_a_btn = AnimatedButton("Skok A")
        self.jump_a_btn.setToolTip("Skocz do Cue A")
        self.jump_a_btn.clicked.connect(self._jump_to_cue_a)
        self.jump_b_btn = AnimatedButton("Skok B")
        self.jump_b_btn.setToolTip("Skocz do Cue B")
        self.jump_b_btn.clicked.connect(self._jump_to_cue_b)
        self.loop_btn = AnimatedButton("Loop A-B")
        self.loop_btn.setToolTip("Włącz/wyłącz pętlę między Cue A i B")
        self.loop_btn.clicked.connect(self._toggle_loop)
        cues.addWidget(self.cue_a_btn)
        cues.addWidget(self.cue_b_btn)
        cues.addWidget(self.jump_a_btn)
        cues.addWidget(self.jump_b_btn)
        cues.addWidget(self.loop_btn)
        cues.addStretch(1)
        layout.addLayout(cues)

        self.player.positionChanged.connect(self._on_position_changed)
        self.player.durationChanged.connect(self._on_duration_changed)
        self._duration_ms = 0
        self._cue_a = None
        self._cue_b = None
        self._loop_enabled = False
        return frame

    def _build_placeholder_pixmap(self, width: int, height: int) -> QtGui.QPixmap:
        pixmap = QtGui.QPixmap(width, height)
        pixmap.fill(QtGui.QColor("#1a1f2e"))
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        painter.setPen(QtGui.QColor("#2b3a55"))
        painter.drawRect(1, 1, width - 2, height - 2)
        painter.setPen(QtGui.QColor("#39ff14"))
        painter.drawText(pixmap.rect(), QtCore.Qt.AlignmentFlag.AlignCenter, "NO\nART")
        painter.end()
        return pixmap

    def _load_tracks(self):
        tracks = list_tracks()
        self._all_tracks = tracks
        self._apply_playlist_view()

    def _load_playlists(self):
        self.playlist_list.clear()
        all_item = QtWidgets.QListWidgetItem("Wszystkie utwory")
        all_item.setData(QtCore.Qt.ItemDataRole.UserRole, None)
        self.playlist_list.addItem(all_item)
        for playlist in list_playlists_full():
            label = playlist.name
            if playlist.is_smart:
                label = f"{label} (smart)"
            item = QtWidgets.QListWidgetItem(label)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, playlist)
            self.playlist_list.addItem(item)

    def _apply_playlist_view(self):
        tracks = getattr(self, "_all_tracks", list_tracks())
        playlist = getattr(self, "_current_playlist", None)
        if not playlist:
            self.table_model.update_tracks(tracks)
            return
        if playlist.is_smart and playlist.rules:
            self.table_model.update_tracks(self._filter_tracks_by_rules(tracks, playlist.rules))
            return
        if playlist.playlist_id is None:
            self.table_model.update_tracks(tracks)
            return
        self.table_model.update_tracks(list_playlist_tracks(playlist.playlist_id))

    def _apply_filters(self):
        self.filter_proxy.search_text = self.search_input.text().strip().lower()
        self.filter_proxy.bpm_min = self.bpm_min.value() or None
        self.filter_proxy.bpm_max = self.bpm_max.value() or None
        self.filter_proxy.key = self.key_input.text().strip()
        self.filter_proxy.genre = self.genre_input.text().strip()
        self.filter_proxy.invalidateFilter()

    def _on_view_toggle(self, index: int):
        self.view_stack.setCurrentIndex(index)
        self._animate_view_change()

    def _animate_view_change(self):
        widget = self.view_stack.currentWidget()
        if widget is None:
            return
        effect = QtWidgets.QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
        animation = QtCore.QPropertyAnimation(effect, b"opacity", self)
        animation.setDuration(180)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.start(QtCore.QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    def _open_import_wizard(self):
        wizard = ImportWizard(self, on_complete=self._load_tracks)
        wizard.exec()

    def _update_scan_progress(self, current: int, total: int):
        self.status.showMessage(f"Scanning {current}/{total} files")

    def _scan_finished(self, tracks: list[Track]):
        upsert_tracks(tracks)
        self._load_tracks()
        self.status.showMessage(f"Scan complete: {len(tracks)} tracks")

    def _update_detail_panel(self):
        indexes = self.table_view.selectionModel().selectedRows()
        if not indexes:
            self.detail_text.clear()
            return
        source_index = self.filter_proxy.mapToSource(indexes[0])
        track = self.table_model.track_at(source_index.row())
        if not track:
            return
        detail = [
            f"Title: {track.title or ''}",
            f"Artist: {track.artist or ''}",
            f"Album: {track.album or ''}",
            f"Genre: {track.genre or ''}",
            f"BPM: {track.bpm or ''}",
            f"Key: {track.key or ''}",
            f"Duration: {track.duration or ''}",
            f"Path: {track.path}",
        ]
        self.detail_text.setPlainText("\n".join(detail))
        self._fill_detail_fields(track)

    def _update_detail_panel_from_grid(self):
        indexes = self.grid_view.selectionModel().selectedIndexes()
        if not indexes:
            self.detail_text.clear()
            return
        source_index = self.filter_proxy.mapToSource(indexes[0])
        track = self.table_model.track_at(source_index.row())
        if not track:
            return
        detail = [
            f"Title: {track.title or ''}",
            f"Artist: {track.artist or ''}",
            f"Album: {track.album or ''}",
            f"Genre: {track.genre or ''}",
            f"BPM: {track.bpm or ''}",
            f"Key: {track.key or ''}",
            f"Duration: {track.duration or ''}",
            f"Path: {track.path}",
        ]
        self.detail_text.setPlainText("\n".join(detail))
        self._fill_detail_fields(track)

    def _play_selected(self):
        indexes = self.table_view.selectionModel().selectedRows()
        if not indexes:
            return
        source_index = self.filter_proxy.mapToSource(indexes[0])
        track = self.table_model.track_at(source_index.row())
        if not track:
            return
        url = QtCore.QUrl.fromLocalFile(track.path)
        self.player.setSource(url)
        self.player.play()

    def _toggle_playback(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self._play_selected()

    def _seek_position(self, value: int):
        if self._duration_ms <= 0:
            return
        self.player.setPosition(int(self._duration_ms * (value / 1000)))

    def _on_duration_changed(self, duration: int):
        self._duration_ms = duration
        self._update_time_label(self.player.position(), duration)

    def _on_position_changed(self, position: int):
        if self._duration_ms > 0:
            self.position_slider.blockSignals(True)
            self.position_slider.setValue(int((position / self._duration_ms) * 1000))
            self.position_slider.blockSignals(False)
        self._update_time_label(position, self._duration_ms)
        if self._loop_enabled and self._cue_a is not None and self._cue_b is not None:
            if position >= self._cue_b:
                self.player.setPosition(self._cue_a)

    def _update_time_label(self, position: int, duration: int):
        def fmt(ms: int) -> str:
            seconds = max(0, ms // 1000)
            mins = seconds // 60
            secs = seconds % 60
            return f"{mins:02d}:{secs:02d}"
        self.time_label.setText(f"{fmt(position)} / {fmt(duration)}")

    def _set_cue_a(self):
        self._cue_a = self.player.position()
        self._show_message("Ustawiono Cue A.")

    def _set_cue_b(self):
        self._cue_b = self.player.position()
        self._show_message("Ustawiono Cue B.")

    def _jump_to_cue_a(self):
        if self._cue_a is not None:
            self.player.setPosition(self._cue_a)

    def _jump_to_cue_b(self):
        if self._cue_b is not None:
            self.player.setPosition(self._cue_b)

    def _toggle_loop(self):
        self._loop_enabled = not self._loop_enabled
        state = "włączona" if self._loop_enabled else "wyłączona"
        self.status.showMessage(f"Pętla {state}.")

    def _grid_context_menu(self, pos):
        index = self.grid_view.indexAt(pos)
        if not index.isValid():
            return
        menu = QtWidgets.QMenu(self)
        play_action = menu.addAction("Odtwórz")
        details_action = menu.addAction("Pokaż szczegóły")
        ai_action = menu.addAction("Analiza AI")
        local_meta_action = menu.addAction("Wczytaj metadane lokalne")
        action = menu.exec(self.grid_view.mapToGlobal(pos))
        if action == play_action:
            source_index = self.filter_proxy.mapToSource(index)
            track = self.table_model.track_at(source_index.row())
            if track:
                url = QtCore.QUrl.fromLocalFile(track.path)
                self.player.setSource(url)
                self.player.play()
        if action == details_action:
            self._update_detail_panel_from_grid()
        if action == ai_action:
            self._run_ai_tagger()
        if action == local_meta_action:
            self._apply_local_metadata_selected()

    def _select_all(self):
        if self.view_stack.currentIndex() == 0:
            self.table_view.selectAll()
        else:
            self.grid_view.selectAll()

    def _clear_selection(self):
        if self.view_stack.currentIndex() == 0:
            self.table_view.clearSelection()
        else:
            self.grid_view.clearSelection()

    def _bulk_edit(self):
        tracks = self._selected_tracks()
        if not tracks:
            self._show_message("Zaznacz utwory najpierw.")
            return
        dialog = BulkEditDialog(tracks, self)
        if dialog.exec():
            self._load_tracks()

    def _compare_tags(self):
        tracks = self._selected_tracks()
        if not tracks:
            self._show_message("Zaznacz utwory najpierw.")
            return
        dialog = TagCompareDialog(tracks, self)
        if dialog.exec():
            self._load_tracks()

    def _open_duplicates(self):
        tracks = self._selected_tracks()
        if not tracks:
            tracks = list_tracks()
        if not tracks:
            self._show_message("Brak utworów do analizy.")
            return
        dialog = DuplicatesDialog(tracks, self)
        if dialog.exec():
            self._load_tracks()

    def _open_renamer(self):
        tracks = self._selected_tracks()
        if not tracks:
            self._show_message("Zaznacz utwory najpierw.")
            return
        dialog = RenamerDialog(tracks, self)
        if dialog.exec():
            self._load_tracks()

    def _open_xml_converter(self):
        dialog = XmlConverterDialog(self)
        dialog.exec()

    def _open_xml_import(self):
        dialog = XmlImportDialog(self)
        if dialog.exec():
            self._load_tracks()

    def _table_context_menu(self, pos):
        index = self.table_view.indexAt(pos)
        if not index.isValid():
            return
        menu = QtWidgets.QMenu(self)
        play_action = menu.addAction("Odtwórz")
        details_action = menu.addAction("Pokaż szczegóły")
        reload_action = menu.addAction("Odczytaj tagi z pliku")
        save_action = menu.addAction("Zapisz tagi do pliku")
        clear_action = menu.addAction("Wyczyść tagi (plik + baza)")
        add_menu = menu.addMenu("Dodaj do playlisty")
        for name in list_playlists():
            add_menu.addAction(name)
        ai_action = menu.addAction("Analiza AI")
        local_meta_action = menu.addAction("Wczytaj metadane lokalne")
        action = menu.exec(self.table_view.viewport().mapToGlobal(pos))
        if action == play_action:
            self._play_selected()
        elif action == details_action:
            self._update_detail_panel()
        elif action == reload_action:
            source_index = self.filter_proxy.mapToSource(index)
            track = self.table_model.track_at(source_index.row())
            if track:
                refreshed = extract_metadata(Path(track.path))
                track.title = refreshed.title
                track.artist = refreshed.artist
                track.album = refreshed.album
                track.genre = refreshed.genre
                update_track(track)
                self._load_tracks()
        elif action == save_action:
            self._save_tags_to_file()
        elif action == clear_action:
            self._clear_tags()
        elif action in add_menu.actions():
            source_index = self.filter_proxy.mapToSource(index)
            track = self.table_model.track_at(source_index.row())
            if track:
                add_track_to_playlist(action.text(), track.path)
                self.status.showMessage(f"Added to playlist: {action.text()}")
        elif action == ai_action:
            self._run_ai_tagger()
        elif action == local_meta_action:
            self._apply_local_metadata_selected()

    def _fill_detail_fields(self, track: Track):
        self.detail_title.setText(track.title or "")
        self.detail_artist.setText(track.artist or "")
        self.detail_album.setText(track.album or "")
        self.detail_genre.setText(track.genre or "")
        self.detail_bpm.setText(str(track.bpm or ""))
        self.detail_key.setText(track.key or "")
        self._selected_track = track
        self._selected_snapshot = {
            "title": track.title,
            "artist": track.artist,
            "album": track.album,
            "genre": track.genre,
            "bpm": track.bpm,
            "key": track.key,
        }
        self._update_cover_preview(track.artwork_path)
        wave_path = generate_waveform(Path(track.path))
        pixmap = QtGui.QPixmap(str(wave_path))
        if not pixmap.isNull():
            self.waveform_label.setPixmap(pixmap)

    def _save_detail_changes(self):
        track = getattr(self, "_selected_track", None)
        if not track:
            return
        snapshot = getattr(self, "_selected_snapshot", {})
        track.title = self.detail_title.text().strip()
        track.artist = self.detail_artist.text().strip()
        track.album = self.detail_album.text().strip()
        track.genre = self.detail_genre.text().strip()
        track.key = self.detail_key.text().strip()
        try:
            track.bpm = float(self.detail_bpm.text()) if self.detail_bpm.text().strip() else None
        except ValueError:
            track.bpm = None
        self._log_changes(track, snapshot)
        update_track(track)
        self._load_tracks()
        self._show_message("Utwór zaktualizowany.")

    def _log_changes(self, track: Track, snapshot: dict):
        for field in ["title", "artist", "album", "genre", "bpm", "key"]:
            old_val = snapshot.get(field)
            new_val = getattr(track, field)
            if old_val != new_val:
                add_change_log(
                    track.path,
                    field,
                    str(old_val) if old_val is not None else None,
                    str(new_val) if new_val is not None else None,
                    "user",
                )

    def _save_tags_to_file(self):
        track = getattr(self, "_selected_track", None)
        if not track:
            return
        tags = {
            "title": self.detail_title.text().strip(),
            "artist": self.detail_artist.text().strip(),
            "album": self.detail_album.text().strip(),
            "genre": self.detail_genre.text().strip(),
            "bpm": self.detail_bpm.text().strip(),
            "key": self.detail_key.text().strip(),
        }
        try:
            write_tags(Path(track.path), tags)
            refreshed = extract_metadata(Path(track.path))
            track.title = refreshed.title
            track.artist = refreshed.artist
            track.album = refreshed.album
            track.genre = refreshed.genre
            update_track(track)
            self._load_tracks()
            self._show_message("Tagi zapisane do pliku.")
        except Exception as exc:
            self._show_message(f"Zapis nieudany: {exc}")

    def _reload_tags_from_file(self):
        track = getattr(self, "_selected_track", None)
        if not track:
            return
        try:
            refreshed = extract_metadata(Path(track.path))
            track.title = refreshed.title
            track.artist = refreshed.artist
            track.album = refreshed.album
            track.genre = refreshed.genre
            update_track(track)
            self._load_tracks()
            self._show_message("Tagi odczytane z pliku.")
        except Exception as exc:
            self._show_message(f"Odczyt nieudany: {exc}")

    def _clear_tags(self):
        track = getattr(self, "_selected_track", None)
        if not track:
            return
        try:
            clear_tags(Path(track.path))
            track.title = None
            track.artist = None
            track.album = None
            track.genre = None
            track.bpm = None
            track.key = None
            update_track(track)
            self._load_tracks()
            self._show_message("Tagi wyczyszczone.")
        except Exception as exc:
            self._show_message(f"Czyszczenie nieudane: {exc}")

    def _change_cover(self):
        track = getattr(self, "_selected_track", None)
        if not track:
            return
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select cover image", "", "Images (*.png *.jpg *.jpeg *.webp)"
        )
        if not file_path:
            return
        dest = cache_dir() / f"cover_{Path(file_path).stem}.png"
        try:
            shutil.copy2(file_path, dest)
            track.artwork_path = str(dest)
            update_track(track)
            self._update_cover_preview(track.artwork_path)
        except Exception as exc:
            self._show_message(f"Nie udało się zmienić okładki: {exc}")

    def _open_change_history(self):
        track = getattr(self, "_selected_track", None)
        if not track:
            return
        dialog = ChangeHistoryDialog(track.path, self)
        dialog.exec()

    def _update_cover_preview(self, path: str | None):
        if path and Path(path).exists():
            pixmap = QtGui.QPixmap(path)
        else:
            pixmap = self._build_placeholder_pixmap(140, 140)
        self.cover_label.setPixmap(pixmap)

    def eventFilter(self, source, event):
        if source is self.playlist_list and event.type() == QtCore.QEvent.Type.Drop:
            item = self.playlist_list.itemAt(event.position().toPoint())
            data = item.data(QtCore.Qt.ItemDataRole.UserRole) if item else None
            if item and data and hasattr(self, "_selected_track") and self._selected_track:
                add_track_to_playlist(data.name, self._selected_track.path)
                self.status.showMessage(f"Dodano do playlisty: {data.name}")
            return True
        return super().eventFilter(source, event)

    def _run_ai_tagger(self):
        tracks = self._selected_tracks()
        if not tracks:
            self._show_message("Zaznacz co najmniej jeden utwór.")
            return
        dialog = AiTaggerDialog(tracks, self)
        if dialog.exec():
            self._load_tracks()

    def _run_auto_tagger(self):
        tracks = self._selected_tracks()
        if not tracks:
            self._show_message("Zaznacz co najmniej jeden utwór.")
            return
        dialog = AiTaggerDialog(tracks, self, auto_fetch=True, auto_method="acoustid")
        if dialog.exec():
            self._load_tracks()

    def _apply_local_metadata_selected(self):
        tracks = self._selected_tracks()
        if not tracks:
            self._show_message("Zaznacz co najmniej jeden utwór.")
            return
        for track in tracks:
            apply_local_metadata(track, Path(track.path))
        update_tracks(tracks)
        self._load_tracks()
        self._show_message("Metadane lokalne zostały uzupełnione.")

    def _run_recognition_queue(self):
        tracks = self._selected_tracks()
        if not tracks:
            self._show_message("Zaznacz co najmniej jeden utwór.")
            return
        settings = load_settings()
        if not settings.acoustid_api_key:
            self._show_message("Brak klucza AcoustID. Uzupełnij go w Ustawieniach.")
            return
        self._recognition_worker = RecognitionBatchWorker(
            tracks,
            settings.acoustid_api_key,
            settings.musicbrainz_app_name,
        )
        progress = QtWidgets.QProgressDialog(
            "Rozpoznawanie metadanych...", "Anuluj", 0, len(tracks), self
        )
        progress.setWindowTitle("Kolejka rozpoznawania")
        progress.setMinimumDuration(0)
        progress.setValue(0)

        def on_progress(current: int, total: int):
            progress.setMaximum(total)
            progress.setValue(current)
            self.status.showMessage(f"Rozpoznano {current}/{total} utworów")
            if progress.wasCanceled():
                self._recognition_worker.stop()

        def on_finished(processed: int, errors: int):
            progress.close()
            self._load_tracks()
            self.status.showMessage(f"Rozpoznawanie zakończone. Błędy: {errors}")

        self._recognition_worker.signals.progress.connect(on_progress)
        self._recognition_worker.signals.finished.connect(on_finished)
        self.thread_pool.start(self._recognition_worker)

    def _selected_tracks(self) -> list[Track]:
        if self.view_stack.currentIndex() == 0:
            indexes = self.table_view.selectionModel().selectedRows()
            return [
                self.table_model.track_at(self.filter_proxy.mapToSource(index).row())
                for index in indexes
                if self.table_model.track_at(self.filter_proxy.mapToSource(index).row())
            ]
        indexes = self.grid_view.selectionModel().selectedIndexes()
        return [
            self.table_model.track_at(self.filter_proxy.mapToSource(index).row())
            for index in indexes
            if self.table_model.track_at(self.filter_proxy.mapToSource(index).row())
        ]

    def _open_settings(self):
        dialog = SettingsDialog(self)
        if dialog.exec():
            self._load_settings()

    def _load_settings(self):
        self.settings = load_settings()
        provider = self.settings.cloud_ai_provider or "local"
        self.status.showMessage(f"Settings loaded. Cloud AI: {provider}")

    def _show_placeholder(self):
        self._show_message("Ta funkcja będzie dostępna wkrótce.")

    def _show_message(self, text: str):
        QtWidgets.QMessageBox.information(self, "Lumbago Music AI", text)

    def _setup_shortcuts(self):
        QtGui.QShortcut(QtGui.QKeySequence("Space"), self, activated=self._toggle_playback)
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+F"), self, activated=self.search_input.setFocus)
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+I"), self, activated=self._open_import_wizard)
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+D"), self, activated=self._open_duplicates)
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+R"), self, activated=self._open_renamer)
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+E"), self, activated=self._open_xml_converter)
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+T"), self, activated=self._run_auto_tagger)

    def _apply_icons(self):
        style = self.style()
        self.btn_scan.setIcon(style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DialogOpenButton))
        self.btn_recognition.setIcon(style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_BrowserReload))
        self.btn_ai.setIcon(style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_ComputerIcon))
        self.btn_local_meta.setIcon(style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DialogResetButton))
        self.btn_duplicates.setIcon(style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DirIcon))
        self.btn_renamer.setIcon(style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_FileIcon))
        self.btn_xml.setIcon(style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_FileDialogDetailedView))
        self.btn_xml_import.setIcon(style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_FileDialogNewFolder))
        self.btn_settings.setIcon(style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_FileDialogInfoView))
        self.settings_btn.setIcon(style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_FileDialogContentsView))
        self.auto_tag_btn.setIcon(style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaPlay))
        self.play_btn.setIcon(style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaPlay))
        self.stop_btn.setIcon(style.standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaStop))

    def _build_menu(self):
        menu = self.menuBar()
        tools = menu.addMenu("Narzędzia")
        tools.addAction("Importuj / Skanuj", self._open_import_wizard)
        tools.addAction("Import XML", self._open_xml_import)
        tools.addAction("AutoTagowanie", self._run_auto_tagger)
        tools.addAction("Metadane lokalne", self._apply_local_metadata_selected)
        tools.addAction("Duplikaty", self._open_duplicates)
        tools.addAction("Renamer", self._open_renamer)
        tools.addAction("Konwerter XML", self._open_xml_converter)
        tools.addAction("Ustawienia", self._open_settings)

        help_menu = menu.addMenu("Pomoc")
        help_menu.addAction("Instrukcja użytkownika", self._open_user_guide)

    def _open_user_guide(self):
        guide_path = Path(__file__).resolve().parents[2] / "docs" / "user_guide.md"
        if guide_path.exists():
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(guide_path)))
        else:
            self._show_message("Brak pliku instrukcji użytkownika.")

    def _playlist_context_menu(self, pos):
        item = self.playlist_list.itemAt(pos)
        menu = QtWidgets.QMenu(self)
        add_action = menu.addAction("Nowa playlista")
        edit_action = menu.addAction("Edytuj playlistę")
        delete_action = menu.addAction("Usuń playlistę")
        order_action = menu.addAction("Kolejność utworów")
        action = menu.exec(self.playlist_list.mapToGlobal(pos))
        if action == add_action:
            self._open_playlist_editor()
        elif action == edit_action and item:
            playlist = item.data(QtCore.Qt.ItemDataRole.UserRole)
            if playlist:
                self._open_playlist_editor(playlist)
        elif action == delete_action and item:
            playlist = item.data(QtCore.Qt.ItemDataRole.UserRole)
            if playlist and playlist.playlist_id:
                delete_playlist(playlist.playlist_id)
                self._load_playlists()
                self._load_tracks()
        elif action == order_action and item:
            playlist = item.data(QtCore.Qt.ItemDataRole.UserRole)
            if playlist and playlist.playlist_id and not playlist.is_smart:
                tracks = list_playlist_tracks(playlist.playlist_id)
                dialog = PlaylistOrderDialog(tracks, self)
                if dialog.exec():
                    set_playlist_track_order(playlist.playlist_id, dialog.ordered_paths())
                    self._apply_playlist_view()

    def _open_playlist_editor(self, playlist=None):
        dialog = PlaylistEditorDialog(playlist, self)
        if dialog.exec():
            payload = dialog.get_payload()
            if playlist and playlist.playlist_id:
                update_playlist(
                    playlist.playlist_id,
                    payload["name"],
                    payload["description"],
                    payload["is_smart"],
                    payload["rules"],
                )
            else:
                create_playlist(
                    payload["name"],
                    payload["description"],
                    payload["is_smart"],
                    payload["rules"],
                )
            self._load_playlists()

    def _select_playlist(self, item: QtWidgets.QListWidgetItem):
        playlist = item.data(QtCore.Qt.ItemDataRole.UserRole)
        self._current_playlist = playlist
        self._apply_playlist_view()

    def _filter_tracks_by_rules(self, tracks: list[Track], rules_json: str) -> list[Track]:
        try:
            rules = json.loads(rules_json)
        except Exception:
            rules = {}
        search = (rules.get("search") or "").lower()
        genre = (rules.get("genre") or "").lower()
        key = (rules.get("key") or "").lower()
        bpm_min = rules.get("bpm_min")
        bpm_max = rules.get("bpm_max")
        filtered: list[Track] = []
        for track in tracks:
            blob = f"{track.title or ''} {track.artist or ''} {track.album or ''}".lower()
            if search and search not in blob:
                continue
            if genre and genre not in (track.genre or "").lower():
                continue
            if key and key not in (track.key or "").lower():
                continue
            if bpm_min is not None and track.bpm is not None and track.bpm < bpm_min:
                continue
            if bpm_max is not None and track.bpm is not None and track.bpm > bpm_max:
                continue
            filtered.append(track)
        return filtered
    def _build_toolbar(self) -> QtWidgets.QFrame:
        frame = QtWidgets.QFrame()
        row = QtWidgets.QHBoxLayout(frame)
        row.setContentsMargins(12, 8, 12, 8)
        self.title_label = QtWidgets.QLabel("Lumbago Music AI")
        font = self.title_label.font()
        font.setPointSize(14)
        font.setBold(True)
        self.title_label.setFont(font)
        row.addWidget(self.title_label)
        row.addStretch(1)

        self.settings_btn = AnimatedButton("Ustawienia")
        self.settings_btn.setToolTip("Konfiguracja aplikacji i kluczy API")
        self.settings_btn.clicked.connect(self._open_settings)
        row.addWidget(self.settings_btn)

        self.select_all_btn = AnimatedButton("Zaznacz wszystko")
        self.select_all_btn.setToolTip("Zaznacz wszystkie utwory na liście/siatce")
        self.select_all_btn.clicked.connect(self._select_all)
        row.addWidget(self.select_all_btn)

        self.clear_sel_btn = AnimatedButton("Wyczyść zaznaczenie")
        self.clear_sel_btn.setToolTip("Odznacz wszystkie utwory")
        self.clear_sel_btn.clicked.connect(self._clear_selection)
        row.addWidget(self.clear_sel_btn)

        self.bulk_edit_btn = AnimatedButton("Edycja zbiorcza")
        self.bulk_edit_btn.setToolTip("Masowa edycja tagów dla wielu utworów")
        self.bulk_edit_btn.clicked.connect(self._bulk_edit)
        row.addWidget(self.bulk_edit_btn)

        self.compare_btn = AnimatedButton("Porównaj tagi")
        self.compare_btn.setToolTip("Porównaj stare i nowe tagi dla utworów")
        self.compare_btn.clicked.connect(self._compare_tags)
        row.addWidget(self.compare_btn)

        self.auto_tag_btn = AnimatedButton("AutoTagowanie")
        self.auto_tag_btn.setToolTip("Uruchom AI + auto‑pobieranie braków")
        self.auto_tag_btn.clicked.connect(self._run_auto_tagger)
        row.addWidget(self.auto_tag_btn)
        return frame
