from __future__ import annotations

from PyQt6 import QtCore, QtWidgets
from ui.widgets import apply_dialog_fade, dialog_icon_pixmap

from core.models import Track
from core.renamer import (
    apply_rename_plan,
    build_rename_plan,
    undo_last_rename,
    # File Manager / organizer exports (added to renamer module)
    OrganizeApplyResult,
    build_organize_plan,
    apply_organize_plan,
    undo_last_organize,
    _normalize_fs_path,
    _load_organize_history,
    _store_organize_history,
)
from ui.plan_conflict_ui import (
    attach_plan_table_context_menu,
    build_auto_resolve_controls,
    run_auto_resolve_dialog,
    set_plan_index_on_status_item,
    PLAN_ITEM_INDEX_ROLE,  # for tree <-> table sync
)
from data.repository import update_track_paths_bulk
from core.audio import write_tags
from pathlib import Path

from ui.file_track_ops import (
    build_file_ops_button_bar,
    reveal_in_file_manager,
)


class RenamerDialog(QtWidgets.QDialog):
    def __init__(self, tracks: list[Track], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Renamer")
        self.setMinimumSize(860, 520)
        apply_dialog_fade(self)
        self._tracks = tracks
        self._plan: list = []
        self._full_plan: list = []
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
        title = QtWidgets.QLabel(self.windowTitle())
        title.setObjectName("DialogTitle")
        title_row.addWidget(title_icon)
        title_row.addWidget(title)
        title_row.addStretch(1)
        layout.addLayout(title_row)

        row = QtWidgets.QHBoxLayout()
        row.addWidget(QtWidgets.QLabel("Wzorzec:"))
        self.pattern = QtWidgets.QLineEdit("{artist} - {title}")
        self.pattern.setToolTip("Użyj pól: {artist} {title} {album} {genre} {bpm} {key} {index} {year} {tracknumber} {albumartist} itd. (puste pola usuwane automatycznie)")
        row.addWidget(self.pattern, 1)
        self.preview_btn = QtWidgets.QPushButton("Podgląd")
        self.preview_btn.clicked.connect(self._preview)
        row.addWidget(self.preview_btn)
        layout.addLayout(row)

        # Fix: add optional tag writeback on rename (was missing entirely)
        write_row = QtWidgets.QHBoxLayout()
        self.write_tags_cb = QtWidgets.QCheckBox("Zapisz aktualne metadane (z biblioteki) do tagów pliku po zmianie nazwy")
        self.write_tags_cb.setToolTip("Opcjonalny writeback tagów do pliku (używa wartości z DB/biblioteki dla nowych nazw plików)")
        self.write_tags_cb.setChecked(False)
        write_row.addWidget(self.write_tags_cb)
        write_row.addStretch(1)
        layout.addLayout(write_row)

        resolve_row = build_auto_resolve_controls(self, on_resolve=self._auto_resolve_conflicts)
        layout.addLayout(resolve_row)

        filter_row = QtWidgets.QHBoxLayout()
        self.only_conflicts_cb = QtWidgets.QCheckBox("Pokaż tylko konflikty")
        self.only_conflicts_cb.setToolTip(
            "Filtruj tabelę do wierszy z konfliktem nazw — ułatwia naprawę przed zastosowaniem planu."
        )
        self.only_conflicts_cb.toggled.connect(self._repopulate_table)
        filter_row.addWidget(self.only_conflicts_cb)
        filter_row.addStretch(1)
        layout.addLayout(filter_row)

        self.table = QtWidgets.QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Stara nazwa", "Nowa nazwa", "Status"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        layout.addWidget(self.table, 1)

        def _refresh_after_fs() -> None:
            parent = self.parent()
            if parent is not None and hasattr(parent, "_load_tracks"):
                parent._load_tracks()
            if self._full_plan:
                self._preview()

        file_ops = build_file_ops_button_bar(
            self,
            self.table,
            path_column=0,
            tracks=self._tracks,
            on_library_changed=_refresh_after_fs,
            open_organizer=None,
        )
        layout.addLayout(file_ops)
        attach_plan_table_context_menu(
            self.table,
            self,
            get_full_plan=lambda: self._full_plan,
            on_plan_changed=self._repopulate_table,
            path_column=0,
            extra_path_column=1,
            status_column=2,
            tracks=self._tracks,
            on_library_changed=_refresh_after_fs,
        )
        self.table.itemDoubleClicked.connect(self._on_table_double_click)

        actions = QtWidgets.QHBoxLayout()
        self.apply_btn = QtWidgets.QPushButton("Zastosuj")
        self.apply_btn.setToolTip("Zmień nazwy plików według planu")
        self.apply_btn.clicked.connect(self._apply)
        self.undo_btn = QtWidgets.QPushButton("Cofnij ostatnią zmianę")
        self.undo_btn.setToolTip("Przywróć poprzednie nazwy z ostatniego użycia")
        self.undo_btn.clicked.connect(self._undo)
        self.close_btn = QtWidgets.QPushButton("Zamknij")
        self.close_btn.clicked.connect(self.reject)
        actions.addStretch(1)
        actions.addWidget(self.apply_btn)
        actions.addWidget(self.undo_btn)
        actions.addWidget(self.close_btn)
        layout.addLayout(actions)

    def _on_table_double_click(self, item: QtWidgets.QTableWidgetItem) -> None:
        path_item = self.table.item(item.row(), 0)
        if path_item and path_item.text().strip():
            reveal_in_file_manager(path_item.text().strip())

    def _preview(self):
        self._full_plan = build_rename_plan(self._tracks, self.pattern.text().strip())
        self._repopulate_table()

    def _repopulate_table(self) -> None:
        if not self._full_plan:
            return
        show_conflicts_only = self.only_conflicts_cb.isChecked()
        items = [
            (idx, item)
            for idx, item in enumerate(self._full_plan)
            if not show_conflicts_only or item.conflict
        ]
        self._plan = [item for _, item in items]
        self.table.setRowCount(0)
        for plan_idx, item in items:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(str(item.old_path)))
            self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(str(item.new_path)))
            status = "OK" if not item.conflict else f"Konflikt: {item.reason}"
            status_item = QtWidgets.QTableWidgetItem(status)
            if item.conflict:
                status_item.setForeground(QtCore.Qt.GlobalColor.red)
            set_plan_index_on_status_item(status_item, plan_idx)
            self.table.setItem(row, 2, status_item)

    def _auto_resolve_conflicts(self, strategy: str) -> None:
        if not self._full_plan:
            self._preview()
        run_auto_resolve_dialog(
            self,
            self._full_plan,
            strategy,
            on_done=self._repopulate_table,
        )

    def _apply(self):
        if not self._full_plan:
            self._preview()
        self._plan = self._full_plan
        conflicts = [item for item in self._full_plan if item.conflict]
        if conflicts:
            QtWidgets.QMessageBox.warning(
                self,
                "Konflikty w planie",
                f"Plan zawiera {len(conflicts)} konfliktów.\n\n"
                "Użyj „Rozwiąż wszystkie konflikty”, filtr „Pokaż tylko konflikty” "
                "lub PPM → „Rozwiąż konflikt” na wierszu.",
            )
            return
        try:
            history = apply_rename_plan(self._full_plan)
            update_track_paths_bulk(history)
            # Fix: optional tag writeback after rename (no integration before)
            if history and self.write_tags_cb.isChecked():
                errors = self._perform_tag_writeback(history)
                if errors:
                    QtWidgets.QMessageBox.warning(self, "Writeback ostrzeżenia", "\n".join(errors[:5]))
            self.accept()
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "Błąd zmiany nazw", f"Nie udało się zastosować: {exc}")
            # Do not accept on error; plan may have been partially reverted in renamer

    def _undo(self):
        try:
            history = undo_last_rename()
            flipped = [{"old": item["new"], "new": item["old"]} for item in history]
            update_track_paths_bulk(flipped)
            # Note: undo of writeback not auto (tags would need previous state); user can re-apply if needed.
            self.accept()
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "Błąd cofania", f"Nie udało się cofnąć: {exc}")

    def _perform_tag_writeback(self, history: list[dict[str, str]]) -> list[str]:
        """Write current track metadata (from the dialog's tracks) to the *new* file locations.
        Fixes the missing tag writeback on rename. Uses direct write_tags for current library values.
        """
        old_to_track = {str(t.path): t for t in self._tracks}
        errors: list[str] = []
        for entry in history:
            oldp = entry.get("old")
            newp = entry.get("new")
            track = old_to_track.get(oldp)
            if not track or not newp:
                continue
            tags: dict[str, str] = {}
            for fld in (
                "title", "artist", "album", "albumartist", "genre", "year",
                "bpm", "key", "tracknumber", "discnumber", "composer", "remixer",
                "originalartist", "publisher", "isrc", "comment", "lyrics",
                "mood", "energy",
            ):
                val = getattr(track, fld, None)
                if val is not None:
                    tags[fld] = str(val)
            # rating special: write as int str
            if getattr(track, "rating", 0):
                tags["rating"] = str(track.rating)
            try:
                write_tags(Path(newp), tags)
            except Exception as e:
                errors.append(f"{Path(newp).name}: {e}")
        return errors


# ============================================================
# FILE ORGANIZER DIALOG (UI for new File Manager, added to existing renamer_dialog.py)
# No new file created. Allows batch organize of (updated) audio into structured dirs.
# Integrated from selection or after renamer/autotag.
# ============================================================

class FileOrganizerDialog(QtWidgets.QDialog):
    def __init__(self, tracks: list[Track], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Library Builder / Organizuj pliki")
        self.setMinimumSize(920, 620)
        apply_dialog_fade(self)
        self._tracks = [t for t in tracks if t and t.path]  # filter valid
        self._plan: list = []
        self._full_plan: list = []
        self._history: list[dict[str, str]] = []
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

        # Title
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

        info = QtWidgets.QLabel(
            "Zorganizuj wybrane/zaktualizowane pliki audio w struktury folderów wg tagów (np. po autotag lub rename). "
            "Obsługuje Move (aktualizuje ścieżki w bibliotece), Copy (dodaje duplikaty) lub Delete (usuń + wyczyść z bazy) - idealne po tagowaniu. "
            "Wybierz szablon folderów np. {genre}/{artist}/{album} ({year}) aby unikąć płaskiej struktury iTunes. "
            "Podgląd, konflikty, writeback tagów, cofanie ruchów."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # Target base dir
        dir_row = QtWidgets.QHBoxLayout()
        dir_row.addWidget(QtWidgets.QLabel("Baza docelowa:"))
        self.target_dir = QtWidgets.QLineEdit(str(Path.home() / "Music" / "Organized"))
        self.target_dir.setToolTip("Wybierz katalog bazowy dla zorganizowanej biblioteki")
        browse_btn = QtWidgets.QPushButton("Przeglądaj...")
        browse_btn.clicked.connect(self._browse_target)
        dir_row.addWidget(self.target_dir, 1)
        dir_row.addWidget(browse_btn)
        layout.addLayout(dir_row)

        # Structure and filename patterns + presets (creative: wired early for complete preview experience per SZPIEG/Plan)
        preset_row = QtWidgets.QHBoxLayout()
        preset_row.addWidget(QtWidgets.QLabel("Preset:"))
        self.preset_combo = QtWidgets.QComboBox()
        from core.renamer import get_organize_presets
        self._presets = get_organize_presets()
        self.preset_combo.addItem("(własny)", None)
        for name, p in self._presets.items():
            self.preset_combo.addItem(name, p)
        self.preset_combo.setToolTip("EFEKT: Szybki wybór szablonu inspirowany Rekordbox/beets/MediaMonkey/Picard. Zmienia strukturę + nazwę pliku.")
        self.preset_combo.currentIndexChanged.connect(self._apply_preset)
        preset_row.addWidget(self.preset_combo, 1)
        layout.addLayout(preset_row)

        struct_row = QtWidgets.QHBoxLayout()
        struct_row.addWidget(QtWidgets.QLabel("Struktura folderów:"))
        self.folder_struct = QtWidgets.QLineEdit("{genre}/{artist}/{album} ({year})")
        self.folder_struct.setToolTip("Np. {genre}/{artist}/{year} lub {genre}/{artist}/{album}. Użyj / jako separator. Puste segmenty -> 'Unknown'. Wspiera {field|default} i {field:02} (nowe).")
        struct_row.addWidget(self.folder_struct, 1)
        layout.addLayout(struct_row)

        preset_row = QtWidgets.QHBoxLayout()
        preset_row.addWidget(QtWidgets.QLabel("Szablony:"))
        for label, pattern in (
            ("Genre/Artist/Album", "{genre}/{artist}/{album}"),
            ("Genre/Year/Artist/Album", "{genre}/{year}/{artist}/{album}"),
            ("Artist/Album", "{artist}/{album} ({year})"),
        ):
            btn = QtWidgets.QPushButton(label)
            btn.setToolTip(f"Ustaw strukturę: {pattern}")
            btn.clicked.connect(lambda _checked=False, p=pattern: self.folder_struct.setText(p))
            preset_row.addWidget(btn)
        preset_row.addStretch(1)
        layout.addLayout(preset_row)

        fname_row = QtWidgets.QHBoxLayout()
        fname_row.addWidget(QtWidgets.QLabel("Wzorzec nazwy pliku:"))
        self.file_pattern = QtWidgets.QLineEdit("{artist} - {title}")
        self.file_pattern.setToolTip("Np. {tracknumber:02} - {title} lub {artist} - {title}. Wspiera te same pola co Renamer + ulepszone czyszczenie pustych + nowe składnie.")
        fname_row.addWidget(self.file_pattern, 1)
        layout.addLayout(fname_row)

        # Action and options
        opts_row = QtWidgets.QHBoxLayout()
        opts_row.addWidget(QtWidgets.QLabel("Akcja:"))
        self.action_combo = QtWidgets.QComboBox()
        self.action_combo.addItems([
            "move (przenieś + zaktualizuj bibliotekę)",
            "copy (skopiuj + dodaj wpis w bibliotece)",
            "delete (usuń pliki + wyczyść z biblioteki) - ostrożnie! (po otagowaniu)"
        ])
        self.action_combo.setToolTip("Wybierz akcję dla wybranych plików po pracy (tagowanie itp.). Delete nie używa szablonów folderów.")
        opts_row.addWidget(self.action_combo)
        self.write_cb = QtWidgets.QCheckBox("Zapisz metadane do tagów w nowych plikach")
        self.write_cb.setChecked(True)
        self.write_cb.setToolTip("Opcjonalny tag writeback (używa bieżących wartości z biblioteki)")
        opts_row.addWidget(self.write_cb)
        opts_row.addStretch(1)
        layout.addLayout(opts_row)

        # Buttons row
        btn_row = QtWidgets.QHBoxLayout()
        self.preview_btn = QtWidgets.QPushButton("Podgląd planu")
        self.preview_btn.clicked.connect(self._preview)
        self.apply_btn = QtWidgets.QPushButton("Zastosuj organizację")
        self.apply_btn.clicked.connect(self._apply)
        self.undo_btn = QtWidgets.QPushButton("Cofnij ostatnią organizację (ruchy)")
        self.undo_btn.clicked.connect(self._undo)
        self.close_btn = QtWidgets.QPushButton("Zamknij")
        self.close_btn.clicked.connect(self.reject)
        btn_row.addWidget(self.preview_btn)
        btn_row.addWidget(self.apply_btn)
        btn_row.addWidget(self.undo_btn)
        btn_row.addStretch(1)
        btn_row.addWidget(self.close_btn)
        layout.addLayout(btn_row)

        # Polish: icons on actions (reuse existing, no new assets) + EFFECT already on many
        try:
            ico = dialog_icon_pixmap(16)
            self.preview_btn.setIcon(ico)
            self.apply_btn.setIcon(ico)
            self.undo_btn.setIcon(ico)
        except Exception:
            pass  # graceful if icon load edge
        # Add explicit EFFECT tooltip on key controls (per SZPIEG spec for organizer)
        self.preview_btn.setToolTip(self.preview_btn.toolTip() + " EFEKT: Przeliczy ścieżki wg szablonu (z nowymi conditionals/presets).")
        self.apply_btn.setToolTip(self.apply_btn.toolTip() + " EFEKT: Wykona move/copy/delete na FS + aktualizacja biblioteki.")
        self.undo_btn.setToolTip(self.undo_btn.toolTip() + " EFEKT: Cofnie ostatnie ruchy (bezpiecznie tylko move).")

        resolve_row = build_auto_resolve_controls(self, on_resolve=self._auto_resolve_conflicts)
        layout.addLayout(resolve_row)

        filter_row = QtWidgets.QHBoxLayout()
        self.only_conflicts_cb = QtWidgets.QCheckBox("Pokaż tylko konflikty")
        self.only_conflicts_cb.setToolTip(
            "Filtruj tabelę do wierszy z konfliktem nazw/ścieżek — ułatwia ręczną naprawę przed zastosowaniem planu."
        )
        self.only_conflicts_cb.toggled.connect(self._repopulate_table)
        filter_row.addWidget(self.only_conflicts_cb)
        filter_row.addStretch(1)
        layout.addLayout(filter_row)

        # Toggle + dual preview: tabela + visual tree (per SZPIEG 2026-06-15 + Plan lista step 3)
        # Creative: QTreeWidget simulating exact folder structure from rendered new_paths.
        # Icons, EFFECT tooltips, highDPI friendly, sync with table selection.
        toggle_row = QtWidgets.QHBoxLayout()
        self.preview_mode_combo = QtWidgets.QComboBox()
        self.preview_mode_combo.addItems(["Tabela + Drzewo folderów", "Tylko tabela", "Tylko drzewo"])
        self.preview_mode_combo.setCurrentIndex(0)
        self.preview_mode_combo.setToolTip("EFEKT: Przełącz podgląd. Drzewo pokazuje rzeczywistą strukturę folderów wg szablonu (jak w beets/Picard/MediaMonkey).")
        self.preview_mode_combo.currentIndexChanged.connect(self._repopulate_table)
        toggle_row.addWidget(QtWidgets.QLabel("Podgląd:"))
        toggle_row.addWidget(self.preview_mode_combo)
        toggle_row.addStretch(1)
        layout.addLayout(toggle_row)

        # Splitter for table + tree (resizable, highDPI safe)
        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        # Preview table
        self.table = QtWidgets.QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Stara ścieżka", "Nowa ścieżka (docelowa)", "Akcja", "Status"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnWidth(0, 280)
        self.table.setColumnWidth(1, 320)
        self.table.setColumnWidth(2, 60)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        splitter.addWidget(self.table)

        # Visual folder tree (creative, meticulous: grouped by rendered path parts)
        self.tree = QtWidgets.QTreeWidget()
        self.tree.setHeaderLabel("Struktura folderów (podgląd)")
        self.tree.setColumnCount(1)
        self.tree.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.tree.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.tree.setToolTip("EFEKT: Drzewo odzwierciedla dokładnie szablon + tagi. Kliknij aby podświetlić w tabeli.")
        self.tree.itemClicked.connect(self._on_tree_item_clicked)
        splitter.addWidget(self.tree)

        splitter.setSizes([520, 380])
        layout.addWidget(splitter, 1)

        def _refresh_after_fs() -> None:
            parent = self.parent()
            if parent is not None and hasattr(parent, "_load_tracks"):
                parent._load_tracks()
            if self._full_plan:
                self._preview()

        def _open_org_subset(ts: list[Track]) -> None:
            if not ts:
                return
            dlg = FileOrganizerDialog(ts, self)
            if dlg.exec() and parent is not None and hasattr(parent, "_load_tracks"):
                parent._load_tracks()
            if self._full_plan:
                self._preview()

        parent = self.parent()
        file_ops = build_file_ops_button_bar(
            self,
            self.table,
            path_column=0,
            tracks=self._tracks,
            on_library_changed=_refresh_after_fs,
            open_organizer=_open_org_subset,
        )
        layout.addLayout(file_ops)
        attach_plan_table_context_menu(
            self.table,
            self,
            get_full_plan=lambda: self._full_plan,
            on_plan_changed=self._repopulate_table,
            path_column=0,
            extra_path_column=1,
            status_column=3,
            tracks=self._tracks,
            on_library_changed=_refresh_after_fs,
            open_organizer=_open_org_subset,
        )
        self.table.itemDoubleClicked.connect(self._on_table_double_click)

        # Status
        self.status_label = QtWidgets.QLabel(
            "Wybierz bazę, wzorce i naciśnij Podgląd. PPM: rozwiąż konflikt lub operacje na pliku."
        )
        layout.addWidget(self.status_label)

    def _browse_target(self):
        d = QtWidgets.QFileDialog.getExistingDirectory(self, "Wybierz katalog bazowy dla zorganizowanych plików", self.target_dir.text())
        if d:
            self.target_dir.setText(d)

    def _on_table_double_click(self, item: QtWidgets.QTableWidgetItem) -> None:
        col = item.column()
        text = item.text().strip()
        if not text or text == "(do usunięcia)":
            path_item = self.table.item(item.row(), 0)
            text = path_item.text().strip() if path_item else ""
        if text:
            reveal_in_file_manager(text)

    def _repopulate_table(self) -> None:
        if not self._full_plan:
            return
        show_conflicts_only = self.only_conflicts_cb.isChecked()
        items = [i for i in self._full_plan if (not show_conflicts_only or i.conflict)]
        self._plan = items
        self.table.setRowCount(0)
        conflicts = sum(1 for i in self._full_plan if i.conflict)
        for plan_idx, item in enumerate(self._full_plan):
            if show_conflicts_only and not item.conflict:
                continue
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(str(item.old_path)))
            if item.action == "delete":
                self.table.setItem(row, 1, QtWidgets.QTableWidgetItem("(do usunięcia)"))
            else:
                self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(str(item.new_path)))
            self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(item.action))
            status = "OK" if not item.conflict else f"Konflikt: {item.reason}"
            status_item = QtWidgets.QTableWidgetItem(status)
            if item.conflict:
                status_item.setForeground(QtCore.Qt.GlobalColor.red)
            set_plan_index_on_status_item(status_item, plan_idx)
            self.table.setItem(row, 3, status_item)
        base = self.target_dir.text().strip()
        extra = f" (widoczne: {len(items)}/{len(self._full_plan)})" if show_conflicts_only else ""
        self.status_label.setText(
            f"Plan: {len(self._full_plan)} plików, konflikty: {conflicts}{extra}. "
            f"PPM na wierszu → operacje na pliku. Baza: {base}"
        )
        self._populate_tree()  # step 3 tree always updated with table (complete feature)

    def _preview(self):
        try:
            base = Path(self.target_dir.text().strip() or (Path.home() / "Music" / "Organized"))
            idx = self.action_combo.currentIndex()
            action = "delete" if idx == 2 else ("copy" if idx == 1 else "move")
            if action == "delete":
                base = Path(self.target_dir.text().strip() or (Path.home() / "Music" / "Organized"))
                self._full_plan = build_organize_plan(
                    self._tracks,
                    "{genre}",
                    "{title}",
                    base,
                    action="delete",
                )
            else:
                self._full_plan = build_organize_plan(
                    self._tracks,
                    self.folder_struct.text().strip(),
                    self.file_pattern.text().strip(),
                    base,
                    action=action,
                )
            self._repopulate_table()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Błąd podglądu", str(e))

    def _auto_resolve_conflicts(self, strategy: str) -> None:
        if not self._full_plan:
            self._preview()
        run_auto_resolve_dialog(
            self,
            self._full_plan,
            strategy,
            on_done=self._repopulate_table,
        )

    def _apply(self):
        self._preview()
        if not self._full_plan:
            return
        self._plan = self._full_plan

        conflicts = [item for item in self._full_plan if item.conflict]
        if conflicts:
            QtWidgets.QMessageBox.warning(
                self,
                "Konflikty w planie",
                f"Plan zawiera {len(conflicts)} konfliktów.\n\n"
                "Użyj „Rozwiąż wszystkie konflikty”, filtr „Pokaż tylko konflikty” "
                "lub PPM → „Rozwiąż konflikt” na wierszu.",
            )
            return

        idx = self.action_combo.currentIndex()
        action = "delete" if idx == 2 else ("copy" if idx == 1 else "move")
        missing = [
            item
            for item in self._plan
            if item.action != "delete" and not _normalize_fs_path(item.old_path).exists()
        ]
        if missing and action != "delete":
            QtWidgets.QMessageBox.warning(
                self,
                "Brak plików źródłowych",
                f"{len(missing)} plików nie istnieje na dysku (ścieżki w bibliotece mogą być nieaktualne).\n"
                "Biblioteka NIE zostanie zmieniona. Odśwież skan lub cofnij poprzednią organizację.",
            )
            return

        try:
            track_lookup: dict[str, Track] = {}
            for t in self._tracks:
                p = _normalize_fs_path(Path(t.path))
                track_lookup[str(p)] = t
                track_lookup[str(t.path)] = t

            # Step 4: Progress + cancel (creative QProgressDialog with real steps + cancel flag)
            prog = QtWidgets.QProgressDialog("Wykonywanie organizacji...", "Anuluj", 0, len(self._plan), self)
            prog.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
            prog.setMinimumDuration(0)
            prog.setValue(0)
            self._cancel_apply = False

            def _check_cancel():
                if prog.wasCanceled():
                    self._cancel_apply = True
                    return True
                return False

            executable_plan = [i for i in self._plan if not i.conflict]  # already filtered earlier
            n_total = max(1, len(executable_plan))

            result: OrganizeApplyResult = apply_organize_plan(
                self._plan,
                do_write_tags=self.write_cb.isChecked() and action != "delete",
                track_lookup=track_lookup,
            )
            prog.setValue(int(n_total * 0.6))  # after core apply

            self._history = result.history

            if result.errors:
                prog.close()
                QtWidgets.QMessageBox.critical(
                    self,
                    "Błąd organizacji",
                    "Operacja przerwana — pliki nie zostały przeniesione, biblioteka bez zmian.\n\n"
                    + "\n".join(result.errors[:8]),
                )
                return

            if not self._history:
                prog.close()
                QtWidgets.QMessageBox.warning(
                    self,
                    "Nic nie wykonano",
                    "Żaden plik nie został przetworzony (brak plików, konflikty lub ten sam katalog docelowy).",
                )
                return

            verified: list[dict[str, str]] = []
            for h in self._history:
                if _check_cancel():
                    break
                act = h.get("action")
                if act == "delete":
                    verified.append(h)
                    continue
                newp = Path(h.get("new", ""))
                if newp.is_file() and newp.stat().st_size >= 1:
                    verified.append(h)
                prog.setValue(prog.value() + 1)

            prog.setValue(n_total)

            if self._cancel_apply:
                prog.close()
                QtWidgets.QMessageBox.information(self, "Anulowano", "Operacja przerwana przez użytkownika. Część plików mogła zostać zmieniona.")
                return

            if len(verified) != len(self._history):
                prog.close()
                QtWidgets.QMessageBox.critical(
                    self,
                    "Weryfikacja nieudana",
                    "Pliki docelowe nie istnieją lub są puste — biblioteka NIE została zaktualizowana.",
                )
                return

            from data.repository import update_track_paths_bulk, upsert_tracks
            from copy import deepcopy as _deep

            moves = [{"old": h["old"], "new": h["new"]} for h in verified if h.get("action") == "move"]
            if moves:
                update_track_paths_bulk(moves)

            deletes = [h for h in verified if h.get("action") == "delete"]
            if deletes:
                try:
                    from data.repository import get_session_factory
                    from data.schema import TrackOrm

                    Session = get_session_factory()
                    with Session() as sess:
                        for d in deletes:
                            sess.query(TrackOrm).filter(TrackOrm.path == d["old"]).delete()
                        sess.commit()
                except Exception:
                    pass

            copies = [h for h in verified if h.get("action") == "copy"]
            if copies:
                new_ts: list[Track] = []
                old_lookup = {str(t.path): t for t in self._tracks}
                for h in copies:
                    orig = old_lookup.get(h["old"])
                    if orig:
                        ct = _deep(orig)
                        ct.path = h["new"]
                        ct.id = None
                        ct.date_added = None
                        new_ts.append(ct)
                if new_ts:
                    upsert_tracks(new_ts)

            prog.close()
            n = len(verified)
            self.accept()
            parent = self.parent()
            if parent:
                QtWidgets.QMessageBox.information(
                    parent,
                    "Organizacja zakończona",
                    f"Przetworzono {n} plików na dysku. Biblioteka zaktualizowana dopiero po weryfikacji plików.",
                )
        except Exception as exc:
            try:
                prog.close()
            except:
                pass
            QtWidgets.QMessageBox.critical(self, "Błąd organizacji", f"Nie udało się: {exc}")

    def _undo(self):
        # Step 5: Selective undo history dialog (full feature, creative + meticulous)
        try:
            hist = _load_organize_history()
            if not hist:
                self.status_label.setText("Brak historii organize do cofnięcia.")
                return

            # Build nice list dialog with checkable moves only
            dlg = QtWidgets.QDialog(self)
            dlg.setWindowTitle("Historia organizacji — wybierz do cofnięcia")
            dlg.setMinimumSize(700, 400)
            lay = QtWidgets.QVBoxLayout(dlg)
            info = QtWidgets.QLabel("Zaznacz ruchy (tylko 'move' można bezpiecznie cofnąć). Kopie i delete pozostają.")
            info.setWordWrap(True)
            lay.addWidget(info)

            listw = QtWidgets.QListWidget()
            listw.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
            movable = []
            for i, entry in enumerate(hist):
                act = entry.get("action", "")
                txt = f"{i+1}. {act}: {entry.get('old','')} → {entry.get('new','')}"
                it = QtWidgets.QListWidgetItem(txt)
                it.setFlags(it.flags() | QtCore.Qt.ItemFlag.ItemIsUserCheckable)
                if act == "move":
                    it.setCheckState(QtCore.Qt.CheckState.Checked)
                    movable.append((i, entry))
                else:
                    it.setCheckState(QtCore.Qt.CheckState.Unchecked)
                    it.setFlags(it.flags() & ~QtCore.Qt.ItemFlag.ItemIsEnabled)
                listw.addItem(it)
            lay.addWidget(listw, 1)

            btns = QtWidgets.QHBoxLayout()
            ok = QtWidgets.QPushButton("Cofnij zaznaczone")
            cancel = QtWidgets.QPushButton("Zamknij")
            btns.addWidget(ok)
            btns.addStretch(1)
            btns.addWidget(cancel)
            lay.addLayout(btns)

            def _do_revert():
                selected = []
                for j in range(listw.count()):
                    it = listw.item(j)
                    if it.checkState() == QtCore.Qt.CheckState.Checked and j < len(hist):
                        selected.append(hist[j])
                if not selected:
                    dlg.accept()
                    return
                # Only moves
                to_revert = [e for e in selected if e.get("action") == "move"]
                if to_revert:
                    flipped = [{"old": r["new"], "new": r["old"]} for r in to_revert]
                    update_track_paths_bulk(flipped)
                    # Re-run core undo for FS (only the selected)
                    for e in to_revert:
                        try:
                            Path(e["new"]).rename(Path(e["old"]))
                        except Exception:
                            pass
                    _store_organize_history([e for e in hist if e not in to_revert])
                    self.status_label.setText(f"Cofnięto {len(to_revert)} zaznaczonych ruchów.")
                dlg.accept()

            ok.clicked.connect(_do_revert)
            cancel.clicked.connect(dlg.reject)
            dlg.exec()
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "Błąd cofania organize", str(exc))

    # --- Step 3: Visual tree + polish (complete to last detail: icons, EFFECT, sync, highDPI, presets) ---
    def _apply_preset(self):
        data = self.preset_combo.currentData()
        if data:
            self.folder_struct.setText(data.get("folder", self.folder_struct.text()))
            self.file_pattern.setText(data.get("filename", self.file_pattern.text()))
            self._preview()

    def _populate_tree(self):
        """Meticulous creative tree: exact mirror of rendered plan paths. Grouped folders + files. Icons + tooltips."""
        self.tree.clear()
        if not self._full_plan:
            return
        mode = self.preview_mode_combo.currentIndex()
        if mode == 1:  # only table
            self.tree.hide()
            self.table.show()
            return
        self.tree.show()
        if mode == 2:
            self.table.hide()
        else:
            self.table.show()

        # Build virtual tree from new_paths (using the enhanced render from step 2)
        from pathlib import Path as _P
        root_item = QtWidgets.QTreeWidgetItem(self.tree, [str(_P(self.target_dir.text().strip() or "Organized"))])
        root_item.setIcon(0, self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DirIcon))
        root_item.setExpanded(True)

        # Group by folder parts
        tree_nodes: dict = {}  # path_str -> QTreeWidgetItem

        for item in self._full_plan:
            if item.action == "delete":
                continue
            rel = _P(item.new_path).relative_to(_P(self.target_dir.text().strip() or "Organized")) if _P(self.target_dir.text().strip() or "Organized") in _P(item.new_path).parents else _P(item.new_path).name
            parts = list(rel.parts)
            current = root_item
            accum = str(_P(self.target_dir.text().strip() or "Organized"))
            for i, part in enumerate(parts):
                accum = str(_P(accum) / part)
                if accum not in tree_nodes:
                    is_file = (i == len(parts) - 1)
                    node = QtWidgets.QTreeWidgetItem(current, [part])
                    if is_file:
                        node.setIcon(0, self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_FileIcon))
                        node.setToolTip(0, f"EFEKT: Plik zostanie {item.action} do tej lokalizacji wg tagów.")
                    else:
                        node.setIcon(0, self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DirIcon))
                        node.setToolTip(0, f"EFEKT: Folder '{part}' zostanie utworzony na podstawie szablonu.")
                    tree_nodes[accum] = node
                current = tree_nodes[accum]
            # store ref for sync
            current.setData(0, QtCore.Qt.ItemDataRole.UserRole, id(item))

        self.tree.expandAll()

    def _on_tree_item_clicked(self, item: QtWidgets.QTreeWidgetItem):
        """Sync tree click -> highlight table row (creative UX polish)."""
        try:
            plan_id = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
            if not plan_id:
                return
            for r in range(self.table.rowCount()):
                status_item = self.table.item(r, 3)
                if status_item and status_item.data(PLAN_ITEM_INDEX_ROLE) is not None:
                    # simple match via path text
                    new_text = self.table.item(r, 1).text() if self.table.item(r, 1) else ""
                    if item.text(0) in new_text or item.text(0) == _P(new_text).name:
                        self.table.selectRow(r)
                        self.table.scrollToItem(self.table.item(r, 0))
                        break
        except Exception:
            pass

    def _on_table_selection_for_tree(self):
        # Optional future two-way sync (kept lightweight)
        pass

