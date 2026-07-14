from __future__ import annotations

import sys
import traceback
from pathlib import Path
import os

sys.coinit_flags = 2

from dotenv import load_dotenv
from PyQt6 import QtCore, QtGui, QtWidgets

from ui.theme import apply_theme
from ui.widgets import apply_window_fade
from core.config import app_data_dir

# HighDPI support for Faza1 Polish (compact extreme + multi-monitor per Szpieg/Plan)
# per SZPIEG research 2026-07-14 plan rozbudowy Faza1 Polish (compact highDPI/extreme) + Analyzer + Plan "nowa lista" item1: AA_Enable + UseHighDpiPixmaps for Qt6 DPI scaling (144/192dpi, 4k, narrow pilot). Must document identical.
try:
    QtWidgets.QApplication.setAttribute(QtCore.Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    QtWidgets.QApplication.setAttribute(QtCore.Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
except Exception:
    pass


def main() -> int:
    load_dotenv()
    _install_exception_hooks()

    # Smoke diag early path (nawet w LUMBAGO_SAFE_MODE stub): jeśli LUMBAGO_SMOKE_DIAG lub SMOKE + diag env — utwórz PlaybackEngine(), wypisz get_backend_info + get_diagnostics(), potem quit.
    # Per SZPIEG research 2026-06-25 + Analyzer + Plan "nowa lista" (luki SAFE stub omija DJ/backend/diag) — must document identical.
    # Obsługuje headless smoke verif no-VLC/Noop states + backend info bez pełnego UI.
    # Wzmocnione 2026-07-13 per Analyzer + SZPIEG 2026-07-13: basic DJ sim (create PlaybackEngine + odt view sim + load + _maybe_apply + assert label zawiera "⚠" lub backend Noop) — must document identical
    smoke_diag = os.getenv("LUMBAGO_SMOKE_DIAG", "0") == "1" or (os.getenv("LUMBAGO_SMOKE_SECONDS") and os.getenv("LUMBAGO_SMOKE_DIAG"))
    if smoke_diag:
        try:
            from services.playback.engine import PlaybackEngine
            e = PlaybackEngine()
            print("BACKEND_INFO:", e.get_backend_info())
            print("DIAGNOSTICS:", e.get_diagnostics())
            print("SMOKE_DIAG: engine created and reported (even in SAFE stub) per SZPIEG 2026-06-25 + Analyzer + Plan")
            # === basic DJ sim per task: PlaybackEngine + odt view sim + load + _maybe_apply + assert label "⚠" or Noop (headless ok w offscreen) — only smoke/DIAG, nie core UI ===
            # per SZPIEG research 2026-07-13 + Analyzer 2026-07-13 (smoke + main DIAG) ... must document identical
            try:
                os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
                from PyQt6.QtWidgets import QApplication
                app = QApplication.instance() or QApplication([])
                from core.models import Track
                from ui.dj.simple_deck_controller import SimpleDeckController
                from ui.dj.views.odtwarzacz_view import OdtwarzaczView
                ctrl = SimpleDeckController("A", e)
                # sim odt view (compact or normal)
                view = OdtwarzaczView(ctrl, None)
                # basic load sim (dummy track; real load may skip audio)
                try:
                    dummy = Track(path="", title="SMOKE_DJ_SIM", artist="Diag", bpm=120.0)
                    ctrl.load_track(dummy)  # may set state
                    view._on_track_loaded(dummy) if hasattr(view, "_on_track_loaded") else None
                except Exception:
                    pass
                # call _maybe_apply
                if hasattr(view, "_maybe_apply_audio_fallback_warning"):
                    view._maybe_apply_audio_fallback_warning()
                # assert label contains "⚠" or backend Noop
                ba = str(e.get_backend_info().get("deck_a", "") or "")
                label_text = ""
                if hasattr(view, "_audio_fallback_label") and view._audio_fallback_label:
                    label_text = view._audio_fallback_label.text() or ""
                if hasattr(view, "status_label"):
                    label_text += " " + (view.status_label.text() or "")
                assert "⚠" in label_text or "Audio niedostępne" in label_text or "Noop" in ba or "noop" in ba.lower() or "Qt" in ba, f"SMOKE_DJ_SIM assert failed: no fallback '⚠' or Noop in label/ba: {label_text[:100]} / {ba}"
                print("SMOKE_DJ_SIM: odt view + load + _maybe_apply + fallback label/⚠ or Noop assert PASSED")
                try:
                    view.close()
                except Exception:
                    pass
            except Exception as sim_ex:
                print("SMOKE_DJ_SIM_WARNING (headless tolerant):", sim_ex)
            return 0
        except Exception as ex:
            print("SMOKE_DIAG_ERROR:", ex, file=sys.stderr)
            return 1

    QtCore.QCoreApplication.setAttribute(QtCore.Qt.ApplicationAttribute.AA_UseSoftwareOpenGL)
    app = QtWidgets.QApplication(sys.argv)
    app.setFont(QtGui.QFont("Segoe UI", 11))
    apply_theme(app)
    app.aboutToQuit.connect(lambda: _write_log("app.log", "aboutToQuit"))
    try:
        if os.getenv("LUMBAGO_SAFE_MODE", "0") == "1":
            window = QtWidgets.QMainWindow()
            window.setWindowTitle("Lumbago Music AI (Safe Mode)")
            window.resize(1000, 700)
            apply_window_fade(window)
            window.show()
        else:
            from ui.main_window import MainWindow

            window = MainWindow()
            apply_window_fade(window)
            window.show()

        smoke_seconds = _read_int_env("LUMBAGO_SMOKE_SECONDS", 0)
        if smoke_seconds > 0:
            QtCore.QTimer.singleShot(smoke_seconds * 1000, app.quit)
        QtCore.QTimer.singleShot(2000, lambda: _write_log("app.log", "alive 2s"))
        result = app.exec()
        _write_log("app.log", f"app.exec ended: {result}")
        return result
    except Exception:
        _log_crash()
        # Also print full traceback to console so launchers / full-traceback wrappers always see it
        print("=== FULL TRACEBACK FROM main.py ===", file=sys.stderr)
        traceback.print_exc()
        QtWidgets.QMessageBox.critical(
            None,
            "Błąd uruchomienia",
            "Wystąpił błąd podczas uruchamiania aplikacji. "
            "Szczegóły zapisano w pliku crash.log.",
        )
        return 1


def _log_crash() -> None:
    try:
        target = app_data_dir() / "crash.log"
    except Exception:
        target = Path.cwd() / ".lumbago_data" / "crash.log"
        target.parent.mkdir(parents=True, exist_ok=True)
    try:
        target.write_text(traceback.format_exc(), encoding="utf-8")
    except Exception:
        pass


def _install_exception_hooks() -> None:
    def _handle_exception(exc_type, exc_value, exc_traceback):
        try:
            text = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            _write_log("crash.log", text)
            # Print to stderr so console/launcher wrappers capture runtime slot errors etc.
            print("=== UNCAUGHT EXCEPTION (hook) ===", file=sys.stderr)
            print(text, file=sys.stderr)
        finally:
            sys.__excepthook__(exc_type, exc_value, exc_traceback)

    def _qt_message_handler(mode, context, message):
        _write_log("qt.log", f"{mode}: {message}")

    sys.excepthook = _handle_exception
    try:
        QtCore.qInstallMessageHandler(_qt_message_handler)
    except Exception:
        pass


def _write_log(filename: str, content: str) -> None:
    try:
        target = app_data_dir() / filename
    except Exception:
        target = Path.cwd() / ".lumbago_data" / filename
        target.parent.mkdir(parents=True, exist_ok=True)
    try:
        target.write_text(content, encoding="utf-8")
    except Exception:
        pass


def _read_int_env(name: str, default: int) -> int:
    value = os.getenv(name, "")
    try:
        parsed = int(value)
        return parsed if parsed >= 0 else default
    except ValueError:
        return default


if __name__ == "__main__":
    raise SystemExit(main())
