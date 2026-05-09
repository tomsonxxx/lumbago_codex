"""Library Widget - 3 tryby widoku: List, Grid, DJ Crate z filtrami."""
from __future__ import annotations
import json, logging
from enum import Enum
from typing import TYPE_CHECKING
from PyQt6 import QtCore, QtGui, QtWidgets

if TYPE_CHECKING:
    from lumbago_app.core.models import Track

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

        self.spin_bpm_min = QtWidgets.QSpinBox(); self.spin_bpm_min.setRange(0,300); self.spin_bpm_min.setSpecialValueText("—"); self.spin_bpm_min.setFixedWidth(55)
        self.spin_bpm_max = QtWidgets.QSpinBox(); self.spin_bpm_max.setRange(0,300); self.spin_bpm_max.setSpecialValueText("—"); self.spin_bpm_max.setFixedWidth(55)
        self.combo_key = QtWidgets.QComboBox(); self.combo_key.addItems(CAMELOT_KEYS); self.combo_key.setFixedWidth(64)
        self.combo_mood = QtWidgets.QComboBox(); self.combo_mood.addItems(MOOD_OPTIONS); self.combo_mood.setFixedWidth(100)
        self.spin_energy_min = QtWidgets.QDoubleSpinBox(); self.spin_energy_min.setRange(0,10); self.spin_energy_min.setSpecialValueText("—"); self.spin_energy_min.setFixedWidth(58)
        self.spin_energy_max = QtWidgets.QDoubleSpinBox(); self.spin_energy_max.setRange(0,10); self.spin_energy_max.setSpecialValueText("—"); self.spin_energy_max.setFixedWidth(58)
        self.combo_rating = QtWidgets.QComboBox(); self.combo_rating.addItems(["—","★","★★","★★★","★★★★","★★★★★"]); self.combo_rating.setFixedWidth(70)

        btn_reset = QtWidgets.QPushButton("✕"); btn_reset.setFixedSize(26,26); btn_reset.clicked.connect(self.reset_filters)

        def lbl(t): l=QtWidgets.QLabel(t); l.setStyleSheet("color:#8fb8d8;font-size:11px;"); return l
        def sep():
            s=QtWidgets.QFrame(); s.setFrameShape(QtWidgets.QFrame.Shape.VLine)
            s.setStyleSheet("color:#1e2d42;"); s.setFixedHeight(20); return s

        for w in [self.edit_search, sep(), lbl("BPM:"), self.spin_bpm_min, lbl("–"), self.spin_bpm_max,
                  sep(), lbl("Klucz:"), self.combo_key, sep(), lbl("Nastrój:"), self.combo_mood,
                  sep(), lbl("Energia:"), self.spin_energy_min, lbl("–"), self.spin_energy_max,
                  sep(), lbl("★:"), self.combo_rating, sep(), btn_reset]:
            layout.addWidget(w)
        layout.addStretch()

        for widget in [self.edit_search,self.spin_bpm_min,self.spin_bpm_max,self.combo_key,
                       self.combo_mood,self.spin_energy_min,self.spin_energy_max,self.combo_rating]:
            if isinstance(widget, QtWidgets.QLineEdit): widget.textChanged.connect(self._emit)
            elif isinstance(widget, (QtWidgets.QSpinBox,QtWidgets.QDoubleSpinBox)): widget.valueChanged.connect(self._emit)
            else: widget.currentIndexChanged.connect(self._emit)

    def _emit(self): self.filter_changed.emit(self.current_filters())

    def current_filters(self) -> dict:
        key = self.combo_key.currentText(); mood = self.combo_mood.currentText()
        return {
            "search_text": self.edit_search.text().strip() or None,
            "bpm_min": self.spin_bpm_min.value() or None,
            "bpm_max": self.spin_bpm_max.value() or None,
            "camelot_key": key if key != "—" else None,
            "mood": mood if mood != "—" else None,
            "energy_min": self.spin_energy_min.value() or None,
            "energy_max": self.spin_energy_max.value() or None,
            "rating_min": self.combo_rating.currentIndex() or None,
        }

    def reset_filters(self):
        self.edit_search.clear(); self.spin_bpm_min.setValue(0); self.spin_bpm_max.setValue(0)
        self.combo_key.setCurrentIndex(CAMELOT_KEYS.index("—")); self.combo_mood.setCurrentIndex(0)
        self.spin_energy_min.setValue(0); self.spin_energy_max.setValue(0); self.combo_rating.setCurrentIndex(0)


class SimpleTrackModel(QtCore.QAbstractTableModel):
    HEADERS = ["Tytuł","Artysta","BPM","Klucz","Gatunek","Czas","Format"]
    FIELDS  = ["title","artist","bpm","key","genre","duration","format"]

    def __init__(self, parent=None):
        super().__init__(parent); self._tracks: list = []

    def set_tracks(self, tracks: list):
        self.beginResetModel(); self._tracks = tracks; self.endResetModel()

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
        self.beginResetModel(); self._tracks = tracks; self.endResetModel()

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
        self._list_model.set_tracks(result); self._crate_model.set_tracks(result)
        self.lbl_count.setText(f"{len(result)} / {len(self._tracks)} tracków")

    @staticmethod
    def _camelot_ok(track_key, filter_key) -> bool:
        if not track_key: return False
        tk = track_key.strip().upper(); fk = filter_key.strip().upper()
        if tk == fk: return True
        try:
            from lumbago_app.services.beatgrid import camelot_adjacent_keys
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

    def _open_col_cfg(self):
        dlg = ColumnConfigDialog(self._col_cfg, self)
        if dlg.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            self._crate_model.refresh_columns()


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
