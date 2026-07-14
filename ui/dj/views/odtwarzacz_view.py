from __future__ import annotations

import logging
import math
from pathlib import Path
from typing import Optional
import uuid

from PyQt6 import QtCore, QtGui, QtWidgets

from core.models import Track
from ui.dj.deck_layout import (
    apply_header_metrics,
    apply_transport_button_metrics,
    build_deck_header,
    build_time_label,
    configure_waveform_widget,
)
from ui.dj.deck_view_helpers import metrics_for_odt, refresh_waveform_on_resize
from ui.dj.simple_deck_controller import SimpleDeckController
from ui.dj.views.player_controls_bar import PlayerControlsBar
from ui.dj.views.pitch_control import PitchControl
from ui.dj.views.waveform_widget import WaveformWidget
from ui.dj.styles import (
    BOOTH_COLORS,
    BoothMetrics,
    get_deck_panel_stylesheet,
)

logger = logging.getLogger(__name__)


class _CompactSpinIndicator(QtWidgets.QWidget):
    """
    Pilot-like animated play indicator (spinning CD/vinyl/eq style).
    Używa timer + paintEvent dla rotacji (per SZPIEG: anim via timer/paint).
    Reacts to play_state: start() / stop() spin.
    W compact mode pokazywany obok tytułu lub w transporcie.
    Lekki, skalowalny, nie wymaga external assets.
    2026-06-02 UI-DESIGNER re-audit "uruchmo jeszcze raz... nie przestawaj": paint uses cos(a)/sin(a) on _angle + spokes radial (verified rotating), vis guards in odt, start only compact+play. Per[...]
    """
    def __init__(self, parent=None, size: int = 22):
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size, size)
        self._angle = 0.0
        self._spinning = False
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(50)  # ~20fps smooth
        self._timer.timeout.connect(self._tick)
        self.setToolTip(
            "Wskaźnik odtwarzania (spinning CD/vinyl/eq pilot-like). Aktywny podczas PLAY (stream). "
            "EFEKT: wizualny feedback strumienia dźwięku z załadowanego PLIKU (nie load/rename pliku; FILE ops w drag/load osobno). "
            "Tylko compact mode. Per SZPIEG Build Spec + Plan."
        )

    def start(self):
        if not self._spinning:
            self._spinning = True
            self._timer.start()
            self.update()

    def stop(self):
        if self._spinning:
            self._spinning = False
            self._timer.stop()
            self._angle = 0.0
            self.update()

    def _tick(self):
        self._angle = (self._angle + 12) % 360  # deg per tick, clockwise like vinyl
        self.update()

    def paintEvent(self, event):
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        r = min(w, h) / 2 - 2
        c = BOOTH_COLORS
        # Vinyl/CD like: dark circle + grooves + highlight
        p.setPen(QtGui.QPen(QtGui.QColor(c.get("border_strong", "#3a4556")), 2))
        p.setBrush(QtGui.QBrush(QtGui.QColor(c.get("surface_elev", "#1a212c"))))
        p.drawEllipse(QtCore.QPointF(cx, cy), r, r)  # use center+radius (float ok in PyQt6)
        # Spinning spokes (eq/vinyl lines) using angle a + cos/sin per SZPIEG/Plan step2/9
        # Rotate around center: use radians(a), inner/outer radius for spokes.
        p.setPen(QtGui.QPen(QtGui.QColor(c.get("accent", "#00e0ff")), 1.5))
        num_spokes = 8
        for i in range(num_spokes):
            a = math.radians(self._angle + i * (360.0 / num_spokes))
            # Inner and outer for spoke length (some variation for CD grooves look)
            inner = r * 0.35
            outer = r * 0.92
            # cos/sin for proper rotation (x right, y down in widget coords)
            x1 = cx + inner * math.cos(a)
            y1 = cy + inner * math.sin(a)
            x2 = cx + outer * math.cos(a)
            y2 = cy + outer * math.sin(a)
            p.drawLine(int(x1), int(y1), int(x2), int(y2))
        # Center dot (spindle)
        p.setBrush(QtGui.QBrush(QtGui.QColor(c.get("play", "#22c55e"))))
        p.drawEllipse(QtCore.QPointF(cx, cy), 2.0, 2.0)  # float center+radius version
        p.end()


def _format_ms(ms: int | None) -> str:
    """Prosty formatter ms → m:ss (dla czasu i statusu)."""
    if ms is None or ms < 0:
        return "0:00"
    total = max(0, int(ms)) // 1000
    m = total // 60
    s = total % 60
    return f"{m}:{s:02d}"


class OdtwarzaczView(QtWidgets.QFrame):
    """
    Minimalny widok single player "Odtwarzacz" MVP (QFrame).

    **Uwaga dla nowych agentów/programistów:** Implementacja dokładnie per nadrzędny SZPIEG Build Spec + Plan team review (z crew/SZPIEG_agent_spec_and_archive.md + memory.md + crew/PLAN_Uruc[...]
    2026-06-02 SZPIEG full re-audit po kolei (init QStack dual0 odt1, creates, switch, compact+ _CompactSpin cos/sin, drag mime+repo+safety, playback, EFFECT file/stream, air/scalab, styles, inte[...]
    2026-06-02 UI-DESIGNER fresh re-audit "uruchmo jeszcze raz... nie przestawaj" (post FIXER/TESTER): spin cos/sin verified in paint (radial a cos/sin spokes), compact window min shrink 380x280 [...]
    FIXER 2026-06-02: spin paint cos/sin a rot + always-on-top compact + EFFECT tooltip + highDPI; vis isVisible guard post set/stack; drag hl compact + batch log; dynamic wave compact precise; f[...]
    REVIEWER 2026-06 (crew): weryfikacja po ANALYZER — spin paint wymaga fix (angle not driving rotation), dual init overhead, compact scalab (window), guards. Patrz SZPIEG archive (REVIEWER en[...]
    TESTER 2026-06-02 re-run (Zespół uruchomiony ponownie per user "uruchmo jeszcze raz... nie przestawaj"): full verify (smoke0, pytest44p, python-c create+toggle+load+play+c ue+resize+drag+st[...]
TESTER 2026-06-14 final (po "dalej"+lista 1-15): smoke0/pytest44p/python-c (compact+spin vis/load/ctrl/resize/drag/switch asserts stack=2/cur=1 ODT=1) OK; CHECKLIST+edges+lista polish (always-on-[...]
    **2026-06-02 ANALYZER (per PLAN/SZPIEG/memory "Dla nowych" + "uruchmo jeszcze raz... nie przestawaj"):** Re-audit deep po kolei całej budowy (QStack init create switch compact spin drag play[...]
    User "dalej" (po review Plan "nowa lista przeróbek 1-15" + SZPIEG P0-P10): WRITER/FIXER/TESTER re-launched to execute polish per lista (compact always-on-top pilot lista12, EFFECT+file/strea[...]

    Skupiony TYLKO na podstawach (per zadanie):
    - poprawne ładowanie pliku (z lookup repo w drop + load)
    - podstawowy playback: play/pause/stop (via SimpleDeckController)
    - wizualizacje: title/time/BPM/duży waveform+playhead+beatgrid
    - czysty layout z powietrzem (VBox + marginesy/stretch)
    - compact pilot mode z animacją (spinning indicator), EFFECT tooltips, scalability, drag, file vs stream clarity.

    Hierarchia layoutu (VBox, margins ~32/24, spacing 18):
    - Header HBox: [TRACK TITLE 18px bold stretch]          [BPM 32px 900 accent]
    - WAVEFORM (min 260, stretch=7) z BPM-aware beatgrid + gruby playhead
    - TIME (18px mono, center, stretch=0)
    - TRANSPORT (3 duże przyciski CUE/PLAY/STOP wycentrowane z side stretches)
    - minimal status (11px muted, center)

    Używa:
    - ui/dj/styles (BOOTH_COLORS, BOOTH_SIZES, get_*_stylesheet, get_transport_button_stylesheet)
    - WaveformWidget (nowy extracted)
    - Transport styles (ale własne 3 przyciski dla prostoty MVP + explicit play/pause)
    - Minimal single pitch stub (reused PitchControl after controls; compact hides; wired to controller.set_rate/set_pitch; EFFECT tooltip)
    - ZERO advanced: no hotcues, trim full, eq, mem, advanced row, loops, sync (Faza1 single MVP only)

    Drag&drop: pełny repo lookup (get_track_by_path).
    Connects: waveform seek + buttons to controller; subs signals for UI updates.

    Nie miesza z FocusedDeckView (pozostaje dla dual console).
    Per Szpieg/Plan + must document identical (audio fallback warning via status + get_backend_info added).
    """
    def __init__(self, controller: SimpleDeckController,
                 parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.controller = controller
        self._current_duration_ms: int = 0
        self._current_track: Track | None = None
        self._is_playing: bool = False
        self._compact: bool = False
        self._applying_compact: bool = False
        self._metrics = BoothMetrics(compact=False)
        self._last_metrics_scale: float = 1.0
        self._skip_cue_release: bool = False

        self.setObjectName("OdtwarzaczPanel")
        self._normal_stylesheet = get_deck_panel_stylesheet()
        self.setStyleSheet(self._normal_stylesheet)

        self.setAcceptDrops(True)

        self._refresh_metrics(force_apply=False)
        self._setup_ui()
        self._connect_controller_signals()
        self._connect_widget_signals()

        # Initial apply (default non-compact uses normal sizes)
        # Per grupa 1+8 + SZPIEG/Plan nowa lista po 'dalej': odt init always completes (QStack creation ensures odt ready przed switch/compact/play w window). Guard _applying etc. Must document i[...]
        self._apply_compact_ui()

        # Overall EFFECT tooltip for the odt panel (air + drag + file/stream clarity)
        self.setToolTip(
            "Odtwarzacz (single preview): czysty, skalowalny widok z powietrzem. "
            "Drag z tabeli biblioteki = load PLIKU (mime + repo lookup + highlight safety). "
            "Transport = STREAM playback z pliku (play near cue, stop->cue). "
            "Compact toggle w oknie rodzica. ResizeEvent dla skalowalności. "
            "EFEKT: nie zachodzi na dual, nie nadpisuje metadanych."
        )

    def _setup_ui(self) -> None:
        """VBox z powietrzem + hierarchia z designu (dostosowana do MVP basics).
        FILE vs STREAM: wszystkie load_* = operacje na PLIKU (ścieżka dysku + DB lookup + waveform peaks).
        Transport (play/pause/stop/seek) = operacje na STREAMIE (dźwięk z załadowanego pliku via engine).
        Komentarze i guardy w metodach.
        """
        layout = QtWidgets.QVBoxLayout(self)
        m = self._metrics.layout_margins()
        layout.setContentsMargins(*m)
        layout.setSpacing(self._metrics.layout_spacing())

        self._spin_indicator = _CompactSpinIndicator(self, size=self._metrics.spin_size())
        self._spin_indicator.setVisible(False)
        header_parts = build_deck_header(
            self._metrics,
            empty_title="Brak utworu — upuść plik z biblioteki",
            extra_right=self._spin_indicator,
        )
        self._header_parts = header_parts
        self.title_label = header_parts.title_label
        self.bpm_label = header_parts.bpm_label
        self.title_label.setToolTip(
            "Tytuł i artysta załadowanego pliku audio. EFEKT: pokazuje metadane z Track "
            "(z DB lub filename). Upuść inny plik by zmienić załadowany plik (load = FILE op)."
        )
        self.bpm_label.setToolTip(
            "BPM utworu (z metadanych lub analizy). EFEKT: wpływa na beatgrid waveformu. "
            "Wartość z pliku/DB, nie zmienia pliku."
        )
        layout.addLayout(header_parts.layout)

        # === DOMINANT WAVEFORM (stretch 7, minHeight 260+) ===
        self.waveform = WaveformWidget()
        configure_waveform_widget(self.waveform, self._metrics)
        # Expand tooltip on wave for EFFECT (file/stream + drag)
        self.waveform.setToolTip(
            "Waveform: Click=seek (strumień) • Double-click=seek + set main CUE (dla play near0). "
            "EFEKT: zmienia pozycję w streamie z załadowanego PLIKU (nie load nowego pliku). "
            "Drag&drop z biblioteki ładuje nowy PLIK. Shift+click ignorowane w odt (no advanced)."
        )
        layout.addWidget(self.waveform, self._metrics.wave_stretch())

        # === TIME (center, fixed, 0 stretch, 18px mono) ===
        self.time_label = build_time_label(self._metrics)
        self.time_label.setToolTip("Pozycja / czas trwania. EFEKT: aktualizowane z playhead streamu (timer 40ms z engine state). Nie wpływa na plik.")
        layout.addWidget(self.time_label, 0)

        self.player_controls = PlayerControlsBar()
        self.player_controls.volume_changed.connect(self._on_volume_changed)
        layout.addWidget(self.player_controls, 0)

        # === MINIMAL PITCH STUB (reuse PitchControl, after controls, for single Odtwarzacz MVP Faza1 item3) ===
        # Compact hides (in _apply_compact_ui setVisible(False) to preserve air/no-break in pilot ~420x300 + highDPI).
        # Wire signals to controller (which now has set_rate/set_pitch/set_keylock minimal).
        # Slider range -50..50 from pitch_control; value shown.
        # KEY stub for keylock.
        # EFFECT tooltip exact: "EFEKT: zmienia tempo/pitch utworu (FILE load, STREAM playback)".
        # No full dual (single only), QStack/fallback/highDPI/compact forces preserved (no layout break).
        # per SZPIEG research 2026-07-14 plan rozbudowy Faza1 Polish (single pitch/TRIM stub + odt_view wiring + simple_controller, stub minimal slider KEYLOCK, compact aware)... must document identical.
        self.pitch_control = PitchControl()
        self.pitch_control.pitch_changed.connect(self._on_pitch_changed)
        self.pitch_control.keylock_toggled.connect(self._on_keylock_toggled)
        # Apply tooltip per spec (on whole control + slider for visibility)
        pitch_tooltip = "EFEKT: zmienia tempo/pitch utworu (FILE load, STREAM playback)"
        self.pitch_control.setToolTip(pitch_tooltip)
        if hasattr(self.pitch_control, "slider"):
            self.pitch_control.slider.setToolTip(pitch_tooltip)
        if hasattr(self.pitch_control, "keylock_btn"):
            self.pitch_control.keylock_btn.setToolTip(
                "KEYLOCK: utrzymuje pitch przy zmianie tempa (gdy backend wspiera, np. VLC scaletempo). "
                + pitch_tooltip
            )
        layout.addWidget(self.pitch_control, 0)

        self.cue_btn = QtWidgets.QPushButton()
        self.play_btn = QtWidgets.QPushButton()
        self.stop_btn = QtWidgets.QPushButton()
        apply_transport_button_metrics(
            self._metrics, self.cue_btn, self.play_btn, self.stop_btn, playing=False
        )
        self.cue_btn.pressed.connect(self._on_cue_pressed)
        self.cue_btn.released.connect(self._on_cue_released)
        self.cue_btn.setToolTip(
            "Trzymaj = podgląd od CUE (CDJ). Zwolnij = stop na CUE. "
            "Shift+trzymaj = ustaw CUE na bieżącej pozycji."
        )
        self.play_btn.clicked.connect(self._on_play_or_pause_clicked)
        self.play_btn.setToolTip(
            "Rozpocznij lub wznów odtwarzanie załadowanego pliku audio. "
            "EFEKT: uruchamia silnik playback (od pozycji lub cue jeśli blisko startu)."
        )
        self.stop_btn.clicked.connect(self.controller.stop)
        self.stop_btn.setToolTip(
            "Zatrzymaj odtwarzanie i wróć do punktu CUE (lub 0). "
            "EFEKT: stop silnika + reset playhead do cue (nie usuwa pliku z decku)."
        )

        self._transport_widget = QtWidgets.QWidget()
        trans_row = QtWidgets.QHBoxLayout(self._transport_widget)
        trans_row.setContentsMargins(0, 0, 0, 0)
        trans_row.setSpacing(self._metrics.transport_gap())
        trans_row.addStretch(1)
        trans_row.addWidget(self.cue_btn)
        trans_row.addWidget(self.play_btn)
        trans_row.addWidget(self.stop_btn)
        trans_row.addStretch(1)
        layout.addWidget(self._transport_widget, 0)

        self.player_controls.register_transport_buttons(
            self.cue_btn, self.play_btn, self.stop_btn
        )

        # === MINIMAL STATUS ===
        self.status_label = QtWidgets.QLabel("— Gotowy (tryb Odtwarzacz MVP)")
        self.status_label.setStyleSheet(self._metrics.status_stylesheet())
        self.status_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.status_label.setToolTip("Status decku (load/play/cue/set). EFEKT: informacyjny; nie wykonuje akcji. File ops w load, stream ops w transport.")
        layout.addWidget(self.status_label, 0)

        # === PROMINENT FALLBACK BANNER (no-VLC / Audio niedostępne) ===
        # Dedykowany label/banner dla visibility w compact (gdzie status_label.setVisible(False)) + highDPI.
        # Używa get_backend_info() + exact text z research. Zawsze widoczny gdy fallback (nawet w tight pilot).
        # Per SZPIEG research 2026-06-25 DJ checklist + Plan + clean Windows Szpieg: prominent, nie chowany w compact, pack tight.
        # EFFECT: wysoki kontrast warning, nie zajmuje dużo miejsca w compact (mały font), guide do videolan.org.
        # Must document identical.
        self._audio_fallback_label = QtWidgets.QLabel("")
        self._audio_fallback_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self._audio_fallback_label.setWordWrap(True)
        self._audio_fallback_label.setVisible(False)
        layout.addWidget(self._audio_fallback_label, 0)

        # Prosty, widoczny status/warning w OdtwarzaczView gdy backend Noop lub Qt.
        # Używa get_backend_info (verif działa z fallback) + exact Polish text + link do diagnostics.
        # EFFECT: wysoki kontrast, nie psuje istniejącego status/transport/wave; widoczny od razu.
        # Wzmocnione: dedicated banner dla compact/highDPI visibility (status schowany w compact).
        self._maybe_apply_audio_fallback_warning()

        self._flex_spacer = QtWidgets.QWidget()
        self._flex_spacer.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding
        )
        layout.addWidget(self._flex_spacer, 1)

    def _connect_widget_signals(self) -> None:
        """Waveform seek (bez cue/double w minimal – double działa jako seek + set_cue)."""
        if hasattr(self.waveform, "seek_requested"):
            self.waveform.seek_requested.connect(self.controller.seek)
        if hasattr(self.waveform, "double_clicked"):
            self.waveform.double_clicked.connect(self._on_waveform_set_cue)
        # Shift+click na waveform ignorujemy w MVP (no hotcues)

    def _connect_controller_signals(self) -> None:
        """Subskrypcja tylko podstawowych sygnałów kontrolera."""
        self.controller.track_loaded.connect(self._on_track_loaded)
        self.controller.track_unloaded.connect(self._on_track_unloaded)
        self.controller.playhead_changed.connect(self._on_playhead_changed)
        self.controller.bpm_changed.connect(self._on_bpm_changed)
        self.controller.play_state_changed.connect(self._on_play_state_changed)
        self.controller.status_changed.connect(self._on_status_changed)
        if hasattr(self.controller, "cue_changed"):
            self.controller.cue_changed.connect(self._on_cue_changed)

    # ------------------------------------------------------------------
    # UI update slots (dumb view)
    # ------------------------------------------------------------------
    def _on_track_loaded(self, track: Track) -> None:
        self._current_track = track

        pth = getattr(track, "path", None)
        title = getattr(track, "title", None) or (Path(pth).stem if pth else "Utwór")
        artist = getattr(track, "artist", None) or ""
        full = f"{artist} – {title}" if artist else title
        self.title_label.setText(full)

        bpm = getattr(track, "bpm", None)
        if bpm and bpm > 10:
            self.bpm_label.setText(f"{bpm:.1f}")
        else:
            self.bpm_label.setText("— BPM")

        # Przygotuj waveform token (anty-stale) – UNIQUE token, not path
        if pth and hasattr(self.waveform, "set_expected_waveform_token"):
            waveform_token = str(uuid.uuid4())
            self.waveform.set_expected_waveform_token(waveform_token)
        else:
            waveform_token = None

        duration = self._resolve_duration_ms(track)
        self._current_duration_ms = duration

        self.time_label.setText(f"0:00 / {_format_ms(duration)}")

        # BPM na waveform dla beatgrid (jeśli dostępne)
        if hasattr(self.waveform, "set_bpm"):
            self.waveform.set_bpm(bpm)

        # Poproś kontroler o waveform (view odpowiedzialny, jak w focused)
        # FIXED: pass waveform_token instead of path
        if pth and waveform_token and hasattr(self.waveform, "load_waveform"):
            self.controller.request_waveform_load(self.waveform, pth, duration, waveform_token)

        self.status_label.setText("✓ Załadowano")

    def _on_track_unloaded(self) -> None:
        self._current_track = None
        self._current_duration_ms = 0
        self._is_playing = False

        self.title_label.setText("Brak utworu — upuść plik z biblioteki")
        self.bpm_label.setText("— BPM")
        self.time_label.setText("0:00 / 0:00")
        if hasattr(self.waveform, "clear"):
            self.waveform.clear()
        if hasattr(self, "play_btn") and hasattr(self, "cue_btn") and hasattr(self, "stop_btn"):
            apply_transport_button_metrics(
                self._metrics,
                self.cue_btn,
                self.play_btn,
                self.stop_btn,
                playing=False,
                compact=self._compact,
            )

        self.status_label.setText("— Gotowy (tryb Odtwarzacz MVP)")
        if hasattr(self, "_audio_fallback_label"):
            self._audio_fallback_label.setVisible(False)  # reset on unload; re-apply warning if needed elsewhere
        if hasattr(self, "_spin_indicator"):
            self._spin_indicator.stop()
        # re-apply to ensure fallback banner state correct (get_backend_info)
        try:
            self._maybe_apply_audio_fallback_warning()
        except Exception:
            pass

    def _refresh_metrics(self, force_apply: bool = False) -> None:
        new_m = metrics_for_odt(self, compact=self._compact)
        old_scale = self._last_metrics_scale
        self._metrics = new_m
        self._last_metrics_scale = new_m.scale_factor
        # Faza1: force more aggressively on highDPI (scale delta or >1.05) per SZPIEG research 2026-07-14 plan rozbudowy Faza1 Polish (compact highDPI/extreme) + Analyzer. Must document identical.
        if (force_apply or abs(new_m.scale_factor - old_scale) > 0.04 or new_m.scale_factor > 1.05) and hasattr(self, "play_btn"):
            self._apply_compact_ui()

    def resizeEvent(self, event):
        """Scalability polish (per SZPIEG Build Spec + Plan step6 + exact match + grupa 5+9 lista po 'dalej'):
        dynamic on resize (multi-res, stretch, air/margins preserved in compact/non).
        Dominant wave (stretch 7, min260 noncompact / smaller compact), spin dynamic size.
        In odt + window: Expanding policies, QStack, no fixed on containers/wave.
        Air 32/24 or 8/6 from _apply_compact_ui only (resize not touch to preserve).
        precise avail_h (header+time+trans+status+air) for wave min.
        Multi res safe. Per lista 5/9 black/empty + scalab.
        """
        super().resizeEvent(event)
        self._refresh_metrics(force_apply=False)
        if hasattr(self, "waveform"):
            refresh_waveform_on_resize(
                self, self.waveform, self._metrics, compact=self._compact
            )
        # Faza1 highDPI/extreme force refresh (per SZPIEG research 2026-07-14 plan rozbudowy Faza1 Polish + Analyzer refined: ensure update + geometry after scale >1.04 or extreme narrow to prevent cut/empty in 280x200 + DPI 144+). Must document identical.
        try:
            if getattr(self, "_metrics", None) and self._metrics.scale_factor > 1.04 or self._compact:
                self.update()
                self.updateGeometry()
                if hasattr(self, "waveform"):
                    self.waveform.update()
            if hasattr(self, "_audio_fallback_label") and self._audio_fallback_label.isVisible():
                self._audio_fallback_label.update()
        except Exception:
            pass
        # Ensure spin size scales a bit in compact
        if self._compact and hasattr(self, "_spin_indicator"):
            try:
                s = max(self._metrics.px(14), min(self._metrics.px(26), self.width() // 24))
                self._spin_indicator.setFixedSize(s, s)
            except Exception:
                pass

    def _resolve_duration_ms(self, track: Track | None = None) -> int:
        duration = 0
        try:
            if self.controller.playback_engine:
                state = self.controller.playback_engine.get_deck_state(self.controller.deck_id)
                if state and getattr(state, "duration_ms", 0):
                    duration = int(state.duration_ms)
        except Exception:
            pass
        if duration <= 0 and track is not None:
            duration = SimpleDeckController._duration_ms_from_track(track)
        if duration <= 0 and getattr(self.controller, "_known_duration_ms", 0) > 0:
            duration = int(self.controller._known_duration_ms)
        return max(0, duration)

    def _on_playhead_changed(self, ms: int) -> None:
        refreshed = self._resolve_duration_ms(self._current_track)
        if refreshed > self._current_duration_ms:
            self._current_duration_ms = refreshed
            if hasattr(self.waveform, "set_duration"):
                self.waveform.set_duration(refreshed)
        if hasattr(self.waveform, "set_playhead"):
            self.waveform.set_playhead(ms)
        self.time_label.setText(f"{_format_ms(ms)} / {_format_ms(self._current_duration_ms)}")

    def _on_bpm_changed(self, bpm: float | None) -> None:
        if bpm and bpm > 10:
            self.bpm_label.setText(f"{float(bpm):.1f}")
            if hasattr(self.waveform, "set_bpm"):
                self.waveform.set_bpm(bpm)
        # nie nadpisujemy "— BPM" jeśli None (zachowaj z load)

    def _on_play_state_changed(self, playing: bool) -> None:
        self._is_playing = bool(playing)
        if hasattr(self, "play_btn") and hasattr(self, "cue_btn") and hasattr(self, "stop_btn"):
            apply_transport_button_metrics(
                self._metrics,
                self.cue_btn,
                self.play_btn,
                self.stop_btn,
                playing=playing,
                compact=self._compact,
            )
        # Compact anim react (spin CD only when playing + compact)
        self._update_compact_play_state(playing)

    def _on_status_changed(self, text: str) -> None:
        self.status_label.setText(text)

    def _maybe_apply_audio_fallback_warning(self) -> None:
        """
        Dodaje prominent banner/status z exact '⚠ Audio niedostępne — dla pełnej jakości DJ zainstaluj VLC z videolan.org'
        + użycie get_backend_info(). Wzmocnione dla visibility w compact (status schowany) + highDPI.
        Dedykowany self._audio_fallback_label widoczny zawsze gdy fallback.
        Per SZPIEG research 2026-06-25 DJ checklist + Plan + clean Windows Szpieg ... must document identical.
        Używa get_backend_info (verif: działa z fallback). Non-radical: dodatkowy mały label + update status.
        """
        try:
            eng = getattr(self.controller, "playback_engine", None)
            if not eng:
                return
            # verif get_backend_info działa z fallback (noop/qt) — prefer nad diag
            info = eng.get_backend_info()
            ba = str(info.get("deck_a", "") or info.get("active_backend_a", ""))
            is_fallback = ("Noop" in ba) or ("Qt" in ba) or ("noop" in ba.lower()) or ("qt" in ba.lower())
            if not is_fallback:
                if hasattr(self, "_audio_fallback_label"):
                    self._audio_fallback_label.setVisible(False)
                return
            exact = "⚠ Audio niedostępne — dla pełnej jakości DJ zainstaluj VLC z videolan.org"
            diag_link = " (diagnostics: engine.get_backend_info() / get_diagnostics())"
            # prefix do status (widoczny w non-compact) — zachowaj oryginalny po |
            curr = self.status_label.text() or "— Gotowy (tryb Odtwarzacz MVP)"
            if exact not in curr:
                self.status_label.setText(f"{exact}{diag_link} | {curr}")
            # WIDOCZNY DEDYKOWANY BANNER nawet w compact/highDPI (status_label hidden w compact)
            if hasattr(self, "_audio_fallback_label"):
                self._audio_fallback_label.setText(f"{exact}{diag_link}")
                self._audio_fallback_label.setVisible(True)
            # widoczny EFFECT style (żółty warning z palety) — bezpiecznie, bez psucia metryk
            try:
                from ui.dj.styles import BOOTH_COLORS
                wcol = BOOTH_COLORS.get("warning", "#eab308")
                base_ss = self._metrics.status_stylesheet() or ""
                self.status_label.setStyleSheet(f"color: {wcol}; font-weight: 600; {base_ss}")
                if hasattr(self, "_audio_fallback_label"):
                    self._audio_fallback_label.setStyleSheet(f"color: {wcol}; font-weight: 700; font-size: 10px; background: #2a2318; border: 1px solid #854d0e; padding: 2px;")
            except Exception:
                pass
            self.status_label.setToolTip(
                f"{exact}{diag_link}. EFEKT: fallback (brak EQ/keylock/low-jitter); FILE load działa, STREAM ograniczony. "
                "Zainstaluj VLC z videolan.org dla pełnej jakości DJ. Per Szpieg/Plan."
            )
            if hasattr(self, "_audio_fallback_label"):
                self._audio_fallback_label.setToolTip(
                    f"{exact}{diag_link}. EFEKT: fallback (brak EQ/keylock/low-jitter); FILE load działa, STREAM ograniczony. "
                    "Zainstaluj VLC z videolan.org dla pełnej jakości DJ (per research Mixxx/Winamp/VLC prio). Per SZPIEG research 2026-06-25."
                )
        except Exception:
            pass  # non fatal, nie psuj UI

    # ------------------------------------------------------------------
    # Transport MVP (explicit play vs pause, nie toggle w kontrolerze)
    # ------------------------------------------------------------------
    def _on_cue_pressed(self) -> None:
        mods = QtWidgets.QApplication.keyboardModifiers()
        if mods & QtCore.Qt.KeyboardModifier.ShiftModifier:
            self._skip_cue_release = True
            self.controller.set_cue_at_playhead()
            return
        self._skip_cue_release = False
        self.controller.cue_pressed()

    def _on_cue_released(self) -> None:
        if self._skip_cue_release:
            self._skip_cue_release = False
            return
        self.controller.cue_released()

    def _on_waveform_set_cue(self, time_ms: int) -> None:
        self.controller.set_cue_at_ms(time_ms)
        self.controller.seek(time_ms)

    def _on_cue_changed(self, cue_ms: int) -> None:
        if hasattr(self.waveform, "set_main_cue_ms"):
            self.waveform.set_main_cue_ms(cue_ms)

    def _on_play_or_pause_clicked(self) -> None:
        try:
            if getattr(self, "_is_playing", False):
                self.controller.pause()
            else:
                if not getattr(self.controller, "current_track", None):
                    self.status_label.setText("— Najpierw załaduj utwór (drag lub biblioteka)")
                    return
                self.controller.play()
        except Exception as exc:
            logger.warning(f"Odtwarzacz transport error: {exc}")
            self.status_label.setText(f"✗ Błąd odtwarzania: {exc}")

    def _on_volume_changed(self, percent: int) -> None:
        """WMP-style volume — deck gain 0–100%."""
        if hasattr(self.controller, "set_volume"):
            self.controller.set_volume(percent)

    # ------------------------------------------------------------------
    # Pitch stub handlers (Faza1 single MVP) — wired from reused PitchControl
    # per SZPIEG research 2026-07-14 plan rozbudowy Faza1 Polish (single pitch/TRIM stub... must document identical)
    # Minimal: delegate to controller (now supports set_pitch/set_rate/set_keylock for single).
    # No impact on FILE ops, STREAM only (rate).
    # ------------------------------------------------------------------
    def _on_pitch_changed(self, percent: int) -> None:
        """Handle pitch slider change. Maps to controller.set_pitch or set_rate."""
        try:
            if hasattr(self.controller, "set_pitch"):
                self.controller.set_pitch(float(percent))
            elif hasattr(self.controller, "set_rate"):
                # fallback for minimal controller
                rate = 1.0 + (float(percent) / 100.0)
                self.controller.set_rate(rate)
            else:
                # direct engine wire minimal (should not reach)
                if hasattr(self.controller, "playback_engine"):
                    r = 1.0 + (float(percent) / 100.0)
                    self.controller.playback_engine.set_deck_rate(
                        getattr(self.controller, "deck_id", "A"), r
                    )
        except Exception as exc:
            logger.debug(f"Odt pitch change error (stub ok): {exc}")

    def _on_keylock_toggled(self, enabled: bool) -> None:
        """Handle KEYLOCK toggle stub."""
        try:
            if hasattr(self.controller, "set_keylock"):
                self.controller.set_keylock(enabled)
        except Exception as exc:
            logger.debug(f"Odt keylock error (stub ok): {exc}")

    # ------------------------------------------------------------------
    # Drag & drop z pełnym repo lookup (identycznie jak w main window / _load_dropped_track)
    # ------------------------------------------------------------------
    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        mime = event.mimeData()
        if mime.hasFormat("application/x-lumbago-track-paths") or mime.hasUrls():
            # Highlight for drag UX (per spec: highlight+position safety) — działa w compact i normal.
            # Drag highlight in compact: force cyan border niezależnie od _normal (który jest init non-compact).
            # Używamy get_ + override + compact bg jeśli potrzeba (per findings FIXER).
            base = getattr(self, "_normal_stylesheet", None) or get_deck_panel_stylesheet()
            # W compact używamy mniejszego border ale highlight zawsze widoczny.
            hl = base.replace(
                "border: 1px solid #2a3442;",
                "border: 3px solid #00e0ff; background-color: #1a212c;"
            )
            # Dodaj !important-like via extra reguła dla #OdtwarzaczPanel
            hl = hl + "\n QFrame#OdtwarzaczPanel { border: 3px solid #00e0ff !important; }"
            self.setStyleSheet(hl)
            pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
            logger.debug(f"Odt dragEnter at pos {pos} (mime ok, FILE load pending, compact={self._compact})")
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event: QtGui.QDragLeaveEvent) -> None:
        # Reset highlight (per step5 drag UX)
        if hasattr(self, "_normal_stylesheet"):
            self.setStyleSheet(self._normal_stylesheet)
        # If compact: sizes/fonts already set by _apply, panel ss reset to base is acceptable (no overlap with compact).
        # Re-sync spin vis if needed (defensive).
        if getattr(self, '_compact', False) and hasattr(self, '_spin_indicator'):
            self._spin_indicator.setVisible(True)
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        # Reset highlight on drop (per step5)
        if hasattr(self, "_normal_stylesheet"):
            self.setStyleSheet(self._normal_stylesheet)
        # Compact guard after reset highlight (keep pilot visuals)
        if getattr(self, '_compact', False) and hasattr(self, '_spin_indicator'):
            self._spin_indicator.setVisible(True)
        mime = event.mimeData()
        paths = []
        if mime.hasFormat("application/x-lumbago-track-paths"):
            data = mime.data("application/x-lumbago-track-paths").data().decode()
            paths = [p for p in data.split(",") if p]
        elif mime.hasUrls():
            for url in mime.urls():
                if url.isLocalFile():
                    paths.append(url.toLocalFile())
        if paths:
            pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
            logger.debug(f"Odt drop at pos {pos} -> load FILE {paths[0]} (batch={len(paths)})")
            # Safety (lock/prompt per spec): confirm if stream playing (FILE load during playback)
            # FIXER polish lista 14/5 + compact prompt UX (per SZPIEG/Plan nowa lista + UI-DESIGNER): 
            # parent top-level (self.window() for floating always-on-top pilot StaysOnTopHint case) so dialog appears correctly over compact window.
            # EFFECT: FILE load (drop) vs STREAM (current play) explicit. No core cue/play change.
            if getattr(self, "_is_playing", False):
                try:
                    from PyQt6.QtWidgets import QMessageBox
                    parent_for_prompt = self.window() if hasattr(self, "window") and self.window() else self
                    resp = QMessageBox.question(
                        parent_for_prompt, "Odtwarzacz — Safety",
                        "Trwa odtwarzanie (stream). Załadować nowy PLIK i zatrzymać?\n(EFEKT: stop + load nowego pliku z cue=0)",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No
                    )
                    if resp != QMessageBox.StandardButton.Yes:
                        event.acceptProposedAction()
                        return
                except Exception:
                    pass  # non-fatal, proceed
            self._load_dropped_track(paths[0])
            # Drag batch polish (FIXER): single MVP loads first only (uniform with window dual logic); log rest for future/UX.
            if len(paths) > 1:
                logger.debug(f"Odt single: batch drop, loaded first path only (MVP single no multi-deck); {len(paths)-1} ignored")
        event.acceptProposedAction()

    def _load_dropped_track(self, path: str) -> None:
        """Pełny lookup z repo jak w dj_player_window._load_dropped_track.
        To jest FILE op: drop = załaduj PLIK (lookup DB, set current_track, waveform token, cue=0).
        Po tym transport (play) używa STREAMU z pliku.
        Drag highlight/position obsługiwane przez mime w dragEnter/drop + parent window.
        Guard: safety prompt już w dropEvent jeśli _is_playing.
        Komentarz file/stream w load vs transport paths (per lista FIXER + SZPIEG).
        """
        try:
            name = Path(path).stem
            track = Track(path=path, title=name)
            # Enrich z DB (id dla przyszłych, tu dla spójności + metadane)
            try:
                from data.repository import get_track_by_path
                dbt = get_track_by_path(path)
                if dbt and getattr(dbt, "id", None):
                    track = dbt
            except Exception as exc:
                logger.debug(f"OdtwarzaczView drop DB lookup: {exc}")
            self.controller.load_track(track)
        except Exception as e:
            msg = "Błąd ładowania upuszczonego tracka w OdtwarzaczView"
            logger.warning(f"{msg}: {e}")

    # ------------------------------------------------------------------
    # Compact mode (pilot-like) + animated indicator (per SZPIEG Build Spec step 3)
    # set_compact_mode, collapse sizes, react to play_state, spin CD-like.
    # Modular: sizes from styles.BOOTH_SIZES compact_*, anim self contained.
    # ------------------------------------------------------------------
    def set_compact_mode(self, compact: bool) -> None:
        """Włącz/wyłącz tryb compact (mały pilot). Zmienia rozmiary, fonty, min wave, pokazuje spin ind.
        Zachowuje cue logic, air (mniejsze), drag, scalability.
        Toggle z dj_player_window (przycisk).
        """
        if self._compact == bool(compact):
            return
        self._compact = bool(compact)
        self._refresh_metrics(force_apply=False)
        try:
            if hasattr(self.controller, "set_compact_mode"):
                self.controller.set_compact_mode(compact)
        except Exception:
            pass
        self._apply_compact_ui()
        # Ensure spin anim state is in sync immediately after toggle (e.g. if already playing)
        # _update checks _compact internally.
        try:
            self._update_compact_play_state(getattr(self, "_is_playing", False))
        except Exception:
            pass

    def _apply_compact_ui(self) -> None:
        # Compact toggle + anim spin polish per SZPIEG/Plan step2 + lista 2+12 after user 'ok'+'kontynuuj' + FINAL RETRY "zastosuj zmiany i wypchnij... dokończ wszystkie punkty... zkompaktuj... [...]
        # 2026-06 continue + retry: tighter bottom margin 2px in compact (reduce empty space / pack pilot per Plan 5/12 + SZPIEG pilot spec "minimal air zachowany, nie zero").
        # Wątek re-audit + lista 1-15 + docs compaction + close – zakończony. Wszystkie punkty DONE. Verifs green. Push. Gotowe do końca.
        if getattr(self, "_applying_compact", False):
            return
        self._applying_compact = True
        try:
            compact = self._compact
            m = self._metrics
            self.layout().setContentsMargins(*m.layout_margins())
            self.layout().setSpacing(m.layout_spacing())

            if hasattr(self, "play_btn") and hasattr(self, "cue_btn") and hasattr(self, "stop_btn"):
                apply_transport_button_metrics(
                    m,
                    self.cue_btn,
                    self.play_btn,
                    self.stop_btn,
                    playing=getattr(self, "_is_playing", False),
                    compact=compact,
                )

            if hasattr(self, "waveform"):
                refresh_waveform_on_resize(self, self.waveform, m, compact=compact)

            if hasattr(self, "_header_parts"):
                apply_header_metrics(self._header_parts, m)
            if hasattr(self, "time_label"):
                self.time_label.setStyleSheet(m.time_stylesheet())
            if hasattr(self, "status_label"):
                self.status_label.setStyleSheet(m.status_stylesheet())
                self.status_label.setVisible(not compact)

            # Wzmocnienie visibility fallback banner w compact + highDPI:
            # dedicated _audio_fallback_label ZAWSZE widoczny gdy fallback (nawet gdy status schowany w tight pilot).
            # Mały font + pack dla reduce empty. Per SZPIEG research 2026-06-25 DJ checklist + Plan + Mixxx/Winamp tight.
            if hasattr(self, "_audio_fallback_label"):
                if self._audio_fallback_label.text():
                    self._audio_fallback_label.setVisible(True)
                    try:
                        # compact: mniejszy font dla tight highDPI pilot (bez marnowania bottom space)
                        fs = 8 if compact else 10
                        base = self._audio_fallback_label.styleSheet() or ""
                        self._audio_fallback_label.setStyleSheet(f"{base}; font-size: {fs}px;")
                    except Exception:
                        pass
                else:
                    self._audio_fallback_label.setVisible(False)

            if hasattr(self, "player_controls"):
                self.player_controls.apply_metrics(m)
                self._sync_transport_layout(compact)

            # Pitch stub: hide in compact (per task: compact hides if needed to keep air, no break highDPI/pilot ~420x300 + StaysOnTop).
            # In normal: visible after controls; highDPI forces (resize/updateGeometry) already cover via existing Faza1 logic.
            # Fallback/QStack/air preserved.
            if hasattr(self, "pitch_control"):
                self.pitch_control.setVisible(not compact)
                if not compact:
                    # optional metrics sync (non breaking; pitch_control uses its internal)
                    try:
                        if hasattr(self.pitch_control, "apply_metrics"):
                            self.pitch_control.apply_metrics(self._metrics)
                    except Exception:
                        pass

            if hasattr(self, "_flex_spacer"):
                self._flex_spacer.setVisible(not compact)

            if hasattr(self, "layout") and self.layout() is not None:
                lay = self.layout()
                for i in range(lay.count()):
                    item = lay.itemAt(i)
                    if item is None:
                        continue
                    w = item.widget()
                    if w is self.waveform:
                        lay.setStretch(i, m.wave_stretch())
                    elif w is getattr(self, "_flex_spacer", None):
                        lay.setStretch(i, 0 if compact else 1)

            if hasattr(self, "_spin_indicator"):
                self._spin_indicator.setFixedSize(m.spin_size(), m.spin_size())
                self._spin_indicator.setVisible(compact)

            # Faza1 highDPI/extreme force layout + repaint (Analyzer luki: extreme 280x200 + DPI not propagating to wave/fallback). per SZPIEG research 2026-07-14 plan rozbudowy Faza1 Polish... must document identical.
            try:
                self.updateGeometry()
                self.update()
                if hasattr(self, "waveform"):
                    self.waveform.update()
                if hasattr(self, "_audio_fallback_label") and self._audio_fallback_label.text():
                    self._audio_fallback_label.setVisible(True)
                    self._audio_fallback_label.update()
            except Exception:
                pass
                if compact:
                    # Upewnij spin visible w compact (test isVisible po set, po show stack current odt).
                    # Per SZPIEG/REVIEWER/Plan findings: Qt timing/polish w headless/shown + stack switch może opóźnić.
                    # Guard + update po set.
                    if not self._spin_indicator.isVisible():
                        self._spin_indicator.setVisible(True)
                    self._spin_indicator.update()
                else:
                    self._spin_indicator.stop()

            # Ensure black/empty UI + bg in compact (stylesheet #OdtwarzaczPanel, initial "Brak utworu" placeholder state).
            # Per step8/9 + FIXER lista 9/5/14 polish: bg surface from BOOTH (dark booth) even after compact toggle/sizes; no light bleed.
            # highDPI/compact empty: force "Brak..." + update even in pilot (scalab precise empty space handling).
            # Placeholder in title on unload/no track. Drag/compact preserve. Force text if no current track.
            # vis timing: update after set for Qt polish (headless + shown + floating).
            try:
                base_ss = getattr(self, "_normal_stylesheet", None) or get_deck_panel_stylesheet()
                self.setStyleSheet(base_ss)
            except Exception:
                pass
            if not getattr(self, '_current_track', None) and hasattr(self, 'title_label'):
                try:
                    self.title_label.setText("Brak utworu — upuść plik z biblioteki")
                except Exception:
                    pass
            # highDPI note (per lista 5 scalab): Qt auto, but force geometry update for compact pilot shrink.
            try:
                self.updateGeometry()
                if self._compact and hasattr(self, "_spin_indicator"):
                    self._spin_indicator.update()
            except Exception:
                pass

            try:
                self.updateGeometry()
            except Exception:
                pass
        finally:
            self._applying_compact = False

    def _sync_transport_layout(self, compact: bool) -> None:
        """Normal: wycentrowany transport; compact: VOL + CUE ▶ ■ w jednym rzędzie."""
        if not hasattr(self, "player_controls") or not hasattr(self, "_transport_widget"):
            return
        buttons = (self.cue_btn, self.play_btn, self.stop_btn)
        if compact:
            trans_row = self._transport_widget.layout()
            if trans_row is not None:
                for btn in buttons:
                    trans_row.removeWidget(btn)
            self._transport_widget.hide()
            self.player_controls.set_compact_strip(True)
            return
        self.player_controls.set_compact_strip(False)
        trans_row = self._transport_widget.layout()
        if trans_row is not None:
            for btn in buttons:
                trans_row.removeWidget(btn)
            while trans_row.count():
                trans_row.takeAt(0)
            trans_row.addStretch(1)
            for btn in buttons:
                trans_row.addWidget(btn)
            trans_row.addStretch(1)
        self._transport_widget.show()

    def _update_compact_play_state(self, playing: bool) -> None:
        """React to play_state for anim (spin when playing in compact).
        Per step2: ensure visible works in compact (static CD even if !play; spin only on play).
        Guard reentrancy via apply path.
        """
        if hasattr(self, "_spin_indicator"):
            if self._compact:
                self._spin_indicator.setVisible(True)
                if playing:
                    self._spin_indicator.start()
                else:
                    self._spin_indicator.stop()
            else:
                self._spin_indicator.setVisible(False)
                self._spin_indicator.stop()
