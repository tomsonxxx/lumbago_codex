from __future__ import annotations

import json

from PyQt6 import QtWidgets, QtGui
from ui.widgets import apply_dialog_fade, dialog_icon_pixmap

from core.models import Playlist
# Smart Collections (per SZPIEG research 2026-06-15 Smart Collections + finalny efekt końcowy... must document identical)
# Licznik na żywo i konwersja używają prawdziwego zapytania do repo na metadanych bazy (bez dotykania plików). Przeciągnięcie wyniku = wczytanie PLIKU do odtwarzacza (izolacja strumienia).
from data.repository import get_tracks_for_smart_rules, create_playlist, list_playlists_full, list_playlist_tracks, add_track_to_playlist


class PlaylistEditorDialog(QtWidgets.QDialog):
    def __init__(self, playlist: Playlist | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Playlista")
        self.setMinimumSize(520, 360)
        apply_dialog_fade(self)
        self._playlist = playlist
        self._build_ui()
        if playlist:
            self._load(playlist)

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

        # Per SZPIEG research 2026-06-15 Smart Collections + finalny efekt końcowy (rich builder like RB/Lexicon/VDJ, any/all, live count, Polish, EFFECT 1-2zd on every, convert snapshot, rules on meta only) — must document identical.
        # Step 2: full rule builder (expand basic form). Polish texts. EFFECT: "EFEKT: reguła na metadanych DB (nie pliki); auto-odświeża kolekcję na zmianie tagu/analizy/historii; drag z kolekcji = bezpieczny FILE load do odt (nie pollute main set)".
        self.name_input = QtWidgets.QLineEdit()
        self.name_input.setToolTip("EFEKT: nazwa kolekcji widoczna w sidebarze playlist i 'Kolekcje Smart' (z (smart) suffix). Zapis do DB; load tej nazwy = dynamiczny query reguł na meta DB.")
        self.desc_input = QtWidgets.QLineEdit()
        self.desc_input.setToolTip("EFEKT: opcjonalny opis reguł (widoczny w UI). Nie wpływa na query.")
        self.smart_check = QtWidgets.QCheckBox("Playlista smart (reguły dynamiczne)")
        self.smart_check.setToolTip("EFEKT: jeśli zaznaczone — to dynamiczna kolekcja (auto-update na zmianie meta w DB: tagi/analiza/play_count/bpm/key/energy). Jeśli odznaczone — zwykła statyczna lista utworów. Drag z smart = zawsze FILE prep (nie stream). Per SZPIEG 2026-06-15 Smart Collections + finalny efekt.")

        layout.addWidget(QtWidgets.QLabel("Nazwa"))
        layout.addWidget(self.name_input)
        layout.addWidget(QtWidgets.QLabel("Opis"))
        layout.addWidget(self.desc_input)
        layout.addWidget(self.smart_check)

        # Rules builder area
        self.rules_widget = QtWidgets.QWidget()
        self.rules_layout = QtWidgets.QVBoxLayout(self.rules_widget)
        self.rules_layout.setContentsMargins(0, 0, 0, 0)
        self.conditions = []  # list of row widgets

        any_all = QtWidgets.QHBoxLayout()
        self.any_all_combo = QtWidgets.QComboBox()
        self.any_all_combo.addItems(["Dopasuj wszystkie reguły", "Dopasuj dowolną regułę"])
        self.any_all_combo.setToolTip("EFEKT: AND (wszystkie muszą pasować) lub OR (dowolna reguła). Reguły na metadanych DB (BPM/key/tag/energia/play_count/data/mood/gatunek/analiza) — nigdy na plikach surowych. Auto refresh kolekcji po meta change. Drag z wyniku = bezpieczny FILE load do odt.")
        any_all.addWidget(QtWidgets.QLabel("Dopasowanie:"))
        any_all.addWidget(self.any_all_combo)
        any_all.addStretch(1)
        layout.addLayout(any_all)

        add_btn = QtWidgets.QPushButton("+ Dodaj regułę")
        add_btn.setToolTip("EFEKT: dodaje wiersz reguły (pole + operator + wartość). Po Zapisz kolekcja staje się dynamiczna w sidebarze i playliście. Per SZPIEG 2026-06-15 Smart Collections + finalny efekt końcowy.")
        add_btn.clicked.connect(self._add_rule_row)
        layout.addWidget(add_btn)
        layout.addWidget(self.rules_widget)

        self.live_count = QtWidgets.QLabel("Pasuje: — (oblicz)")
        calc_btn = QtWidgets.QPushButton("Oblicz pasujące")
        calc_btn.setToolTip("EFEKT: wykonuje live query get_tracks_for_smart_rules na DB meta (bezdotykowo na plikach); pokazuje aktualną liczbę pasujących utworów. Użyj do podglądu przed zapisem.")
        calc_btn.clicked.connect(self._calc_live_count)
        h = QtWidgets.QHBoxLayout()
        h.addWidget(self.live_count)
        h.addWidget(calc_btn)
        layout.addLayout(h)

        # Convert button (P1)
        conv_btn = QtWidgets.QPushButton("Konwertuj na statyczną (snapshot)")
        conv_btn.setToolTip("EFEKT: tworzy kopię statyczną z aktualnych wyników reguł (snapshot z DB); oryginał smart zostaje i nadal auto-aktualizuje się. Drag ze statycznej = FILE. Per SZPIEG.")
        conv_btn.clicked.connect(self._convert_static)
        layout.addWidget(conv_btn)

        row = QtWidgets.QHBoxLayout()
        row.addStretch(1)
        save_btn = QtWidgets.QPushButton("Zapisz")
        save_btn.setToolTip("EFEKT: zapisuje nazwę + is_smart + reguły JSON do DB (PlaylistOrm). Natychmiast odświeża playlist_list i smart_tree; następny load z tej kolekcji = dynamiczny query + FILE na drag.")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QtWidgets.QPushButton("Anuluj")
        cancel_btn.setToolTip("EFEKT: zamyka bez zapisu zmian reguł (żadne pliki ani DB nie są modyfikowane).")
        cancel_btn.clicked.connect(self.reject)
        row.addWidget(save_btn)
        row.addWidget(cancel_btn)
        layout.addLayout(row)

        # initial row if smart
        self.smart_check.toggled.connect(lambda c: self.rules_widget.setVisible(c))
        self.rules_widget.setVisible(False)
        # initial example row for smart users (per SZPIEG)
        self._add_rule_row()

    def _add_rule_row(self):
        row_w = QtWidgets.QWidget()
        hl = QtWidgets.QHBoxLayout(row_w)
        field = QtWidgets.QComboBox()
        field.addItems(["bpm", "key", "tag", "energy", "play_count", "date_added", "mood", "genre", "analysis"])
        field.setToolTip("EFEKT: wybierz pole metadanych DB (bpm/key/tag/energia/il. odtworzeń/data/mood/gatunek/analiza). Reguła działa tylko na DB, nigdy na surowym pliku. Per SZPIEG 2026-06-15 Smart Collections + finalny efekt.")
        op = QtWidgets.QComboBox()
        op.addItems([">", "<", "=", "zawiera", "nie zawiera", "range"])
        op.setToolTip("EFEKT: operator porównania dla reguły smart (range dla BPM min,max). Wynik = dynamiczny z DB query; load z tego = FILE do odt (stream nie wpływa na reguły).")
        val = QtWidgets.QLineEdit()
        val.setPlaceholderText("wartość lub min,max")
        val.setToolTip("EFEKT: wartość/warunek (dla range '128,132'). Auto-update kolekcji po zmianie tagów w DB.")
        del_btn = QtWidgets.QPushButton("−")
        del_btn.setToolTip("EFEKT: usuń tę regułę z buildera (nie wpływa na zapisane playlisty dopóki nie Zapisz).")
        del_btn.clicked.connect(lambda: (self.rules_layout.removeWidget(row_w), row_w.deleteLater(), self.conditions.remove(row_w) if row_w in self.conditions else None))
        hl.addWidget(field)
        hl.addWidget(op)
        hl.addWidget(val)
        hl.addWidget(del_btn)
        self.rules_layout.addWidget(row_w)
        self.conditions.append(row_w)
        # store widgets for extraction
        row_w._field = field
        row_w._op = op
        row_w._val = val

    def _build_rules_from_rows(self) -> dict:
        conds = []
        for rw in self.conditions:
            if not hasattr(rw, '_field'):
                continue
            f = rw._field.currentText().strip().lower()
            o = rw._op.currentText().strip()
            v = rw._val.text().strip()
            c = {"field": f, "op": o}
            if o == "range" and "," in v:
                parts = [p.strip() for p in v.split(",")]
                if len(parts) >= 2:
                    c["min"] = float(parts[0]) if parts[0] else None
                    c["max"] = float(parts[1]) if parts[1] else None
            elif v:
                if f in ("bpm", "energy", "play_count"):
                    try:
                        c["value"] = float(v)
                    except:
                        c["value"] = v
                else:
                    c["value"] = v
            conds.append(c)
        return {
            "any": self.any_all_combo.currentText().startswith("Dopasuj dowolną"),
            "conditions": conds,
        }

    def _calc_live_count(self):
        # Smart Collections (per SZPIEG research 2026-06-15 Smart Collections + finalny efekt końcowy... must document identical)
        # Prawdziwe zapytanie do bazy (tylko metadane) dla podglądu na żywo. Ochrona przed pustym. EFEKT: pokazuje ile utworów pasuje do reguł w tej chwili; wynik jest dynamiczny, nie zapisuje plików.
        try:
            rules = self._build_rules_from_rows()
            tracks = get_tracks_for_smart_rules(rules)
            self.live_count.setText(f"Pasuje: {len(tracks)} (meta DB)")
        except Exception as e:
            self.live_count.setText(f"Pasuje: błąd ({e})")

    def _convert_static(self):
        # Smart Collections (per SZPIEG research 2026-06-15 Smart Collections + finalny efekt końcowy... must document identical)
        # Konwersja tworzy statyczną playlistę-migawkę z bieżącego wyniku metadanych z bazy dla aktualnych reguł (bez odczytu plików). Oryginalne reguły smart pozostają dynamiczne. Przeciągnięcie z którejkolwiek = wczytanie PLIKU (izolacja strumienia). Ochrona przed pustymi wynikami.
        # EFEKT: "EFEKT: tworzy statyczną kopię bieżących utworów pasujących do reguł (migawka); oryginał smart nadal automatycznie się aktualizuje przy zmianach metadanych; wczytanie z migawki lub smart = bezpieczne wczytanie PLIKU do odtwarzacza (nie wpływa na reguły ani historię)."
        try:
            rules = self._build_rules_from_rows()
            tracks = get_tracks_for_smart_rules(rules)
            if not tracks:
                QtWidgets.QMessageBox.information(self, "Migawka", "Brak utworów do migawki.")
                return
            base_name = self.name_input.text().strip() or "Migawka Smart"
            static_name = base_name + " (statyczna)"
            create_playlist(static_name, "Migawka z reguł smart", is_smart=False, rules=None)
            # znajdź nową (świeża lista)
            for p in list_playlists_full():
                if p.name == static_name and not getattr(p, 'is_smart', False):
                    pid = p.playlist_id
                    for t in tracks:
                        add_track_to_playlist(pid, t.path)
                    break
            QtWidgets.QMessageBox.information(self, "Migawka", f"Utworzono statyczną '{static_name}' z {len(tracks)} utworów. Reguły smart oryginału pozostają.")
            # próba odświeżenia rodzica (główne okno) jeśli dostępne dla natychmiastowej aktualizacji interfejsu
            if self.parent() and hasattr(self.parent(), '_refresh_smart_collections'):
                try:
                    self.parent()._refresh_smart_collections()
                except Exception:
                    pass
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Błąd", f"Nie udało się stworzyć migawki: {e}")

    def _load(self, playlist: Playlist):
        self.name_input.setText(playlist.name)
        self.desc_input.setText(playlist.description or "")
        self.smart_check.setChecked(bool(playlist.is_smart))
        self.rules_widget.setVisible(bool(playlist.is_smart))
        if playlist.rules:
            try:
                rules = json.loads(playlist.rules)
            except Exception:
                rules = {}
            # load any/all
            if rules.get("any"):
                self.any_all_combo.setCurrentIndex(1)
            # clear existing rows, load from conditions
            for rw in list(self.conditions):
                self.rules_layout.removeWidget(rw)
                rw.deleteLater()
            self.conditions.clear()
            for cond in rules.get("conditions", []):
                self._add_rule_row()
                rw = self.conditions[-1]
                # set values
                f = cond.get("field", "bpm")
                # map to combo text if needed
                for i in range(rw._field.count()):
                    if rw._field.itemText(i).lower() == f:
                        rw._field.setCurrentIndex(i)
                        break
                o = cond.get("op", "=")
                for i in range(rw._op.count()):
                    if rw._op.itemText(i) == o or (o == "range" and rw._op.itemText(i) == "range"):
                        rw._op.setCurrentIndex(i)
                        break
                if "min" in cond and "max" in cond:
                    rw._val.setText(f"{cond.get('min','')},{cond.get('max','')}")
                elif "value" in cond:
                    rw._val.setText(str(cond.get("value", "")))
            # legacy fallback
            if not rules.get("conditions") and (rules.get("search") or rules.get("genre")):
                # add one legacy style if needed (simple)
                pass

    def get_payload(self) -> dict:
        rules = None
        if self.smart_check.isChecked():
            rules = self._build_rules_from_rows()
            # ensure serializable
        return {
            "name": self.name_input.text().strip(),
            "description": self.desc_input.text().strip() or None,
            "is_smart": self.smart_check.isChecked(),
            "rules": json.dumps(rules, ensure_ascii=False) if rules else None,
        }




