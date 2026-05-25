from __future__ import annotations

import csv
import shutil
import re
from datetime import datetime
from pathlib import Path

from PyQt6 import QtCore, QtGui, QtWidgets

from core.audio import file_hash
from core.models import DuplicateGroup, Track
from core.services import DuplicateResult, find_duplicates_by_tags
from data.repository import (
    delete_tracks_by_paths,
    update_track,
    update_track_paths_bulk,
    update_tracks_file_meta,
)
from services.duplicate_merge import apply_duplicate_merge_plan, build_duplicate_merge_plan
from services.recognizer import AcoustIdRecognizer
from services.track_filters import filter_group_rows
from ui.widgets import apply_dialog_fade, dialog_icon_pixmap


class DuplicateMergePreviewDialog(QtWidgets.QDialog):
    def __init__(self, plans, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Podgląd scalania metadanych")
        self.setMinimumSize(920, 560)
        apply_dialog_fade(self)
        self._plans = list(plans)
        self._build_ui()
        self._populate()

    def _build_ui(self) -> None:
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
        title = QtWidgets.QLabel(self.windowTitle())
        title.setObjectName("DialogTitle")
        title_row.addWidget(title_icon)
        title_row.addWidget(title)
        title_row.addStretch(1)
        layout.addLayout(title_row)

        self.summary_label = QtWidgets.QLabel("")
        self.summary_label.setWordWrap(True)
        layout.addWidget(self.summary_label)

        self.tree = QtWidgets.QTreeWidget()
        self.tree.setColumnCount(6)
        self.tree.setHeaderLabels(["Grupa / pole", "Źródło", "Pewność", "Stare", "Nowe", "Powód"])
        self.tree.setRootIsDecorated(True)
        self.tree.setAlternatingRowColors(True)
        self.tree.setUniformRowHeights(False)
        header = self.tree.header()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Interactive)
        header.setSectionsMovable(True)
        layout.addWidget(self.tree, 1)

        footer = QtWidgets.QHBoxLayout()
        self.select_all_btn = QtWidgets.QPushButton("Zaznacz wszystkie")
        self.select_all_btn.clicked.connect(self._select_all)
        self.select_none_btn = QtWidgets.QPushButton("Odznacz wszystkie")
        self.select_none_btn.clicked.connect(self._select_none)
        self.cancel_btn = QtWidgets.QPushButton("Anuluj")
        self.cancel_btn.clicked.connect(self.reject)
        self.apply_btn = QtWidgets.QPushButton("Zastosuj wybrane")
        self.apply_btn.clicked.connect(self.accept)
        footer.addWidget(self.select_all_btn)
        footer.addWidget(self.select_none_btn)
        footer.addStretch(1)
        footer.addWidget(self.cancel_btn)
        footer.addWidget(self.apply_btn)
        layout.addLayout(footer)

        self.tree.itemChanged.connect(self._refresh_summary)

    def _populate(self) -> None:
        self.tree.blockSignals(True)
        self.tree.clear()
        for idx, plan in enumerate(self._plans):
            survivor_name = Path(plan.survivor.path).name
            top = QtWidgets.QTreeWidgetItem(
                [
                    f"Grupa {idx + 1}: {survivor_name}",
                    "AI" if plan.ai_used else "Konsensus",
                    f"{len(plan.field_decisions)}",
                    Path(plan.survivor.path).parent.name,
                    "",
                    "zaznaczone",
                ]
            )
            top.setFlags(
                top.flags()
                | QtCore.Qt.ItemFlag.ItemIsUserCheckable
                | QtCore.Qt.ItemFlag.ItemIsEnabled
                | QtCore.Qt.ItemFlag.ItemIsSelectable
            )
            top.setCheckState(0, QtCore.Qt.CheckState.Checked)
            top.setData(0, QtCore.Qt.ItemDataRole.UserRole, idx)
            self.tree.addTopLevelItem(top)

            for decision in plan.field_decisions:
                child = QtWidgets.QTreeWidgetItem(
                    [
                        decision.field_name,
                        decision.source,
                        f"{decision.confidence:.2f}",
                        _format_preview_value(decision.current_value),
                        _format_preview_value(decision.resolved_value),
                        decision.reason,
                    ]
                )
                child.setFlags(child.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
                top.addChild(child)
            top.setExpanded(True)
        self.tree.blockSignals(False)
        self._refresh_summary()

    def _select_all(self) -> None:
        for idx in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(idx)
            item.setCheckState(0, QtCore.Qt.CheckState.Checked)
        self._refresh_summary()

    def _select_none(self) -> None:
        for idx in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(idx)
            item.setCheckState(0, QtCore.Qt.CheckState.Unchecked)
        self._refresh_summary()

    def _refresh_summary(self, *_args) -> None:
        selected = self.selected_plans()
        total_fields = sum(len(plan.field_decisions) for plan in selected)
        self.summary_label.setText(
            f"Wybrano {len(selected)} z {len(self._plans)} grup. "
            f"Podgląd pokazuje {total_fields} pól do zapisu."
        )

    def selected_plans(self):
        plans = []
        for idx in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(idx)
            if item.checkState(0) != QtCore.Qt.CheckState.Checked:
                continue
            plan_index = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
            if isinstance(plan_index, int) and 0 <= plan_index < len(self._plans):
                plans.append(self._plans[plan_index])
        return plans


class DuplicatesDialog(QtWidgets.QDialog):
    def __init__(self, tracks: list[Track], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Duplikaty")
        self.setMinimumSize(900, 520)
        apply_dialog_fade(self)
        self._tracks = tracks
        self._track_map = {track.path: track for track in tracks}
        self._scanner = None
        self._source_group_rows: list[tuple[str, list[Track]]] = []
        self._group_rows: list[tuple[str, list[Track]]] = []
        self._groups: list[list[Track]] = []
        self._show_audio_only = True
        self._hide_system_like = False
        self._excluded_roots: list[str] = []
        self._search_query: str = ""
        self._sort_column: int | None = None
        self._sort_order: QtCore.Qt.SortOrder = QtCore.Qt.SortOrder.AscendingOrder
        self._audio_only_action: QtGui.QAction | None = None
        self._system_filter_action: QtGui.QAction | None = None
        self._exclude_folders_action: QtGui.QAction | None = None
        self._clear_excluded_folders_action: QtGui.QAction | None = None
        self.system_like_check: QtWidgets.QCheckBox | None = None
        self.search_edit: QtWidgets.QLineEdit | None = None
        self.excluded_folders_label: QtWidgets.QLabel | None = None
        self.group_limit_spin: QtWidgets.QSpinBox | None = None
        self._reverse_shortcut: QtGui.QShortcut | None = None
        self._reverse_group_shortcut: QtGui.QShortcut | None = None
        self._merge_ai_action: QtGui.QAction | None = None
        self._merge_quick_action: QtGui.QAction | None = None
        self._survivor_action: QtGui.QAction | None = None
        self._merge_worker: DuplicateMergeWorker | None = None
        self._selection_shortcuts: list[QtGui.QShortcut] = []
        self._build_ui()

    def _build_ui(self) -> None:
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
        title = QtWidgets.QLabel(self.windowTitle())
        title.setObjectName("DialogTitle")
        title_row.addWidget(title_icon)
        title_row.addWidget(title)
        title_row.addStretch(1)
        layout.addLayout(title_row)

        top = QtWidgets.QHBoxLayout()
        top.setSpacing(10)
        top.addWidget(QtWidgets.QLabel("Metoda wykrywania:"))
        self.method = QtWidgets.QComboBox()
        self.method.addItems(["Hash", "Tagi", "Fingerprint", "Etapowo", "Fuzzy"])
        self.method.setToolTip("Wybierz metodę wykrywania duplikatów")
        top.addWidget(self.method)

        self.run_btn = QtWidgets.QPushButton("Szukaj")
        self.run_btn.setToolTip("Uruchom skan duplikatów")
        self.run_btn.clicked.connect(self._run_scan)
        top.addWidget(self.run_btn)

        search_label = QtWidgets.QLabel("Szukaj:")
        top.addWidget(search_label)
        self.search_edit = QtWidgets.QLineEdit()
        self.search_edit.setPlaceholderText("Tytuł, artysta, ścieżka lub grupa")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.textChanged.connect(self._set_search_query)
        top.addWidget(self.search_edit, 1)

        self.actions_btn = QtWidgets.QToolButton()
        self.actions_btn.setText("Akcje")
        self.actions_btn.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)
        self.actions_btn.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.actions_btn.setToolTip("Menu podstawowych i dodatkowych operacji")
        self.actions_btn.setMenu(self._build_actions_menu())
        top.addWidget(self.actions_btn)

        self.audio_only_check = QtWidgets.QCheckBox("Tylko audio")
        self.audio_only_check.setChecked(True)
        self.audio_only_check.setToolTip("Pokazuj wyłącznie pliki z obsługiwanymi rozszerzeniami audio")
        self.audio_only_check.toggled.connect(self._set_audio_only)
        top.addWidget(self.audio_only_check)

        self.system_like_check = QtWidgets.QCheckBox("Ukryj systemowe")
        self.system_like_check.setChecked(False)
        self.system_like_check.setToolTip(
            "Ukrywaj pliki wyglądające na systemowe, pomocnicze lub nie-muzyczne artefakty."
        )
        self.system_like_check.toggled.connect(self._set_hide_system_like)
        top.addWidget(self.system_like_check)

        self.reset_filters_btn = QtWidgets.QPushButton("Reset filtrów")
        self.reset_filters_btn.setToolTip("Przywróć domyślne filtry: tylko audio włączone, pliki systemowe ukryte wyłączone")
        self.reset_filters_btn.clicked.connect(self._reset_filters)
        top.addWidget(self.reset_filters_btn)

        top.addWidget(QtWidgets.QLabel("Limit grup:"))
        self.group_limit_spin = QtWidgets.QSpinBox()
        self.group_limit_spin.setRange(0, 5000)
        self.group_limit_spin.setSpecialValueText("bez limitu")
        self.group_limit_spin.setValue(100)
        self.group_limit_spin.setToolTip(
            "Maksymalna liczba grup przetwarzanych w jednym przebiegu. 0 oznacza brak limitu."
        )
        top.addWidget(self.group_limit_spin)
        top.addStretch(1)
        layout.addLayout(top)

        self.excluded_folders_label = QtWidgets.QLabel("")
        self.excluded_folders_label.setWordWrap(True)
        self.excluded_folders_label.setVisible(False)
        layout.addWidget(self.excluded_folders_label)

        self.tree = QtWidgets.QTreeWidget()
        self.tree.setColumnCount(7)
        self.tree.setHeaderLabels(
            ["Grupa", "Tytuł", "Artysta", "Ścieżka", "Rozmiar", "BPM", "Tonacja"]
        )
        self.tree.setRootIsDecorated(True)
        self.tree.setAlternatingRowColors(True)
        self.tree.setUniformRowHeights(True)
        header = self.tree.header()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Interactive)
        header.setSectionsMovable(True)
        header.setSortIndicatorShown(False)
        header.sectionClicked.connect(self._handle_header_click)
        header.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        header.customContextMenuRequested.connect(self._show_column_menu)
        self.tree.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_tree_context_menu)
        self.tree.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.tree.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        layout.addWidget(self.tree, 1)

        actions = QtWidgets.QHBoxLayout()
        actions.setSpacing(8)
        self.mark_btn = QtWidgets.QPushButton("Zaznacz duplikaty")
        self.mark_btn.setToolTip("Zaznacz wszystkie duplikaty, zostawiając pierwszy plik w grupie")
        self.mark_btn.clicked.connect(self._mark_duplicates)

        self.clear_btn = QtWidgets.QPushButton("Wyczyść zaznaczenie")
        self.clear_btn.setToolTip("Odznacz wszystkie pozycje")
        self.clear_btn.clicked.connect(self._clear_marks)

        self.close_btn = QtWidgets.QPushButton("Zamknij")
        self.close_btn.clicked.connect(self.reject)

        actions.addWidget(self.mark_btn)
        actions.addWidget(self.clear_btn)
        self.merge_ai_btn = QtWidgets.QPushButton("Scal metadane (AI)")
        self.merge_ai_btn.setToolTip("Zbuduj spójny zestaw tagów dla każdej grupy, używając konsensusu i AI")
        self.merge_ai_btn.clicked.connect(self._merge_metadata_with_ai)
        actions.addWidget(self.merge_ai_btn)
        self.survivor_btn = QtWidgets.QPushButton("Ocalałe...")
        self.survivor_btn.setToolTip("Przenieś lub skopiuj ocalałe pliki do wybranego katalogu")
        self.survivor_btn.clicked.connect(self._export_survivors)
        actions.addWidget(self.survivor_btn)
        self.merge_quick_btn = QtWidgets.QPushButton("Szybkie scalanie")
        self.merge_quick_btn.setToolTip("Scalanie bez AI, tylko na bazie lokalnych tagow i konsensusu")
        self.merge_quick_btn.clicked.connect(self._merge_metadata_quick)
        actions.addWidget(self.merge_quick_btn)
        actions.addStretch(1)
        actions.addWidget(self.close_btn)
        layout.addLayout(actions)

        self._reverse_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+I"), self)
        self._reverse_shortcut.setContext(QtCore.Qt.ShortcutContext.WindowShortcut)
        self._reverse_shortcut.activated.connect(self._reverse_selection)
        self._reverse_group_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Shift+I"), self)
        self._reverse_group_shortcut.setContext(QtCore.Qt.ShortcutContext.WindowShortcut)
        self._reverse_group_shortcut.activated.connect(self._reverse_group_selection)
        self._bind_selection_shortcuts()

    def _bind_selection_shortcuts(self) -> None:
        bindings = [
            ("Ctrl+Alt+N", self._select_newest_tracks),
            ("Ctrl+Alt+F", self._select_shortest_filenames),
            ("Ctrl+Alt+L", self._select_largest_tracks),
            ("Ctrl+Alt+Shift+L", self._select_smallest_tracks),
            ("Ctrl+Alt+P", self._select_highest_play_count_tracks),
            ("Ctrl+Alt+Shift+P", self._select_lowest_play_count_tracks),
            ("Ctrl+Alt+C", self._select_most_complete_tracks),
        ]
        for keyseq, callback in bindings:
            shortcut = QtGui.QShortcut(QtGui.QKeySequence(keyseq), self)
            shortcut.setContext(QtCore.Qt.ShortcutContext.WindowShortcut)
            shortcut.activated.connect(callback)
            self._selection_shortcuts.append(shortcut)

    def _build_actions_menu(self) -> QtWidgets.QMenu:
        menu = QtWidgets.QMenu(self)

        basic_menu = menu.addMenu("Podstawowe")
        basic_menu.addAction("Zaznacz duplikaty", self._mark_duplicates)
        basic_menu.addAction("Wyczyść zaznaczenie", self._clear_marks)
        basic_menu.addSeparator()
        basic_menu.addAction("Zamknij", self.reject)

        extra_menu = menu.addMenu("Dodatkowe")
        extra_menu.addAction("Odwróć zaznaczenie\tCtrl+I", self._reverse_selection)
        extra_menu.addAction("Odwroc wybor grup\tCtrl+Shift+I", self._reverse_group_selection)
        self._audio_only_action = extra_menu.addAction("Tylko audio")
        self._audio_only_action.setCheckable(True)
        self._audio_only_action.setChecked(True)
        self._audio_only_action.toggled.connect(self._set_audio_only)
        self._system_filter_action = extra_menu.addAction("Ukryj pliki systemowe")
        self._system_filter_action.setCheckable(True)
        self._system_filter_action.setChecked(False)
        self._system_filter_action.toggled.connect(self._set_hide_system_like)
        extra_menu.addSeparator()
        self._exclude_folders_action = extra_menu.addAction("Wyklucz folder...")
        self._exclude_folders_action.triggered.connect(self._add_excluded_folder)
        self._clear_excluded_folders_action = extra_menu.addAction("Wyczyść wykluczone foldery")
        self._clear_excluded_folders_action.triggered.connect(self._clear_excluded_folders)
        extra_menu.addSeparator()
        extra_menu.addAction("Przenieś zaznaczone", self._move_selected)
        extra_menu.addAction("Scal metadane", self._merge_selected)
        self._merge_ai_action = extra_menu.addAction("Scal metadane (AI)")
        self._merge_ai_action.triggered.connect(self._merge_metadata_with_ai)
        self._merge_quick_action = extra_menu.addAction("Szybkie scalanie bez AI")
        self._merge_quick_action.triggered.connect(self._merge_metadata_quick)
        extra_menu.addAction("Scal AI tylko zaznaczone grupy", self._merge_metadata_with_ai_selected)
        extra_menu.addAction("Szybkie scalanie tylko zaznaczonych", self._merge_metadata_quick_selected)
        extra_menu.addAction("Eksportuj raport", self._export_report)
        self._survivor_action = extra_menu.addAction("Wyprowadź ocalałe...")
        self._survivor_action.triggered.connect(self._export_survivors)
        select_menu = extra_menu.addMenu("Inteligentne zaznaczanie")
        select_menu.addAction("Zaznacz najnowsze", self._select_newest_tracks)
        select_menu.addAction("Odznacz najnowsze", lambda: self._select_newest_tracks(False))
        select_menu.addSeparator()
        select_menu.addAction("Zaznacz najkrótszą nazwę pliku", self._select_shortest_filenames)
        select_menu.addAction("Odznacz najkrótszą nazwę pliku", lambda: self._select_shortest_filenames(False))
        select_menu.addSeparator()
        select_menu.addAction("Zaznacz największy rozmiar", self._select_largest_tracks)
        select_menu.addAction("Odznacz największy rozmiar", lambda: self._select_largest_tracks(False))
        select_menu.addAction("Zaznacz najmniejszy rozmiar", self._select_smallest_tracks)
        select_menu.addAction("Odznacz najmniejszy rozmiar", lambda: self._select_smallest_tracks(False))
        select_menu.addSeparator()
        select_menu.addAction("Zaznacz najwyższy DJ play count", self._select_highest_play_count_tracks)
        select_menu.addAction("Odznacz najwyższy DJ play count", lambda: self._select_highest_play_count_tracks(False))
        select_menu.addAction("Zaznacz najniższy DJ play count", self._select_lowest_play_count_tracks)
        select_menu.addAction("Odznacz najniższy DJ play count", lambda: self._select_lowest_play_count_tracks(False))
        select_menu.addSeparator()
        select_menu.addAction("Zaznacz najbardziej kompletne dane", self._select_most_complete_tracks)
        select_menu.addAction("Odznacz najbardziej kompletne dane", lambda: self._select_most_complete_tracks(False))
        destructive_menu = menu.addMenu("Nieodwracalne")
        destructive_menu.setStyleSheet(
            """
            QMenu {
                background-color: #1a1013;
            }
            QMenu::item {
                color: #ff6b6b;
                padding: 6px 18px 6px 18px;
            }
            QMenu::item:selected {
                background-color: #5a1f2a;
                color: #ffecec;
            }
            """
        )
        destructive_menu.addAction("Usuń zaznaczone", self._delete_selected)
        return menu

    def _run_scan(self) -> None:
        self.tree.clear()
        self._set_source_group_rows([])
        method = self.method.currentText()

        if method == "Fuzzy":
            from services.fuzzy_dedup import FuzzyDedupService

            progress = QtWidgets.QProgressDialog(
                "Skanowanie duplikatów (fuzzy)...", None, 0, 1, self
            )
            progress.setWindowTitle("Duplikaty")
            progress.setMinimumDuration(0)
            progress.setValue(0)
            QtWidgets.QApplication.processEvents()
            svc = FuzzyDedupService()
            groups = svc.find_fuzzy_duplicates(self._tracks)
            rows = [
                (f"Grupa {group_idx}", group.tracks)
                for group_idx, group in enumerate(groups, 1)
                if len(group.tracks) > 1
            ]
            progress.setValue(1)
            progress.close()
            self._set_source_group_rows(rows)
            return

        progress = QtWidgets.QProgressDialog(
            "Skanowanie duplikatów...", "Anuluj", 0, len(self._tracks), self
        )
        progress.setWindowTitle("Duplikaty")
        progress.setMinimumDuration(0)

        self._scanner = DuplicateScanWorker(self._tracks, method)

        def on_progress(current: int, total: int) -> None:
            progress.setMaximum(total)
            progress.setValue(current)
            if progress.wasCanceled():
                self._scanner.stop()

        def on_finished(result) -> None:
            progress.close()
            rows = self._rows_from_result(result)
            self._set_source_group_rows(rows)

        self._scanner.signals.progress.connect(on_progress)
        self._scanner.signals.finished.connect(on_finished)
        QtCore.QThreadPool.globalInstance().start(self._scanner)

    def _rows_from_result(self, result) -> list[tuple[str, list[Track]]]:
        rows: list[tuple[str, list[Track]]] = []
        for group_idx, group in enumerate(result.groups, 1):
            tracks = [self._tracks[i - 1] for i in group.track_ids if 0 < i <= len(self._tracks)]
            if len(tracks) < 2:
                continue
            rows.append((f"Grupa {group_idx} (sim {group.similarity:.2f})", tracks))
        return rows

    def _show_column_menu(self, pos) -> None:
        column = self.tree.header().logicalIndexAt(pos)
        menu = QtWidgets.QMenu(self)
        show_all = menu.addAction("Pokaż wszystkie")
        hide_all = menu.addAction("Ukryj wszystkie")
        menu.addSeparator()
        if column >= 0:
            menu.addAction("Sortuj rosnąco", lambda: self._set_sorting(column, QtCore.Qt.SortOrder.AscendingOrder))
            menu.addAction("Sortuj malejąco", lambda: self._set_sorting(column, QtCore.Qt.SortOrder.DescendingOrder))
            menu.addSeparator()
        actions: list[tuple[QtWidgets.QAction, int]] = []
        for col in range(self.tree.columnCount()):
            name = self.tree.headerItem().text(col)
            action = QtWidgets.QAction(name, menu)
            action.setCheckable(True)
            action.setChecked(not self.tree.isColumnHidden(col))
            actions.append((action, col))
            menu.addAction(action)
        chosen = menu.exec(self.tree.header().mapToGlobal(pos))
        if chosen == show_all:
            for _, col in actions:
                self.tree.setColumnHidden(col, False)
            return
        if chosen == hide_all:
            self._hide_all_but_anchor([col for _, col in actions])
            return
        for action, col in actions:
            if chosen == action:
                if action.isChecked():
                    self.tree.setColumnHidden(col, False)
                else:
                    visible = sum(1 for _, c in actions if not self.tree.isColumnHidden(c))
                    if visible > 1:
                        self.tree.setColumnHidden(col, True)
                    else:
                        action.setChecked(True)
                break

    def _show_tree_context_menu(self, pos) -> None:
        item = self.tree.itemAt(pos)
        parents, files = self._context_targets_for_item(item)
        if not parents and not files:
            return

        menu = QtWidgets.QMenu(self)

        if files:
            files_menu = menu.addMenu("Pliki")
            files_menu.addAction(
                "Zaznacz plik(i)",
                lambda: self._set_items_checked(files, QtCore.Qt.CheckState.Checked),
            )
            files_menu.addAction(
                "Odznacz plik(i)",
                lambda: self._set_items_checked(files, QtCore.Qt.CheckState.Unchecked),
            )

        if parents:
            group_menu = menu.addMenu("Grupy")
            group_menu.addAction(
                "Zaznacz grupę/grupy",
                lambda: self._set_group_items_checked(parents, QtCore.Qt.CheckState.Checked),
            )
            group_menu.addAction(
                "Odznacz grupę/grupy",
                lambda: self._set_group_items_checked(parents, QtCore.Qt.CheckState.Unchecked),
            )
            group_menu.addSeparator()
            group_menu.addAction("Zaznacz duplikaty w grupie/grupach", lambda: self._mark_duplicates(parents))
            group_menu.addAction("Wyczyść zaznaczenie w grupie/grupach", lambda: self._clear_marks(parents))
            group_menu.addAction("Odwróć zaznaczenie w grupie/grupach", lambda: self._reverse_selection(parents))

            smart_menu = group_menu.addMenu("Inteligentny wybór")
            smart_menu.addAction("Najnowsze", lambda: self._select_newest_tracks_context(parents, True))
            smart_menu.addAction("Odznacz najnowsze", lambda: self._select_newest_tracks_context(parents, False))
            smart_menu.addSeparator()
            smart_menu.addAction("Najkrótsza nazwa pliku", lambda: self._select_shortest_filenames_context(parents, True))
            smart_menu.addAction("Odznacz najkrótszą nazwę", lambda: self._select_shortest_filenames_context(parents, False))
            smart_menu.addSeparator()
            smart_menu.addAction("Największy rozmiar", lambda: self._select_largest_tracks_context(parents, True))
            smart_menu.addAction("Odznacz największy rozmiar", lambda: self._select_largest_tracks_context(parents, False))
            smart_menu.addAction("Najmniejszy rozmiar", lambda: self._select_smallest_tracks_context(parents, True))
            smart_menu.addAction("Odznacz najmniejszy rozmiar", lambda: self._select_smallest_tracks_context(parents, False))
            smart_menu.addAction("Najwyższy DJ play count", lambda: self._select_highest_play_count_context(parents, True))
            smart_menu.addAction("Odznacz najwyższy DJ play count", lambda: self._select_highest_play_count_context(parents, False))
            smart_menu.addAction("Najniższy DJ play count", lambda: self._select_lowest_play_count_context(parents, True))
            smart_menu.addAction("Odznacz najniższy DJ play count", lambda: self._select_lowest_play_count_context(parents, False))
            smart_menu.addSeparator()
            smart_menu.addAction("Najbardziej kompletne dane", lambda: self._select_most_complete_context(parents, True))
            smart_menu.addAction("Odznacz najbardziej kompletne dane", lambda: self._select_most_complete_context(parents, False))

        actions_menu = menu.addMenu("Akcje")
        context_paths = self._context_paths_for_items(files or self._all_child_items(parents))
        actions_menu.addAction("Przenieś zaznaczone", lambda: self._move_paths(context_paths))
        actions_menu.addAction("Usuń zaznaczone", lambda: self._delete_paths(context_paths))
        actions_menu.addSeparator()
        actions_menu.addAction("Scal metadane lokalnie", lambda: self._merge_context_groups(parents, use_ai=False))
        actions_menu.addAction("Szybkie scalanie bez AI", lambda: self._merge_context_groups(parents, use_ai=False))
        actions_menu.addAction("Scal metadane (AI)", lambda: self._merge_context_groups(parents, use_ai=True))
        actions_menu.addAction("Ocalałe...", self._export_survivors)

        menu.exec(self.tree.viewport().mapToGlobal(pos))

    def _handle_header_click(self, column: int) -> None:
        if self._sort_column == column:
            self._sort_order = (
                QtCore.Qt.SortOrder.DescendingOrder
                if self._sort_order == QtCore.Qt.SortOrder.AscendingOrder
                else QtCore.Qt.SortOrder.AscendingOrder
            )
        else:
            self._sort_column = column
            self._sort_order = QtCore.Qt.SortOrder.AscendingOrder
        self._set_sorting(self._sort_column, self._sort_order)

    def _set_sorting(self, column: int | None, order: QtCore.Qt.SortOrder) -> None:
        self._sort_column = column
        self._sort_order = order
        header = self.tree.header()
        if column is not None:
            header.setSortIndicatorShown(True)
            header.setSortIndicator(column, order)
        self._apply_view_filters()

    def _hide_all_but_anchor(self, columns: list[int]) -> None:
        if not columns:
            return
        anchor = columns[0]
        for col in columns:
            self.tree.setColumnHidden(col, col != anchor)

    def _set_source_group_rows(self, rows: list[tuple[str, list[Track]]]) -> None:
        self._source_group_rows = [(label, tracks) for label, tracks in rows if len(tracks) > 1]
        self._apply_view_filters()

    def _apply_view_filters(self) -> None:
        rows = filter_group_rows(
            self._source_group_rows,
            audio_only=self._show_audio_only,
            hide_system_like=self._hide_system_like,
            excluded_roots=self._excluded_roots,
        )
        query = self._search_query.strip().casefold()
        if query:
            rows = [(label, tracks) for label, tracks in rows if self._row_matches_query(label, tracks, query)]
        self._group_rows = rows
        self._groups = [tracks for _, tracks in self._group_rows]
        self._refresh_excluded_folder_label()
        self._rebuild_tree()

    def _set_audio_only(self, enabled: bool) -> None:
        self._show_audio_only = bool(enabled)
        if hasattr(self, "audio_only_check") and self.audio_only_check.isChecked() != self._show_audio_only:
            self.audio_only_check.blockSignals(True)
            self.audio_only_check.setChecked(self._show_audio_only)
            self.audio_only_check.blockSignals(False)
        if self._audio_only_action is not None and self._audio_only_action.isChecked() != self._show_audio_only:
            self._audio_only_action.blockSignals(True)
            self._audio_only_action.setChecked(self._show_audio_only)
            self._audio_only_action.blockSignals(False)
        self._apply_view_filters()

    def _set_hide_system_like(self, enabled: bool) -> None:
        self._hide_system_like = bool(enabled)
        if self.system_like_check is not None and self.system_like_check.isChecked() != self._hide_system_like:
            self.system_like_check.blockSignals(True)
            self.system_like_check.setChecked(self._hide_system_like)
            self.system_like_check.blockSignals(False)
        if self._system_filter_action is not None and self._system_filter_action.isChecked() != self._hide_system_like:
            self._system_filter_action.blockSignals(True)
            self._system_filter_action.setChecked(self._hide_system_like)
            self._system_filter_action.blockSignals(False)
        self._apply_view_filters()

    def _set_search_query(self, text: str) -> None:
        self._search_query = text or ""
        self._apply_view_filters()

    def _reset_filters(self) -> None:
        self._set_audio_only(True)
        self._set_hide_system_like(False)
        self._search_query = ""
        if self.search_edit is not None and self.search_edit.text():
            self.search_edit.blockSignals(True)
            self.search_edit.clear()
            self.search_edit.blockSignals(False)
        if self.system_like_check is not None and self.system_like_check.isChecked():
            self.system_like_check.blockSignals(True)
            self.system_like_check.setChecked(False)
            self.system_like_check.blockSignals(False)
        self._clear_excluded_folders()

    def _add_excluded_folder(self) -> None:
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Wybierz folder do wykluczenia")
        if not folder:
            return
        normalized = str(Path(folder))
        if normalized not in self._excluded_roots:
            self._excluded_roots.append(normalized)
            self._excluded_roots.sort(key=str.lower)
        self._apply_view_filters()

    def _clear_excluded_folders(self) -> None:
        self._excluded_roots = []
        self._apply_view_filters()

    def _refresh_excluded_folder_label(self) -> None:
        if self.excluded_folders_label is None:
            return
        if not self._excluded_roots:
            self.excluded_folders_label.clear()
            self.excluded_folders_label.setVisible(False)
            return
        names = ", ".join(Path(root).name or root for root in self._excluded_roots[:4])
        if len(self._excluded_roots) > 4:
            names += f" +{len(self._excluded_roots) - 4}"
        self.excluded_folders_label.setText(f"Wykluczone foldery: {names}")
        self.excluded_folders_label.setVisible(True)

    def _selected_group_labels(self) -> list[str]:
        labels: list[str] = []
        seen: set[str] = set()
        for item in self.tree.selectedItems():
            parent = item.parent() or item
            label = parent.text(0)
            if label and label not in seen:
                seen.add(label)
                labels.append(label)
        return labels

    def _row_matches_query(self, label: str, tracks: list[Track], query: str) -> bool:
        if not query:
            return True
        if query in label.casefold():
            return True
        for track in tracks:
            values = [
                track.title,
                track.artist,
                track.album,
                track.albumartist,
                track.genre,
                track.comment,
                track.path,
                Path(track.path).name,
            ]
            for value in values:
                if value and query in str(value).casefold():
                    return True
        return False

    def _resolve_merge_groups(self, *, only_selected: bool) -> list[tuple[str, list[Track]]]:
        groups = list(self._group_rows)
        if only_selected:
            selected = set(self._selected_group_labels())
            groups = [row for row in groups if row[0] in selected]
        limit = self.group_limit_spin.value() if self.group_limit_spin is not None else 0
        if limit > 0:
            groups = groups[:limit]
        return groups

    def _reverse_group_selection(self) -> None:
        selected = set(self._selected_group_labels())
        self.tree.blockSignals(True)
        self.tree.clearSelection()
        for idx in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(idx)
            if item.text(0) not in selected:
                item.setSelected(True)
        self.tree.blockSignals(False)

    def _merge_metadata_quick(self) -> None:
        self._start_merge_flow(use_ai=False, only_selected=False)

    def _merge_metadata_quick_selected(self) -> None:
        self._start_merge_flow(use_ai=False, only_selected=True)

    def _merge_metadata_with_ai_selected(self) -> None:
        self._start_merge_flow(use_ai=True, only_selected=True)

    def _merge_metadata_with_ai(self) -> None:
        self._start_merge_flow(use_ai=True, only_selected=False)

    def _start_merge_flow(self, *, use_ai: bool, only_selected: bool) -> None:
        if self._merge_worker is not None:
            QtWidgets.QMessageBox.information(
                self,
                "Scal metadane (AI)",
                "Przygotowywanie konsensusu juz trwa.",
            )
            return

        groups = self._resolve_merge_groups(only_selected=only_selected)
        if not groups:
            message = (
                "Nie zaznaczono zadnych grup do scalenia."
                if only_selected
                else "Brak grup do scalenia."
            )
            QtWidgets.QMessageBox.information(self, "Scal metadane (AI)", message)
            return

        try:
            from core.config import load_settings

            settings = load_settings()
        except Exception:
            settings = None

        self._start_merge_worker(groups, settings, use_ai=use_ai)
        return

        progress = QtWidgets.QProgressDialog("Przygotowywanie konsensusu AI...", "Anuluj", 0, len(groups), self)
        progress.setWindowTitle("Scal metadane (AI)")
        progress.setMinimumDuration(0)

        plans = []
        for idx, (_, tracks) in enumerate(groups, 1):
            if progress.wasCanceled():
                break
            plan = build_duplicate_merge_plan(tracks, settings=settings, use_ai=True)
            if plan is not None and plan.changed_fields:
                plans.append(plan)
            progress.setValue(idx)
            QtWidgets.QApplication.processEvents()
        progress.close()

        if not plans:
            QtWidgets.QMessageBox.information(
                self,
                "Scal metadane (AI)",
                "Silnik nie znalazł niczego do poprawy w aktualnym zestawie duplikatów.",
            )
            return

        preview = DuplicateMergePreviewDialog(plans, self)
        if preview.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return

        selected_plans = preview.selected_plans()
        if not selected_plans:
            QtWidgets.QMessageBox.information(
                self,
                "Scal metadane (AI)",
                "Nie zaznaczono żadnych grup do zapisu.",
            )
            return

        changed_tracks = 0
        changed_fields = 0
        for plan in selected_plans:
            applied = apply_duplicate_merge_plan(plan)
            if applied:
                changed_tracks += 1
                changed_fields += len(applied)
        if changed_tracks:
            self._apply_view_filters()
            QtWidgets.QMessageBox.information(
                self,
                "Scal metadane (AI)",
                f"Zaktualizowano {changed_fields} pól w {changed_tracks} grupach.",
            )

    def _start_merge_worker(self, groups: list[tuple[str, list[Track]]], settings, *, use_ai: bool) -> None:
        progress = QtWidgets.QProgressDialog(
            "Przygotowywanie konsensusu AI...", "Anuluj", 0, len(groups), self
        )
        progress.setWindowTitle("Scal metadane")
        progress.setMinimumDuration(0)
        progress.setWindowModality(QtCore.Qt.WindowModality.WindowModal)

        self._set_merge_actions_enabled(False)
        self._merge_worker = DuplicateMergeWorker(groups, settings=settings, use_ai=use_ai)

        def on_progress(current: int, total: int, label: str) -> None:
            progress.setMaximum(total)
            progress.setValue(current)
            if label:
                progress.setLabelText(label)

        def on_failed(message: str) -> None:
            progress.close()
            self._merge_worker = None
            self._set_merge_actions_enabled(True)
            QtWidgets.QMessageBox.warning(self, "Scal metadane (AI)", message)

        def on_finished(plans: list) -> None:
            progress.close()
            self._merge_worker = None
            self._set_merge_actions_enabled(True)
            self._show_merge_preview(plans)

        progress.canceled.connect(self._merge_worker.stop)
        self._merge_worker.signals.progress.connect(on_progress)
        self._merge_worker.signals.failed.connect(on_failed)
        self._merge_worker.signals.finished.connect(on_finished)
        QtCore.QThreadPool.globalInstance().start(self._merge_worker)

    def _show_merge_preview(self, plans: list) -> None:
        if not plans:
            QtWidgets.QMessageBox.information(
                self,
                "Scal metadane (AI)",
                "Silnik nie znalazl niczego do poprawy w aktualnym zestawie duplikatow.",
            )
            return

        preview = DuplicateMergePreviewDialog(plans, self)
        if preview.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return

        selected_plans = preview.selected_plans()
        if not selected_plans:
            QtWidgets.QMessageBox.information(
                self,
                "Scal metadane (AI)",
                "Nie zaznaczono zadnych grup do zapisu.",
            )
            return

        changed_tracks = 0
        changed_fields = 0
        for plan in selected_plans:
            applied = apply_duplicate_merge_plan(plan)
            if applied:
                changed_tracks += 1
                changed_fields += len(applied)
        if changed_tracks:
            self._apply_view_filters()
            QtWidgets.QMessageBox.information(
                self,
                "Scal metadane (AI)",
                f"Zaktualizowano {changed_fields} pol w {changed_tracks} grupach.",
            )

    def _set_merge_actions_enabled(self, enabled: bool) -> None:
        self.merge_ai_btn.setEnabled(enabled)
        self.merge_quick_btn.setEnabled(enabled)
        if self._merge_ai_action is not None:
            self._merge_ai_action.setEnabled(enabled)
        if self._merge_quick_action is not None:
            self._merge_quick_action.setEnabled(enabled)

    def _export_survivors(self) -> None:
        survivors = self._survivor_tracks()
        if not survivors:
            QtWidgets.QMessageBox.information(
                self,
                "Ocalałe pliki",
                "Nie znaleziono żadnych ocalałych plików do wyprowadzenia.",
            )
            return

        target_dir = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Wybierz katalog dla ocalałych plików",
        )
        if not target_dir:
            return

        mode, ok = QtWidgets.QInputDialog.getItem(
            self,
            "Ocalałe pliki",
            "Co zrobić z ocalałymi plikami?",
            ["Skopiuj", "Przenieś"],
            0,
            False,
        )
        if not ok:
            return

        dest_root = Path(target_dir)
        history: list[dict[str, str]] = []
        copied = 0
        moved = 0
        for group_label, track in survivors:
            src = Path(track.path)
            if not src.exists():
                continue
            dest_dir = dest_root / _safe_folder_name(group_label)
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = dest_dir / src.name
            if dest.exists():
                dest = dest_dir / f"survivor_{src.name}"
            if mode == "Przenieś":
                shutil.move(str(src), str(dest))
                history.append({"old": str(src), "new": str(dest)})
                moved += 1
            else:
                shutil.copy2(str(src), str(dest))
                copied += 1

        if history:
            update_track_paths_bulk(history)
            self._apply_view_filters()

        QtWidgets.QMessageBox.information(
            self,
            "Ocalałe pliki",
            f"{'Przeniesiono' if mode == 'Przenieś' else 'Skopiowano'} "
            f"{moved if mode == 'Przenieś' else copied} plików do: {dest_root}",
        )

    def _survivor_tracks(self) -> list[tuple[str, Track]]:
        survivors: list[tuple[str, Track]] = []
        for row_idx in range(self.tree.topLevelItemCount()):
            parent = self.tree.topLevelItem(row_idx)
            if parent is None or parent.childCount() == 0:
                continue
            survivor_child = next(
                (
                    parent.child(idx)
                    for idx in range(parent.childCount())
                    if parent.child(idx).checkState(0) != QtCore.Qt.CheckState.Checked
                ),
                parent.child(0),
            )
            survivor_path = survivor_child.data(0, QtCore.Qt.ItemDataRole.UserRole)
            if not survivor_path:
                continue
            track = self._track_map.get(survivor_path)
            if track is None:
                continue
            survivors.append((parent.text(0), track))
        return survivors

    def _rebuild_tree(self) -> None:
        self.tree.clear()
        rows = self._sorted_group_rows(self._group_rows)
        for label, tracks in rows:
            parent = QtWidgets.QTreeWidgetItem([label])
            parent.setFirstColumnSpanned(True)
            self.tree.addTopLevelItem(parent)
            for track in self._sorted_tracks(tracks):
                size = track.file_size or _safe_size(track.path)
                item = QtWidgets.QTreeWidgetItem(
                    [
                        "",
                        track.title or "",
                        track.artist or "",
                        track.path,
                        f"{size or ''}",
                        f"{track.bpm or ''}",
                        track.key or "",
                    ]
                )
                item.setCheckState(0, QtCore.Qt.CheckState.Unchecked)
                item.setData(0, QtCore.Qt.ItemDataRole.UserRole, track.path)
                parent.addChild(item)
            parent.setExpanded(True)

    def _sorted_group_rows(self, rows: list[tuple[str, list[Track]]]) -> list[tuple[str, list[Track]]]:
        if self._sort_column is None:
            return list(rows)
        return sorted(
            rows,
            key=lambda row: self._group_sort_key(row[0], row[1], self._sort_column),
        )

    def _sorted_tracks(self, tracks: list[Track]) -> list[Track]:
        if self._sort_column is None:
            return list(tracks)
        return sorted(
            tracks,
            key=lambda track: self._track_sort_key(track, self._sort_column),
        )

    def _group_sort_key(self, label: str, tracks: list[Track], column: int):
        if column == 0:
            return self._text_sort_key(label)
        track = self._representative_track(tracks)
        return self._track_sort_key(track, column)

    def _representative_track(self, tracks: list[Track]) -> Track:
        for track in tracks:
            if track:
                return track
        return Track(path="")

    def _track_sort_key(self, track: Track, column: int):
        if column == 0:
            return self._text_sort_key(Path(track.path).name)
        if column == 1:
            return self._text_sort_key(track.title or "")
        if column == 2:
            return self._text_sort_key(track.artist or "")
        if column == 3:
            return self._text_sort_key(track.path or "")
        if column == 4:
            size = track.file_size if isinstance(track.file_size, int) else _safe_size(track.path)
            return self._numeric_sort_key(size)
        if column == 5:
            bpm = track.bpm if isinstance(track.bpm, (int, float)) else None
            return self._numeric_sort_key(bpm)
        if column == 6:
            return self._text_sort_key(track.key or "")
        return self._text_sort_key(track.path or "")

    def _text_sort_key(self, value: str):
        text = (value or "").casefold()
        if self._sort_order == QtCore.Qt.SortOrder.DescendingOrder:
            return (text == "", tuple(-ord(ch) for ch in text))
        return (text == "", text)

    def _numeric_sort_key(self, value: int | float | None):
        if value is None:
            return (1, 0)
        adjusted = -float(value) if self._sort_order == QtCore.Qt.SortOrder.DescendingOrder else float(value)
        return (0, adjusted)

    def _mark_duplicates(self, parents: list[QtWidgets.QTreeWidgetItem] | None = None) -> None:
        targets = parents or [self.tree.topLevelItem(i) for i in range(self.tree.topLevelItemCount())]
        for parent in targets:
            if parent.childCount() <= 1:
                continue
            parent.child(0).setCheckState(0, QtCore.Qt.CheckState.Unchecked)
            for idx in range(1, parent.childCount()):
                parent.child(idx).setCheckState(0, QtCore.Qt.CheckState.Checked)

    def _select_newest_tracks(self, checked: bool = True) -> None:
        self._select_best_track(
            checked=checked,
            score_fn=lambda track: (
                track.file_mtime if isinstance(track.file_mtime, (int, float)) else 0.0,
                track.date_modified.timestamp() if getattr(track, "date_modified", None) else 0.0,
            ),
        )

    def _select_newest_tracks_context(self, parents: list[QtWidgets.QTreeWidgetItem], checked: bool = True) -> None:
        self._select_best_track(
            checked=checked,
            parents=parents,
            score_fn=lambda track: (
                track.file_mtime if isinstance(track.file_mtime, (int, float)) else 0.0,
                track.date_modified.timestamp() if getattr(track, "date_modified", None) else 0.0,
            ),
        )

    def _select_shortest_filenames(self, checked: bool = True) -> None:
        self._select_best_track(
            checked=checked,
            score_fn=lambda track: (-len(Path(track.path).name), -(len(track.path))),
        )

    def _select_shortest_filenames_context(
        self,
        parents: list[QtWidgets.QTreeWidgetItem],
        checked: bool = True,
    ) -> None:
        self._select_best_track(
            checked=checked,
            parents=parents,
            score_fn=lambda track: (-len(Path(track.path).name), -(len(track.path))),
        )

    def _select_largest_tracks(self, checked: bool = True) -> None:
        self._select_best_track(
            checked=checked,
            score_fn=lambda track: (
                track.file_size if isinstance(track.file_size, int) else _safe_size(track.path) or -1,
                track.file_mtime if isinstance(track.file_mtime, (int, float)) else 0.0,
            ),
        )

    def _select_largest_tracks_context(self, parents: list[QtWidgets.QTreeWidgetItem], checked: bool = True) -> None:
        self._select_best_track(
            checked=checked,
            parents=parents,
            score_fn=lambda track: (
                track.file_size if isinstance(track.file_size, int) else _safe_size(track.path) or -1,
                track.file_mtime if isinstance(track.file_mtime, (int, float)) else 0.0,
            ),
        )

    def _select_smallest_tracks(self, checked: bool = True) -> None:
        self._select_best_track(
            checked=checked,
            score_fn=lambda track: (
                -1 * (track.file_size if isinstance(track.file_size, int) else _safe_size(track.path) or -1),
                track.file_mtime if isinstance(track.file_mtime, (int, float)) else 0.0,
            ),
        )

    def _select_smallest_tracks_context(self, parents: list[QtWidgets.QTreeWidgetItem], checked: bool = True) -> None:
        self._select_best_track(
            checked=checked,
            parents=parents,
            score_fn=lambda track: (
                -1 * (track.file_size if isinstance(track.file_size, int) else _safe_size(track.path) or -1),
                track.file_mtime if isinstance(track.file_mtime, (int, float)) else 0.0,
            ),
        )

    def _select_highest_play_count_tracks(self, checked: bool = True) -> None:
        self._select_best_track(
            checked=checked,
            score_fn=lambda track: (
                track.play_count if isinstance(track.play_count, int) else 0,
                track.file_mtime if isinstance(track.file_mtime, (int, float)) else 0.0,
            ),
        )

    def _select_highest_play_count_tracks_context(
        self,
        parents: list[QtWidgets.QTreeWidgetItem],
        checked: bool = True,
    ) -> None:
        self._select_best_track(
            checked=checked,
            parents=parents,
            score_fn=lambda track: (
                track.play_count if isinstance(track.play_count, int) else 0,
                track.file_mtime if isinstance(track.file_mtime, (int, float)) else 0.0,
            ),
        )

    def _select_lowest_play_count_tracks(self, checked: bool = True) -> None:
        self._select_best_track(
            checked=checked,
            score_fn=lambda track: (
                -1 * (track.play_count if isinstance(track.play_count, int) else 0),
                track.file_mtime if isinstance(track.file_mtime, (int, float)) else 0.0,
            ),
        )

    def _select_lowest_play_count_tracks_context(
        self,
        parents: list[QtWidgets.QTreeWidgetItem],
        checked: bool = True,
    ) -> None:
        self._select_best_track(
            checked=checked,
            parents=parents,
            score_fn=lambda track: (
                -1 * (track.play_count if isinstance(track.play_count, int) else 0),
                track.file_mtime if isinstance(track.file_mtime, (int, float)) else 0.0,
            ),
        )

    def _select_most_complete_tracks(self, checked: bool = True) -> None:
        self._select_best_track(
            checked=checked,
            score_fn=lambda track: self._track_completeness_score(track),
        )

    def _select_most_complete_context(
        self,
        parents: list[QtWidgets.QTreeWidgetItem],
        checked: bool = True,
    ) -> None:
        self._select_best_track(
            checked=checked,
            parents=parents,
            score_fn=lambda track: self._track_completeness_score(track),
        )

    def _select_best_track(
        self,
        *,
        checked: bool,
        score_fn,
        parents: list[QtWidgets.QTreeWidgetItem] | None = None,
    ) -> None:
        targets = parents or [self.tree.topLevelItem(i) for i in range(self.tree.topLevelItemCount())]
        for parent in targets:
            if parent.childCount() < 1:
                continue
            best_child = None
            best_score = None
            for idx in range(parent.childCount()):
                child = parent.child(idx)
                track = self._track_map.get(child.data(0, QtCore.Qt.ItemDataRole.UserRole))
                if track is None:
                    continue
                score = score_fn(track)
                if best_score is None or score > best_score:
                    best_score = score
                    best_child = child
            if best_child is not None:
                if checked:
                    for idx in range(parent.childCount()):
                        parent.child(idx).setCheckState(0, QtCore.Qt.CheckState.Unchecked)
                    best_child.setCheckState(0, QtCore.Qt.CheckState.Checked)
                else:
                    best_child.setCheckState(0, QtCore.Qt.CheckState.Unchecked)

    def _reverse_selection(self, parents: list[QtWidgets.QTreeWidgetItem] | None = None) -> None:
        targets = parents or [self.tree.topLevelItem(i) for i in range(self.tree.topLevelItemCount())]
        for parent in targets:
            for idx in range(parent.childCount()):
                child = parent.child(idx)
                current = child.checkState(0)
                child.setCheckState(
                    0,
                    QtCore.Qt.CheckState.Unchecked
                    if current == QtCore.Qt.CheckState.Checked
                    else QtCore.Qt.CheckState.Checked,
                )

    def _clear_marks(self, parents: list[QtWidgets.QTreeWidgetItem] | None = None) -> None:
        targets = parents or [self.tree.topLevelItem(i) for i in range(self.tree.topLevelItemCount())]
        for parent in targets:
            for idx in range(parent.childCount()):
                parent.child(idx).setCheckState(0, QtCore.Qt.CheckState.Unchecked)

    def _track_completeness_score(self, track: Track) -> tuple[int, int, int, int]:
        fields = [
            track.title,
            track.artist,
            track.album,
            track.albumartist,
            track.year,
            track.genre,
            track.tracknumber,
            track.discnumber,
            track.composer,
            track.comment,
            track.lyrics,
            track.originalartist,
            track.isrc,
            track.publisher,
            track.grouping,
            track.copyright,
            track.remixer,
            track.key,
            track.mood,
        ]
        score = 0
        for value in fields:
            if value:
                score += 2
        if track.bpm is not None:
            score += 2
        if track.duration is not None:
            score += 2
        if track.file_size is not None:
            score += 1
        if track.file_hash:
            score += 2
        if track.fingerprint:
            score += 2
        if track.waveform_path:
            score += 1
        if track.artwork_path:
            score += 1
        if track.bitrate is not None:
            score += 1
        if track.sample_rate is not None:
            score += 1
        completeness_bonus = sum(1 for value in [track.title, track.artist, track.album] if value)
        recent_bonus = int(track.file_mtime or 0)
        size_bonus = int(track.file_size or 0)
        return score, completeness_bonus, recent_bonus, size_bonus

    def _selected_paths(self) -> list[str]:
        paths: list[str] = []
        for i in range(self.tree.topLevelItemCount()):
            parent = self.tree.topLevelItem(i)
            for idx in range(parent.childCount()):
                child = parent.child(idx)
                if child.checkState(0) != QtCore.Qt.CheckState.Checked:
                    continue
                path = child.data(0, QtCore.Qt.ItemDataRole.UserRole)
                if path:
                    paths.append(path)
        return paths

    def _context_targets_for_item(
        self, item: QtWidgets.QTreeWidgetItem | None
    ) -> tuple[list[QtWidgets.QTreeWidgetItem], list[QtWidgets.QTreeWidgetItem]]:
        selected = self.tree.selectedItems()
        if item is None:
            parents = [it for it in selected if it.parent() is None]
            files = [it for it in selected if it.parent() is not None]
            return self._unique_items(parents), self._unique_items(files)

        if item.parent() is None:
            if item in selected:
                parents = [it for it in selected if it.parent() is None] or [item]
            else:
                parents = [item]
            files = self._all_child_items(parents)
            return self._unique_items(parents), self._unique_items(files)

        parent = item.parent()
        if item in selected:
            files = [it for it in selected if it.parent() == parent]
            if not files:
                files = [item]
        else:
            files = [item]
        return [parent], self._unique_items(files)

    def _all_child_items(self, parents: list[QtWidgets.QTreeWidgetItem]) -> list[QtWidgets.QTreeWidgetItem]:
        children: list[QtWidgets.QTreeWidgetItem] = []
        for parent in parents:
            for idx in range(parent.childCount()):
                children.append(parent.child(idx))
        return self._unique_items(children)

    def _context_paths_for_items(self, items: list[QtWidgets.QTreeWidgetItem]) -> list[str]:
        paths: list[str] = []
        for item in items:
            path = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
            if path and path not in paths:
                paths.append(path)
        return paths

    def _set_items_checked(
        self,
        items: list[QtWidgets.QTreeWidgetItem],
        state: QtCore.Qt.CheckState,
    ) -> None:
        for item in items:
            item.setCheckState(0, state)

    def _set_group_items_checked(
        self,
        parents: list[QtWidgets.QTreeWidgetItem],
        state: QtCore.Qt.CheckState,
    ) -> None:
        for parent in parents:
            for idx in range(parent.childCount()):
                parent.child(idx).setCheckState(0, state)

    def _merge_context_groups(self, parents: list[QtWidgets.QTreeWidgetItem], *, use_ai: bool) -> None:
        if not parents:
            return
        groups = [
            (
                parent.text(0),
                [
                    track
                    for item in self._group_child_items(parent)
                    if (track := self._track_map.get(item.data(0, QtCore.Qt.ItemDataRole.UserRole))) is not None
                ],
            )
            for parent in parents
        ]
        groups = [(label, tracks) for label, tracks in groups if len(tracks) > 1]
        if not groups:
            return
        try:
            from core.config import load_settings

            settings = load_settings()
        except Exception:
            settings = None
        self._start_merge_worker(groups, settings, use_ai=use_ai)

    def _group_child_items(self, parent: QtWidgets.QTreeWidgetItem) -> list[QtWidgets.QTreeWidgetItem]:
        return [parent.child(idx) for idx in range(parent.childCount())]

    def _unique_items(self, items: list[QtWidgets.QTreeWidgetItem]) -> list[QtWidgets.QTreeWidgetItem]:
        unique: list[QtWidgets.QTreeWidgetItem] = []
        seen: set[int] = set()
        for item in items:
            key = id(item)
            if key in seen:
                continue
            seen.add(key)
            unique.append(item)
        return unique

    def _move_selected(self) -> None:
        paths = self._selected_paths()
        if not paths:
            return
        target_dir = QtWidgets.QFileDialog.getExistingDirectory(self, "Wybierz folder docelowy")
        if not target_dir:
            return
        history: list[dict[str, str]] = []
        for path in paths:
            src = Path(path)
            if not src.exists():
                continue
            dest = Path(target_dir) / src.name
            if dest.exists():
                dest = Path(target_dir) / f"dup_{src.name}"
            shutil.move(str(src), str(dest))
            history.append({"old": str(src), "new": str(dest)})
        if history:
            update_track_paths_bulk(history)
            self.accept()

    def _move_paths(self, paths: list[str]) -> None:
        if not paths:
            return
        target_dir = QtWidgets.QFileDialog.getExistingDirectory(self, "Wybierz folder docelowy")
        if not target_dir:
            return
        history: list[dict[str, str]] = []
        for path in paths:
            src = Path(path)
            if not src.exists():
                continue
            dest = Path(target_dir) / src.name
            if dest.exists():
                dest = Path(target_dir) / f"dup_{src.name}"
            shutil.move(str(src), str(dest))
            history.append({"old": str(src), "new": str(dest)})
        if history:
            update_track_paths_bulk(history)
            self._apply_view_filters()

    def _delete_paths(self, paths: list[str]) -> None:
        if not paths:
            return
        confirm = QtWidgets.QMessageBox.question(
            self,
            "Potwierdzenie",
            "Czy na pewno usunąć zaznaczone pliki z dysku i bazy?",
        )
        if confirm != QtWidgets.QMessageBox.StandardButton.Yes:
            return
        for path in paths:
            try:
                Path(path).unlink(missing_ok=True)
            except Exception:
                continue
        delete_tracks_by_paths(paths)
        self._apply_view_filters()

    def _delete_selected(self) -> None:
        paths = self._selected_paths()
        if not paths:
            return
        confirm = QtWidgets.QMessageBox.question(
            self,
            "Potwierdzenie",
            "Czy na pewno usunąć zaznaczone pliki z dysku i bazy?",
        )
        if confirm != QtWidgets.QMessageBox.StandardButton.Yes:
            return
        for path in paths:
            try:
                Path(path).unlink(missing_ok=True)
            except Exception:
                continue
        delete_tracks_by_paths(paths)
        self.accept()

    def _export_report(self) -> None:
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Zapisz raport CSV",
            "",
            "CSV (*.csv)",
        )
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["group", "title", "artist", "path", "size", "bpm", "key"])
            for i in range(self.tree.topLevelItemCount()):
                parent = self.tree.topLevelItem(i)
                for idx in range(parent.childCount()):
                    child = parent.child(idx)
                    writer.writerow(
                        [
                            parent.text(0),
                            child.text(1),
                            child.text(2),
                            child.text(3),
                            child.text(4),
                            child.text(5),
                            child.text(6),
                        ]
                    )

    def _merge_selected(self) -> None:
        changed = False
        for i in range(self.tree.topLevelItemCount()):
            parent = self.tree.topLevelItem(i)
            if parent.childCount() < 2:
                continue
            master_item = parent.child(0)
            master_path = master_item.data(0, QtCore.Qt.ItemDataRole.UserRole)
            if not master_path:
                continue
            master_track = self._track_map.get(master_path)
            if not master_track:
                continue
            for idx in range(1, parent.childCount()):
                child = parent.child(idx)
                if child.checkState(0) != QtCore.Qt.CheckState.Checked:
                    continue
                child_path = child.data(0, QtCore.Qt.ItemDataRole.UserRole)
                child_track = self._track_map.get(child_path)
                if not child_track:
                    continue
                master_track.title = master_track.title or child_track.title
                master_track.artist = master_track.artist or child_track.artist
                master_track.album = master_track.album or child_track.album
                master_track.genre = master_track.genre or child_track.genre
                master_track.bpm = master_track.bpm or child_track.bpm
                master_track.key = master_track.key or child_track.key
                changed = True
            if changed:
                update_track(master_track)
        if changed:
            self.accept()

def _safe_size(path: str) -> int | None:
    try:
        return Path(path).stat().st_size
    except Exception:
        return None


def _safe_folder_name(name: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*]+', "_", name).strip(" ._")
    return cleaned or "survivors"


def _format_preview_value(value) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return f"{value:.4f}".rstrip("0").rstrip(".")
    text = str(value).strip()
    return text or "—"


def _process_log(message: str) -> None:
    try:
        target = Path.cwd() / ".lumbago_data" / "process.log"
        target.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with target.open("a", encoding="utf-8", errors="ignore") as handle:
            handle.write(f"{timestamp} {message}\n")
    except Exception:
        pass


class DuplicateScanSignals(QtCore.QObject):
    progress = QtCore.pyqtSignal(int, int)
    finished = QtCore.pyqtSignal(object)


class DuplicateMergeSignals(QtCore.QObject):
    progress = QtCore.pyqtSignal(int, int, str)
    finished = QtCore.pyqtSignal(list)
    failed = QtCore.pyqtSignal(str)


class DuplicateScanWorker(QtCore.QRunnable):
    def __init__(self, tracks: list[Track], method: str):
        super().__init__()
        self.tracks = tracks
        self.method = method
        self.signals = DuplicateScanSignals()
        self._stop = False

    def stop(self) -> None:
        self._stop = True

    def run(self) -> None:
        result = self._scan()
        self.signals.finished.emit(result)

    def _scan(self):
        if self.method == "Tagi":
            return find_duplicates_by_tags(self.tracks)

        paths = [Path(t.path) for t in self.tracks]
        updates: list[Track] = []
        stat_map: dict[str, tuple[int | None, float | None]] = {}
        for idx, track in enumerate(self.tracks, 1):
            if self._stop:
                break
            size, mtime = _stat_track(track.path)
            stat_map[track.path] = (size, mtime)
            if track.file_size != size or track.file_mtime != mtime:
                track.file_size = size
                track.file_mtime = mtime
                updates.append(track)
            self.signals.progress.emit(idx, len(self.tracks))
        if updates:
            update_tracks_file_meta(updates)

        if self.method == "Hash":
            self._ensure_hashes(stat_map)
            return self._groups_from_hash()
        if self.method == "Fingerprint":
            self._ensure_fingerprints(stat_map)
            return self._groups_from_fingerprint()
        return self._scan_staged(paths, stat_map)

    def _ensure_hashes(
        self,
        stat_map: dict[str, tuple[int | None, float | None]],
        subset: list[Track] | None = None,
    ) -> None:
        targets = subset or self.tracks
        updates: list[Track] = []
        for idx, track in enumerate(targets, 1):
            if self._stop:
                break
            size, mtime = stat_map.get(track.path, (track.file_size, track.file_mtime))
            if track.file_hash and track.file_mtime == mtime:
                continue
            try:
                track.file_hash = file_hash(Path(track.path))
                track.file_mtime = mtime
                track.file_size = size
                updates.append(track)
            except Exception:
                continue
            self.signals.progress.emit(idx, len(targets))
        if updates:
            update_tracks_file_meta(updates)

    def _ensure_fingerprints(
        self,
        stat_map: dict[str, tuple[int | None, float | None]],
        subset: list[Track] | None = None,
    ) -> None:
        recognizer = AcoustIdRecognizer(api_key=None)
        targets = subset or self.tracks
        updates: list[Track] = []
        for idx, track in enumerate(targets, 1):
            if self._stop:
                break
            size, mtime = stat_map.get(track.path, (track.file_size, track.file_mtime))
            if track.fingerprint and track.file_mtime == mtime:
                continue
            try:
                fp = recognizer.fingerprint(Path(track.path))
            except Exception:
                fp = None
            if fp:
                _, fingerprint = fp
                track.fingerprint = fingerprint
                track.file_mtime = mtime
                track.file_size = size
                updates.append(track)
            self.signals.progress.emit(idx, len(targets))
        if updates:
            update_tracks_file_meta(updates)

    def _scan_staged(
        self, paths: list[Path], stat_map: dict[str, tuple[int | None, float | None]]
    ):
        size_groups: dict[tuple[int | None, float | None], list[Track]] = {}
        for track in self.tracks:
            size, mtime = stat_map.get(track.path, (track.file_size, track.file_mtime))
            size_groups.setdefault((size, mtime), []).append(track)
        candidate_tracks = [t for group in size_groups.values() if len(group) > 1 for t in group]
        if not candidate_tracks:
            return find_duplicates_by_hash([])
        self._ensure_hashes(stat_map, subset=candidate_tracks)

        hash_groups: dict[str, list[Track]] = {}
        for track in candidate_tracks:
            if not track.file_hash:
                continue
            hash_groups.setdefault(track.file_hash, []).append(track)
        hash_candidates = [t for group in hash_groups.values() if len(group) > 1 for t in group]
        if not hash_candidates:
            return find_duplicates_by_hash([])

        self._ensure_fingerprints(stat_map, subset=hash_candidates)
        fingerprint_groups: dict[str, list[int]] = {}
        for idx, track in enumerate(self.tracks, 1):
            if track in hash_candidates and track.fingerprint:
                fingerprint_groups.setdefault(track.fingerprint, []).append(idx)
        groups = [
            DuplicateGroup(track_ids=ids, similarity=0.97)
            for ids in fingerprint_groups.values()
            if len(ids) > 1
        ]
        return DuplicateResult(groups=groups)

    def _groups_from_hash(self) -> DuplicateResult:
        hash_groups: dict[str, list[int]] = {}
        for idx, track in enumerate(self.tracks, 1):
            if not track.file_hash:
                continue
            hash_groups.setdefault(track.file_hash, []).append(idx)
        groups = [
            DuplicateGroup(track_ids=ids, similarity=1.0)
            for ids in hash_groups.values()
            if len(ids) > 1
        ]
        return DuplicateResult(groups=groups)

    def _groups_from_fingerprint(self) -> DuplicateResult:
        fp_groups: dict[str, list[int]] = {}
        for idx, track in enumerate(self.tracks, 1):
            if not track.fingerprint:
                continue
            fp_groups.setdefault(track.fingerprint, []).append(idx)
        groups = [
            DuplicateGroup(track_ids=ids, similarity=0.95)
            for ids in fp_groups.values()
            if len(ids) > 1
        ]
        return DuplicateResult(groups=groups)


class DuplicateMergeWorker(QtCore.QRunnable):
    def __init__(self, groups: list[tuple[str, list[Track]]], *, settings=None, use_ai: bool = True):
        super().__init__()
        self.groups = groups
        self.settings = settings
        self.use_ai = use_ai
        self.signals = DuplicateMergeSignals()
        self._stop = False

    def stop(self) -> None:
        self._stop = True

    def run(self) -> None:
        try:
            plans = []
            total = len(self.groups)
            for idx, (label, tracks) in enumerate(self.groups, 1):
                if self._stop:
                    _process_log(f"[dupmerge] canceled | processed={idx - 1} total={total}")
                    break
                group_label = label
                survivor_name = Path(tracks[0].path).name if tracks else ""
                mode_name = "AI" if self.use_ai else "quick"
                status = f"Scalanie {mode_name}: {group_label} | {survivor_name}".strip()
                self.signals.progress.emit(max(0, idx - 1), total, status)
                _process_log(
                    f"[dupmerge] {idx}/{total} | group={group_label} | file={survivor_name} "
                    f"| mode={mode_name} | stage=start"
                )
                plan = build_duplicate_merge_plan(
                    tracks,
                    settings=self.settings,
                    use_ai=self.use_ai,
                    logger=_process_log,
                    group_label=group_label,
                )
                if plan is not None and plan.changed_fields:
                    plans.append(plan)
                    _process_log(
                        f"[dupmerge] {idx}/{total} | group={group_label} | mode={mode_name} "
                        f"| stage=done | changed_fields={len(plan.changed_fields)}"
                    )
                else:
                    _process_log(
                        f"[dupmerge] {idx}/{total} | group={group_label} | mode={mode_name} "
                        f"| stage=done | changed_fields=0"
                    )
                self.signals.progress.emit(idx, total, status)
            _process_log(f"[dupmerge] finished | plans={len(plans)} total={total} | use_ai={int(self.use_ai)}")
            self.signals.finished.emit(plans)
        except Exception as exc:
            _process_log(f"[dupmerge] failed | error={exc}")
            self.signals.failed.emit(str(exc))


def _stat_track(path: str) -> tuple[int | None, float | None]:
    try:
        stat = Path(path).stat()
        return stat.st_size, stat.st_mtime
    except Exception:
        return None, None
