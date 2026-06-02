from __future__ import annotations

from PyQt6 import QtCore, QtWidgets
from ui.widgets import apply_dialog_fade, dialog_icon_pixmap

from core.models import Track
from core.renamer import (
    apply_rename_plan,
    build_rename_plan,
    undo_last_rename,
    # File Manager / organizer exports (added to renamer module)
    build_organize_plan,
    apply_organize_plan,
    undo_last_organize,
)
from data.repository import update_track_paths_bulk
from core.audio import write_tags
from pathlib import Path


class RenamerDialog(QtWidgets.QDialog):
    def __init__(self, tracks: list[Track], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Renamer")
        self.setMinimumSize(860, 520)
        apply_dialog_fade(self)
        self._tracks = tracks
        self._plan = []
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

        self.table = QtWidgets.QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Stara nazwa", "Nowa nazwa", "Status"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table, 1)

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

    def _preview(self):
        self._plan = build_rename_plan(self._tracks, self.pattern.text().strip())
        self.table.setRowCount(0)
        for item in self._plan:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(str(item.old_path)))
            self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(str(item.new_path)))
            status = "OK" if not item.conflict else f"Konflikt: {item.reason}"
            status_item = QtWidgets.QTableWidgetItem(status)
            if item.conflict:
                status_item.setForeground(QtCore.Qt.GlobalColor.red)
            self.table.setItem(row, 2, status_item)

    def _apply(self):
        if not self._plan:
            self._preview()
        try:
            history = apply_rename_plan(self._plan)
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
        self.setWindowTitle("File Manager / Organizuj pliki")
        self.setMinimumSize(920, 620)
        apply_dialog_fade(self)
        self._tracks = [t for t in tracks if t and t.path]  # filter valid
        self._plan: list = []
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

        # Structure and filename patterns
        struct_row = QtWidgets.QHBoxLayout()
        struct_row.addWidget(QtWidgets.QLabel("Struktura folderów:"))
        self.folder_struct = QtWidgets.QLineEdit("{genre}/{artist}/{album} ({year})")
        self.folder_struct.setToolTip("Np. {genre}/{artist}/{year} lub {genre}/{artist}/{album}. Użyj / jako separator. Puste segmenty -> 'Unknown'")
        struct_row.addWidget(self.folder_struct, 1)
        layout.addLayout(struct_row)

        fname_row = QtWidgets.QHBoxLayout()
        fname_row.addWidget(QtWidgets.QLabel("Wzorzec nazwy pliku:"))
        self.file_pattern = QtWidgets.QLineEdit("{artist} - {title}")
        self.file_pattern.setToolTip("Np. {tracknumber:02} - {title} lub {artist} - {title}. Wspiera te same pola co Renamer + ulepszone czyszczenie pustych.")
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

        # Preview table
        self.table = QtWidgets.QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Stara ścieżka", "Nowa ścieżka (docelowa)", "Akcja", "Status"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnWidth(0, 280)
        self.table.setColumnWidth(1, 320)
        self.table.setColumnWidth(2, 60)
        layout.addWidget(self.table, 1)

        # Status
        self.status_label = QtWidgets.QLabel("Wybierz bazę, wzorce i naciśnij Podgląd. Pliki z biblioteki.")
        layout.addWidget(self.status_label)

    def _browse_target(self):
        d = QtWidgets.QFileDialog.getExistingDirectory(self, "Wybierz katalog bazowy dla zorganizowanych plików", self.target_dir.text())
        if d:
            self.target_dir.setText(d)

    def _preview(self):
        try:
            base = Path(self.target_dir.text().strip() or (Path.home() / "Music" / "Organized"))
            idx = self.action_combo.currentIndex()
            action = "delete" if idx == 2 else ("copy" if idx == 1 else "move")
            if action == "delete":
                # For delete, folder/fname templates ignored; use dummy base
                base = Path(self.target_dir.text().strip() or (Path.home() / "Music" / "Organized"))
                self._plan = build_organize_plan(
                    self._tracks,
                    "{genre}",  # dummy
                    "{title}",  # dummy
                    base,
                    action="delete",
                )
            else:
                self._plan = build_organize_plan(
                    self._tracks,
                    self.folder_struct.text().strip(),
                    self.file_pattern.text().strip(),
                    base,
                    action=action,
                )
            self.table.setRowCount(0)
            conflicts = 0
            for item in self._plan:
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(str(item.old_path)))
                if item.action == "delete":
                    self.table.setItem(row, 1, QtWidgets.QTableWidgetItem("(do usunięcia)"))
                else:
                    self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(str(item.new_path)))
                act_item = QtWidgets.QTableWidgetItem(item.action)
                self.table.setItem(row, 2, act_item)
                status = "OK" if not item.conflict else f"Konflikt: {item.reason}"
                if item.conflict:
                    conflicts += 1
                status_item = QtWidgets.QTableWidgetItem(status)
                if item.conflict:
                    status_item.setForeground(QtCore.Qt.GlobalColor.red)
                self.table.setItem(row, 3, status_item)
            self.status_label.setText(f"Plan: {len(self._plan)} plików, konflikty: {conflicts}. Baza: {base} (delete ignoruje strukturę)")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Błąd podglądu", str(e))

    def _apply(self):
        if not self._plan:
            self._preview()
        if not self._plan:
            return
        try:
            base = Path(self.target_dir.text().strip())
            idx = self.action_combo.currentIndex()
            action = "delete" if idx == 2 else ("copy" if idx == 1 else "move")
            # re-build to be fresh? but use current plan
            track_lookup = {str(t.path): t for t in self._tracks}
            self._history = apply_organize_plan(
                self._plan,
                do_write_tags=self.write_cb.isChecked() and action != "delete",
                track_lookup=track_lookup,
            )
            # NOW update library/repo after FS ops (key requirement)
            if self._history:
                from data.repository import update_track_paths_bulk, upsert_tracks, list_tracks
                from copy import deepcopy as _deep

                moves = [{"old": h["old"], "new": h["new"]} for h in self._history if h.get("action") == "move"]
                if moves:
                    update_track_paths_bulk(moves)

                deletes = [h for h in self._history if h.get("action") == "delete"]
                if deletes:
                    # Remove from DB (simple path match)
                    # Note: for production better batch delete by path, here use repo if avail
                    try:
                        from data.repository import get_session_factory
                        from data.schema import TrackOrm
                        Session = get_session_factory()
                        with Session() as sess:
                            for d in deletes:
                                sess.query(TrackOrm).filter(TrackOrm.path == d["old"]).delete()
                            sess.commit()
                    except Exception as de:
                        # fallback: nothing, or log
                        pass

                copies = [h for h in self._history if h.get("action") == "copy"]
                if copies:
                    new_ts: list[Track] = []
                    old_lookup = {str(t.path): t for t in self._tracks}
                    for h in copies:
                        orig = old_lookup.get(h["old"])
                        if orig:
                            ct = _deep(orig)
                            ct.path = h["new"]
                            ct.id = None  # new entry
                            # ensure dates fresh-ish
                            ct.date_added = None
                            new_ts.append(ct)
                    if new_ts:
                        upsert_tracks(new_ts)

            n = len(self._history)
            self.accept()
            # show after close to parent
            parent = self.parent()
            if parent:
                QtWidgets.QMessageBox.information(
                    parent,
                    "Organizacja zakończona",
                    f"Przetworzono {n} plików (ruchy/kopie). Biblioteka/repo zaktualizowane po operacjach FS. Użyj Cofnij w dialogu jeśli potrzeba.",
                )
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "Błąd organizacji", f"Nie udało się: {exc}")

    def _undo(self):
        try:
            reverted = undo_last_organize()
            if reverted:
                # update DB for the reverted moves (flip paths)
                flipped = [{"old": r["new"], "new": r["old"]} for r in reverted]
                update_track_paths_bulk(flipped)
                self.status_label.setText(f"Cofnięto {len(reverted)} ruchów. Odśwież bibliotekę po zamknięciu.")
            else:
                self.status_label.setText("Brak ruchów do cofnięcia w ostatniej historii organize (kopie pozostają).")
            # Do not auto accept; allow user to preview again if wanted
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "Błąd cofania organize", str(exc))

