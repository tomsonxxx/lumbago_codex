"""Wspólne operacje na fizycznych plikach audio + wpisach biblioteki."""

from __future__ import annotations

import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

from PyQt6 import QtCore, QtGui, QtWidgets

from core.models import Track
from data.repository import delete_tracks_by_paths, get_track_by_path, update_track_path


def _normalize_paths(paths: list[str | Path]) -> list[Path]:
    seen: set[str] = set()
    result: list[Path] = []
    for raw in paths:
        if not raw:
            continue
        p = Path(str(raw))
        key = str(p)
        if key in seen:
            continue
        seen.add(key)
        result.append(p)
    return result


def reveal_in_file_manager(path: str | Path) -> bool:
    """Otwórz Eksplorator / menedżer plików z zaznaczonym plikiem lub folderem."""
    p = Path(path)
    target = p if p.exists() else p.parent
    if not target.exists():
        return False
    try:
        if sys.platform == "win32":
            if p.is_file() and p.exists():
                subprocess.run(
                    ["explorer", "/select,", str(p.resolve())],
                    check=False,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
            else:
                subprocess.run(
                    ["explorer", str(target.resolve())],
                    check=False,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
            return True
        url = QtCore.QUrl.fromLocalFile(str(target if target.is_dir() else target.parent))
        return QtGui.QDesktopServices.openUrl(url)
    except Exception:
        return False


def copy_files_to_folder(
    parent: QtWidgets.QWidget,
    paths: list[str | Path],
    *,
    on_done: Callable[[], None] | None = None,
) -> int:
    files = [p for p in _normalize_paths(paths) if p.is_file()]
    if not files:
        QtWidgets.QMessageBox.information(parent, "Kopiuj plik", "Brak istniejących plików do skopiowania.")
        return 0
    dest_dir = QtWidgets.QFileDialog.getExistingDirectory(parent, "Kopiuj do folderu")
    if not dest_dir:
        return 0
    dest = Path(dest_dir)
    ok = 0
    errors: list[str] = []
    for src in files:
        try:
            target = dest / src.name
            if target.exists():
                stem, suffix = src.stem, src.suffix
                n = 1
                while target.exists():
                    target = dest / f"{stem}_{n}{suffix}"
                    n += 1
            shutil.copy2(src, target)
            ok += 1
        except Exception as exc:
            errors.append(f"{src.name}: {exc}")
    if errors:
        QtWidgets.QMessageBox.warning(
            parent,
            "Kopiowanie — ostrzeżenia",
            f"Skopiowano {ok}/{len(files)}.\n" + "\n".join(errors[:6]),
        )
    elif ok:
        QtWidgets.QMessageBox.information(parent, "Kopiuj plik", f"Skopiowano {ok} plik(ów) do:\n{dest}")
    if ok and on_done:
        on_done()
    return ok


def move_files_to_folder(
    parent: QtWidgets.QWidget,
    paths: list[str | Path],
    *,
    on_done: Callable[[], None] | None = None,
) -> int:
    files = [p for p in _normalize_paths(paths) if p.is_file()]
    if not files:
        QtWidgets.QMessageBox.information(parent, "Przenieś plik", "Brak istniejących plików do przeniesienia.")
        return 0
    dest_dir = QtWidgets.QFileDialog.getExistingDirectory(parent, "Przenieś do folderu")
    if not dest_dir:
        return 0
    dest = Path(dest_dir)
    ok = 0
    errors: list[str] = []
    for src in files:
        try:
            target = dest / src.name
            if target.exists():
                stem, suffix = src.stem, src.suffix
                n = 1
                while target.exists():
                    target = dest / f"{stem}_{n}{suffix}"
                    n += 1
            shutil.move(str(src), str(target))
            try:
                update_track_path(str(src), str(target))
            except Exception:
                pass
            ok += 1
        except Exception as exc:
            errors.append(f"{src.name}: {exc}")
    if errors:
        QtWidgets.QMessageBox.warning(
            parent,
            "Przenoszenie — ostrzeżenia",
            f"Przeniesiono {ok}/{len(files)}.\n" + "\n".join(errors[:6]),
        )
    elif ok:
        QtWidgets.QMessageBox.information(parent, "Przenieś plik", f"Przeniesiono {ok} plik(ów). Ścieżki w bibliotece zaktualizowane.")
    if ok and on_done:
        on_done()
    return ok


def delete_files_physical(
    parent: QtWidgets.QWidget,
    paths: list[str | Path],
    *,
    also_remove_from_library: bool = True,
    on_done: Callable[[], None] | None = None,
) -> int:
    files = [p for p in _normalize_paths(paths) if p.is_file()]
    if not files:
        QtWidgets.QMessageBox.information(parent, "Usuń plik", "Brak plików na dysku (już usunięte?).")
        return 0
    names = "\n".join(f"• {p}" for p in files[:8])
    if len(files) > 8:
        names += f"\n… i {len(files) - 8} więcej"
    answer = QtWidgets.QMessageBox.question(
        parent,
        "Usuń plik z dysku",
        f"Trwale usunąć {len(files)} plik(ów)?\n\n{names}",
        QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
        QtWidgets.QMessageBox.StandardButton.No,
    )
    if answer != QtWidgets.QMessageBox.StandardButton.Yes:
        return 0
    removed = 0
    path_strs: list[str] = []
    for src in files:
        try:
            src.unlink()
            removed += 1
            path_strs.append(str(src))
        except Exception:
            pass
    if also_remove_from_library and path_strs:
        try:
            delete_tracks_by_paths(path_strs)
        except Exception:
            pass
    if removed:
        QtWidgets.QMessageBox.information(
            parent,
            "Usuń plik",
            f"Usunięto {removed} plik(ów)" + (" i wpisy z biblioteki." if also_remove_from_library else "."),
        )
    if removed and on_done:
        on_done()
    return removed


def remove_from_library_only(
    parent: QtWidgets.QWidget,
    paths: list[str | Path],
    *,
    on_done: Callable[[], None] | None = None,
) -> int:
    norm = [str(p) for p in _normalize_paths(paths)]
    if not norm:
        return 0
    answer = QtWidgets.QMessageBox.question(
        parent,
        "Usuń z biblioteki",
        f"Usunąć {len(norm)} wpis(ów) z biblioteki?\nPliki na dysku pozostaną bez zmian.",
        QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
        QtWidgets.QMessageBox.StandardButton.No,
    )
    if answer != QtWidgets.QMessageBox.StandardButton.Yes:
        return 0
    try:
        delete_tracks_by_paths(norm)
    except Exception as exc:
        QtWidgets.QMessageBox.critical(parent, "Błąd", f"Nie udało się usunąć z biblioteki: {exc}")
        return 0
    if on_done:
        on_done()
    return len(norm)


def tracks_for_paths(paths: list[str | Path]) -> list[Track]:
    found: list[Track] = []
    for p in paths:
        try:
            t = get_track_by_path(str(p))
            if t:
                found.append(t)
        except Exception:
            pass
    return found


def add_file_operations_to_menu(
    menu: QtWidgets.QMenu,
    parent: QtWidgets.QWidget,
    paths: list[str | Path],
    *,
    tracks: list[Track] | None = None,
    on_library_changed: Callable[[], None] | None = None,
    open_organizer: Callable[[list[Track]], None] | None = None,
) -> None:
    """Dodaje podmenu „Plik” z podstawowymi operacjami."""
    norm = _normalize_paths(paths)
    if not norm:
        return
    file_menu = menu.addMenu("Plik")
    reveal_act = file_menu.addAction("Pokaż w Eksploratorze")
    copy_act = file_menu.addAction("Kopiuj plik do…")
    move_act = file_menu.addAction("Przenieś plik do…")
    file_menu.addSeparator()
    del_file_act = file_menu.addAction("Usuń plik z dysku")
    del_lib_act = file_menu.addAction("Usuń z biblioteki (zostaw plik)")
    if open_organizer is not None:
        file_menu.addSeparator()
        org_act = file_menu.addAction("Organizuj w kreatorze plików…")
    else:
        org_act = None

    def _paths_list() -> list[Path]:
        return norm

    reveal_act.triggered.connect(lambda: reveal_in_file_manager(str(norm[0])))
    copy_act.triggered.connect(lambda: copy_files_to_folder(parent, _paths_list(), on_done=on_library_changed))
    move_act.triggered.connect(lambda: move_files_to_folder(parent, _paths_list(), on_done=on_library_changed))
    del_file_act.triggered.connect(
        lambda: delete_files_physical(parent, _paths_list(), on_done=on_library_changed)
    )
    del_lib_act.triggered.connect(
        lambda: remove_from_library_only(parent, _paths_list(), on_done=on_library_changed)
    )
    if org_act is not None and open_organizer is not None:
        def _open_org() -> None:
            ts = tracks if tracks else tracks_for_paths(_paths_list())
            if ts:
                open_organizer(ts)
            else:
                QtWidgets.QMessageBox.information(
                    parent,
                    "Organizator",
                    "Brak wpisów w bibliotece dla wybranych ścieżek.",
                )

        org_act.triggered.connect(_open_org)


def attach_table_file_context_menu(
    table: QtWidgets.QTableWidget,
    parent: QtWidgets.QWidget,
    *,
    path_column: int = 0,
    extra_path_column: int | None = None,
    tracks: list[Track] | None = None,
    on_library_changed: Callable[[], None] | None = None,
    open_organizer: Callable[[list[Track]], None] | None = None,
) -> None:
    """Podłącza PPM do tabeli (np. w kreatorze organizacji / renamer)."""

    def _selected_paths() -> list[str]:
        rows = {idx.row() for idx in table.selectedIndexes()}
        if not rows and table.currentRow() >= 0:
            rows = {table.currentRow()}
        paths: list[str] = []
        for row in sorted(rows):
            item = table.item(row, path_column)
            if item and item.text().strip() and item.text() != "(do usunięcia)":
                paths.append(item.text().strip())
            if extra_path_column is not None:
                item2 = table.item(row, extra_path_column)
                if item2 and item2.text().strip() and item2.text() != "(do usunięcia)":
                    paths.append(item2.text().strip())
        return paths

    def _show_menu(pos) -> None:
        paths = _selected_paths()
        if not paths:
            return
        menu = QtWidgets.QMenu(table)
        add_file_operations_to_menu(
            menu,
            parent,
            paths,
            tracks=tracks,
            on_library_changed=on_library_changed,
            open_organizer=open_organizer,
        )
        menu.exec(table.viewport().mapToGlobal(pos))

    table.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
    table.customContextMenuRequested.connect(_show_menu)


def build_file_ops_button_bar(
    parent: QtWidgets.QWidget,
    table: QtWidgets.QTableWidget,
    *,
    path_column: int = 0,
    tracks: list[Track] | None = None,
    on_library_changed: Callable[[], None] | None = None,
    open_organizer: Callable[[list[Track]], None] | None = None,
) -> QtWidgets.QHBoxLayout:
    """Pasek przycisków operacji na plikach (dla kreatorów z konfliktami)."""

    def _paths() -> list[Path]:
        rows = {idx.row() for idx in table.selectedIndexes()}
        if not rows and table.currentRow() >= 0:
            rows = {table.currentRow()}
        out: list[Path] = []
        for row in sorted(rows):
            item = table.item(row, path_column)
            if item and item.text().strip() and item.text() != "(do usunięcia)":
                out.append(Path(item.text().strip()))
        return out

    bar = QtWidgets.QHBoxLayout()
    btn_explorer = QtWidgets.QPushButton("Eksplorator")
    btn_copy = QtWidgets.QPushButton("Kopiuj…")
    btn_move = QtWidgets.QPushButton("Przenieś…")
    btn_del_file = QtWidgets.QPushButton("Usuń plik")
    btn_del_lib = QtWidgets.QPushButton("Usuń z biblioteki")
    for b in (btn_explorer, btn_copy, btn_move, btn_del_file, btn_del_lib):
        b.setFixedHeight(28)
    if open_organizer is not None:
        btn_org = QtWidgets.QPushButton("Organizuj…")
        btn_org.setFixedHeight(28)
        bar.addWidget(btn_org)
        btn_org.clicked.connect(
            lambda: open_organizer(tracks or tracks_for_paths(_paths())) if _paths() else None
        )
    bar.addWidget(btn_explorer)
    bar.addWidget(btn_copy)
    bar.addWidget(btn_move)
    bar.addWidget(btn_del_file)
    bar.addWidget(btn_del_lib)
    bar.addStretch(1)
    btn_explorer.clicked.connect(lambda: reveal_in_file_manager(str(_paths()[0])) if _paths() else None)
    btn_copy.clicked.connect(lambda: copy_files_to_folder(parent, _paths(), on_done=on_library_changed))
    btn_move.clicked.connect(lambda: move_files_to_folder(parent, _paths(), on_done=on_library_changed))
    btn_del_file.clicked.connect(lambda: delete_files_physical(parent, _paths(), on_done=on_library_changed))
    btn_del_lib.clicked.connect(lambda: remove_from_library_only(parent, _paths(), on_done=on_library_changed))
    return bar