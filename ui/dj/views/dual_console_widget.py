"""
ui/dj/views/dual_console_widget.py

DualConsoleWidget – kontener na dwa decki w trybie Dual Console + globalny Mixer (crossfader + master).

Zgodny z sekcją 5 dokumentu AGENT3_UI_Designer_Rekordbox_Redo.md:
- Side-by-side (A | B) – profesjonalny wygląd Rekordbox/Traktor
- Każdy deck to pełny ConsoleDeckView (identyczny kod)
- Poniżej: duży, wyraźny crossfader (min 280-320px, wys. 34px) z etykietami A / B i linią środka
- Globalny MixerStrip: Master Volume + Cue/Headphone Volume (stub dla cue – silnik wspiera master)
- Zawsze widoczne, bez żadnych toggle barów "Pokaż/Ukryj"

Architektura:
- "Dumb container": tylko buduje layout, przekazuje kontrolery do decków
- Pełny wiring SYNC (A↔B)
- Crossfader bezpośrednio steruje PlaybackEngine.set_crossfader()
- Master Volume → engine.set_master_volume()
- Cue Volume – wizualny + status (rozszerzenie silnika w przyszłości)

Używa wyłącznie helperów ze styles.py.
Zero logiki DJ w tym pliku – wszystko delegowane do DeckController + engine.
Pełne polskie komentarze.
"""

from __future__ import annotations

from PyQt6 import QtCore, QtWidgets

from services.playback import PlaybackEngine
from ui.dj.deck_controller import DeckController
from ui.dj.views.console_deck_view import ConsoleDeckView
from ui.dj.styles import (
    BOOTH_SIZES,
    BOOTH_COLORS,
    get_deck_panel_stylesheet,
    get_section_label_stylesheet,
    get_slider_stylesheet,
    get_value_label_stylesheet,
)


class DualConsoleWidget(QtWidgets.QWidget):
    """
    Kontener trybu "Konsola DJ" – dwa decki bok-obok + pełny mikser na dole.

    Użycie (w DJPlayerWindow):
        self.dual_container = DualConsoleWidget(controller_a, controller_b, playback_engine)
        layout.addWidget(self.dual_container)

    Po stworzeniu SYNC między deckami działa natychmiast.
    Crossfader i master są podłączone.
    """

    def __init__(
        self,
        controller_a: DeckController,
        controller_b: DeckController,
        playback_engine: PlaybackEngine | None = None,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.controller_a = controller_a
        self.controller_b = controller_b
        self.playback_engine = playback_engine

        self.setStyleSheet(get_deck_panel_stylesheet())

        self._setup_ui()
        self._wire_decks()
        self._wire_mixer()

        # Inicjalne wartości miksera
        QtCore.QTimer.singleShot(0, self._apply_initial_mixer)

    def _setup_ui(self) -> None:
        main = QtWidgets.QVBoxLayout(self)
        main.setContentsMargins(12, 10, 12, 10)
        main.setSpacing(12)

        # === DWA DECKI SIDE-BY-SIDE (QSplitter dla elastyczności) ===
        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(6)

        self.deck_a_view = ConsoleDeckView(self.controller_a, deck_label="A")
        self.deck_b_view = ConsoleDeckView(self.controller_b, deck_label="B")

        splitter.addWidget(self.deck_a_view)
        splitter.addWidget(self.deck_b_view)
        splitter.setSizes([480, 480])  # równe na starcie

        main.addWidget(splitter, 1)

        # === GLOBALNY MIXER + CROSSFADER ===
        mixer_frame = QtWidgets.QFrame()
        c = BOOTH_COLORS  # use central (imported via styles)
        mixer_frame.setStyleSheet(
            f"""
            QFrame {{
                background-color: {c["wave_bg"]};
                border: 1px solid {c["border"]};
                border-radius: 8px;
            }}
            """
        )
        mixer_layout = QtWidgets.QVBoxLayout(mixer_frame)
        mixer_layout.setContentsMargins(16, 10, 16, 10)
        mixer_layout.setSpacing(8)

        # Etykieta sekcji
        mix_title = QtWidgets.QLabel("MIXER / CROSSFADER")
        mix_title.setStyleSheet(get_section_label_stylesheet())
        mix_title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        mixer_layout.addWidget(mix_title)

        # CROSSFADER – duży, wyraźny, z A | B i linią środka
        cross_row = QtWidgets.QHBoxLayout()
        cross_row.setSpacing(8)

        a_lbl = QtWidgets.QLabel("A")
        a_lbl.setStyleSheet("color:#00e0ff; font-size:16px; font-weight:900; min-width:18px;")
        a_lbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self.crossfader = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.crossfader.setRange(0, 100)
        self.crossfader.setValue(50)
        self.crossfader.setMinimumHeight(BOOTH_SIZES["crossfader_height"])
        self.crossfader.setStyleSheet(get_slider_stylesheet("horizontal"))
        self.crossfader.setToolTip("Crossfader — środek = oba decki słyszalne. Przeciągnij A↔B")

        # Krok 6: menu PPM dla crossfader w dual
        self.crossfader.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.crossfader.customContextMenuRequested.connect(self._show_dual_cross_menu)

        b_lbl = QtWidgets.QLabel("B")
        b_lbl.setStyleSheet("color:#00e0ff; font-size:16px; font-weight:900; min-width:18px;")
        b_lbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        cross_row.addWidget(a_lbl, 0)
        cross_row.addWidget(self.crossfader, 1)
        cross_row.addWidget(b_lbl, 0)
        mixer_layout.addLayout(cross_row)

        # MASTER + CUE VOLUME (prosty mixer strip)
        vols = QtWidgets.QHBoxLayout()
        vols.setSpacing(20)

        # Master
        master_box = QtWidgets.QVBoxLayout()
        master_box.setSpacing(2)
        m_lbl = QtWidgets.QLabel("MASTER")
        m_lbl.setStyleSheet(get_section_label_stylesheet())
        master_box.addWidget(m_lbl)
        self.master_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.master_slider.setRange(0, 100)
        self.master_slider.setValue(85)
        self.master_slider.setStyleSheet(get_slider_stylesheet("horizontal"))
        self.master_slider.setFixedWidth(160)
        self.master_val = QtWidgets.QLabel("85")
        self.master_val.setStyleSheet(get_value_label_stylesheet())
        master_box.addWidget(self.master_slider)
        master_box.addWidget(self.master_val, 0, QtCore.Qt.AlignmentFlag.AlignCenter)

        # Krok 6: menu PPM dla master w dual
        self.master_slider.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.master_slider.customContextMenuRequested.connect(self._show_dual_master_menu)

        vols.addLayout(master_box)

        # Cue / Headphone
        cue_box = QtWidgets.QVBoxLayout()
        cue_box.setSpacing(2)
        c_lbl = QtWidgets.QLabel("CUE (HP)")
        c_lbl.setStyleSheet(get_section_label_stylesheet())
        cue_box.addWidget(c_lbl)
        self.cue_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.cue_slider.setRange(0, 100)
        self.cue_slider.setValue(70)
        self.cue_slider.setStyleSheet(get_slider_stylesheet("horizontal"))
        self.cue_slider.setFixedWidth(140)
        self.cue_val = QtWidgets.QLabel("70")
        self.cue_val.setStyleSheet(get_value_label_stylesheet())
        cue_box.addWidget(self.cue_slider)
        cue_box.addWidget(self.cue_val, 0, QtCore.Qt.AlignmentFlag.AlignCenter)

        # Krok 6: menu PPM dla cue w dual
        self.cue_slider.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.cue_slider.customContextMenuRequested.connect(self._show_dual_cue_menu)

        vols.addLayout(cue_box)

        vols.addStretch(1)
        mixer_layout.addLayout(vols)

        main.addWidget(mixer_frame, 0)

    def _wire_decks(self) -> None:
        """Podłącz partnerów SYNC + wszelkie cross-deck rzeczy."""
        self.deck_a_view.set_partner_controller(self.controller_b)
        self.deck_b_view.set_partner_controller(self.controller_a)

    def _wire_mixer(self) -> None:
        """Crossfader + master → silnik playbacku."""
        self.crossfader.valueChanged.connect(self._on_crossfader_changed)
        self.master_slider.valueChanged.connect(self._on_master_changed)
        self.cue_slider.valueChanged.connect(self._on_cue_changed)

    def _apply_initial_mixer(self) -> None:
        """Ustaw początkowe wartości (master 0.85, cross 0.0 = center)."""
        if self.playback_engine:
            try:
                self.playback_engine.set_master_volume(0.85)
                self.playback_engine.set_crossfader(0.0)
            except Exception:
                pass

        # Wizualnie
        self.master_val.setText("85")
        self.cue_val.setText("70")

    def _show_dual_cross_menu(self, pos):
        menu = QtWidgets.QMenu(self)
        menu.addAction("Wyśrodkuj crossfader")
        menu.addAction("Pełne A")
        menu.addAction("Pełne B")
        menu.exec(self.crossfader.mapToGlobal(pos))

    def _show_dual_master_menu(self, pos):
        menu = QtWidgets.QMenu(self)
        menu.addAction("Reset Master 85")
        menu.addAction("Master 100")
        menu.addAction("Master 50")
        menu.exec(self.master_slider.mapToGlobal(pos))

    def _show_dual_cue_menu(self, pos):
        menu = QtWidgets.QMenu(self)
        menu.addAction("Reset Cue 70")
        menu.addAction("Cue 100")
        menu.addAction("Mute Cue")
        menu.exec(self.cue_slider.mapToGlobal(pos))

    def _on_crossfader_changed(self, value: int) -> None:
        """0..100 → -1.0 (A) ... 0 (center) ... +1.0 (B)"""
        if not self.playback_engine:
            return
        pos = (value / 50.0) - 1.0
        try:
            self.playback_engine.set_crossfader(pos)
        except Exception:
            pass

    def _on_master_changed(self, value: int) -> None:
        self.master_val.setText(str(value))
        if self.playback_engine:
            try:
                self.playback_engine.set_master_volume(value / 100.0)
            except Exception:
                pass

    def _on_cue_changed(self, value: int) -> None:
        """Cue volume (headphone) – w tej fazie tylko status + wartość.
        Gdy silnik dostanie set_cue_volume / set_headphone_volume – podłączymy.
        """
        self.cue_val.setText(str(value))
        if self.playback_engine:
            # Placeholder – nie psujemy nic, tylko informujemy
            try:
                # self.playback_engine.set_cue_volume(value / 100.0)  # gdy dostępne
                pass
            except Exception:
                pass
        # Delikatny feedback
        if value % 20 == 0:
            # Nie spamujemy – tylko co kilka kroków
            pass

    # ------------------------------------------------------------------
    # API dla DJPlayerWindow (przełączanie trybów, drag&drop itp.)
    # ------------------------------------------------------------------
    def get_deck_view(self, deck_id: str) -> ConsoleDeckView | None:
        """Zwraca widok decku A lub B."""
        if deck_id.upper() == "A":
            return self.deck_a_view
        if deck_id.upper() == "B":
            return self.deck_b_view
        return None

    def refresh_mixer(self) -> None:
        """Wymusza ponowne zastosowanie aktualnych wartości (po zmianie trybu)."""
        QtCore.QTimer.singleShot(10, self._apply_initial_mixer)


__all__ = ["DualConsoleWidget"]
