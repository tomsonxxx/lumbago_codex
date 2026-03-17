from __future__ import annotations

from pathlib import Path
import json
from datetime import datetime
import os

from PyQt6 import QtCore, QtGui, QtWidgets

from lumbago_app.core.audio import (
    apply_local_metadata,
    clear_tags,
    extract_metadata,
    iter_audio_files,
    read_tags,
    write_tags,
)
import shutil
from lumbago_app.core.analysis_cache import save_analysis_cache
from lumbago_app.core.backup import perform_backup
from lumbago_app.core.config import cache_dir, load_settings
from lumbago_app.core.models import Track
from lumbago_app.core.services import heuristic_analysis
from lumbago_app.core.waveform import generate_waveform
from lumbago_app.services.beatgrid import auto_cue_points, compute_beatgrid
from lumbago_app.services.key_detection import detect_key
from lumbago_app.services.loudness import analyze_loudness, normalize_loudness
from lumbago_app.services.xml_converter import XmlTrack, export_virtualdj_xml
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
    reset_library,
    search_tracks_fts,
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
from lumbago_app.ui.recognition_results_dialog import RecognitionResultsDialog
from lumbago_app.ui.renamer_dialog import RenamerDialog
from lumbago_app.ui.settings_dialog import SettingsDialog
from lumbago_app.ui.tag_compare_dialog import TagCompareDialog
from lumbago_app.ui.widgets import AnimatedButton
from lumbago_app.ui.xml_converter_dialog import XmlConverterDialog
from lumbago_app.ui.xml_import_dialog import XmlImportDialog


def _debug_log(message: str) -> None:
    try:
        target = Path.cwd() / ".lumbago_data" / "startup.log"
        target.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with target.open("a", encoding="utf-8", errors="ignore") as handle:
            handle.write(f"{timestamp} {message}\n")
    except Exception:
        pass


def _normalized_path(output_dir: Path, source: Path) -> Path:
    stem = f"{source.stem}_lufs"
    candidate = output_dir / f"{stem}{source.suffix}"
    if not candidate.exists():
        return candidate
    idx = 2
    while True:
        candidate = output_dir / f"{stem}_{idx}{source.suffix}"
        if not candidate.exists():
            return candidate
        idx += 1


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


class LoudnessWorkerSignals(QtCore.QObject):
    progress = QtCore.pyqtSignal(int, int)
    finished = QtCore.pyqtSignal(list)


class LoudnessWorker(QtCore.QRunnable):
    def __init__(self, tracks: list[Track]):
        super().__init__()
        self.tracks = tracks
        self.signals = LoudnessWorkerSignals()

    def run(self):
        updated: list[Track] = []
        total = len(self.tracks)
        for idx, track in enumerate(self.tracks, 1):
            try:
                lufs = analyze_loudness(Path(track.path))
                track.loudness_lufs = lufs
            except Exception:
                lufs = None
            cue_in, cue_out = auto_cue_points(track.duration)
            track.cue_in_ms = cue_in
            track.cue_out_ms = cue_out
            beatgrid = compute_beatgrid(track.duration, track.bpm)
            save_analysis_cache(
                Path(track.path),
                {
                    "loudness_lufs": lufs,
                    "cue_in_ms": cue_in,
                    "cue_out_ms": cue_out,
                    "beatgrid": beatgrid,
                },
            )
            updated.append(track)
            self.signals.progress.emit(idx, total)
        self.signals.finished.emit(updated)


class KeyDetectionWorkerSignals(QtCore.QObject):
    progress = QtCore.pyqtSignal(int, int)
    finished = QtCore.pyqtSignal(list)


class KeyDetectionWorker(QtCore.QRunnable):
    def __init__(self, tracks: list[Track], force: bool = False):
        super().__init__()
        self.tracks = tracks
        self.force = force
        self.signals = KeyDetectionWorkerSignals()

    def run(self):
        updated: list[Track] = []
        total = len(self.tracks)
        for idx, track in enumerate(self.tracks, 1):
            if track.key and not self.force:
                updated.append(track)
                self.signals.progress.emit(idx, total)
                continue
            detected = detect_key(Path(track.path))
            if detected:
                track.key = detected
            updated.append(track)
            self.signals.progress.emit(idx, total)
        self.signals.finished.emit(updated)


class NormalizeWorkerSignals(QtCore.QObject):
    progress = QtCore.pyqtSignal(int, int)
    finished = QtCore.pyqtSignal(int, int)


class NormalizeWorker(QtCore.QRunnable):
    def __init__(self, tracks: list[Track], output_dir: Path, target_lufs: float):
        super().__init__()
        self.tracks = tracks
        self.output_dir = output_dir
        self.target_lufs = target_lufs
        self.signals = NormalizeWorkerSignals()

    def run(self):
        created = 0
        errors = 0
        total = len(self.tracks)
        for idx, track in enumerate(self.tracks, 1):
            try:
                source = Path(track.path)
                dest = _normalized_path(self.output_dir, source)
                ok = normalize_loudness(source, dest, target_lufs=self.target_lufs)
                if ok:
                    tags = read_tags(source)
                    if tags:
                        write_tags(dest, tags)
                    new_track = extract_metadata(dest)
                    upsert_tracks([new_track])
                    created += 1
                else:
                    errors += 1
            except Exception:
                errors += 1
            self.signals.progress.emit(idx, total)
        self.signals.finished.emit(created, errors)


class _SimpleWorker(QtCore.QRunnable):
    """Generyczny worker uruchamiający funkcję w wątku i wywołujący callback w głównym wątku."""
    def __init__(self, fn, callback):
        super().__init__()
        self._fn = fn
        self._callback = callback
        self.signals = _SimpleWorkerSignals()
        self.signals.result.connect(callback)

    def run(self):
        try:
            result = self._fn()
        except Exception:
            result = None
        self.signals.result.emit(result)


class _SimpleWorkerSignals(QtCore.QObject):
    result = QtCore.pyqtSignal(object)


# Column presets — indices based on TrackTableModel.headers order
# Tytuł=0, Artysta=1, Album=2, Rok=3, Gatunek=4, BPM=5, Tonacja=6, Nastrój=7, Energia=8, Czas=10, Format=11, Ocena=16, Ścieżka=25
_DJ_COLUMNS = [0, 1, 4, 5, 6, 7, 8, 10, 16, 25]          # DJ View
_META_COLUMNS = [0, 1, 2, 3, 4, 5, 6, 10, 11, 12, 25]    # Metadata View


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        _debug_log("MainWindow: start init")
        init_db()
        _debug_log("MainWindow: init_db ok")
        perform_backup()
        self.setWindowTitle("Lumbago Music AI")
        self.setMinimumSize(1200, 720)
        self.thread_pool = QtCore.QThreadPool.globalInstance()
        self._apply_app_icon()

        self._build_ui()
        _debug_log("MainWindow: build_ui ok")
        self._load_tracks()
        _debug_log("MainWindow: load_tracks ok")
        self._load_settings()
        _debug_log("MainWindow: load_settings ok")
        self.setAcceptDrops(True)

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
        header.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        header.customContextMenuRequested.connect(self._show_table_column_menu)
        # Inline gwiazdki dla kolumny Ocena (indeks 16)
        from lumbago_app.ui.models import StarRatingDelegate
        self._star_delegate = StarRatingDelegate()
        self.table_view.setItemDelegateForColumn(16, self._star_delegate)

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
        self.btn_scan.enable_pulse()
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
        self.btn_local_meta.setToolTip("Uzupełnij metadane z nazwy pliku i folderu")
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
        self.playlist_list = QtWidgets.QTreeWidget()
        self.playlist_list.setHeaderHidden(True)
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
        frame.setObjectName("HeaderBar")
        row = QtWidgets.QHBoxLayout(frame)
        row.setContentsMargins(12, 12, 12, 12)
        header_label = QtWidgets.QLabel("Przeglądarka biblioteki")
        header_label.setObjectName("SectionTitle")
        row.addWidget(header_label)

        self.search_input = QtWidgets.QLineEdit()
        self.search_input.setObjectName("SearchInput")
        self.search_input.setPlaceholderText("Szukaj: tytuł / artysta / album")
        self.search_input.setToolTip("Wpisz frazę, aby filtrować listę")
        self.search_input.textChanged.connect(self._apply_filters)
        row.addWidget(self.search_input, 1)

        self.bpm_min = QtWidgets.QDoubleSpinBox()
        self.bpm_min.setObjectName("FilterSpin")
        self.bpm_min.setPrefix("BPM min ")
        self.bpm_min.setToolTip("Minimalne BPM")
        self.bpm_min.setRange(0, 300)
        self.bpm_min.valueChanged.connect(self._apply_filters)
        row.addWidget(self.bpm_min)

        self.bpm_max = QtWidgets.QDoubleSpinBox()
        self.bpm_max.setObjectName("FilterSpin")
        self.bpm_max.setPrefix("BPM max ")
        self.bpm_max.setToolTip("Maksymalne BPM")
        self.bpm_max.setRange(0, 300)
        self.bpm_max.valueChanged.connect(self._apply_filters)
        row.addWidget(self.bpm_max)

        self.key_input = QtWidgets.QLineEdit()
        self.key_input.setObjectName("FilterInput")
        self.key_input.setPlaceholderText("Tonacja")
        self.key_input.setToolTip("Filtrowanie po tonacji")
        self.key_input.textChanged.connect(self._apply_filters)
        row.addWidget(self.key_input)

        self.genre_input = QtWidgets.QLineEdit()
        self.genre_input.setObjectName("FilterInput")
        self.genre_input.setPlaceholderText("Gatunek")
        self.genre_input.setToolTip("Filtrowanie po gatunku")
        self.genre_input.textChanged.connect(self._apply_filters)
        row.addWidget(self.genre_input)

        self.view_toggle = QtWidgets.QComboBox()
        self.view_toggle.setObjectName("ViewToggle")
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
        self.detail_year = QtWidgets.QLineEdit()
        self.detail_genre = QtWidgets.QLineEdit()
        self.detail_bpm = QtWidgets.QLineEdit()
        self.detail_key = QtWidgets.QLineEdit()
        self.detail_loudness = QtWidgets.QLineEdit()
        self.detail_loudness.setReadOnly(True)
        self.detail_loudness.setToolTip("Zintegrowana głośność (LUFS)")
        form.addRow("Tytuł", self.detail_title)
        form.addRow("Artysta", self.detail_artist)
        form.addRow("Album", self.detail_album)
        form.addRow("Rok", self.detail_year)
        form.addRow("Gatunek", self.detail_genre)
        # BPM z Tap
        bpm_row = QtWidgets.QHBoxLayout()
        bpm_row.addWidget(self.detail_bpm)
        self._tap_btn = QtWidgets.QPushButton("Tap")
        self._tap_btn.setFixedWidth(40)
        self._tap_btn.setToolTip("Kliknij w rytm aby zmierzyć BPM")
        self._tap_btn.clicked.connect(self._tap_bpm)
        self._tap_times: list[float] = []
        bpm_row.addWidget(self._tap_btn)
        form.addRow("BPM", bpm_row)
        # Tonacja z auto-detect
        key_row = QtWidgets.QHBoxLayout()
        key_row.addWidget(self.detail_key)
        self._detect_key_btn = QtWidgets.QPushButton("Wykryj")
        self._detect_key_btn.setFixedWidth(52)
        self._detect_key_btn.setToolTip("Wykryj tonację przez librosa (chroma_cqt)")
        self._detect_key_btn.clicked.connect(self._detect_key_detail)
        key_row.addWidget(self._detect_key_btn)
        form.addRow("Tonacja", key_row)
        form.addRow("LUFS", self.detail_loudness)
        layout.addLayout(form)

        # Auto-save z debounce 1.5s
        self._autosave_timer = QtCore.QTimer(self)
        self._autosave_timer.setSingleShot(True)
        self._autosave_timer.setInterval(1500)
        self._autosave_timer.timeout.connect(self._save_detail_changes)
        for field in (self.detail_title, self.detail_artist, self.detail_album,
                      self.detail_year, self.detail_genre, self.detail_bpm, self.detail_key):
            field.textChanged.connect(self._autosave_timer.start)

        self.tag_quality_label = QtWidgets.QLabel("")
        self.tag_quality_label.setObjectName("DialogHint")
        self.tag_quality_label.setToolTip("Procent wypełnionych pól metadanych")
        layout.addWidget(self.tag_quality_label)

        self.save_btn = AnimatedButton("Zapisz zmiany")
        self.save_btn.setToolTip("Zapisz zmiany w bazie (auto-save działa po 1.5s)")
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

        related_label = QtWidgets.QLabel("Inne tracki artysty:")
        related_label.setObjectName("DialogHint")
        layout.addWidget(related_label)
        self.related_list = QtWidgets.QListWidget()
        self.related_list.setFixedHeight(90)
        self.related_list.setToolTip("Inne tracki tego artysty w bibliotece. Kliknij dwukrotnie aby wybrać.")
        self.related_list.itemDoubleClicked.connect(self._jump_to_related)
        layout.addWidget(self.related_list)

        return frame

    def _build_player(self) -> QtWidgets.QFrame:
        frame = QtWidgets.QFrame()
        frame.setObjectName("PlayerDock")
        layout = QtWidgets.QVBoxLayout(frame)
        layout.setContentsMargins(12, 8, 12, 8)
        row = QtWidgets.QHBoxLayout()
        self.player = None
        self.audio_output = None
        if os.getenv("LUMBAGO_DISABLE_MULTIMEDIA", "1") == "1":
            _debug_log("Player init skipped (LUMBAGO_DISABLE_MULTIMEDIA=1)")
        else:
            try:
                from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer

                self.player = QMediaPlayer()
                self.audio_output = QAudioOutput()
                self.player.setAudioOutput(self.audio_output)
            except Exception as exc:
                _debug_log(f"Player init failed: {exc}")

        self.play_btn = AnimatedButton("Odtwarzaj / Pauza")
        self.play_btn.setToolTip("Odtwarzaj lub wstrzymaj wybrany utwór")
        self.play_btn.clicked.connect(self._toggle_playback)
        row.addWidget(self.play_btn)

        self.stop_btn = AnimatedButton("Stop")
        self.stop_btn.setToolTip("Zatrzymaj odtwarzanie")
        if self.player:
            self.stop_btn.clicked.connect(self.player.stop)
        row.addWidget(self.stop_btn)
        row.addStretch(1)
        layout.addLayout(row)

        timeline = QtWidgets.QHBoxLayout()
        self.position_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.position_slider.setRange(0, 1000)
        self.position_slider.sliderMoved.connect(self._seek_position)
        self.time_label = QtWidgets.QLabel("00:00 / 00:00")
        self.bpm_sync_label = QtWidgets.QLabel("")
        self.bpm_sync_label.setObjectName("DialogHint")
        self.bpm_sync_label.setToolTip("BPM bieżącego i poprzedniego tracku")
        timeline.addWidget(self.position_slider, 1)
        timeline.addWidget(self.time_label)
        timeline.addWidget(self.bpm_sync_label)
        layout.addLayout(timeline)
        self._last_played_bpm: float | None = None
        self._current_played_bpm: float | None = None

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
        self.auto_cue_btn = AnimatedButton("Auto-cue")
        self.auto_cue_btn.setToolTip("Ustaw automatyczne Cue (intro/outro)")
        self.auto_cue_btn.clicked.connect(self._auto_cue_selected)
        cues.addWidget(self.cue_a_btn)
        cues.addWidget(self.cue_b_btn)
        cues.addWidget(self.jump_a_btn)
        cues.addWidget(self.jump_b_btn)
        cues.addWidget(self.loop_btn)
        cues.addWidget(self.auto_cue_btn)
        cues.addStretch(1)
        layout.addLayout(cues)

        # Hot cues 1-8
        _HC_COLORS = ["#ff8800", "#0088ff", "#00cc44", "#ff2244",
                      "#aa44ff", "#00dddd", "#ff44aa", "#dddd00"]
        hot_row = QtWidgets.QHBoxLayout()
        hot_row.addWidget(QtWidgets.QLabel("Hot cues:"))
        self._hot_cue_btns: list[QtWidgets.QPushButton] = []
        self._hot_cues: dict[int, int | None] = {i: None for i in range(8)}
        for i in range(8):
            btn = QtWidgets.QPushButton(str(i + 1))
            btn.setFixedSize(32, 26)
            btn.setToolTip(f"Hot Cue {i + 1} — kliknij aby ustawić/skoczyć, PPM aby wyczyścić")
            btn.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
            btn.customContextMenuRequested.connect(lambda _, idx=i: self._clear_hot_cue(idx))
            btn.clicked.connect(lambda _, idx=i: self._toggle_hot_cue(idx))
            self._update_hot_cue_btn_style(btn, i, _HC_COLORS[i], active=False)
            hot_row.addWidget(btn)
            self._hot_cue_btns.append(btn)
        hot_row.addStretch(1)
        layout.addLayout(hot_row)

        if self.player:
            self.player.positionChanged.connect(self._on_position_changed)
            self.player.durationChanged.connect(self._on_duration_changed)
        self._duration_ms = 0
        self._cue_a = None
        self._cue_b = None
        self._loop_enabled = False
        self._hot_cue_colors = _HC_COLORS
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
        all_count = len(getattr(self, "_all_tracks", list_tracks()))
        all_item = QtWidgets.QTreeWidgetItem(self.playlist_list, [f"Wszystkie utwory ({all_count})"])
        all_item.setData(0, QtCore.Qt.ItemDataRole.UserRole, None)
        # Grupuj playlisty wg konwencji "Folder/Nazwa"
        folders: dict[str, QtWidgets.QTreeWidgetItem] = {}
        for playlist in list_playlists_full():
            raw_name = playlist.name
            suffix = ""
            if playlist.is_smart:
                suffix += " (smart)"
            if playlist.playlist_id:
                count = len(list_playlist_tracks(playlist.playlist_id))
                suffix += f" ({count})"
            if "/" in raw_name:
                folder_name, short_name = raw_name.split("/", 1)
                if folder_name not in folders:
                    folder_item = QtWidgets.QTreeWidgetItem(self.playlist_list, [f"📁 {folder_name}"])
                    folder_item.setExpanded(True)
                    folders[folder_name] = folder_item
                parent = folders[folder_name]
                item = QtWidgets.QTreeWidgetItem(parent, [f"  {short_name}{suffix}"])
            else:
                item = QtWidgets.QTreeWidgetItem(self.playlist_list, [f"{raw_name}{suffix}"])
            item.setData(0, QtCore.Qt.ItemDataRole.UserRole, playlist)

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
        query = self.search_input.text().strip()
        if len(query) >= 3:
            fts_results = search_tracks_fts(query)
            if fts_results:
                self.table_model.update_tracks(fts_results)
                self.filter_proxy.search_text = ""
                self.filter_proxy.bpm_min = self.bpm_min.value() or None
                self.filter_proxy.bpm_max = self.bpm_max.value() or None
                self.filter_proxy.key = self.key_input.text().strip()
                self.filter_proxy.genre = self.genre_input.text().strip()
                self.filter_proxy.invalidateFilter()
                return
        if not query:
            tracks = getattr(self, "_all_tracks", list_tracks())
            self.table_model.update_tracks(tracks)
        self.filter_proxy.search_text = query.lower()
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
            f"Year: {track.year or ''}",
            f"Genre: {track.genre or ''}",
            f"BPM: {track.bpm or ''}",
            f"Key: {track.key or ''}",
            f"LUFS: {track.loudness_lufs or ''}",
            f"Cue A: {track.cue_in_ms or ''}",
            f"Cue B: {track.cue_out_ms or ''}",
            f"Duration: {track.duration or ''}",
            f"Path: {track.path}",
        ]
        self.detail_text.setPlainText("\n".join(detail))
        self._fill_detail_fields(track)
        self._update_related_tracks(track)

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
            f"LUFS: {track.loudness_lufs or ''}",
            f"Cue A: {track.cue_in_ms or ''}",
            f"Cue B: {track.cue_out_ms or ''}",
            f"Duration: {track.duration or ''}",
            f"Path: {track.path}",
        ]
        self.detail_text.setPlainText("\n".join(detail))
        self._fill_detail_fields(track)
        self._update_related_tracks(track)

    def _update_related_tracks(self, track) -> None:
        self.related_list.clear()
        if not track.artist:
            return
        from lumbago_app.data.repository import list_tracks
        related = [
            t for t in list_tracks()
            if t.artist == track.artist and t.path != track.path
        ][:20]
        for t in related:
            item = QtWidgets.QListWidgetItem(t.title or t.path)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, t.path)
            self.related_list.addItem(item)

    def _jump_to_related(self, item: QtWidgets.QListWidgetItem) -> None:
        path = item.data(QtCore.Qt.ItemDataRole.UserRole)
        if not path:
            return
        # Wyszukaj track w tabeli i zaznacz
        for row in range(self.table_model.rowCount()):
            t = self.table_model.track_at(row)
            if t and t.path == path:
                proxy_idx = self.filter_proxy.mapFromSource(
                    self.table_model.index(row, 0)
                )
                self.table_view.setCurrentIndex(proxy_idx)
                self.table_view.scrollTo(proxy_idx)
                self.view_stack.setCurrentWidget(self.table_view)
                break

    def _play_selected(self):
        if not self.player:
            self._show_message("Odtwarzacz jest niedostępny w tej wersji.")
            return
        indexes = self.table_view.selectionModel().selectedRows()
        if not indexes:
            return
        source_index = self.filter_proxy.mapToSource(indexes[0])
        track = self.table_model.track_at(source_index.row())
        if not track:
            return
        self._cue_a = track.cue_in_ms
        self._cue_b = track.cue_out_ms
        url = QtCore.QUrl.fromLocalFile(track.path)
        self.player.setSource(url)
        self.player.play()
        self.table_model.set_now_playing(track.path)

    def _toggle_playback(self):
        if not self.player:
            self._show_message("Odtwarzacz jest niedostępny w tej wersji.")
            return
        from PyQt6.QtMultimedia import QMediaPlayer
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self._play_selected()

    def _seek_position(self, value: int):
        if not self.player:
            return
        if self._duration_ms <= 0:
            return
        self.player.setPosition(int(self._duration_ms * (value / 1000)))

    def _on_duration_changed(self, duration: int):
        if not self.player:
            return
        self._duration_ms = duration
        self._update_time_label(self.player.position(), duration)

    def _on_position_changed(self, position: int):
        if not self.player:
            return
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
        if not self.player:
            return
        self._cue_a = self.player.position()
        self._show_message("Ustawiono Cue A.")

    def _set_cue_b(self):
        if not self.player:
            return
        self._cue_b = self.player.position()
        self._show_message("Ustawiono Cue B.")

    def _jump_to_cue_a(self):
        if self.player and self._cue_a is not None:
            self.player.setPosition(self._cue_a)

    def _jump_to_cue_b(self):
        if self.player and self._cue_b is not None:
            self.player.setPosition(self._cue_b)

    def _toggle_loop(self):
        self._loop_enabled = not self._loop_enabled
        state = "włączona" if self._loop_enabled else "wyłączona"
        self.status.showMessage(f"Pętla {state}.")

    def _toggle_hot_cue(self, idx: int):
        pos = self._hot_cues.get(idx)
        if pos is None:
            # Ustaw hot cue w aktualnej pozycji
            if self.player:
                self._hot_cues[idx] = self.player.position()
            else:
                self._hot_cues[idx] = 0
            self._update_hot_cue_btn_style(
                self._hot_cue_btns[idx], idx, self._hot_cue_colors[idx], active=True
            )
            self._show_message(f"Hot Cue {idx + 1} ustawiony.")
        else:
            # Skocz do hot cue
            if self.player:
                self.player.setPosition(pos)

    def _clear_hot_cue(self, idx: int):
        self._hot_cues[idx] = None
        self._update_hot_cue_btn_style(
            self._hot_cue_btns[idx], idx, self._hot_cue_colors[idx], active=False
        )
        self._show_message(f"Hot Cue {idx + 1} wyczyszczony.")

    def _update_hot_cue_btn_style(self, btn: QtWidgets.QPushButton, idx: int, color: str, active: bool):
        if active:
            btn.setStyleSheet(
                f"QPushButton {{ background: {color}; color: #000; font-weight: bold; "
                f"border-radius: 4px; border: 1px solid {color}; }}"
                f"QPushButton:hover {{ background: #fff; color: #000; }}"
            )
        else:
            btn.setStyleSheet(
                f"QPushButton {{ background: #1a1f2e; color: {color}; font-weight: bold; "
                f"border-radius: 4px; border: 1px solid {color}; }}"
                f"QPushButton:hover {{ background: {color}33; }}"
            )

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
            if not self.player:
                self._show_message("Odtwarzacz jest niedostępny w tej wersji.")
                return
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

    def _reset_library(self):
        confirm = QtWidgets.QMessageBox.question(
            self,
            "Zerowanie biblioteki",
            "Czy na pewno chcesz usunąć całą bibliotekę?\n"
            "To skasuje utwory, playlisty i historię zmian.",
        )
        if confirm != QtWidgets.QMessageBox.StandardButton.Yes:
            return
        reset_library()
        self._load_tracks()
        self._load_playlists()
        self.detail_text.clear()
        self._show_message("Biblioteka została wyzerowana.")

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
        manual_search_action = menu.addAction("Szukaj metadanych ręcznie…")
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
                self.status.showMessage(f"Dodano do playlisty: {action.text()}")
        elif action == ai_action:
            self._run_ai_tagger()
        elif action == manual_search_action:
            source_index = self.filter_proxy.mapToSource(index)
            track = self.table_model.track_at(source_index.row())
            if track:
                self._open_manual_search(track)
        elif action == local_meta_action:
            self._apply_local_metadata_selected()

    def _open_manual_search(self, track) -> None:
        from lumbago_app.ui.manual_search_dialog import ManualSearchDialog
        from lumbago_app.core.config import load_settings
        settings = load_settings()
        dlg = ManualSearchDialog(
            track,
            musicbrainz_app=settings.musicbrainz_app,
            parent=self
        )
        if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            self._load_tracks()

    def _show_table_column_menu(self, pos):
        menu = QtWidgets.QMenu(self)
        show_all = menu.addAction("Pokaż wszystkie")
        hide_all = menu.addAction("Ukryj wszystkie")
        menu.addSeparator()
        actions = []
        for col, name in enumerate(self.table_model.headers):
            action = QtWidgets.QAction(name, menu)
            action.setCheckable(True)
            action.setChecked(not self.table_view.isColumnHidden(col))
            actions.append((action, col))
            menu.addAction(action)
        chosen = menu.exec(self.table_view.horizontalHeader().mapToGlobal(pos))
        if chosen == show_all:
            for _, col in actions:
                self.table_view.setColumnHidden(col, False)
            return
        if chosen == hide_all:
            for _, col in actions:
                self.table_view.setColumnHidden(col, True)
            return
        for action, col in actions:
            if chosen == action:
                self.table_view.setColumnHidden(col, not action.isChecked())
                break
    def _fill_detail_fields(self, track: Track):
        self.detail_title.setText(track.title or "")
        self.detail_artist.setText(track.artist or "")
        self.detail_album.setText(track.album or "")
        self.detail_year.setText(track.year or "")
        self.detail_genre.setText(track.genre or "")
        self.detail_bpm.setText(str(track.bpm or ""))
        self.detail_key.setText(track.key or "")
        self.detail_loudness.setText(str(track.loudness_lufs or ""))
        self._cue_a = track.cue_in_ms
        self._cue_b = track.cue_out_ms
        self._selected_track = track
        # BPM sync indicator
        self._update_bpm_sync(track.bpm)
        # Tag quality
        self._update_tag_quality(track)
        self._selected_snapshot = {
            "title": track.title,
            "artist": track.artist,
            "album": track.album,
            "year": track.year,
            "genre": track.genre,
            "bpm": track.bpm,
            "key": track.key,
        }
        self._update_cover_preview(track.artwork_path)
        wave_path = generate_waveform(Path(track.path))
        pixmap = QtGui.QPixmap(str(wave_path))
        if not pixmap.isNull():
            self.waveform_label.setPixmap(pixmap)

    def _update_tag_quality(self, track: Track):
        if not hasattr(self, "tag_quality_label"):
            return
        fields = [track.title, track.artist, track.album, track.year, track.genre,
                  track.bpm, track.key, track.artwork_path, track.mood, track.energy]
        filled = sum(1 for f in fields if f)
        total = len(fields)
        pct = int(filled / total * 100)
        color = "#66ff66" if pct >= 80 else "#ffaa44" if pct >= 50 else "#ff6666"
        self.tag_quality_label.setText(
            f'<span style="color:{color}">Jakość tagów: {filled}/{total} ({pct}%)</span>'
        )
        self.tag_quality_label.setTextFormat(QtCore.Qt.TextFormat.RichText)

    def _update_bpm_sync(self, new_bpm: float | None):
        """Aktualizuje wskaźnik różnicy BPM między poprzednim a bieżącym trackiem."""
        if not hasattr(self, "bpm_sync_label"):
            return
        if new_bpm and self._current_played_bpm and new_bpm != self._current_played_bpm:
            # Nowy utwór — poprzedni staje się "last"
            self._last_played_bpm = self._current_played_bpm
        self._current_played_bpm = new_bpm
        label = self.bpm_sync_label
        if not new_bpm:
            label.setText("")
            return
        txt = f"{new_bpm:.1f} BPM"
        if self._last_played_bpm:
            diff = new_bpm - self._last_played_bpm
            sign = "+" if diff >= 0 else ""
            txt += f"  ({sign}{diff:.1f} vs poprzedni)"
        label.setText(txt)

    def _save_detail_changes(self):
        track = getattr(self, "_selected_track", None)
        if not track:
            return
        snapshot = getattr(self, "_selected_snapshot", {})
        track.title = self.detail_title.text().strip()
        track.artist = self.detail_artist.text().strip()
        track.album = self.detail_album.text().strip()
        track.year = self.detail_year.text().strip()
        track.genre = self.detail_genre.text().strip()
        track.key = self.detail_key.text().strip()
        try:
            track.bpm = float(self.detail_bpm.text()) if self.detail_bpm.text().strip() else None
        except ValueError:
            track.bpm = None
        self._log_changes(track, snapshot)
        update_track(track)
        # Odśwież snapshot żeby nie duplikować change_log przy auto-save
        self._selected_snapshot = {
            "title": track.title, "artist": track.artist, "album": track.album,
            "year": track.year, "genre": track.genre, "bpm": track.bpm, "key": track.key,
        }
        self._show_message("Utwór zaktualizowany.")

    def _tap_bpm(self):
        import time
        now = time.monotonic()
        # Zresetuj jeśli przerwa > 3s
        if self._tap_times and (now - self._tap_times[-1]) > 3.0:
            self._tap_times.clear()
        self._tap_times.append(now)
        if len(self._tap_times) > 8:
            self._tap_times = self._tap_times[-8:]
        if len(self._tap_times) >= 2:
            intervals = [self._tap_times[i] - self._tap_times[i - 1]
                         for i in range(1, len(self._tap_times))]
            avg_interval = sum(intervals) / len(intervals)
            bpm = 60.0 / avg_interval if avg_interval > 0 else 0
            self.detail_bpm.setText(f"{bpm:.1f}")

    def _detect_key_detail(self):
        track = getattr(self, "_selected_track", None)
        if not track:
            self._show_message("Nie wybrano utworu.")
            return
        self._detect_key_btn.setEnabled(False)
        self._detect_key_btn.setText("…")

        def run():
            return detect_key(Path(track.path))

        def on_done(key):
            self._detect_key_btn.setEnabled(True)
            self._detect_key_btn.setText("Wykryj")
            if key:
                self.detail_key.setText(key)
                self._show_message(f"Wykryta tonacja: {key}")
            else:
                self._show_message("Nie udało się wykryć tonacji.")

        worker = _SimpleWorker(run, on_done)
        self.thread_pool.start(worker)

    def _log_changes(self, track: Track, snapshot: dict):
        for field in ["title", "artist", "album", "year", "genre", "bpm", "key"]:
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
            "year": self.detail_year.text().strip(),
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
            track.year = refreshed.year
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
            track.year = refreshed.year
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
            track.year = None
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
            data = item.data(0, QtCore.Qt.ItemDataRole.UserRole) if item else None
            if item and data and hasattr(self, "_selected_track") and self._selected_track:
                add_track_to_playlist(data.name, self._selected_track.path)
                self.status.showMessage(f"Dodano do playlisty: {data.name}")
            return True
        return super().eventFilter(source, event)

    def closeEvent(self, event):
        _debug_log("MainWindow: closeEvent")
        super().closeEvent(event)

    def showEvent(self, event):
        _debug_log("MainWindow: showEvent")
        super().showEvent(event)

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
        dialog = AiTaggerDialog(
            tracks,
            self,
            auto_fetch=True,
            auto_method="acoustid",
            allow_auto_fetch=True,
        )
        if dialog.exec():
            self._load_tracks()

    def _run_auto_tagger_cloud(self):
        tracks = self._selected_tracks()
        if not tracks:
            self._show_message("Zaznacz co najmniej jeden utwór.")
            return
        dialog = AiTaggerDialog(
            tracks,
            self,
            auto_fetch=False,
            allow_auto_fetch=False,
            force_cloud=True,
        )
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

    def _run_loudness_analysis(self):
        tracks = self._selected_tracks()
        if not tracks:
            self._show_message("Zaznacz co najmniej jeden utwór.")
            return
        worker = LoudnessWorker(tracks)
        progress = QtWidgets.QProgressDialog(
            "Analiza loudness (LUFS)...", "Zamknij", 0, len(tracks), self
        )
        progress.setWindowTitle("Analiza loudness")
        progress.setMinimumDuration(0)
        progress.setValue(0)

        def on_progress(current: int, total: int):
            progress.setMaximum(total)
            progress.setValue(current)
            self.status.showMessage(f"Analiza {current}/{total} utworów")

        def on_finished(updated: list[Track]):
            progress.close()
            update_tracks(updated)
            self._load_tracks()
            self.status.showMessage("Analiza loudness zakończona.")

        worker.signals.progress.connect(on_progress)
        worker.signals.finished.connect(on_finished)
        self.thread_pool.start(worker)

    def _run_loudness_normalize(self):
        tracks = self._selected_tracks()
        if not tracks:
            self._show_message("Zaznacz co najmniej jeden utwór.")
            return
        output_dir = QtWidgets.QFileDialog.getExistingDirectory(self, "Wybierz katalog wyjściowy")
        if not output_dir:
            return
        target, ok = QtWidgets.QInputDialog.getDouble(
            self,
            "Normalizacja loudness",
            "Docelowy poziom LUFS:",
            -14.0,
            -30.0,
            -5.0,
            1,
        )
        if not ok:
            return
        worker = NormalizeWorker(tracks, Path(output_dir), target)
        progress = QtWidgets.QProgressDialog(
            "Normalizacja do LUFS...", "Zamknij", 0, len(tracks), self
        )
        progress.setWindowTitle("Normalizacja loudness")
        progress.setMinimumDuration(0)
        progress.setValue(0)

        def on_progress(current: int, total: int):
            progress.setMaximum(total)
            progress.setValue(current)
            self.status.showMessage(f"Normalizacja {current}/{total}")

        def on_finished(created: int, errors: int):
            progress.close()
            self._load_tracks()
            self.status.showMessage(f"Normalizacja zakończona. Nowe pliki: {created}, błędy: {errors}")

        worker.signals.progress.connect(on_progress)
        worker.signals.finished.connect(on_finished)
        self.thread_pool.start(worker)

    def _run_key_detection(self):
        tracks = self._selected_tracks()
        if not tracks:
            self._show_message("Zaznacz co najmniej jeden utwór.")
            return
        worker = KeyDetectionWorker(tracks, force=False)
        progress = QtWidgets.QProgressDialog(
            "Wykrywanie tonacji...", "Zamknij", 0, len(tracks), self
        )
        progress.setWindowTitle("Auto‑key")
        progress.setMinimumDuration(0)
        progress.setValue(0)

        def on_progress(current: int, total: int):
            progress.setMaximum(total)
            progress.setValue(current)
            self.status.showMessage(f"Tonacja {current}/{total}")

        def on_finished(updated: list[Track]):
            progress.close()
            update_tracks(updated)
            self._load_tracks()
            self.status.showMessage("Wykrywanie tonacji zakończone.")

        worker.signals.progress.connect(on_progress)
        worker.signals.finished.connect(on_finished)
        self.thread_pool.start(worker)

    def _run_bpm_scan(self):
        """Skanuje BPM przez librosa dla wszystkich tracków bez BPM."""
        all_tracks = list(self.table_model._tracks)
        targets = [t for t in all_tracks if not t.bpm]
        if not targets:
            self._show_message("Wszystkie tracki mają już BPM.")
            return
        from lumbago_app.services.beatgrid import detect_bpm as _detect_bpm

        progress = QtWidgets.QProgressDialog(
            "Skanowanie BPM (librosa)...", "Anuluj", 0, len(targets), self
        )
        progress.setWindowTitle("BPM Scan")
        progress.setMinimumDuration(0)
        progress.setValue(0)
        updated: list[Track] = []
        cancelled = [False]

        class BpmScanWorker(QtCore.QRunnable):
            class Sig(QtCore.QObject):
                progress = QtCore.pyqtSignal(int, int)
                finished = QtCore.pyqtSignal(list)
            def __init__(self, tracks):
                super().__init__()
                self.tracks = tracks
                self.signals = BpmScanWorker.Sig()
                self._stop = False
            def stop(self): self._stop = True
            def run(self):
                done = []
                for idx, track in enumerate(self.tracks, 1):
                    if self._stop:
                        break
                    bpm = _detect_bpm(track.path)
                    if bpm:
                        track.bpm = bpm
                        done.append(track)
                    self.signals.progress.emit(idx, len(self.tracks))
                self.signals.finished.emit(done)

        worker = BpmScanWorker(targets)

        def on_progress(current, total):
            progress.setValue(current)
            if progress.wasCanceled():
                worker.stop()

        def on_finished(done):
            progress.close()
            if done:
                update_tracks(done)
                self._load_tracks()
            self._show_message(f"BPM wykryty dla {len(done)} / {len(targets)} tracków.")

        worker.signals.progress.connect(on_progress)
        worker.signals.finished.connect(on_finished)
        self.thread_pool.start(worker)

    def _auto_cue_selected(self):
        tracks = self._selected_tracks()
        if not tracks:
            self._show_message("Zaznacz co najmniej jeden utwór.")
            return
        for track in tracks:
            cue_in, cue_out = auto_cue_points(track.duration)
            track.cue_in_ms = cue_in
            track.cue_out_ms = cue_out
            save_analysis_cache(
                Path(track.path),
                {
                    "cue_in_ms": cue_in,
                    "cue_out_ms": cue_out,
                },
            )
        update_tracks(tracks)
        if getattr(self, "_selected_track", None):
            self._cue_a = self._selected_track.cue_in_ms
            self._cue_b = self._selected_track.cue_out_ms
        self._show_message("Auto‑cue ustawione.")

    def _export_playlist_virtualdj(self):
        playlist = getattr(self, "_current_playlist", None)
        if playlist and playlist.playlist_id:
            tracks = list_playlist_tracks(playlist.playlist_id)
        else:
            tracks = list(self.table_model._tracks)
        if not tracks:
            self._show_message("Brak utworów do eksportu.")
            return
        output_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Zapisz VirtualDJ XML",
            "",
            "VirtualDJ XML (*.xml)",
        )
        if not output_path:
            return
        xml_tracks: list[XmlTrack] = []
        for track in tracks:
            xml_tracks.append(
                XmlTrack(
                    path=track.path,
                    title=track.title,
                    artist=track.artist,
                    album=track.album,
                    genre=track.genre,
                    bpm=f"{track.bpm:.1f}" if track.bpm else None,
                    key=track.key,
                )
            )
        export_virtualdj_xml(xml_tracks, Path(output_path))
        self._show_message("Eksport VirtualDJ zakończony.")

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
            settings.validation_policy,
            settings.metadata_cache_ttl_days,
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

        def on_finished(results: list):
            progress.close()
            dialog = RecognitionResultsDialog(results, self)
            if dialog.exec():
                self._load_tracks()
            success = sum(1 for r in results if r.success)
            self.status.showMessage(f"Rozpoznano: {success}/{len(results)}")

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
        self._update_mode_pill()

    def _update_mode_pill(self):
        if not hasattr(self, "mode_pill"):
            return
        if not hasattr(self, "settings"):
            self.settings = load_settings()
        provider = self.settings.cloud_ai_provider or "local"
        if provider == "local":
            self.mode_pill.setText("Tryb mieszany (lokalny)")
            self.mode_pill.setProperty("mode", "mixed")
        else:
            self.mode_pill.setText(f"Tryb API • {provider}")
            self.mode_pill.setProperty("mode", "api")
        self.mode_pill.style().unpolish(self.mode_pill)
        self.mode_pill.style().polish(self.mode_pill)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        try:
            perform_backup()
        finally:
            super().closeEvent(event)

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
        QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Shift+T"), self, activated=self._run_auto_tagger_cloud)

    def _apply_icons(self):
        icons_dir = Path(__file__).resolve().parent / "assets" / "icons"
        def icon(name: str) -> QtGui.QIcon:
            return QtGui.QIcon(str(icons_dir / name))

        self.btn_scan.setIcon(icon("scan.svg"))
        self.btn_recognition.setIcon(icon("refresh.svg"))
        self.btn_ai.setIcon(icon("ai.svg"))
        self.btn_local_meta.setIcon(icon("tag.svg"))
        self.btn_duplicates.setIcon(icon("duplicates.svg"))
        self.btn_renamer.setIcon(icon("rename.svg"))
        self.btn_xml.setIcon(icon("xml.svg"))
        self.btn_xml_import.setIcon(icon("import.svg"))
        self.btn_settings.setIcon(icon("settings.svg"))
        self.settings_btn.setIcon(icon("settings.svg"))
        self.auto_tag_btn.setIcon(icon("magic.svg"))
        self.play_btn.setIcon(icon("play.svg"))
        self.stop_btn.setIcon(icon("stop.svg"))

    def _build_menu(self):
        menu = self.menuBar()
        tools = menu.addMenu("Narzędzia")
        tools.addAction("Importuj / Skanuj", self._open_import_wizard)
        tools.addAction("Import XML", self._open_xml_import)
        tools.addAction("Zeruj bibliotekę", self._reset_library)
        tools.addAction("AutoTagowanie (wyszukiwanie)", self._run_auto_tagger)
        tools.addAction("AutoTagowanie (API)", self._run_auto_tagger_cloud)
        tools.addAction("Analiza loudness (LUFS)", self._run_loudness_analysis)
        tools.addAction("Normalizuj do -14 LUFS (nowy plik)", self._run_loudness_normalize)
        tools.addAction("Auto‑cue (intro/outro)", self._auto_cue_selected)
        tools.addAction("Wykryj tonację (auto‑key)", self._run_key_detection)
        tools.addAction("Skanuj BPM librosa (brakujące)", self._run_bpm_scan)
        tools.addAction("Statystyki biblioteki", self._show_library_stats)
        tools.addAction("Metadane lokalne", self._apply_local_metadata_selected)
        tools.addAction("Duplikaty", self._open_duplicates)
        tools.addAction("Renamer", self._open_renamer)
        tools.addAction("Konwerter XML", self._open_xml_converter)
        tools.addAction("Eksport playlisty → VirtualDJ XML", self._export_playlist_virtualdj)
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
        menu.addSeparator()
        stats_action = menu.addAction("Statystyki playlisty")
        export_m3u_action = menu.addAction("Eksportuj do M3U")
        import_m3u_action = menu.addAction("Importuj M3U jako playlistę")
        merge_action = menu.addAction("Scal z inną playlistą…")
        action = menu.exec(self.playlist_list.mapToGlobal(pos))
        if action == add_action:
            self._open_playlist_editor()
        elif action == edit_action and item:
            playlist = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
            if playlist:
                self._open_playlist_editor(playlist)
        elif action == delete_action and item:
            playlist = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
            if playlist and playlist.playlist_id:
                delete_playlist(playlist.playlist_id)
                self._load_playlists()
                self._load_tracks()
        elif action == order_action and item:
            playlist = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
            if playlist and playlist.playlist_id and not playlist.is_smart:
                tracks = list_playlist_tracks(playlist.playlist_id)
                dialog = PlaylistOrderDialog(tracks, self)
                if dialog.exec():
                    set_playlist_track_order(playlist.playlist_id, dialog.ordered_paths())
                    self._apply_playlist_view()
        elif action == stats_action:
            self._show_playlist_stats(item)
        elif action == export_m3u_action:
            self._export_playlist_m3u(item)
        elif action == import_m3u_action:
            self._import_playlist_m3u()
        elif action == merge_action and item:
            self._merge_playlist(item)

    def _show_playlist_stats(self, item: QtWidgets.QTreeWidgetItem | None):
        if item:
            playlist = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
            if playlist and playlist.playlist_id:
                tracks = list_playlist_tracks(playlist.playlist_id)
                name = playlist.name
            else:
                tracks = list(self.table_model._tracks)
                name = "Wszystkie utwory"
        else:
            tracks = list(self.table_model._tracks)
            name = "Wszystkie utwory"

        count = len(tracks)
        total_s = sum(t.duration or 0 for t in tracks)
        total_min, total_sec = divmod(int(total_s), 60)
        total_h, total_min = divmod(total_min, 60)
        bpms = [t.bpm for t in tracks if t.bpm]
        avg_bpm = f"{sum(bpms) / len(bpms):.1f}" if bpms else "—"
        keys = [t.key for t in tracks if t.key]
        key_dist: dict[str, int] = {}
        for k in keys:
            key_dist[k] = key_dist.get(k, 0) + 1
        top_keys = sorted(key_dist.items(), key=lambda x: x[1], reverse=True)[:5]
        key_text = ", ".join(f"{k} ({n})" for k, n in top_keys) if top_keys else "—"

        msg = (
            f"<b>Playlista: {name}</b><br><br>"
            f"Liczba utworów: <b>{count}</b><br>"
            f"Łączny czas: <b>{total_h}h {total_min:02d}m {total_sec:02d}s</b><br>"
            f"Średnie BPM: <b>{avg_bpm}</b><br>"
            f"Najczęstsze tonacje: <b>{key_text}</b>"
        )
        QtWidgets.QMessageBox.information(self, "Statystyki playlisty", msg)

    def _show_library_stats(self):
        tracks = list_tracks()
        count = len(tracks)
        total_s = sum(t.duration or 0 for t in tracks)
        total_h, rem = divmod(int(total_s), 3600)
        total_m, total_sec = divmod(rem, 60)
        total_size = sum(t.file_size or 0 for t in tracks)
        size_gb = total_size / 1024 / 1024 / 1024
        bpms = [t.bpm for t in tracks if t.bpm]
        avg_bpm = f"{sum(bpms)/len(bpms):.1f}" if bpms else "—"
        genres: dict[str, int] = {}
        for t in tracks:
            g = (t.genre or "").strip()
            if g:
                genres[g] = genres.get(g, 0) + 1
        top_genres = sorted(genres.items(), key=lambda x: x[1], reverse=True)[:8]
        genre_lines = "  " + ", ".join(f"{g} ({n})" for g, n in top_genres) if top_genres else "  —"
        keys: dict[str, int] = {}
        for t in tracks:
            k = (t.key or "").strip()
            if k:
                keys[k] = keys.get(k, 0) + 1
        top_keys = sorted(keys.items(), key=lambda x: x[1], reverse=True)[:6]
        key_line = "  " + ", ".join(f"{k} ({n})" for k, n in top_keys) if top_keys else "  —"
        fmt: dict[str, int] = {}
        for t in tracks:
            f = (t.format or "?").upper()
            fmt[f] = fmt.get(f, 0) + 1
        fmt_line = "  " + ", ".join(f"{f} ({n})" for f, n in sorted(fmt.items(), key=lambda x: x[1], reverse=True))
        msg = (
            f"<b>Statystyki biblioteki</b><br><br>"
            f"Liczba utworów: <b>{count}</b><br>"
            f"Łączny czas: <b>{total_h}h {total_m:02d}m {total_sec:02d}s</b><br>"
            f"Łączny rozmiar: <b>{size_gb:.2f} GB</b><br>"
            f"Średnie BPM: <b>{avg_bpm}</b><br><br>"
            f"Formaty:<br>{fmt_line}<br><br>"
            f"Najczęstsze gatunki:<br>{genre_lines}<br><br>"
            f"Najczęstsze tonacje:<br>{key_line}"
        )
        QtWidgets.QMessageBox.information(self, "Statystyki biblioteki", msg)

    def _export_playlist_m3u(self, item: QtWidgets.QTreeWidgetItem | None):
        if item:
            playlist = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
            if playlist and playlist.playlist_id:
                tracks = list_playlist_tracks(playlist.playlist_id)
                default_name = f"{playlist.name}.m3u"
            else:
                tracks = list(self.table_model._tracks)
                default_name = "playlist.m3u"
        else:
            tracks = list(self.table_model._tracks)
            default_name = "playlist.m3u"
        if not tracks:
            self._show_message("Brak utworów do eksportu.")
            return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Eksportuj do M3U", default_name, "M3U (*.m3u)"
        )
        if not path:
            return
        lines = ["#EXTM3U"]
        for track in tracks:
            duration = int(track.duration) if track.duration else -1
            artist = track.artist or ""
            title = track.title or Path(track.path).stem
            display = f"{artist} - {title}" if artist else title
            lines.append(f"#EXTINF:{duration},{display}")
            lines.append(track.path)
        Path(path).write_text("\n".join(lines), encoding="utf-8")
        self._show_message(f"Wyeksportowano {len(tracks)} utworów do M3U.")

    def _import_playlist_m3u(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Importuj M3U", "", "M3U (*.m3u *.m3u8)"
        )
        if not path:
            return
        lines = Path(path).read_text(encoding="utf-8", errors="ignore").splitlines()
        file_paths = [ln.strip() for ln in lines if ln.strip() and not ln.startswith("#")]
        if not file_paths:
            self._show_message("Brak ścieżek w pliku M3U.")
            return
        playlist_name = Path(path).stem
        create_playlist(playlist_name)
        added = 0
        for fp in file_paths:
            try:
                add_track_to_playlist(playlist_name, fp)
                added += 1
            except Exception:
                pass
        self._load_playlists()
        self._show_message(f"Zaimportowano playlistę '{playlist_name}' ({added} utworów).")

    def _merge_playlist(self, item: QtWidgets.QTreeWidgetItem):
        src_playlist = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if not src_playlist or not src_playlist.playlist_id:
            return
        all_playlists = list_playlists_full()
        others = [p for p in all_playlists if p.playlist_id != src_playlist.playlist_id]
        if not others:
            self._show_message("Brak innych playlisty do scalenia.")
            return
        names = [p.name for p in others]
        chosen, ok = QtWidgets.QInputDialog.getItem(
            self, "Scal playliste",
            f"Dodaj tracki z '{src_playlist.name}' do:", names, 0, False
        )
        if not ok or not chosen:
            return
        target = next(p for p in others if p.name == chosen)
        src_tracks = list_playlist_tracks(src_playlist.playlist_id)
        merged = 0
        for track in src_tracks:
            try:
                add_track_to_playlist(target.name, track.path)
                merged += 1
            except Exception:
                pass
        self._load_playlists()
        self._show_message(f"Scalono {merged} utworów do '{target.name}'.")

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

    def _select_playlist(self, item: QtWidgets.QTreeWidgetItem):
        playlist = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if playlist is None and item.childCount() > 0:
            # Kliknięto folder — rozwiń/zwiń
            item.setExpanded(not item.isExpanded())
            return
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
        date_added_days = rules.get("date_added_days")
        cutoff_dt = None
        if date_added_days:
            from datetime import timedelta
            cutoff_dt = datetime.utcnow() - timedelta(days=int(date_added_days))
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
            if cutoff_dt is not None and track.date_added is not None and track.date_added < cutoff_dt:
                continue
            filtered.append(track)
        return filtered
    def _build_toolbar(self) -> QtWidgets.QFrame:
        frame = QtWidgets.QFrame()
        frame.setObjectName("Toolbar")
        row = QtWidgets.QHBoxLayout(frame)
        row.setContentsMargins(12, 8, 12, 8)
        self.title_label = QtWidgets.QLabel("Lumbago Music AI")
        font = self.title_label.font()
        font.setPointSize(14)
        font.setBold(True)
        self.title_label.setFont(font)
        self.title_label.setObjectName("SectionTitle")
        row.addWidget(self.title_label)

        self.mode_pill = QtWidgets.QLabel()
        self.mode_pill.setObjectName("ModePill")
        self._update_mode_pill()
        row.addWidget(self.mode_pill)
        row.addStretch(1)

        self.settings_btn = AnimatedButton("Ustawienia")
        self.settings_btn.setToolTip("Konfiguracja aplikacji i kluczy API")
        self.settings_btn.clicked.connect(self._open_settings)
        row.addWidget(self.settings_btn)

        self.reset_library_btn = AnimatedButton("Zeruj bibliotekę")
        self.reset_library_btn.setObjectName("DangerAction")
        self.reset_library_btn.setToolTip("Usuń wszystkie utwory, playlisty i cache z bazy")
        self.reset_library_btn.clicked.connect(self._reset_library)
        row.addWidget(self.reset_library_btn)

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

        self.auto_tag_btn = AnimatedButton("AutoTag (wyszukiwanie)")
        self.auto_tag_btn.setObjectName("AutoTagSearch")
        self.auto_tag_btn.setToolTip("Uruchom AI + uzupełnianie braków przez wyszukiwanie")
        self.auto_tag_btn.clicked.connect(self._run_auto_tagger)
        self.auto_tag_btn.enable_pulse()
        row.addWidget(self.auto_tag_btn)

        self.auto_tag_cloud_btn = AnimatedButton("AutoTag (API)")
        self.auto_tag_cloud_btn.setObjectName("AutoTagApi")
        self.auto_tag_cloud_btn.setToolTip("Tagowanie wyłącznie przez API (OpenAI/Grok/DeepSeek/Gemini)")
        self.auto_tag_cloud_btn.clicked.connect(self._run_auto_tagger_cloud)
        row.addWidget(self.auto_tag_cloud_btn)

        preset_label = QtWidgets.QLabel("Kolumny:")
        preset_label.setStyleSheet("color: #9aa6b2; margin-left: 8px;")
        row.addWidget(preset_label)
        for name, cols in [("DJ", _DJ_COLUMNS), ("Metadane", _META_COLUMNS), ("Pełny", None)]:
            btn = QtWidgets.QPushButton(name)
            btn.setFixedHeight(24)
            btn.setMaximumWidth(72)
            btn.setToolTip(f"Preset kolumn: {name}")
            btn.clicked.connect(lambda _, c=cols: self._apply_column_preset(c))
            row.addWidget(btn)

        density_label = QtWidgets.QLabel("Gęstość:")
        density_label.setStyleSheet("color: #9aa6b2; margin-left: 8px;")
        row.addWidget(density_label)
        self.density_combo = QtWidgets.QComboBox()
        self.density_combo.addItems(["Normalny", "Kompakt", "Przestronny"])
        self.density_combo.setFixedWidth(110)
        self.density_combo.setToolTip("Wysokość wierszy listy utworów")
        self.density_combo.currentIndexChanged.connect(self._on_density_changed)
        row.addWidget(self.density_combo)
        return frame

    def _apply_column_preset(self, visible_cols: list[int] | None):
        from lumbago_app.ui.models import TrackTableModel
        total = len(TrackTableModel.headers)
        for col in range(total):
            if visible_cols is None:
                self.table_view.setColumnHidden(col, False)
            else:
                self.table_view.setColumnHidden(col, col not in visible_cols)

    def _on_density_changed(self, idx: int):
        heights = {0: 28, 1: 20, 2: 40}  # Normalny / Kompakt / Przestronny
        height = heights.get(idx, 28)
        vheader = self.table_view.verticalHeader()
        vheader.setDefaultSectionSize(height)
        vheader.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Fixed)

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event: QtGui.QDragMoveEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event: QtGui.QDropEvent):
        urls = event.mimeData().urls()
        if not urls:
            return
        paths = [Path(url.toLocalFile()) for url in urls]
        folders = [p for p in paths if p.is_dir()]
        files = [p for p in paths if p.is_file()]
        if folders:
            folder = folders[0]
            wizard = ImportWizard(self, on_complete=self._load_tracks)
            wizard.folder_input.setText(str(folder))
            wizard.exec()
        elif files:
            from lumbago_app.core.audio import AUDIO_EXTENSIONS
            audio_files = [p for p in files if p.suffix.lower() in AUDIO_EXTENSIONS]
            if audio_files:
                wizard = ImportWizard(self, on_complete=self._load_tracks)
                wizard.folder_input.setText(str(audio_files[0].parent))
                wizard.exec()
        event.acceptProposedAction()


