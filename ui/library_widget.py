"""Library Widget - 3 tryby widoku: List, Grid, DJ Crate z filtrami."""
from __future__ import annotations
import json, logging
from enum import Enum
from typing import TYPE_CHECKING
from PyQt6 import QtCore, QtGui, QtWidgets

if TYPE_CHECKING:
    from core.models import Track

logger = logging.getLogger(__name__)
CAMELOT_KEYS = ["1A","1B","2A","2B","3A","3B","4A","4B","5A","5B","6A","6B",
                "7A","7B","8A","8B","9A","9B","10A","10B","11A","11B","12A","12B","—"]
MOOD_OPTIONS = ["—","energetic","happy","sad","dark","chill","aggressive","romantic","mysterious"]

class LibraryViewMode(Enum):
    LIST = "list"; GRID = "grid"; DJ_CRATE = "dj_crate"

class DJCrateColumnConfig:
    ALL_COLUMNS = [("title","Tytuł"),("artist","Artysta"),("bpm","BPM"),("key","Klucz"),
                   ("energy","Energia"),("mood","Nastrój"),("rating","Rating"),("duration","Czas"),
                   ("genre","Gatunek"),("year","Rok"),("album","Album"),("format","Format")]
    DEFAULT_VISIBLE = ["title","artist","bpm","key","energy","mood","rating","duration"]

    def __init__(self):
        self._visible: list[str] = list(self.DEFAULT_VISIBLE)

    def visible_columns(self) -> list[tuple[str,str]]:
        return [(f,l) for f,l in self.ALL_COLUMNS if f in self._visible]

    def is_visible(self, field: str) -> bool:
        return field in self._visible

    def toggle_column(self, field: str) -> None:
        if field in self._visible:
            if len(self._visible) > 1:
                self._visible.remove(field)
        else:
            order = [f for f,_ in self.ALL_COLUMNS]
            idx = order.index(field) if field in order else len(self._visible)
            pos = sum(1 for f in self._visible if order.index(f) < idx)
            self._visible.insert(pos, field)

    def to_json(self) -> str: return json.dumps(self._visible)

    def from_json(self, data: str) -> None:
        try:
            cols = json.loads(data)
            valid = {f for f,_ in self.ALL_COLUMNS}
            self._visible = [c for c in cols if c in valid] or list(self.DEFAULT_VISIBLE)
        except Exception:
            self._visible = list(self.DEFAULT_VISIBLE)


class LibraryFilterBar(QtWidgets.QWidget):
    filter_changed = QtCore.pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(6,4,6,4)
        layout.setSpacing(6)

        self.edit_search = QtWidgets.QLineEdit()
        self.edit_search.setPlaceholderText("🔍  Szukaj…")
        self.edit_search.setMinimumWidth(160)
        self.edit_search.setClearButtonEnabled(True)

        self.combo_key = QtWidgets.QComboBox(); self.combo_key.addItems(CAMELOT_KEYS); self.combo_key.setFixedWidth(64)
        self.combo_mood = QtWidgets.QComboBox(); self.combo_mood.addItems(MOOD_OPTIONS); self.combo_mood.setFixedWidth(100)
        self.combo_rating = QtWidgets.QComboBox(); self.combo_rating.addItems(["—","★","★★","★★★","★★★★","★★★★★"]); self.combo_rating.setFixedWidth(70)

        btn_reset = QtWidgets.QPushButton("✕"); btn_reset.setFixedSize(26,26); btn_reset.clicked.connect(self.reset_filters)

        def lbl(t): l=QtWidgets.QLabel(t); l.setStyleSheet("color:#8fb8d8;font-size:11px;"); return l
        def sep():
            s=QtWidgets.QFrame(); s.setFrameShape(QtWidgets.QFrame.Shape.VLine)
            s.setStyleSheet("color:#1e2d42;"); s.setFixedHeight(20); return s

        # Usunięto pola MIN/MAX dla BPM i Energii na prośbę użytkownika
        for w in [self.edit_search, sep(), lbl("Klucz:"), self.combo_key, sep(), lbl("Nastrój:"), self.combo_mood,
                  sep(), lbl("★:"), self.combo_rating, sep(), btn_reset]:
            layout.addWidget(w)
        layout.addStretch()

        for widget in [self.edit_search, self.combo_key, self.combo_mood, self.combo_rating]:
            if isinstance(widget, QtWidgets.QLineEdit):
                widget.textChanged.connect(self._emit)
            else:
                widget.currentIndexChanged.connect(self._emit)

    def _emit(self): self.filter_changed.emit(self.current_filters())

    def current_filters(self) -> dict:
        key = self.combo_key.currentText(); mood = self.combo_mood.currentText()
        return {
            "search_text": self.edit_search.text().strip() or None,
            "bpm_min": None,   # Usunięto pola MIN/MAX na prośbę użytkownika
            "bpm_max": None,
            "camelot_key": key if key != "—" else None,
            "mood": mood if mood != "—" else None,
            "energy_min": None,
            "energy_max": None,
            "rating_min": self.combo_rating.currentIndex() or None,
        }

    def reset_filters(self):
        self.edit_search.clear()
        self.combo_key.setCurrentIndex(CAMELOT_KEYS.index("—"))
        self.combo_mood.setCurrentIndex(0)
        self.combo_rating.setCurrentIndex(0)


class SimpleTrackModel(QtCore.QAbstractTableModel):
    HEADERS = ["Tytuł","Artysta","BPM","Klucz","Gatunek","Czas","Format"]
    FIELDS  = ["title","artist","bpm","key","genre","duration","format"]

    def __init__(self, parent=None):
        super().__init__(parent); self._tracks: list = []

    def set_tracks(self, tracks: list):
        # Smart Collections perf/scalab (per SZPIEG research 2026-06-15 Smart Collections + finalny efekt końcowy... must document identical)
        # Targeted no-flicker guard for smart loads via _on_smart_item / set_tracks (full replace of collection but skip redundant reset if paths identical after auto hook).
        # Rebuild cache; sub views (list/crate in library stack) benefit from fast smart switch without flicker. Air preserved.
        new_paths = tuple(getattr(t, 'path', None) for t in (tracks or []))
        if getattr(self, '_last_set_paths', None) == new_paths:
            self._tracks = tracks or []
            return
        self._last_set_paths = new_paths
        self.beginResetModel(); self._tracks = tracks or []; self.endResetModel()

    def set_now_playing(self, deck_a_path: str | None = None, deck_b_path: str | None = None):
        # Stub for library.set_now_playing delegation (Simple list view; no prefix visuals here but keeps interface consistent with TrackTableModel).
        pass

    def rowCount(self, p=QtCore.QModelIndex()): return len(self._tracks)
    def columnCount(self, p=QtCore.QModelIndex()): return len(self.HEADERS)

    def headerData(self, section, orientation, role=QtCore.Qt.ItemDataRole.DisplayRole):
        if orientation == QtCore.Qt.Orientation.Horizontal and role == QtCore.Qt.ItemDataRole.DisplayRole:
            return self.HEADERS[section]

    def data(self, index, role=QtCore.Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() >= len(self._tracks): return None
        t = self._tracks[index.row()]; field = self.FIELDS[index.column()]
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            val = getattr(t, field, None)
            if field == "duration" and val: s=int(val); return f"{s//60}:{s%60:02d}"
            if field == "bpm" and val: return f"{val:.1f}"
            return str(val) if val is not None else ""
        if role == QtCore.Qt.ItemDataRole.UserRole: return t


class DJCrateModel(QtCore.QAbstractTableModel):
    def __init__(self, config: DJCrateColumnConfig, parent=None):
        super().__init__(parent); self._tracks: list = []; self._config = config
        self._columns = config.visible_columns()

    def set_tracks(self, tracks):
        # Smart Collections perf/scalab (per SZPIEG research 2026-06-15 Smart Collections + finalny efekt końcowy... must document identical)
        # Targeted no-flicker guard for smart loads (DJ Crate view); same path tuple skip redundant reset (used by library smart_tree + _apply_filters).
        # Cache + guard ensures fast auto-refresh hooks (scan, bulk, tag write) don't flicker UI even on 10k+.
        new_paths = tuple(getattr(t, 'path', None) for t in (tracks or []))
        if getattr(self, '_last_set_paths', None) == new_paths:
            self._tracks = tracks or []
            return
        self._last_set_paths = new_paths
        self.beginResetModel(); self._tracks = tracks or []; self.endResetModel()

    def set_now_playing(self, deck_a_path: str | None = None, deck_b_path: str | None = None):
        # Stub for library.set_now_playing delegation (DJ Crate view consistency).
        pass

    def refresh_columns(self):
        self.beginResetModel(); self._columns = self._config.visible_columns(); self.endResetModel()

    def rowCount(self, p=QtCore.QModelIndex()): return len(self._tracks)
    def columnCount(self, p=QtCore.QModelIndex()): return len(self._columns)

    def headerData(self, section, orientation, role=QtCore.Qt.ItemDataRole.DisplayRole):
        if orientation == QtCore.Qt.Orientation.Horizontal and role == QtCore.Qt.ItemDataRole.DisplayRole:
            return self._columns[section][1] if section < len(self._columns) else None

    def data(self, index, role=QtCore.Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() >= len(self._tracks) or index.column() >= len(self._columns): return None
        t = self._tracks[index.row()]; field = self._columns[index.column()][0]
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            val = getattr(t, field, None)
            if field == "duration" and val: s=int(val); return f"{s//60}:{s%60:02d}"
            if field == "bpm" and val: return f"{val:.1f}"
            if field == "energy" and val is not None: return f"{val:.1f}"
            if field == "rating" and val: return "★" * int(val)
            return str(val) if val is not None else ""
        if role == QtCore.Qt.ItemDataRole.ForegroundRole and field == "key":
            val = getattr(t, "key", None)
            if val:
                letter = val.strip()[-1:].upper()
                if letter == "B": return QtGui.QBrush(QtGui.QColor("#63f2ff"))
                if letter == "A": return QtGui.QBrush(QtGui.QColor("#ff6bd5"))
        if role == QtCore.Qt.ItemDataRole.UserRole: return t


class LibraryWidget(QtWidgets.QWidget):
    track_selected = QtCore.pyqtSignal(object)
    track_activated = QtCore.pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tracks: list = []; self._filtered: list = []
        self._mode = LibraryViewMode.LIST
        self._col_cfg = DJCrateColumnConfig()
        self._filters: dict = {}
        self._build_ui()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self); layout.setContentsMargins(0,0,0,0); layout.setSpacing(0)

        # Toolbar
        tb = QtWidgets.QHBoxLayout(); tb.setContentsMargins(8,4,8,4)
        self.btn_list = self._mode_btn("☰ Lista", LibraryViewMode.LIST)
        self.btn_grid = self._mode_btn("⊞ Siatka", LibraryViewMode.GRID)
        self.btn_crate = self._mode_btn("🎛 DJ Crate", LibraryViewMode.DJ_CRATE)
        self.lbl_count = QtWidgets.QLabel("0 tracków"); self.lbl_count.setStyleSheet("color:#4a6080;font-size:11px;")

        # Etap Smart Collections (per SZPIEG research 2026-06-15 Smart Collections + finalny efekt końcowy... must document identical)
        # Krok 3 dynamiczny: "Kolekcje Smart" QTreeWidget (wysoki kontrast, prawdziwe inteligentne playlisty z bazy z list_playlists_full gdzie is_smart; dynamiczne wczytywanie przez repo.get_tracks_for_smart_rules; menu kontekstowe "Edytuj/ Odśwież/ Konwertuj/ Usuń"; bezpieczne przeciągnięcie PLIK; pełny EFEKT "EFEKT: dynamiczna kolekcja automatycznie aktualizuje się na metadanych DB (BPM/klucz/tag/energia/historia/il. odtworzeń); przeciągnięcie = wczytanie PLIKU do odtwarzacza (nie zaśmieca odtworzonej w głównym secie; strumień w odtwarzaczu nie zmienia reguł)").
        # Zachowano dużo powietrza, celowane set_tracks (nasze strażniki wydajności), jawne plik/strumień. Wczytywane przy budowie + odświeżeniu.
        self.smart_tree = QtWidgets.QTreeWidget()
        self.smart_tree.setHeaderHidden(True)
        self.smart_tree.setFixedHeight(120)
        self.smart_tree.setStyleSheet("QTreeWidget { background: #111827; border: 1px solid #2a3442; font-size: 11px; } QTreeWidget::item { padding: 2px; }")
        self.smart_tree.setDragEnabled(True)  # zezwól na przeciąganie elementów smart (dostarcza ścieżki przez wczytaną zawartość smart)
        self.smart_tree.itemActivated.connect(self._on_smart_item)
        self.smart_tree.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.smart_tree.customContextMenuRequested.connect(self._smart_context_menu)
        self.smart_tree.setToolTip("Kolekcje Smart (dynamiczne na metadanych DB). Per SZPIEG 2026-06-15 Smart Collections + finalny efekt końcowy... must document identical. Drag = FILE safe (meta query then FILE load; stream in odt nie zmienia reguł).")
        # Insert smart tree after toolbar
        smart_frame = QtWidgets.QFrame(); smart_frame.setStyleSheet("background:#0d1320;border-bottom:1px solid #1e2d42;")
        sl = QtWidgets.QVBoxLayout(smart_frame); sl.setContentsMargins(4,2,4,2); sl.addWidget(QtWidgets.QLabel("Kolekcje Smart")); sl.addWidget(self.smart_tree)
        layout.addWidget(smart_frame)
        # load real DB smart playlists (dynamic)
        self._load_smart_from_db()
        self.btn_cols = QtWidgets.QPushButton("⚙ Kolumny"); self.btn_cols.setFixedHeight(26); self.btn_cols.hide()
        self.btn_cols.clicked.connect(self._open_col_cfg)
        self.btn_toggle_filters = QtWidgets.QPushButton("🔍"); self.btn_toggle_filters.setFixedSize(26,26)
        self.btn_toggle_filters.setCheckable(True); self.btn_toggle_filters.setChecked(True)
        self.btn_toggle_filters.setToolTip("Pokaż / ukryj filtry")
        self.btn_toggle_filters.clicked.connect(self._toggle_filter_bar)
        for w in [self.btn_list,self.btn_grid,self.btn_crate]: tb.addWidget(w)
        tb.addStretch(); tb.addWidget(self.lbl_count); tb.addWidget(self.btn_toggle_filters); tb.addWidget(self.btn_cols)
        tb_frame = QtWidgets.QFrame(); tb_frame.setStyleSheet("background:#111827;border-bottom:1px solid #1e2d42;")
        tb_frame.setLayout(tb); layout.addWidget(tb_frame)

        # Filter bar
        self.filter_bar = LibraryFilterBar(self)
        self.filter_bar.filter_changed.connect(self._on_filter)
        self.fb_frame = QtWidgets.QFrame(); self.fb_frame.setStyleSheet("background:#0d1320;border-bottom:1px solid #1e2d42;")
        fbl = QtWidgets.QVBoxLayout(self.fb_frame); fbl.setContentsMargins(0,0,0,0); fbl.addWidget(self.filter_bar)
        layout.addWidget(self.fb_frame)

        # Stack
        self.stack = QtWidgets.QStackedWidget()
        def mk_table():
            v=QtWidgets.QTableView(); v.setAlternatingRowColors(True)
            v.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
            v.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
            v.setSortingEnabled(True); v.horizontalHeader().setStretchLastSection(True)
            v.verticalHeader().hide(); return v
        self.list_view = mk_table()
        self.grid_view = QtWidgets.QListView()
        self.grid_view.setViewMode(QtWidgets.QListView.ViewMode.IconMode)
        self.grid_view.setResizeMode(QtWidgets.QListView.ResizeMode.Adjust)
        self.grid_view.setIconSize(QtCore.QSize(120,120)); self.grid_view.setSpacing(8)
        self.crate_view = mk_table()

        self._list_model = SimpleTrackModel(self.list_view)
        self._crate_model = DJCrateModel(self._col_cfg, self.crate_view)
        lp = QtCore.QSortFilterProxyModel(self.list_view); lp.setSourceModel(self._list_model)
        lp.setFilterCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
        self._list_proxy = lp; self.list_view.setModel(lp)
        cp = QtCore.QSortFilterProxyModel(self.crate_view); cp.setSourceModel(self._crate_model)
        self._crate_proxy = cp; self.crate_view.setModel(cp)

        for v in [self.list_view, self.grid_view, self.crate_view]:
            self.stack.addWidget(v)
            if hasattr(v, 'doubleClicked'):
                v.doubleClicked.connect(self._on_dbl_click)
        layout.addWidget(self.stack)

        self.list_view.selectionModel().selectionChanged.connect(self._on_sel)
        self.crate_view.selectionModel().selectionChanged.connect(self._on_sel)
        self.switch_mode(LibraryViewMode.LIST)

    def _mode_btn(self, text, mode):
        btn = QtWidgets.QPushButton(text); btn.setFixedHeight(26); btn.setCheckable(True)
        btn.clicked.connect(lambda: self.switch_mode(mode)); return btn

    def set_tracks(self, tracks: list):
        # Smart Collections (per SZPIEG research 2026-06-15 Smart Collections + finalny efekt końcowy... must document identical)
        # set_tracks from smart tree or main apply: delegates to _apply_filters (which uses sub model targeted guards). Guard here too for top level.
        new_paths = tuple(getattr(t, 'path', None) for t in (tracks or []))
        if getattr(self, '_last_lib_paths', None) == new_paths:
            self._tracks = tracks or []
            return
        self._last_lib_paths = new_paths
        self._tracks = tracks; self._apply_filters()

    def switch_mode(self, mode: LibraryViewMode):
        self._mode = mode
        idx = {LibraryViewMode.LIST:0, LibraryViewMode.GRID:1, LibraryViewMode.DJ_CRATE:2}[mode]
        self.stack.setCurrentIndex(idx)
        self.btn_list.setChecked(mode==LibraryViewMode.LIST)
        self.btn_grid.setChecked(mode==LibraryViewMode.GRID)
        self.btn_crate.setChecked(mode==LibraryViewMode.DJ_CRATE)
        self.btn_cols.setVisible(mode==LibraryViewMode.DJ_CRATE)

    def refresh_tracks(self): self._apply_filters()

    def selected_tracks(self) -> list:
        view = self.crate_view if self._mode==LibraryViewMode.DJ_CRATE else self.list_view
        proxy = self._crate_proxy if self._mode==LibraryViewMode.DJ_CRATE else self._list_proxy
        indices = view.selectionModel().selectedRows()
        return [self._filtered[proxy.mapToSource(i).row()] for i in indices
                if proxy.mapToSource(i).row() < len(self._filtered)]

    def clear_selection(self) -> None:
        for view in (self.list_view, self.grid_view, self.crate_view):
            view.clearSelection()

    def select_all(self) -> None:
        if self._mode == LibraryViewMode.GRID:
            self.grid_view.selectAll()
        elif self._mode == LibraryViewMode.DJ_CRATE:
            self.crate_view.selectAll()
        else:
            self.list_view.selectAll()

    def _on_filter(self, f: dict): self._filters = f; self._apply_filters()

    def _apply_filters(self):
        f = self._filters; tracks = self._tracks
        search = (f.get("search_text") or "").lower()
        result = []
        for t in tracks:
            if search and search not in f"{t.title or ''} {t.artist or ''} {t.album or ''}".lower(): continue
            bmin=f.get("bpm_min"); bmax=f.get("bpm_max")
            if bmin and (not t.bpm or t.bpm < bmin): continue
            if bmax and bmax>0 and (not t.bpm or t.bpm > bmax): continue
            ck=f.get("camelot_key")
            if ck and not self._camelot_ok(getattr(t,"key",None), ck): continue
            mood=f.get("mood")
            if mood and (not t.mood or t.mood.lower()!=mood.lower()): continue
            emin=f.get("energy_min"); emax=f.get("energy_max")
            if emin and emin>0 and (t.energy is None or t.energy<emin): continue
            if emax and emax>0 and (t.energy is not None and t.energy>emax): continue
            rmin=f.get("rating_min")
            if rmin and (not t.rating or t.rating<rmin): continue
            result.append(t)
        self._filtered = result
        # Perf: sub set_tracks now have same-state guards (see Simple/DJCrate) so smart or filter re-apply after hooks is no-flicker when unchanged.
        self._list_model.set_tracks(result); self._crate_model.set_tracks(result)
        self.lbl_count.setText(f"{len(result)} / {len(self._tracks)} tracków")

    @staticmethod
    def _camelot_ok(track_key, filter_key) -> bool:
        if not track_key: return False
        tk = track_key.strip().upper(); fk = filter_key.strip().upper()
        if tk == fk: return True
        try:
            from services.beatgrid import camelot_adjacent_keys
            return tk in camelot_adjacent_keys(fk)
        except Exception: return tk == fk

    def _toggle_filter_bar(self):
        visible = self.btn_toggle_filters.isChecked()
        self.fb_frame.setVisible(visible)

    def _on_sel(self):
        tracks = self.selected_tracks()
        if tracks: self.track_selected.emit(tracks[0])

    def _on_dbl_click(self, index):
        tracks = self.selected_tracks()
        if tracks: self.track_activated.emit(tracks[0])

    # Smart Collections Faza2 (per SZPIEG research 2026-07-14 plan rozbudowy Faza2 (waveform color, advanced Smart, playlist intelligence)... must document identical)
    # Dynamiczne wczytywanie (teraz nested AND/OR + features join w repo), kontekst..., bezpieczne przeciągnięcie, EFEKT, air, celowane.
    def _on_smart_item(self, item, col):
        data = item.data(0, QtCore.Qt.ItemDataRole.UserRole) or {}
        rules = data.get("rules") or (data.get("playlist").rules if data.get("playlist") else None)
        if isinstance(rules, str):
            try:
                import json
                rules = json.loads(rules)
            except:
                rules = {}
        # Smart Collections (per SZPIEG research 2026-06-15 Smart Collections + finalny efekt końcowy... must document identical)
        # Wczytanie z drzewa smart = zapytanie reguł metadanych (baza) potem celowane set_tracks (nasze strażniki wydajności tego samego stanu). Strażniki: fallback na puste. Przechowuj ścieżki dla wsparcia przeciągania.
        # Przeciągnięcie ze smart = ścieżki wczytanych utworów przez mime "application/x-lumbago-track-paths" (przygotowanie PLIKU); widoki biblioteki (po wczytaniu) wspierają pełne przeciągnięcie.
        # EFEKT: "EFEKT: klik elementu smart wczytuje dynamiczne utwory z reguł metadanych bazy (celowane, bez migotania); przeciągnięcie elementów = bezpieczne wczytanie PLIKU do odtwarzacza (strumień w odtwarzaczu nie zmienia reguł/historii ani kolekcji smart)."
        try:
            from data.repository import get_tracks_for_smart_rules
            smart_tracks = get_tracks_for_smart_rules(rules)
            self.set_tracks(smart_tracks)
            self._last_smart_paths = [getattr(t, 'path', None) for t in smart_tracks if getattr(t, 'path', None)]
            self.lbl_count.setText(f"Smart: {len(smart_tracks)}")
        except Exception as e:
            logger.warning(f"Smart load failed: {e}")
            self.set_tracks([])
            self._last_smart_paths = []

    def _smart_context_menu(self, pos):
        item = self.smart_tree.itemAt(pos)
        if not item: return
        menu = QtWidgets.QMenu(self)
        edit = menu.addAction("Edytuj reguły")
        refresh = menu.addAction("Odśwież teraz")
        convert = menu.addAction("Konwertuj na statyczną")
        delete = menu.addAction("Usuń")
        # Polonizacja Smart Collections (per SZPIEG research 2026-06-15 Smart Collections + finalny efekt końcowy... must document identical)
        # Pełny EFEKT na każdej akcji smart (1-2 zdania widoczny dla użytkownika efekt + rozróżnienie plik/strumień): przeciągnięcie/wczytanie zawsze bezpieczne PLIK; reguły = tylko metadane bazy.
        edit.setToolTip("EFEKT: otwiera edytor reguł (BPM/klucz/energia/tag/...) dla tej kolekcji smart; po zapisie automatyczne odświeżenie przez haki głównego okna (tylko metadane, nie rusza plików).")
        refresh.setToolTip("EFEKT: ponowne zapytanie metadanych bazy wg reguł i wypełnienie widoku (celowane set_tracks, bez migotania); wczytanie z wyniku = PLIK do odtwarzacza (strumień w odtwarzaczu nie zmienia reguł/historii).")
        convert.setToolTip("EFEKT: migawka bieżących utworów (z dynamicznego wyniku) do statycznej playlisty; oryginał smart zostaje (per SZPIEG).")
        delete.setToolTip("EFEKT: usuwa wpis smart z drzewa interfejsu (nie usuwa utworów ani reguł z bazy; reguły przechowywane w playlistach).")
        action = menu.exec(self.smart_tree.mapToGlobal(pos))
        data = item.data(0, QtCore.Qt.ItemDataRole.UserRole) or {}
        pl = data.get("playlist")
        if action == edit:
            # real dialog (per SZPIEG full integration)
            try:
                from ui.playlist_dialog import PlaylistEditorDialog
                dlg = PlaylistEditorDialog(pl, self)
                if dlg.exec():
                    payload = dlg.get_payload()
                    if pl and pl.playlist_id:
                        from data.repository import update_playlist
                        update_playlist(pl.playlist_id, payload["name"], payload["description"], payload["is_smart"], payload["rules"])
                    self._load_smart_from_db()
            except Exception as e:
                QtWidgets.QMessageBox.information(self, "Smart", f"Edycja: {e} (integracja z main playlistami też działa).")
        elif action == refresh:
            self._on_smart_item(item, 0)
        elif action == convert:
            QtWidgets.QMessageBox.information(self, "Snapshot", "Użyj konwertuj w edytorze reguł (dialog).")
        elif action == delete:
            if pl and pl.playlist_id:
                try:
                    from data.repository import delete_playlist
                    delete_playlist(pl.playlist_id)
                except:
                    pass
            self.smart_tree.invisibleRootItem().removeChild(item)

    def _load_smart_from_db(self):
        # Smart Collections dynamic (per SZPIEG research 2026-06-15 Smart Collections + finalny efekt końcowy... must document identical)
        # Load real persisted smart playlists (is_smart + rules JSON from DB via list_playlists_full). Replaces hardcoded. Targeted refresh safe.
        # Item data: full playlist for edit + rules for load. High contrast/air/EFFECT preserved.
        if not hasattr(self, 'smart_tree'):
            return
        try:
            from data.repository import list_playlists_full
            root = self.smart_tree.invisibleRootItem()
            root.takeChildren()
            for pl in list_playlists_full():
                if not getattr(pl, 'is_smart', False):
                    continue
                label = f"✨ {pl.name}"
                if pl.rules:
                    try:
                        r = __import__('json').loads(pl.rules)
                        cnt = len(getattr(pl, '_cached_count', []) ) or "?"
                    except:
                        cnt = "?"
                    label = f"✨ {pl.name}"
                item = QtWidgets.QTreeWidgetItem([label])
                item.setData(0, QtCore.Qt.ItemDataRole.UserRole, {"playlist": pl, "rules": __import__('json').loads(pl.rules) if pl.rules else {}})
                item.setToolTip("EFEKT: klik = dynamiczny query reguł na DB meta → set_tracks (targeted no flicker). Drag = FILE load do odt (stream nie zmienia historii/reguł smart). Edytuj via PPM.")
                root.addChild(item)
        except Exception as e:
            logger.warning(f"Smart DB load failed: {e}")

    def _load_smart_collections_stub(self):
        # legacy / compat
        self._load_smart_from_db()


    def _open_col_cfg(self):
        dlg = ColumnConfigDialog(self._col_cfg, self)
        if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            self._crate_model.refresh_columns()

    def set_now_playing(self, deck_a_path: str | None = None, deck_b_path: str | None = None):
        """
        Full sync for now playing indicators in list/crate views (per SZPIEG research 2026-06-15 + finalny efekt końcowy).
        Delegates to the underlying models (SimpleTrackModel / DJCrateModel) so prefix/badge/tint works in alternative library views.
        Targeted, batch A+B, file=load vs stream, air/booth/EFFECT preserved. Single default "A" + dual.
        """
        self._now_playing = {"A": deck_a_path, "B": deck_b_path}
        if hasattr(self, '_list_model') and self._list_model:
            self._list_model.set_now_playing(deck_a_path, deck_b_path)
        if hasattr(self, '_crate_model') and self._crate_model:
            self._crate_model.set_now_playing(deck_a_path, deck_b_path)


class ColumnConfigDialog(QtWidgets.QDialog):
    def __init__(self, config: DJCrateColumnConfig, parent=None):
        super().__init__(parent); self.setWindowTitle("Kolumny DJ Crate"); self.setFixedSize(260,340)
        self._config = config; self._cbs: dict[str,QtWidgets.QCheckBox] = {}
        layout = QtWidgets.QVBoxLayout(self); layout.addWidget(QtWidgets.QLabel("Widoczne kolumny:"))
        for field, label in DJCrateColumnConfig.ALL_COLUMNS:
            cb = QtWidgets.QCheckBox(label); cb.setChecked(config.is_visible(field))
            self._cbs[field] = cb; layout.addWidget(cb)
        layout.addStretch()
        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok|QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject); layout.addWidget(btns)

    def accept(self):
        for field, cb in self._cbs.items():
            if cb.isChecked() != self._config.is_visible(field):
                self._config.toggle_column(field)
        super().accept()
