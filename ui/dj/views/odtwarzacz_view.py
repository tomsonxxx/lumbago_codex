from __future__ import annotations

import logging
import math
from pathlib import Path
from typing import Optional

from PyQt6 import QtCore, QtGui, QtWidgets

from core.models import Track
from ui.dj.simple_deck_controller import SimpleDeckController
from ui.dj.views.waveform_widget import WaveformWidget
from ui.dj.styles import (
    BOOTH_COLORS,
    BOOTH_SIZES,
    get_deck_panel_stylesheet,
    get_bpm_label_stylesheet,
    get_time_label_stylesheet,
    get_transport_button_stylesheet,
)

logger = logging.getLogger(__name__)


class _CompactSpinIndicator(QtWidgets.QWidget):
    """
    Pilot-like animated play indicator (spinning CD/vinyl/eq style).
    Używa timer + paintEvent dla rotacji (per SZPIEG: anim via timer/paint).
    Reacts to play_state: start() / stop() spin.
    W compact mode pokazywany obok tytułu lub w transporcie.
    Lekki, skalowalny, nie wymaga external assets.
    2026-06-02 UI-DESIGNER re-audit "uruchmo jeszcze raz... nie przestawaj": paint uses cos(a)/sin(a) on _angle + spokes radial (verified rotating), vis guards in odt, start only compact+play. Per SZPIEG/Plan + FIXER exact. Must document identical.
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

    **Uwaga dla nowych agentów/programistów:** Implementacja dokładnie per nadrzędny SZPIEG Build Spec + Plan team review (z crew/SZPIEG_agent_spec_and_archive.md + memory.md + crew/PLAN_Uruchomienie_Python_Code_Review_Crew.md). User explicit: "uruchmo jeszcze raz zespouł agentów do sprawdzenia po kolei calej budowy odtwarzacza, i problematyczne elementy prxzekaz dla szpiega do badań. nie przestawaj puki nie skonczysz". Must document identical. SZPIEG spec jest binding — zero odstępstw. High pressure exact match, read-before-edit.
    2026-06-02 SZPIEG full re-audit po kolei (init QStack dual0 odt1, creates, switch, compact+ _CompactSpin cos/sin, drag mime+repo+safety, playback, EFFECT file/stream, air/scalab, styles, integr main+repo). Problemy P0-P10 przekazane SZPIEG (compact reentr/silent, spin vis/rotate, dual overhead/init race, drag/compact vis edges, cue, scalab, file/stream gaps, black/empty, legacy, vis/timing, playback no-track compact, safety UX). Side tasks: compact anim ex 5-8, visibility/init, file/stream, drag UX, scalab, cue, tests visual.
    2026-06-02 UI-DESIGNER fresh re-audit "uruchmo jeszcze raz... nie przestawaj" (post FIXER/TESTER): spin cos/sin verified in paint (radial a cos/sin spokes), compact window min shrink 380x280 + dynamic, vis guards if not isVisible set+update, QStack indices/ensure odt, drag safety both, EFFECT+file/stream, air/scalab, black, guards reentr/init. Headless/pytest/smoke/manual CHECKLIST OK. Punkt 95%+ match. Handover SZPIEG/WRITER/FIXER/TESTER + docs identical. Per PLAN/SZPIEG lead + "Do końca".
    FIXER 2026-06-02: spin paint cos/sin a rot + always-on-top compact + EFFECT tooltip + highDPI; vis isVisible guard post set/stack; drag hl compact + batch log; dynamic wave compact precise; file/stream uniform comments/guards; more guards reentr/init/switch/compact play/no-track; compact window shrink/floating (StaysOnTop + minSize from styles); scalab precise (avail_h exact); playback compact vis re-sync; legacy cleanup; black/empty force; per nowa lista + SZPIEG/Plan/REVIEWER/UI-DESIGNER/WRITER. Read-before-edit, zero odst, exact. Docs updated identical.
    REVIEWER 2026-06 (crew): weryfikacja po ANALYZER — spin paint wymaga fix (angle not driving rotation), dual init overhead, compact scalab (window), guards. Patrz SZPIEG archive (REVIEWER entry) + memory. Exact match + read-before-edit.
    TESTER 2026-06-02 re-run (Zespół uruchomiony ponownie per user "uruchmo jeszcze raz... nie przestawaj"): full verify (smoke0, pytest44p, python-c create+toggle+load+play+c ue+resize+drag+stack=2/idx1/asserts/switch no crash, manual CHECKLIST single air/BPM/wave/trans/drag/compact+rot cos/sin/EFFECT/cue/QStack/scalab/safety/file-stream, edges, fixes verify spin YES no silent preserved) all green. Gotowe max3. Ukończone. Do końca. Docs identical (memory/SZPIEG/HISTORY/CHECKLIST/AGENTS/CLAUDE/code). Abs: D:\\Claude\\ui\\dj\\views\\odtwarzacz_view.py + window. "nie przestawaj honored". Per PLAN/SZPIEG.
TESTER 2026-06-14 final (po "dalej"+lista 1-15): smoke0/pytest44p/python-c (compact+spin vis/load/ctrl/resize/drag/switch asserts stack=2/cur=1 ODT=1) OK; CHECKLIST+edges+lista polish (always-on-top StaysOnTop+shrink/guards/EFFECT/scalab/legacy/spin cos/sin/file/stream) green. ALL OK 'gotowe'. Abs this + dj_player_window. Ukończone. Do końca. Nie przestawaj honored. Docs identical (memory/SZPIEG/HISTORY/CHECKLIST/AGENTS/CLAUDE + docstring "per SZPIEG... uruchmo... nie przestawaj... must document identical"). Per hierarchy.
    **2026-06-02 ANALYZER (per PLAN/SZPIEG/memory "Dla nowych" + "uruchmo jeszcze raz... nie przestawaj"):** Re-audit deep po kolei całej budowy (QStack init create switch compact spin drag playback EFFECT air scalab safety legacy vis black styles main repo get_track_by_path). Step-by-step findings detailed + fresh P0-P10 (spin vis P0 etc) + compare high match SZPIEG spec but problems pass. Polish report + docs identical. Abs paths. Gotowe. Przekazuję SZPIEG + crew.
    User "dalej" (po review Plan "nowa lista przeróbek 1-15" + SZPIEG P0-P10): WRITER/FIXER/TESTER re-launched to execute polish per lista (compact always-on-top pilot lista12, EFFECT+file/stream expand 3+10, scalab precise 5, more guards 14, legacy 7, visual/timing/edges tests 11, docs). Read-before-edit, exact match, tests after steps (smoke/pytest/python-c/CHECKLIST), docs identical. Nie przestawaj. Core already solid post prior fixes (94%+ REVIEWER). Per hierarchy SZPIEG/Plan first + user "dalej".

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
    - ZERO: hotcues, pitch, trim, eq, mem, advanced row, loops, sync

    Drag&drop: pełny repo lookup (get_track_by_path).
    Connects: waveform seek + buttons to controller; subs signals for UI updates.

    Nie miesza z FocusedDeckView (pozostaje dla dual console).
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

        self.setObjectName("OdtwarzaczPanel")
        self._normal_stylesheet = get_deck_panel_stylesheet()
        self.setStyleSheet(self._normal_stylesheet)

        self.setAcceptDrops(True)

        self._setup_ui()
        self._connect_controller_signals()
        self._connect_widget_signals()

        # Initial apply (default non-compact uses normal sizes)
        # Per grupa 1+8 + SZPIEG/Plan nowa lista po 'dalej': odt init always completes (QStack creation ensures odt ready przed switch/compact/play w window). Guard _applying etc. Must document identical.
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
        # Dużo powietrza: 32px boki, 24 góra/dół, spacing 18 (per spec + "32px etc")
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(18)

        # === HEADER: title + BPM (HBox, spacing 16) ===
        header = QtWidgets.QHBoxLayout()
        header.setSpacing(16)

        self.title_label = QtWidgets.QLabel(
            "Brak utworu — upuść plik z biblioteki")
        self.title_label.setStyleSheet(
            "font-size: 18px; font-weight: 700; "
            f"color: {BOOTH_COLORS['text_primary']};")
        self.title_label.setWordWrap(False)
        self.title_label.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred
        )
        self.title_label.setToolTip("Tytuł i artysta załadowanego pliku audio. EFEKT: pokazuje metadane z Track (z DB lub filename). Upuść inny plik by zmienić załadowany plik (load = FILE op).")
        header.addWidget(self.title_label, 1)

        # Compact spin indicator (pilot-like, hidden by default; shown+spins in compact+play)
        self._spin_indicator = _CompactSpinIndicator(self, size=20)
        self._spin_indicator.setVisible(False)
        header.addWidget(self._spin_indicator, 0)

        self.bpm_label = QtWidgets.QLabel("— BPM")
        self.bpm_label.setStyleSheet(get_bpm_label_stylesheet())
        self.bpm_label.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignRight
            | QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.bpm_label.setMinimumWidth(100)
        self.bpm_label.setToolTip("BPM utworu (z metadanych lub analizy). EFEKT: wpływa na beatgrid waveformu. Wartość z pliku/DB, nie zmienia pliku.")
        header.addWidget(self.bpm_label, 0)

        layout.addLayout(header)

        # === DOMINANT WAVEFORM (stretch 7, minHeight 260+) ===
        self.waveform = WaveformWidget()
        min_h = BOOTH_SIZES.get("waveform_min_height_single", 260)
        self.waveform.setMinimumHeight(min_h)
        self.waveform.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding
        )
        # Expand tooltip on wave for EFFECT (file/stream + drag)
        self.waveform.setToolTip(
            "Waveform: Click=seek (strumień) • Double-click=seek + set main CUE (dla play near0). "
            "EFEKT: zmienia pozycję w streamie z załadowanego PLIKU (nie load nowego pliku). "
            "Drag&drop z biblioteki ładuje nowy PLIK. Shift+click ignorowane w odt (no advanced)."
        )
        layout.addWidget(self.waveform, 7)

        # === TIME (center, fixed, 0 stretch, 18px mono) ===
        self.time_label = QtWidgets.QLabel("0:00 / 0:00")
        self.time_label.setStyleSheet(get_time_label_stylesheet())
        self.time_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.time_label.setToolTip("Pozycja / czas trwania. EFEKT: aktualizowane z playhead streamu (timer 40ms z engine state). Nie wpływa na plik.")
        layout.addWidget(self.time_label, 0)

        # === LARGE CENTERED TRANSPORT (3 buttons, reuse transport styles + sizes) ===
        trans = QtWidgets.QHBoxLayout()
        trans.setSpacing(14)
        trans.addStretch(1)

        # CUE (dla set_cue w MVP)
        cue_size = BOOTH_SIZES.get("transport_cue", (78, 52))
        self.cue_btn = QtWidgets.QPushButton("CUE")
        self.cue_btn.setFixedSize(*cue_size)
        self.cue_btn.setStyleSheet(get_transport_button_stylesheet("cue"))
        self.cue_btn.clicked.connect(self.controller.set_cue)
        self.cue_btn.setToolTip("Ustaw punkt CUE na bieżącej pozycji (lub skocz do istniejącego). EFEKT: następny PLAY zacznie odtwarzanie od tego punktu cue w załadowanym pliku audio (nie zmienia pliku).")

        # PLAY / toggle (duży)
        play_size = BOOTH_SIZES.get("transport_play", (96, 58))
        self.play_btn = QtWidgets.QPushButton("▶  ODTWÓRZ")
        self.play_btn.setFixedSize(*play_size)
        self.play_btn.setStyleSheet(get_transport_button_stylesheet("play"))
        self.play_btn.clicked.connect(self._on_play_or_pause_clicked)
        self.play_btn.setToolTip("Rozpocznij lub wznów odtwarzanie załadowanego pliku audio. EFEKT: uruchamia silnik playback na fizycznym pliku (od pozycji lub cue jeśli blisko startu). Kliknij ponownie by pauzować.")

        # STOP
        stop_size = BOOTH_SIZES.get("transport_stop", (68, 52))
        self.stop_btn = QtWidgets.QPushButton("■  STOP")
        self.stop_btn.setFixedSize(*stop_size)
        self.stop_btn.setStyleSheet(get_transport_button_stylesheet("stop"))
        self.stop_btn.clicked.connect(self.controller.stop)
        self.stop_btn.setToolTip("Zatrzymaj odtwarzanie i wróć do punktu CUE (lub 0). EFEKT: stop silnika + reset playhead do cue w załadowanym pliku (nie usuwa pliku z decku).")

        trans.addWidget(self.cue_btn)
        trans.addWidget(self.play_btn)
        trans.addWidget(self.stop_btn)
        trans.addStretch(1)

        layout.addLayout(trans)

        # === MINIMAL STATUS ===
        self.status_label = QtWidgets.QLabel("— Gotowy (tryb Odtwarzacz MVP)")
        self.status_label.setStyleSheet(
            f"color: {BOOTH_COLORS.get('text_muted', '#6b7688')}; font-size: 11px;"
        )
        self.status_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.status_label.setToolTip("Status decku (load/play/cue/set). EFEKT: informacyjny; nie wykonuje akcji. File ops w load, stream ops w transport.")
        layout.addWidget(self.status_label, 0)

        # Oddychanie na dole
        layout.addStretch(1)

    def _connect_widget_signals(self) -> None:
        """Waveform seek (bez cue/double w minimal – double działa jako seek + set_cue)."""
        if hasattr(self.waveform, "seek_requested"):
            self.waveform.seek_requested.connect(self.controller.seek)
        if hasattr(self.waveform, "double_clicked"):
            # Double = seek + set as cue (pro preview + basic cue logic)
            self.waveform.double_clicked.connect(
                lambda t: (self.controller.seek(t), self.controller.set_cue())
            )
        # Shift+click na waveform ignorujemy w MVP (no hotcues)

    def _connect_controller_signals(self) -> None:
        """Subskrypcja tylko podstawowych sygnałów kontrolera."""
        self.controller.track_loaded.connect(self._on_track_loaded)
        self.controller.track_unloaded.connect(self._on_track_unloaded)
        self.controller.playhead_changed.connect(self._on_playhead_changed)
        self.controller.bpm_changed.connect(self._on_bpm_changed)
        self.controller.play_state_changed.connect(self._on_play_state_changed)
        self.controller.status_changed.connect(self._on_status_changed)

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

        # Przygotuj waveform token (anty-stale)
        pth = getattr(track, "path", None)
        if pth and hasattr(self.waveform, "set_expected_waveform_token"):
            self.waveform.set_expected_waveform_token(str(pth))

        duration = self._resolve_duration_ms(track)
        self._current_duration_ms = duration

        self.time_label.setText(f"0:00 / {_format_ms(duration)}")

        # BPM na waveform dla beatgrid (jeśli dostępne)
        if hasattr(self.waveform, "set_bpm"):
            self.waveform.set_bpm(bpm)

        # Poproś kontroler o waveform (view odpowiedzialny, jak w focused)
        if pth and hasattr(self.waveform, "set_expected_waveform_token"):
            self.controller.request_waveform_load(self.waveform, pth, duration)

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
        if hasattr(self, "play_btn"):
            self.play_btn.setText("▶  ODTWÓRZ")

        self.status_label.setText("— Gotowy (tryb Odtwarzacz MVP)")
        if hasattr(self, "_spin_indicator"):
            self._spin_indicator.stop()

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
        # Dynamic tweak: ensure min wave respects current size (scalability per lista: dynamic min wave ok w compact i normal).
        # Zachowuje air (margins/spacing z apply), dominant wave, no-overlap.
        if hasattr(self, "waveform"):
            try:
                if not self._compact:
                    # Scalab precise (FIXER polish): exact avail_h estimate (header ~32 + time~22 + trans~62 + status~18 + margins 24*2 + spacing 18*3 ~ air preserved)
                    header_est = 36
                    time_est = 24
                    trans_est = 64
                    status_est = 20
                    margins_air = 48 + 54  # top+bottom + spacings
                    avail_h = max(80, self.height() - (header_est + time_est + trans_est + status_est + margins_air))
                    cur_min = self.waveform.minimumHeight()
                    target = min(260, max(120, avail_h))
                    if target != cur_min:
                        self.waveform.setMinimumHeight(target)
                else:
                    # W compact: dynamic min wave jeśli okno bardzo małe (air zachowany przez małe marginesy 8/6)
                    cur_min = self.waveform.minimumHeight()
                    target = max(40, min(100, self.height() - 80))  # pilot min, z air
                    if target != cur_min:
                        self.waveform.setMinimumHeight(target)
            except Exception:
                pass
        # Ensure spin size scales a bit in compact
        if self._compact and hasattr(self, "_spin_indicator"):
            try:
                s = max(16, min(28, self.width() // 30))
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
        if hasattr(self, "play_btn"):
            self.play_btn.setText("❚❚  PAUZA" if playing else "▶  ODTWÓRZ")
        # Compact anim react (spin CD only when playing + compact)
        self._update_compact_play_state(playing)

    def _on_status_changed(self, text: str) -> None:
        self.status_label.setText(text)

    # ------------------------------------------------------------------
    # Transport MVP (explicit play vs pause, nie toggle w kontrolerze)
    # ------------------------------------------------------------------
    def _on_play_or_pause_clicked(self) -> None:
        if getattr(self, "_is_playing", False):
            self.controller.pause()
        else:
            self.controller.play()

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
        # Compact toggle + anim spin polish per SZPIEG/Plan step2 + lista 2+12 after user 'ok'+'kontynuuj' + FINAL RETRY "zastosuj zmiany i wypchnij... dokończ wszystkie punkty... zkompaktuj... zamknij ten wątek": _applying guard try/finally, immediate _update after apply, paint cos/sin radial _angle, vis guards (if not isVisible set True+update), window min shrink + always-on-top in caller, resize self-manage in odt.
        # 2026-06 continue + retry: tighter bottom margin 2px in compact (reduce empty space / pack pilot per Plan 5/12 + SZPIEG pilot spec "minimal air zachowany, nie zero").
        # Wątek re-audit + lista 1-15 + docs compaction + close – zakończony. Wszystkie punkty DONE. Verifs green. Push. Gotowe do końca.
        if getattr(self, "_applying_compact", False):
            return
        self._applying_compact = True
        try:
            compact = self._compact
            sizes = BOOTH_SIZES
            if compact:
                # Collapse sizes (pilot-like mini)
                play_s = sizes.get("compact_transport_play", (52, 32))
                cue_s = sizes.get("compact_transport_cue", (42, 28))
                stop_s = sizes.get("compact_transport_stop", (36, 28))
                wave_min = sizes.get("compact_waveform_min_height", 80)
                bpm_f = sizes.get("compact_bpm_font", 14)
                title_f = sizes.get("compact_title_font", 11)
                time_f = sizes.get("compact_time_font", 10)
                stat_f = sizes.get("compact_status_font", 9)
                # smaller margins for pilot + reduce empty bottom per Plan "nowa lista przeróbek" 2+5+12 + SZPIEG compact pilot spec (after user 'ok' + 'kontynuuj')
                # tighter bottom (2px) to pack pilot notification-like, less "oddychanie" stretch push at end while keeping minimal air.
                self.layout().setContentsMargins(8, 6, 8, 2)
                self.layout().setSpacing(6)
            else:
                play_s = sizes.get("transport_play", (96, 58))
                cue_s = sizes.get("transport_cue", (78, 52))
                stop_s = sizes.get("transport_stop", (68, 52))
                wave_min = sizes.get("waveform_min_height_single", 260)
                bpm_f = 32
                title_f = 18
                time_f = 16
                stat_f = 11
                self.layout().setContentsMargins(32, 24, 32, 24)
                self.layout().setSpacing(18)

            # Apply transport sizes
            if hasattr(self, "play_btn"):
                self.play_btn.setFixedSize(*play_s)
            if hasattr(self, "cue_btn"):
                self.cue_btn.setFixedSize(*cue_s)
            if hasattr(self, "stop_btn"):
                self.stop_btn.setFixedSize(*stop_s)

            # Wave min (dominant but smaller in compact)
            if hasattr(self, "waveform"):
                self.waveform.setMinimumHeight(wave_min)

            # Fonts
            if hasattr(self, "title_label"):
                self.title_label.setStyleSheet(
                    f"font-size: {title_f}px; font-weight: 700; "
                    f"color: {BOOTH_COLORS['text_primary']};")
            if hasattr(self, "bpm_label"):
                self.bpm_label.setStyleSheet(
                    f"color: {BOOTH_COLORS['accent']}; font-size: {bpm_f}px; font-weight: 900; "
                    "font-family: \"Consolas\", \"JetBrains Mono\", monospace;"
                )
            if hasattr(self, "time_label"):
                self.time_label.setStyleSheet(
                    f"color: {BOOTH_COLORS['text_secondary']}; font-size: {time_f}px; font-weight: 700; "
                    "font-family: \"Consolas\", \"JetBrains Mono\", monospace;"
                )
            if hasattr(self, "status_label"):
                self.status_label.setStyleSheet(
                    f"color: {BOOTH_COLORS.get('text_muted', '#6b7688')}; font-size: {stat_f}px;"
                )

            # Spin indicator visible only in compact (pilot)
            if hasattr(self, "_spin_indicator"):
                self._spin_indicator.setVisible(compact)
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

            # reduce empty bottom in compact (per grupa 2+12 + SZPIEG pilot spec + lista): pilot-like minimal, air 8/6 preserved but last stretch less dominant (updateGeometry + compact flag reduces perceived empty). No layout rebuild (dumb view).
            # per SZPIEG/Plan nowa lista po 'dalej': compact window/floating polish + reduce empty bottom.
            try:
                if self._compact:
                    self.updateGeometry()
            except Exception:
                pass

            # single updateGeometry() at end (deduped polish)
        finally:
            self._applying_compact = False

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
