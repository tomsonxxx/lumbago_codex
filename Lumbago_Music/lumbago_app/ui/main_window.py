"""
Lumbago Music AI — Główne okno aplikacji
==========================================
QMainWindow z paskiem menu, toolbarem, dokami i splitterami.
"""

import logging
import os

from PyQt6.QtCore import Qt, QSettings, QSize
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import (
    QDockWidget, QMainWindow, QSplitter,
    QStatusBar, QToolBar, QWidget, QLabel,
)

logger = logging.getLogger(__name__)

_APP_ORG = "LumbagoMusic"
_APP_NAME = "LumbagoMusicAI"


class MainWindow(QMainWindow):
    """
    Główne okno Lumbago Music AI.

    Układ:
    - Lewa kolumna: LibraryPanel (drzewo playlist + filtr)
    - Centrum: TrackTable
    - Dół: PlayerPanel (waveform + transport)
    - Prawy dok: DetailsPanel (metadane aktywnego utworu)
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Lumbago Music AI")
        self.setMinimumSize(1100, 700)

        self._settings = QSettings(_APP_ORG, _APP_NAME)
        self._build_ui()
        self._build_menu()
        self._build_toolbar()
        self._build_statusbar()
        self._restore_geometry()
        logger.info("MainWindow zainicjalizowana")

    # ------------------------------------------------------------------ #
    # Budowanie UI
    # ------------------------------------------------------------------ #

    def _build_ui(self) -> None:
        """Buduje główny układ okna z splitterem."""
        from lumbago_app.ui.panels.library_panel import LibraryPanel
        from lumbago_app.ui.panels.player_panel import PlayerPanel
        from lumbago_app.ui.panels.playlist_panel import PlaylistPanel
        from lumbago_app.ui.panels.filter_panel import FilterPanel

        # Główny splitter poziomy (lista playlist | tabela)
        h_splitter = QSplitter(Qt.Orientation.Horizontal)
        h_splitter.setHandleWidth(3)

        # Lewa strona: drzewo playlist + filtry
        left_widget = QWidget()
        from PyQt6.QtWidgets import QVBoxLayout
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        left_layout.addWidget(FilterPanel())
        left_layout.addWidget(PlaylistPanel())

        # Centrum: tabela + player (splitter pionowy)
        v_splitter = QSplitter(Qt.Orientation.Vertical)
        v_splitter.setHandleWidth(3)
        v_splitter.addWidget(LibraryPanel())
        v_splitter.addWidget(PlayerPanel())
        v_splitter.setSizes([550, 150])

        h_splitter.addWidget(left_widget)
        h_splitter.addWidget(v_splitter)
        h_splitter.setSizes([220, 880])
        h_splitter.setStretchFactor(0, 0)
        h_splitter.setStretchFactor(1, 1)

        self.setCentralWidget(h_splitter)

        # Prawy dok: Details
        self._build_details_dock()

    def _build_details_dock(self) -> None:
        """Tworzy dok z detalami aktywnego utworu."""
        from lumbago_app.ui.dialogs.details_panel import DetailsPanel

        dock = QDockWidget("Szczegóły utworu", self)
        dock.setObjectName("DetailsDock")
        dock.setAllowedAreas(
            Qt.DockWidgetArea.RightDockWidgetArea |
            Qt.DockWidgetArea.LeftDockWidgetArea
        )
        dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetClosable |
            QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        dock.setWidget(DetailsPanel())
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)

    def _build_menu(self) -> None:
        """Buduje pasek menu."""
        menubar = self.menuBar()
        if menubar is None:
            return

        # --- Plik ---
        file_menu = menubar.addMenu("&Plik")

        act_import_dir = QAction("Importuj katalog...", self)
        act_import_dir.setShortcut(QKeySequence("Ctrl+I"))
        act_import_dir.triggered.connect(self._on_import_directory)
        file_menu.addAction(act_import_dir)

        act_import_files = QAction("Importuj pliki...", self)
        act_import_files.setShortcut(QKeySequence("Ctrl+Shift+I"))
        act_import_files.triggered.connect(self._on_import_files)
        file_menu.addAction(act_import_files)

        file_menu.addSeparator()

        act_settings = QAction("Ustawienia...", self)
        act_settings.setShortcut(QKeySequence("Ctrl+,"))
        act_settings.triggered.connect(self._on_settings)
        file_menu.addAction(act_settings)

        file_menu.addSeparator()

        act_quit = QAction("Zakończ", self)
        act_quit.setShortcut(QKeySequence("Ctrl+Q"))
        act_quit.triggered.connect(self.close)
        file_menu.addAction(act_quit)

        # --- Biblioteka ---
        lib_menu = menubar.addMenu("&Biblioteka")

        act_analyze = QAction("Analizuj audio...", self)
        act_analyze.setShortcut(QKeySequence("Ctrl+A"))
        act_analyze.triggered.connect(self._on_analyze)
        lib_menu.addAction(act_analyze)

        act_tag_ai = QAction("Taguj przez AI...", self)
        act_tag_ai.setShortcut(QKeySequence("Ctrl+T"))
        act_tag_ai.triggered.connect(self._on_tag_ai)
        lib_menu.addAction(act_tag_ai)

        act_duplicates = QAction("Znajdź duplikaty...", self)
        act_duplicates.triggered.connect(self._on_find_duplicates)
        lib_menu.addAction(act_duplicates)

        lib_menu.addSeparator()

        act_backup = QAction("Utwórz backup...", self)
        act_backup.triggered.connect(self._on_backup)
        lib_menu.addAction(act_backup)

        # --- Widok ---
        view_menu = menubar.addMenu("&Widok")

        act_theme_cyber = QAction("Motyw Cyber Neon", self)
        act_theme_cyber.triggered.connect(lambda: self._set_theme("cyber_neon"))
        view_menu.addAction(act_theme_cyber)

        act_theme_fluent = QAction("Motyw Fluent Dark", self)
        act_theme_fluent.triggered.connect(lambda: self._set_theme("fluent_dark"))
        view_menu.addAction(act_theme_fluent)

        # --- Pomoc ---
        help_menu = menubar.addMenu("&Pomoc")

        act_about = QAction("O programie...", self)
        act_about.triggered.connect(self._on_about)
        help_menu.addAction(act_about)

    def _build_toolbar(self) -> None:
        """Buduje główny pasek narzędzi."""
        toolbar = QToolBar("Główne narzędzia", self)
        toolbar.setObjectName("MainToolbar")
        toolbar.setIconSize(QSize(20, 20))
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        act_import = QAction("⬆ Import", self)
        act_import.setToolTip("Importuj katalog z muzyką (Ctrl+I)")
        act_import.triggered.connect(self._on_import_directory)
        toolbar.addAction(act_import)

        toolbar.addSeparator()

        act_analyze = QAction("⚙ Analiza", self)
        act_analyze.setToolTip("Analizuj BPM i tonację wybranych utworów")
        act_analyze.triggered.connect(self._on_analyze)
        toolbar.addAction(act_analyze)

        act_tag_ai = QAction("✦ AI Tagger", self)
        act_tag_ai.setToolTip("Taguj wybrane utwory przez AI (Ctrl+T)")
        act_tag_ai.triggered.connect(self._on_tag_ai)
        toolbar.addAction(act_tag_ai)

        toolbar.addSeparator()

        act_duplicates = QAction("⊕ Duplikaty", self)
        act_duplicates.triggered.connect(self._on_find_duplicates)
        toolbar.addAction(act_duplicates)

    def _build_statusbar(self) -> None:
        """Buduje pasek statusu."""
        self._status_label = QLabel("Gotowy")
        self._status_label.setObjectName("statusLabel")
        self._track_count_label = QLabel("0 utworów")

        status = QStatusBar()
        status.addWidget(self._status_label, stretch=1)
        status.addPermanentWidget(self._track_count_label)
        self.setStatusBar(status)

    # ------------------------------------------------------------------ #
    # Obsługa akcji menu / toolbar
    # ------------------------------------------------------------------ #

    def _on_import_directory(self) -> None:
        """Otwiera wizard importu katalogu."""
        from PyQt6.QtWidgets import QFileDialog
        directory = QFileDialog.getExistingDirectory(
            self, "Wybierz katalog z muzyką"
        )
        if directory:
            from lumbago_app.ui.dialogs.import_wizard import ImportWizard
            wizard = ImportWizard(directory, parent=self)
            wizard.exec()
            self._refresh_status()

    def _on_import_files(self) -> None:
        """Otwiera dialog importu plików."""
        from PyQt6.QtWidgets import QFileDialog
        files, _ = QFileDialog.getOpenFileNames(
            self, "Wybierz pliki audio", "",
            "Audio (*.mp3 *.flac *.wav *.aiff *.ogg *.m4a *.aac);;Wszystkie (*)",
        )
        if files:
            from lumbago_app.ui.dialogs.import_wizard import ImportWizard
            wizard = ImportWizard(None, file_paths=files, parent=self)
            wizard.exec()
            self._refresh_status()

    def _on_analyze(self) -> None:
        """Uruchamia analizę audio wybranych/wszystkich utworów."""
        logger.info("Analiza audio — do implementacji w FAZIE 2")
        self._show_status("Analiza audio — wkrótce (FAZA 2)")

    def _on_tag_ai(self) -> None:
        """Otwiera dialog tagowania AI."""
        from lumbago_app.ui.dialogs.tagger_dialog import TaggerDialog
        dialog = TaggerDialog(parent=self)
        dialog.exec()

    def _on_find_duplicates(self) -> None:
        """Otwiera dialog duplikatów."""
        from lumbago_app.ui.dialogs.duplicate_dialog import DuplicateDialog
        dialog = DuplicateDialog(parent=self)
        dialog.exec()

    def _on_settings(self) -> None:
        """Otwiera panel ustawień."""
        from lumbago_app.ui.panels.settings_panel import SettingsPanel
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QDialogButtonBox
        dlg = QDialog(self)
        dlg.setWindowTitle("Ustawienia")
        dlg.resize(700, 500)
        layout = QVBoxLayout(dlg)
        layout.addWidget(SettingsPanel())
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btns.rejected.connect(dlg.close)
        layout.addWidget(btns)
        dlg.exec()

    def _on_backup(self) -> None:
        """Tworzy kopię zapasową bazy."""
        from lumbago_app.ui.dialogs.backup_dialog import BackupDialog
        dialog = BackupDialog(parent=self)
        dialog.exec()

    def _on_about(self) -> None:
        """Wyświetla okno informacyjne."""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.about(
            self,
            "O Lumbago Music AI",
            "<h2>Lumbago Music AI v1.0.0</h2>"
            "<p>DJ Library Manager z AI tagowaniem</p>"
            "<p>Obsługuje: MP3, FLAC, WAV, AIFF, OGG, M4A</p>"
            "<p>AI: OpenAI, Claude, Grok, DeepSeek, Gemini</p>",
        )

    def _set_theme(self, theme_name: str) -> None:
        """Zmienia motyw w locie."""
        from PyQt6.QtWidgets import QApplication
        from lumbago_app.ui.themes import THEMES
        qss = THEMES.get(theme_name, "")
        if qss:
            QApplication.instance().setStyleSheet(qss)  # type: ignore[union-attr]
            logger.info("Zmieniono motyw na: %s", theme_name)

    # ------------------------------------------------------------------ #
    # Pomocnicze
    # ------------------------------------------------------------------ #

    def _refresh_status(self) -> None:
        """Odświeża licznik utworów w pasku statusu."""
        try:
            from lumbago_app.data.database import session_scope
            from lumbago_app.data.repository import TrackRepository
            with session_scope() as session:
                count = TrackRepository(session).count()
            self._track_count_label.setText(f"{count:,} utworów")
        except Exception as exc:
            logger.debug("Błąd odczytu liczby utworów: %s", exc)

    def _show_status(self, message: str, timeout_ms: int = 3000) -> None:
        """Wyświetla komunikat w pasku statusu."""
        self._status_label.setText(message)
        if statusbar := self.statusBar():
            statusbar.showMessage(message, timeout_ms)

    def _restore_geometry(self) -> None:
        """Przywraca rozmiar i pozycję okna z QSettings."""
        geometry = self._settings.value("mainwindow/geometry")
        state = self._settings.value("mainwindow/state")
        if geometry:
            self.restoreGeometry(geometry)
        if state:
            self.restoreState(state)

    def closeEvent(self, event: object) -> None:
        """Zapisuje geometrię okna przed zamknięciem."""
        self._settings.setValue("mainwindow/geometry", self.saveGeometry())
        self._settings.setValue("mainwindow/state", self.saveState())
        logger.info("Okno zamknięte — geometria zapisana")
        super().closeEvent(event)  # type: ignore[arg-type]
