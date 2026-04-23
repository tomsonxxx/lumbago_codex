from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import os

from PyQt6 import QtCore, QtGui, QtWidgets

from .automation import WatchFolderService
from .models import Track
from .scanner import auto_tag_from_filename, extract_track, iter_audio_files
from .storage import load_library, load_settings, save_library, save_settings


class ScanWorkerSignals(QtCore.QObject):
    progress = QtCore.pyqtSignal(int, int)
    finished = QtCore.pyqtSignal(list)


class ScanWorker(QtCore.QRunnable):
    def __init__(self, folder: Path) -> None:
        super().__init__()
        self.folder = folder
        self.signals = ScanWorkerSignals()

    def run(self) -> None:
        files = list(iter_audio_files(self.folder))
        total = len(files)
        output: list[Track] = []
        for idx, path in enumerate(files, start=1):
            output.append(extract_track(path, source="import"))
            self.signals.progress.emit(idx, total)
        self.signals.finished.emit(output)


class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, settings: dict, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Ustawienia")
        self.setModal(True)
        self.resize(420, 220)

        layout = QtWidgets.QVBoxLayout(self)
        form = QtWidgets.QFormLayout()

        self.watch_folder_edit = QtWidgets.QLineEdit(str(settings.get("watch_folder", "")))
        browse_btn = QtWidgets.QPushButton("...")
        browse_btn.setFixedWidth(34)
        browse_btn.clicked.connect(self._choose_folder)
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.watch_folder_edit, 1)
        row.addWidget(browse_btn)
        holder = QtWidgets.QWidget()
        holder.setLayout(row)
        form.addRow("Watch folder", holder)

        self.watch_enabled = QtWidgets.QCheckBox("Włącz automatyczne monitorowanie folderu")
        self.watch_enabled.setChecked(bool(settings.get("watch_enabled", False)))
        form.addRow("", self.watch_enabled)

        self.interval = QtWidgets.QSpinBox()
        self.interval.setRange(2, 120)
        self.interval.setValue(int(settings.get("watch_interval_sec", 6)))
        self.interval.setSuffix(" s")
        form.addRow("Interwał", self.interval)

        self.auto_tag = QtWidgets.QCheckBox("Auto-tag po imporcie (lokalny parser nazwy pliku)")
        self.auto_tag.setChecked(bool(settings.get("auto_tag_on_import", True)))
        form.addRow("", self.auto_tag)

        layout.addLayout(form)
        layout.addStretch(1)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _choose_folder(self) -> None:
        chosen = QtWidgets.QFileDialog.getExistingDirectory(self, "Wybierz watch folder")
        if chosen:
            self.watch_folder_edit.setText(chosen)

    def result_settings(self) -> dict:
        return {
            "watch_folder": self.watch_folder_edit.text().strip(),
            "watch_enabled": self.watch_enabled.isChecked(),
            "watch_interval_sec": self.interval.value(),
            "auto_tag_on_import": self.auto_tag.isChecked(),
        }


class MainWindow(QtWidgets.QMainWindow):
    NAV_LIBRARY = "library"
    NAV_PLAYLISTS = "playlists"
    NAV_DUPLICATES = "duplicates"
    NAV_RENAMER = "renamer"
    NAV_XML = "xml"

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Lumbago Fresh")
        self.resize(1280, 800)

        self.thread_pool = QtCore.QThreadPool.globalInstance()
        self.settings = load_settings()
        self.tracks: list[Track] = load_library()
        self.filtered_tracks: list[Track] = []
        self.current_nav = self.NAV_LIBRARY
        self.current_path: str | None = None

        self.watch_service = WatchFolderService(self)
        self.watch_service.new_files.connect(self._on_watch_new_files)
        self.watch_service.status.connect(lambda msg: self.statusBar().showMessage(msg, 3500))
        self.watch_service.set_known_paths([str(Path(t.path).resolve()) for t in self.tracks if t.path])

        self._build_ui()
        self._apply_styles()
        self._apply_watch_settings()
        self._refresh_table()
        self._refresh_sidebar_counts()
        self.statusBar().showMessage("Gotowe")

    def _build_ui(self) -> None:
        root = QtWidgets.QWidget()
        self.setCentralWidget(root)
        root_layout = QtWidgets.QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.sidebar = self._build_sidebar()
        root_layout.addWidget(self.sidebar, 0)

        right = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self.stack = QtWidgets.QStackedWidget()
        self.stack.addWidget(self._build_library_view())
        self.stack.addWidget(self._build_placeholder("Playlisty", "Zarządzanie playlistami - moduł uproszczony."))
        self.stack.addWidget(self._build_duplicates_view())
        self.stack.addWidget(self._build_renamer_view())
        self.stack.addWidget(self._build_placeholder("XML Konwerter", "Import/eksport XML - w tej wersji jako placeholder."))
        right_layout.addWidget(self.stack, 1)

        right_layout.addWidget(self._build_player_bar(), 0)
        root_layout.addWidget(right, 1)
        self._set_nav(self.NAV_LIBRARY)

    def _build_sidebar(self) -> QtWidgets.QWidget:
        panel = QtWidgets.QFrame()
        panel.setObjectName("Sidebar")
        panel.setFixedWidth(290)
        layout = QtWidgets.QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        logo = QtWidgets.QLabel("Lumbago")
        logo.setObjectName("LogoTitle")
        sub = QtWidgets.QLabel("Music AI")
        sub.setObjectName("LogoSub")
        layout.addWidget(logo)
        layout.addWidget(sub)

        import_btn = QtWidgets.QPushButton("Importuj muzykę\nWybierz folder")
        import_btn.setObjectName("ImportButton")
        import_btn.clicked.connect(self._import_folder)
        layout.addWidget(import_btn)

        self.nav_buttons: dict[str, QtWidgets.QPushButton] = {}
        nav_items = [
            (self.NAV_LIBRARY, "♫  Biblioteka"),
            (self.NAV_PLAYLISTS, "≡  Playlisty"),
            (self.NAV_DUPLICATES, "⊕  Duplikaty"),
            (self.NAV_RENAMER, "✎  Renamer"),
            (self.NAV_XML, "↔  XML Konwerter"),
        ]
        for nav_id, label in nav_items:
            btn = QtWidgets.QPushButton(label)
            btn.setProperty("nav", True)
            btn.clicked.connect(lambda _=False, nid=nav_id: self._set_nav(nid))
            layout.addWidget(btn)
            self.nav_buttons[nav_id] = btn

        layout.addSpacing(4)
        section = QtWidgets.QLabel("Narzędzia automatyzacji")
        section.setObjectName("SectionTitle")
        layout.addWidget(section)

        self.btn_tagger = QtWidgets.QPushButton("🔍  AutoTag lokalny")
        self.btn_tagger.clicked.connect(self._run_auto_tag_selected)
        layout.addWidget(self.btn_tagger)

        self.btn_watch_toggle = QtWidgets.QPushButton("▶  Watch-folder: start")
        self.btn_watch_toggle.clicked.connect(self._toggle_watch_folder)
        layout.addWidget(self.btn_watch_toggle)

        layout.addStretch(1)
        self.btn_settings = QtWidgets.QPushButton("⚙  Ustawienia")
        self.btn_settings.clicked.connect(self._open_settings)
        layout.addWidget(self.btn_settings)

        self.version = QtWidgets.QLabel("v1.0 - Fresh")
        self.version.setObjectName("Version")
        layout.addWidget(self.version)

        return panel

    def _build_library_view(self) -> QtWidgets.QWidget:
        holder = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(holder)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        top = QtWidgets.QHBoxLayout()
        self.search = QtWidgets.QLineEdit()
        self.search.setPlaceholderText("Szukaj: tytuł, artysta, album, gatunek...")
        self.search.textChanged.connect(self._refresh_table)
        top.addWidget(self.search, 1)

        refresh_btn = QtWidgets.QPushButton("Odśwież")
        refresh_btn.clicked.connect(self._refresh_table)
        top.addWidget(refresh_btn)
        layout.addLayout(top)

        self.table = QtWidgets.QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(
            ["Tytuł", "Artysta", "Album", "Gatunek", "Rok", "Długość", "Źródło", "Plik"]
        )
        self.table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(7, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        self.table.itemDoubleClicked.connect(lambda _item: self._open_in_system_player())
        layout.addWidget(self.table, 1)

        return holder

    def _build_duplicates_view(self) -> QtWidgets.QWidget:
        holder = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(holder)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)
        info = QtWidgets.QLabel(
            "Wykrywanie duplikatów na podstawie: (artist, title) lub identycznej nazwy pliku."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        btn = QtWidgets.QPushButton("Wyszukaj duplikaty")
        btn.clicked.connect(self._find_duplicates)
        layout.addWidget(btn, 0)

        self.duplicates_list = QtWidgets.QListWidget()
        layout.addWidget(self.duplicates_list, 1)
        return holder

    def _build_renamer_view(self) -> QtWidgets.QWidget:
        holder = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(holder)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        desc = QtWidgets.QLabel(
            "Prosty renamer: zmienia nazwę wybranego pliku na schemat `Artist - Title.ext`."
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)

        btn = QtWidgets.QPushButton("Zmień nazwę zaznaczonego utworu")
        btn.clicked.connect(self._rename_selected_track)
        layout.addWidget(btn)

        self.renamer_status = QtWidgets.QLabel("Wybierz utwór w Bibliotece, potem uruchom zmianę nazwy.")
        self.renamer_status.setWordWrap(True)
        layout.addWidget(self.renamer_status)
        layout.addStretch(1)
        return holder

    def _build_placeholder(self, title: str, subtitle: str) -> QtWidgets.QWidget:
        holder = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(holder)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(8)
        layout.addStretch(1)
        name = QtWidgets.QLabel(title)
        name.setObjectName("PlaceholderTitle")
        name.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name)
        text = QtWidgets.QLabel(subtitle)
        text.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        text.setStyleSheet("color:#8a90a2;")
        layout.addWidget(text)
        layout.addStretch(2)
        return holder

    def _build_player_bar(self) -> QtWidgets.QWidget:
        bar = QtWidgets.QFrame()
        bar.setObjectName("PlayerBar")
        layout = QtWidgets.QHBoxLayout(bar)
        layout.setContentsMargins(14, 8, 14, 8)

        prev_btn = QtWidgets.QPushButton("⏮")
        prev_btn.clicked.connect(self._play_prev)
        play_btn = QtWidgets.QPushButton("▶ Otwórz")
        play_btn.clicked.connect(self._open_in_system_player)
        next_btn = QtWidgets.QPushButton("⏭")
        next_btn.clicked.connect(self._play_next)

        layout.addWidget(prev_btn)
        layout.addWidget(play_btn)
        layout.addWidget(next_btn)

        self.now_playing = QtWidgets.QLabel("Brak aktywnego utworu")
        self.now_playing.setObjectName("NowPlaying")
        layout.addWidget(self.now_playing, 1)

        return bar

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow, QWidget {
                background-color: #0f1116;
                color: #e7ebf5;
                font-family: Segoe UI;
                font-size: 13px;
            }
            #Sidebar {
                background-color: #151925;
                border-right: 1px solid #262c3b;
            }
            #LogoTitle {
                font-size: 28px;
                font-weight: 700;
            }
            #LogoSub {
                color: #8a90a2;
                margin-bottom: 8px;
            }
            #ImportButton {
                padding: 10px;
                border: 1px solid #357ddf;
                border-radius: 10px;
                text-align: left;
                background: #1a2235;
                font-weight: 600;
            }
            QPushButton[nav="true"] {
                text-align: left;
                border: 1px solid #2a3040;
                border-radius: 8px;
                padding: 9px;
                background: #171b28;
            }
            QPushButton[active="true"] {
                border-color: #4e8ff0;
                background: #202c45;
            }
            QPushButton {
                border: 1px solid #2a3040;
                border-radius: 8px;
                background: #1b1f2c;
                padding: 8px 10px;
            }
            QPushButton:hover {
                border-color: #4e8ff0;
            }
            #SectionTitle {
                color: #8a90a2;
                margin-top: 8px;
            }
            #Version {
                color: #7480a0;
                font-size: 11px;
            }
            QLineEdit, QSpinBox {
                border: 1px solid #2a3040;
                border-radius: 8px;
                padding: 8px;
                background: #111522;
            }
            QTableWidget {
                border: 1px solid #262c3b;
                border-radius: 10px;
                gridline-color: #232837;
                background: #0f131d;
                selection-background-color: #2a4269;
            }
            QHeaderView::section {
                background: #161c2b;
                border: none;
                border-bottom: 1px solid #262c3b;
                padding: 8px;
                font-weight: 600;
            }
            #PlayerBar {
                border-top: 1px solid #262c3b;
                background: #121723;
            }
            #NowPlaying {
                color: #a4acc2;
                padding-left: 10px;
            }
            #PlaceholderTitle {
                font-size: 24px;
                font-weight: 700;
            }
            """
        )

    def _set_nav(self, nav_id: str) -> None:
        self.current_nav = nav_id
        index_map = {
            self.NAV_LIBRARY: 0,
            self.NAV_PLAYLISTS: 1,
            self.NAV_DUPLICATES: 2,
            self.NAV_RENAMER: 3,
            self.NAV_XML: 4,
        }
        self.stack.setCurrentIndex(index_map[nav_id])
        for nid, btn in self.nav_buttons.items():
            btn.setProperty("active", nid == nav_id)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _import_folder(self) -> None:
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Wybierz folder muzyki")
        if not folder:
            return
        self.statusBar().showMessage("Skanowanie folderu...")
        self._start_scan(Path(folder))

    def _start_scan(self, folder: Path) -> None:
        worker = ScanWorker(folder)
        worker.signals.progress.connect(self._scan_progress)
        worker.signals.finished.connect(self._scan_finished)
        self.thread_pool.start(worker)

    def _scan_progress(self, current: int, total: int) -> None:
        self.statusBar().showMessage(f"Skanowanie {current}/{total}")

    def _scan_finished(self, scanned: list[Track]) -> None:
        existing = {str(Path(t.path).resolve()): t for t in self.tracks if t.path}
        added = 0
        for track in scanned:
            normalized = str(Path(track.path).resolve())
            if normalized in existing:
                continue
            if self.settings.get("auto_tag_on_import", True):
                track = auto_tag_from_filename(track)
            self.tracks.append(track)
            existing[normalized] = track
            added += 1
        save_library(self.tracks)
        self.watch_service.set_known_paths([str(Path(t.path).resolve()) for t in self.tracks if t.path])
        self._refresh_table()
        self._refresh_sidebar_counts()
        self.statusBar().showMessage(f"Import zakończony. Dodano: {added}", 5000)

    def _refresh_table(self) -> None:
        query = self.search.text().strip().lower() if hasattr(self, "search") else ""
        if query:
            filtered = []
            for t in self.tracks:
                blob = f"{t.title} {t.artist} {t.album} {t.genre} {t.filename}".lower()
                if query in blob:
                    filtered.append(t)
            self.filtered_tracks = filtered
        else:
            self.filtered_tracks = list(self.tracks)

        self.table.setRowCount(len(self.filtered_tracks))
        for row, track in enumerate(self.filtered_tracks):
            values = [
                track.title or track.filename,
                track.artist,
                track.album,
                track.genre,
                track.year,
                self._format_duration(track.duration),
                track.source,
                track.filename,
            ]
            for col, value in enumerate(values):
                item = QtWidgets.QTableWidgetItem(str(value or ""))
                if col == 7:
                    item.setToolTip(track.path)
                self.table.setItem(row, col, item)
        self.table.resizeRowsToContents()

    def _refresh_sidebar_counts(self) -> None:
        total = len(self.tracks)
        not_analyzed = sum(1 for t in self.tracks if not t.analyzed)
        lib = self.nav_buttons.get(self.NAV_LIBRARY)
        if lib:
            lib.setText(f"♫  Biblioteka ({total})")
        self.btn_tagger.setText(f"🔍  AutoTag lokalny ({not_analyzed})")

    def _on_selection_changed(self) -> None:
        row = self.table.currentRow()
        if row < 0 or row >= len(self.filtered_tracks):
            self.current_path = None
            self.now_playing.setText("Brak aktywnego utworu")
            return
        track = self.filtered_tracks[row]
        self.current_path = track.path
        self.now_playing.setText(f"{track.artist or 'Unknown'} - {track.title or track.filename}")

    def _open_in_system_player(self) -> None:
        track = self._current_track()
        if track is None:
            self.statusBar().showMessage("Najpierw wybierz utwór.", 2500)
            return
        try:
            os.startfile(track.path)  # type: ignore[attr-defined]
            self.statusBar().showMessage(f"Otwieram: {track.filename}", 3000)
        except Exception as exc:
            self.statusBar().showMessage(f"Nie udało się otworzyć pliku: {exc}", 5000)

    def _play_next(self) -> None:
        if not self.filtered_tracks:
            return
        current = self.table.currentRow()
        target = min(len(self.filtered_tracks) - 1, max(0, current + 1))
        self.table.selectRow(target)
        self._open_in_system_player()

    def _play_prev(self) -> None:
        if not self.filtered_tracks:
            return
        current = self.table.currentRow()
        target = max(0, current - 1)
        self.table.selectRow(target)
        self._open_in_system_player()

    def _run_auto_tag_selected(self) -> None:
        changed = 0
        updated: list[Track] = []
        for track in self.tracks:
            before = (track.title, track.artist, track.analyzed)
            candidate = auto_tag_from_filename(replace(track))
            after = (candidate.title, candidate.artist, candidate.analyzed)
            if before != after:
                changed += 1
                updated.append(candidate)
            else:
                updated.append(track)
        self.tracks = updated
        save_library(self.tracks)
        self._refresh_table()
        self._refresh_sidebar_counts()
        self.statusBar().showMessage(f"AutoTag zakończony. Zmieniono: {changed}", 4500)

    def _find_duplicates(self) -> None:
        by_pair: dict[tuple[str, str], list[Track]] = {}
        by_file: dict[str, list[Track]] = {}
        for track in self.tracks:
            key = (track.artist.strip().lower(), track.title.strip().lower())
            by_pair.setdefault(key, []).append(track)
            by_file.setdefault(track.filename.lower(), []).append(track)

        found: list[str] = []
        for pair, group in by_pair.items():
            if pair == ("", ""):
                continue
            if len(group) > 1:
                found.append(
                    f"[Artist+Title] {pair[0] or '?'} - {pair[1] or '?'} ({len(group)}x)"
                )
                for t in group:
                    found.append(f"   • {t.path}")
        for file_name, group in by_file.items():
            if len(group) > 1:
                found.append(f"[Filename] {file_name} ({len(group)}x)")
                for t in group:
                    found.append(f"   • {t.path}")

        self.duplicates_list.clear()
        if not found:
            self.duplicates_list.addItem("Brak wykrytych duplikatów.")
        else:
            self.duplicates_list.addItems(found)
        self._set_nav(self.NAV_DUPLICATES)

    def _rename_selected_track(self) -> None:
        track = self._current_track()
        if track is None:
            self.renamer_status.setText("Nie wybrano utworu.")
            return
        src = Path(track.path)
        if not src.exists():
            self.renamer_status.setText("Plik nie istnieje na dysku.")
            return
        artist = (track.artist or "").strip() or "Unknown Artist"
        title = (track.title or src.stem).strip()
        safe_artist = self._safe_name(artist)
        safe_title = self._safe_name(title)
        target = src.with_name(f"{safe_artist} - {safe_title}{src.suffix}")
        if target == src:
            self.renamer_status.setText("Nazwa już jest zgodna z szablonem.")
            return
        if target.exists():
            self.renamer_status.setText("Docelowa nazwa już istnieje.")
            return
        try:
            src.rename(target)
            track.path = str(target)
            save_library(self.tracks)
            self._refresh_table()
            self.renamer_status.setText(f"Zmieniono nazwę:\n{target.name}")
            self.statusBar().showMessage("Zmiana nazwy zakończona.", 3000)
        except Exception as exc:
            self.renamer_status.setText(f"Błąd zmiany nazwy: {exc}")

    def _open_settings(self) -> None:
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return
        self.settings.update(dialog.result_settings())
        save_settings(self.settings)
        self._apply_watch_settings()
        self.statusBar().showMessage("Ustawienia zapisane.", 3000)

    def _toggle_watch_folder(self) -> None:
        if self.watch_service is None:
            return
        if self.settings.get("watch_enabled", False):
            self.settings["watch_enabled"] = False
            self.watch_service.stop()
        else:
            if not self.settings.get("watch_folder"):
                self.statusBar().showMessage("Ustaw watch-folder w ustawieniach.", 3500)
                return
            self.settings["watch_enabled"] = True
            self.watch_service.start()
        save_settings(self.settings)
        self._refresh_watch_button()

    def _apply_watch_settings(self) -> None:
        self.watch_service.configure(
            str(self.settings.get("watch_folder", "")),
            int(self.settings.get("watch_interval_sec", 6)),
        )
        if self.settings.get("watch_enabled", False):
            self.watch_service.start()
        else:
            self.watch_service.stop()
        self._refresh_watch_button()

    def _refresh_watch_button(self) -> None:
        enabled = bool(self.settings.get("watch_enabled", False))
        folder = str(self.settings.get("watch_folder", "")).strip()
        if enabled:
            text = "⏸  Watch-folder: aktywny"
            if folder:
                text += f"\n{folder}"
        else:
            text = "▶  Watch-folder: start"
        self.btn_watch_toggle.setText(text)

    def _on_watch_new_files(self, new_paths: list[str]) -> None:
        incoming: list[Track] = []
        for p in new_paths:
            path = Path(p)
            if path.exists():
                track = extract_track(path, source="watch")
                if self.settings.get("auto_tag_on_import", True):
                    track = auto_tag_from_filename(track)
                incoming.append(track)
        if not incoming:
            return
        existing = {str(Path(t.path).resolve()) for t in self.tracks if t.path}
        added = 0
        for track in incoming:
            normalized = str(Path(track.path).resolve())
            if normalized in existing:
                continue
            self.tracks.append(track)
            existing.add(normalized)
            added += 1
        if added > 0:
            save_library(self.tracks)
            self._refresh_table()
            self._refresh_sidebar_counts()
            self.statusBar().showMessage(f"Watch-folder: dodano {added} plik(ów).", 4500)

    def _current_track(self) -> Track | None:
        path = self.current_path
        if not path:
            return None
        for track in self.tracks:
            if track.path == path:
                return track
        return None

    @staticmethod
    def _safe_name(value: str) -> str:
        invalid = '<>:"/\\|?*'
        result = "".join("_" if c in invalid else c for c in value)
        return " ".join(result.split())

    @staticmethod
    def _format_duration(seconds: float) -> str:
        total = int(seconds or 0)
        mm, ss = divmod(total, 60)
        return f"{mm:02d}:{ss:02d}"

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:  # noqa: N802
        save_library(self.tracks)
        save_settings(self.settings)
        self.watch_service.stop()
        super().closeEvent(event)
