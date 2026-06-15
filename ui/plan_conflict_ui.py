"""Menu kontekstowe i kontrolki auto-rozwiązywania konfliktów w planach rename/organize."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PyQt6 import QtCore, QtWidgets

from core.renamer import (
    PlanItem,
    auto_resolve_plan_conflicts,
    refresh_plan_conflicts,
    remove_plan_items_at_indices,
    resolve_plan_item_to_conflicts_folder,
    resolve_plan_item_with_suffix,
    set_plan_item_target_path,
)
from ui.file_track_ops import add_file_operations_to_menu, delete_files_physical

PLAN_ITEM_INDEX_ROLE = QtCore.Qt.ItemDataRole.UserRole + 42


def plan_index_from_row(table: QtWidgets.QTableWidget, row: int, status_column: int) -> int | None:
    item = table.item(row, status_column)
    if item is None:
        return None
    idx = item.data(PLAN_ITEM_INDEX_ROLE)
    return int(idx) if idx is not None else None


def set_plan_index_on_status_item(
    status_item: QtWidgets.QTableWidgetItem,
    plan_index: int,
) -> None:
    status_item.setData(PLAN_ITEM_INDEX_ROLE, plan_index)


def build_auto_resolve_controls(
    parent: QtWidgets.QWidget,
    *,
    on_resolve: Callable[[str], None],
) -> QtWidgets.QHBoxLayout:
    """Combo strategii + przycisk automatycznego rozwiązywania konfliktów."""
    row = QtWidgets.QHBoxLayout()
    row.addWidget(QtWidgets.QLabel("Auto-rozwiązywanie:"))
    strategy_combo = QtWidgets.QComboBox(parent)
    strategy_combo.addItem("Sufiks numerowany (_2, _3…)", "suffix")
    strategy_combo.addItem("Folder _Konflikty", "duplicates_folder")
    strategy_combo.setToolTip(
        "Strategia dla przycisku „Rozwiąż wszystkie konflikty” — nadaje unikalne ścieżki docelowe."
    )
    resolve_btn = QtWidgets.QPushButton("Rozwiąż wszystkie konflikty")
    resolve_btn.setToolTip("Automatycznie nadpisz docelowe ścieżki dla wszystkich kolizji w planie.")
    resolve_btn.clicked.connect(
        lambda: on_resolve(str(strategy_combo.currentData() or "suffix"))
    )
    row.addWidget(strategy_combo, 1)
    row.addWidget(resolve_btn)
    row.addStretch(1)
    return row


def _selected_plan_indices(
    table: QtWidgets.QTableWidget,
    status_column: int,
) -> list[int]:
    rows = {idx.row() for idx in table.selectedIndexes()}
    if not rows and table.currentRow() >= 0:
        rows = {table.currentRow()}
    indices: list[int] = []
    for row in sorted(rows):
        plan_idx = plan_index_from_row(table, row, status_column)
        if plan_idx is not None:
            indices.append(plan_idx)
    return indices


def _paths_from_rows(
    table: QtWidgets.QTableWidget,
    rows: set[int],
    *,
    path_column: int,
    extra_path_column: int | None,
) -> list[str]:
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


def attach_plan_table_context_menu(
    table: QtWidgets.QTableWidget,
    parent: QtWidgets.QWidget,
    *,
    get_full_plan: Callable[[], list[PlanItem]],
    on_plan_changed: Callable[[], None],
    path_column: int = 0,
    extra_path_column: int | None = None,
    status_column: int = 2,
    tracks: list | None = None,
    on_library_changed: Callable[[], None] | None = None,
    open_organizer: Callable[[list], None] | None = None,
) -> None:
    """PPM: rozwiązywanie konfliktów + standardowe operacje na plikach."""

    def _refresh() -> None:
        on_plan_changed()
        if on_library_changed:
            on_library_changed()

    def _show_menu(pos) -> None:
        rows = {idx.row() for idx in table.selectedIndexes()}
        if not rows and table.currentRow() >= 0:
            rows = {table.currentRow()}
        if not rows:
            return

        plan = get_full_plan()
        plan_indices = _selected_plan_indices(table, status_column)
        paths = _paths_from_rows(
            table,
            rows,
            path_column=path_column,
            extra_path_column=extra_path_column,
        )

        menu = QtWidgets.QMenu(table)
        conflict_items: list[tuple[int, PlanItem]] = []
        for pidx in plan_indices:
            if 0 <= pidx < len(plan) and plan[pidx].conflict:
                conflict_items.append((pidx, plan[pidx]))

        if conflict_items:
            conflict_menu = menu.addMenu("Rozwiąż konflikt")
            act_suffix = conflict_menu.addAction("Dodaj sufiks do nazwy (_2, _3…)")
            act_folder = conflict_menu.addAction("Przenieś do folderu _Konflikty")
            act_edit = conflict_menu.addAction("Zmień docelową ścieżkę…")
            conflict_menu.addSeparator()
            act_skip = conflict_menu.addAction("Pomiń w planie (usuń wiersz)")
            act_del_src = conflict_menu.addAction("Usuń plik źródłowy z dysku")
            act_del_dst = conflict_menu.addAction("Usuń istniejący plik docelowy")

            def _apply_to_conflicts(handler: Callable[[PlanItem, list[PlanItem]], bool | None]) -> None:
                full = get_full_plan()
                touched = False
                for pidx, item in conflict_items:
                    if 0 <= pidx < len(full):
                        if handler(full[pidx], full):
                            touched = True
                if touched:
                    on_plan_changed()

            act_suffix.triggered.connect(
                lambda: _apply_to_conflicts(
                    lambda item, full: resolve_plan_item_with_suffix(item, full)
                )
            )
            act_folder.triggered.connect(
                lambda: _apply_to_conflicts(
                    lambda item, full: resolve_plan_item_to_conflicts_folder(item, full)
                )
            )

            def _edit_target() -> None:
                full = get_full_plan()
                if not conflict_items:
                    return
                pidx, item = conflict_items[0]
                if getattr(item, "action", "rename") == "delete":
                    return
                start = str(item.new_path)
                new_text, ok = QtWidgets.QInputDialog.getText(
                    parent,
                    "Zmień docelową ścieżkę",
                    "Nowa ścieżka docelowa:",
                    QtWidgets.QLineEdit.EchoMode.Normal,
                    start,
                )
                if ok and new_text.strip():
                    set_plan_item_target_path(item, Path(new_text.strip()), full)
                    on_plan_changed()

            act_edit.triggered.connect(_edit_target)

            def _skip_rows() -> None:
                full = get_full_plan()
                remove_plan_items_at_indices(full, plan_indices)
                on_plan_changed()

            act_skip.triggered.connect(_skip_rows)

            def _delete_sources() -> None:
                src_paths = [str(plan[pidx].old_path) for pidx, _ in conflict_items if 0 <= pidx < len(plan)]
                if src_paths:
                    delete_files_physical(parent, src_paths, on_done=_refresh)

            act_del_src.triggered.connect(_delete_sources)

            def _delete_destinations() -> None:
                full = get_full_plan()
                dst_paths: list[str] = []
                for pidx, item in conflict_items:
                    if 0 <= pidx < len(full):
                        dst = full[pidx].new_path
                        if dst.exists() and dst != full[pidx].old_path:
                            dst_paths.append(str(dst))
                if not dst_paths:
                    QtWidgets.QMessageBox.information(
                        parent,
                        "Brak pliku docelowego",
                        "Nie znaleziono istniejącego pliku docelowego do usunięcia "
                        "(konflikt może wynikać z duplikatu w samym planie).",
                    )
                    return
                delete_files_physical(
                    parent,
                    dst_paths,
                    also_remove_from_library=False,
                    on_done=lambda: (refresh_plan_conflicts(full), on_plan_changed()),
                )

            act_del_dst.triggered.connect(_delete_destinations)
            menu.addSeparator()

        if paths:
            add_file_operations_to_menu(
                menu,
                parent,
                paths,
                tracks=tracks,
                on_library_changed=on_library_changed,
                open_organizer=open_organizer,
            )

        if not menu.isEmpty():
            menu.exec(table.viewport().mapToGlobal(pos))

    table.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
    table.customContextMenuRequested.connect(_show_menu)


def run_auto_resolve_dialog(
    parent: QtWidgets.QWidget,
    plan: list[PlanItem],
    strategy: str,
    *,
    on_done: Callable[[], None],
) -> None:
    """Uruchom auto-resolve i pokaż podsumowanie."""
    before = sum(1 for i in plan if i.conflict)
    if before == 0:
        QtWidgets.QMessageBox.information(parent, "Konflikty", "Brak konfliktów w planie.")
        return
    changed = auto_resolve_plan_conflicts(plan, strategy=strategy)
    after = sum(1 for i in plan if i.conflict)
    on_done()
    QtWidgets.QMessageBox.information(
        parent,
        "Rozwiązywanie konfliktów",
        f"Zmieniono {changed} pozycji.\n"
        f"Konflikty: {before} → {after}"
        + ("" if after == 0 else "\n\nPozostałe kolizje wymagają ręcznej interwencji (PPM na wierszu)."),
    )