from __future__ import annotations

"""
DownloaderWindow — główne okno modułu pobierania/konwersji.

UI dokładnie wg spec z lumbago_grok_build_prompt.txt:
- URL, dir, format, quality/profile
- 2 progress bary (overall + current)
- log scroll
- START / CANCEL (PAUSE opcjonalnie)
- obsługa błędów per plik + continue
- real-time status playlisty

Integracja z workerem + bridge.
Opcjonalnie: checkbox "Dodaj do biblioteki po zakończeniu" (sugestia A).
Detekcja ffmpeg / yt-dlp + instrukcje.
Styl cyber spójny z resztą Lumbago (DialogCard, apply_fade).

Per all guidelines (QThread, read-before, add don't overwrite, identical docs).
Per SZPIEG research + consolidated raw + detailed prompt 2026-06-27 + CHECKLIST_Downloader_AI_Panel.md + PLAN + "dalej" (search B, est dialog+disk, wiring, A info) + FIXER (more sandbox comments, full A wiring, portable note) ... must document identical.
"""

import shutil
from pathlib import Path

from PyQt6 import QtCore, QtGui, QtWidgets

from core.config import load_settings, save_settings, get_resource_path
from downloader.download_worker import DownloadWorker
from downloader.format_profiles import PROFILES, FORMATS, get_quality_label, normalize_format, normalize_profile
from downloader.progress_bridge import ProgressBridge
from downloader import playlist_manager
from ui.widgets import apply_dialog_fade

import yt_dlp  # for preflight probe
import shutil  # for disk check in est
import json  # for history details in F


def _has_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


def _has_ytdlp() -> bool:
    try:
        import yt_dlp  # noqa: F401
        return True
    except Exception:
        return False


class DownloaderWindow(QtWidgets.QDialog):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Lumbago Downloader / Konwerter")
        self.setMinimumSize(820, 620)
        apply_dialog_fade(self)

        self.settings = load_settings()
        self._worker: DownloadWorker | None = None
        self._bridge: ProgressBridge | None = None

        self._build_ui()
        self._load_prefs()
        self._check_tools()

    def _build_ui(self) -> None:
        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(12)

        # Card główny
        card = QtWidgets.QFrame()
        card.setObjectName("DialogCard")
        card_lay = QtWidgets.QVBoxLayout(card)
        card_lay.setContentsMargins(16, 14, 16, 16)
        card_lay.setSpacing(10)
        lay.addWidget(card)

        # Header
        header = QtWidgets.QHBoxLayout()
        icon_lbl = QtWidgets.QLabel()
        icon_lbl.setPixmap(QtGui.QPixmap(str(get_resource_path("ui/assets/icons/download.svg")) if Path(get_resource_path("ui/assets/icons/download.svg")).exists() else ""))
        icon_lbl.setFixedSize(22, 22)
        title = QtWidgets.QLabel("Pobieranie z YouTube / SoundCloud")
        title.setObjectName("DialogTitle")
        header.addWidget(icon_lbl)
        header.addWidget(title)
        header.addStretch(1)
        card_lay.addLayout(header)

        # URL row
        url_row = QtWidgets.QHBoxLayout()
        url_row.addWidget(QtWidgets.QLabel("URL (film lub playlista):"))
        self.url_edit = QtWidgets.QLineEdit()
        self.url_edit.setPlaceholderText("https://youtube.com/playlist?list=... lub pojedynczy link")
        url_row.addWidget(self.url_edit, 1)
        card_lay.addLayout(url_row)

        # Search row (sugestia B)
        search_row = QtWidgets.QHBoxLayout()
        search_row.addWidget(QtWidgets.QLabel("Szukaj na YT:"))
        self.search_edit = QtWidgets.QLineEdit()
        self.search_edit.setPlaceholderText("tytuł utworu lub artysty")
        self.search_btn = QtWidgets.QPushButton("Szukaj")
        self.search_btn.clicked.connect(self._search_yt)
        search_row.addWidget(self.search_edit, 1)
        search_row.addWidget(self.search_btn)
        card_lay.addLayout(search_row)

        # Dir row
        dir_row = QtWidgets.QHBoxLayout()
        dir_row.addWidget(QtWidgets.QLabel("Folder docelowy:"))
        self.dir_edit = QtWidgets.QLineEdit()
        self.dir_btn = QtWidgets.QPushButton("Wybierz...")
        self.dir_btn.clicked.connect(self._choose_dir)
        dir_row.addWidget(self.dir_edit, 1)
        dir_row.addWidget(self.dir_btn)
        card_lay.addLayout(dir_row)

        # Format + Profile
        opt_row = QtWidgets.QHBoxLayout()
        opt_row.addWidget(QtWidgets.QLabel("Format:"))
        self.fmt_combo = QtWidgets.QComboBox()
        self.fmt_combo.addItems(list(FORMATS))
        opt_row.addWidget(self.fmt_combo)

        opt_row.addWidget(QtWidgets.QLabel("Jakość / profil:"))
        self.profile_combo = QtWidgets.QComboBox()
        self.profile_combo.addItems(list(PROFILES))
        self.profile_combo.setCurrentText("BALANCE")
        opt_row.addWidget(self.profile_combo)

        self.quality_label = QtWidgets.QLabel("")
        opt_row.addWidget(self.quality_label)
        opt_row.addStretch(1)
        card_lay.addLayout(opt_row)

        self.fmt_combo.currentTextChanged.connect(self._update_quality_label)
        self.profile_combo.currentTextChanged.connect(self._update_quality_label)
        self._update_quality_label()

        # Throttle (zaawansowane, ale proste)
        adv_row = QtWidgets.QHBoxLayout()
        adv_row.addWidget(QtWidgets.QLabel("Opóźnienie między plikami (s):"))
        self.throttle_spin = QtWidgets.QDoubleSpinBox()
        self.throttle_spin.setRange(0.0, 10.0)
        self.throttle_spin.setSingleStep(0.5)
        self.throttle_spin.setValue(1.5)
        adv_row.addWidget(self.throttle_spin)
        adv_row.addWidget(QtWidgets.QLabel("   Max concurrent fragments:"))
        self.frag_spin = QtWidgets.QSpinBox()
        self.frag_spin.setRange(1, 16)
        self.frag_spin.setValue(4)
        adv_row.addWidget(self.frag_spin)
        adv_row.addStretch(1)
        card_lay.addLayout(adv_row)

        # Checkbox sugestia A
        self.import_cb = QtWidgets.QCheckBox("Dodaj pobrane pliki do biblioteki Lumbago po zakończeniu")
        self.import_cb.setChecked(True)
        card_lay.addWidget(self.import_cb)

        # Sugestia D: named/last profiles
        profile_row = QtWidgets.QHBoxLayout()
        self.profile_name_edit = QtWidgets.QLineEdit()
        self.profile_name_edit.setPlaceholderText("nazwa profilu (opcjonalnie)")
        self.save_profile_btn = QtWidgets.QPushButton("Zapisz jako ostatni")
        self.save_profile_btn.clicked.connect(self._save_last_profile)
        self.load_profile_btn = QtWidgets.QPushButton("Wczytaj ostatni")
        self.load_profile_btn.clicked.connect(self._load_last_profile)
        self.list_profiles_btn = QtWidgets.QPushButton("Pokaż profile (D)")
        self.list_profiles_btn.clicked.connect(self._list_named_profiles)
        profile_row.addWidget(self.profile_name_edit)
        profile_row.addWidget(self.save_profile_btn)
        profile_row.addWidget(self.load_profile_btn)
        profile_row.addWidget(self.list_profiles_btn)
        card_lay.addLayout(profile_row)

        # Progress overall
        card_lay.addWidget(QtWidgets.QLabel("Postęp playlisty:"))
        self.overall_bar = QtWidgets.QProgressBar()
        self.overall_bar.setRange(0, 100)
        card_lay.addWidget(self.overall_bar)
        self.overall_label = QtWidgets.QLabel("0 / 0")
        card_lay.addWidget(self.overall_label)

        # Per file
        card_lay.addWidget(QtWidgets.QLabel("Bieżący plik:"))
        self.file_bar = QtWidgets.QProgressBar()
        self.file_bar.setRange(0, 100)
        card_lay.addWidget(self.file_bar)
        self.file_label = QtWidgets.QLabel("—")
        card_lay.addWidget(self.file_label)

        # Log
        card_lay.addWidget(QtWidgets.QLabel("Log:"))
        self.log_edit = QtWidgets.QPlainTextEdit()
        self.log_edit.setReadOnly(True)
        self.log_edit.setMinimumHeight(160)
        card_lay.addWidget(self.log_edit, 1)

        # Sugestia F: historia
        self.history_btn = QtWidgets.QPushButton("Pokaż historię pobrań (sugestia F)")
        self.history_btn.clicked.connect(self._show_history)
        self.resume_btn = QtWidgets.QPushButton("Wznów ostatnie (F stub)")
        self.resume_btn.clicked.connect(self._resume_last)
        card_lay.addWidget(self.history_btn)
        card_lay.addWidget(self.resume_btn)

        # Buttons
        btn_row = QtWidgets.QHBoxLayout()
        self.start_btn = QtWidgets.QPushButton("START")
        self.start_btn.setStyleSheet("font-weight: bold; padding: 6px 18px;")
        self.start_btn.clicked.connect(self._start)
        self.cancel_btn = QtWidgets.QPushButton("ANULUJ")
        self.cancel_btn.clicked.connect(self._cancel)
        self.cancel_btn.setEnabled(False)
        self.close_btn = QtWidgets.QPushButton("Zamknij")
        self.close_btn.clicked.connect(self.accept)
        btn_row.addWidget(self.start_btn)
        btn_row.addWidget(self.cancel_btn)
        btn_row.addStretch(1)
        btn_row.addWidget(self.close_btn)
        card_lay.addLayout(btn_row)

        # Warning / status line
        self.status_line = QtWidgets.QLabel("")
        self.status_line.setWordWrap(True)
        card_lay.addWidget(self.status_line)

        lay.addStretch(0)

    def _update_quality_label(self) -> None:
        fmt = self.fmt_combo.currentText()
        prof = self.profile_combo.currentText()
        self.quality_label.setText(get_quality_label(prof, fmt))

    def _check_tools(self) -> None:
        msgs = []
        if not _has_ffmpeg():
            msgs.append("⚠ ffmpeg nie w PATH — na czystym Windows: winget install ffmpeg lub https://www.gyan.dev/ffmpeg/builds/ (dodaj do PATH). Wymagane dla konwersji WAV/MP3 wysokiej jakości.")
        if not _has_ytdlp():
            msgs.append("⚠ yt-dlp nie zaimportowany — pip install yt-dlp (lub w venv portable). Wymagane dla pobierania z YT/SC.")
        if msgs:
            self.status_line.setText("  |  ".join(msgs))
            self.status_line.setStyleSheet("color: #ffcc66;")
        else:
            self.status_line.setText("Narzędzia gotowe (yt-dlp + ffmpeg). Priorytet: najwyższa słyszalna jakość (bestaudio + profile MAX).")
            self.status_line.setStyleSheet("color: #88ffaa;")

    def _choose_dir(self) -> None:
        d = QtWidgets.QFileDialog.getExistingDirectory(self, "Wybierz folder docelowy", self.dir_edit.text() or str(Path.home() / "Music"))
        if d:
            self.dir_edit.setText(d)

    def _search_yt(self) -> None:
        """Sugestia B: wyszukiwarka YT używająca ytsearch: prefix."""
        q = self.search_edit.text().strip()
        if not q:
            return
        search_url = f"ytsearch:{q}"
        self.url_edit.setText(search_url)
        self._append_log(f"Ustawiono wyszukiwanie: {search_url} (pierwszy wynik zostanie pobrany jako audio)")
        self._check_tools()

    def _save_last_profile(self) -> None:
        """Sugestia D: zapisz bieżące jako nazwany profil (multiple via prefix, full support for named by name).
        Mirrors LAST for 'last' case. Per 'dalej' enhancements + FINAL POLISH.
        Per SZPIEG research + consolidated raw + detailed prompt 2026-06-27 + CHECKLIST_Downloader_AI_Panel.md + PLAN + 'dalej' (D multiple named) ... must document identical.
        """
        name = self.profile_name_edit.text().strip() or "last"
        upper = name.upper()
        vals = {
            f"DOWNLOADER_PROFILE_{upper}_FORMAT": self.fmt_combo.currentText(),
            f"DOWNLOADER_PROFILE_{upper}_QUALITY": self.profile_combo.currentText(),
            f"DOWNLOADER_PROFILE_{upper}_THROTTLE": str(self.throttle_spin.value()),
            f"DOWNLOADER_PROFILE_{upper}_FRAGMENTS": str(self.frag_spin.value()),
        }
        if name.lower() == "last":
            vals.update({
                "DOWNLOADER_LAST_FORMAT": self.fmt_combo.currentText(),
                "DOWNLOADER_LAST_QUALITY": self.profile_combo.currentText(),
                "DOWNLOADER_LAST_THROTTLE": str(self.throttle_spin.value()),
                "DOWNLOADER_LAST_FRAGMENTS": str(self.frag_spin.value()),
            })
        save_settings(vals)
        self._append_log(f"Profil '{name}' zapisany.")

    def _load_last_profile(self) -> None:
        """Sugestia D: wczytaj nazwany lub last profil (supports multiple named by name via direct json).
        Per 'dalej' enhancements to D.
        Per SZPIEG research + consolidated raw + detailed prompt 2026-06-27 + CHECKLIST_Downloader_AI_Panel.md + PLAN + 'dalej' (D multiple named) ... must document identical.
        """
        # Read directly from json (support arbitrary named profiles saved as DOWNLOADER_PROFILE_*) + fallback last/defaults
        file_path = self.settings.settings_file if hasattr(self.settings, 'settings_file') else None
        payload = {}
        if file_path and file_path.exists():
            try:
                payload = json.loads(file_path.read_text(encoding="utf-8"))
            except Exception:
                payload = {}
        name = self.profile_name_edit.text().strip().upper() or "LAST"
        prof_key = f"DOWNLOADER_PROFILE_{name}_"
        last_key = "DOWNLOADER_LAST_"
        fmt = payload.get(prof_key + "FORMAT") or payload.get(last_key + "FORMAT") or getattr(self.settings, "downloader_default_format", "mp3")
        qual = payload.get(prof_key + "QUALITY") or payload.get(last_key + "QUALITY") or getattr(self.settings, "downloader_default_quality", "BALANCE")
        thr = payload.get(prof_key + "THROTTLE") or payload.get(last_key + "THROTTLE") or getattr(self.settings, "downloader_throttle_seconds", 1.5)
        fr = payload.get(prof_key + "FRAGMENTS") or payload.get(last_key + "FRAGMENTS") or getattr(self.settings, "downloader_max_fragments", 4)
        self.fmt_combo.setCurrentText(normalize_format(fmt))
        self.profile_combo.setCurrentText(normalize_profile(qual))
        try:
            self.throttle_spin.setValue(float(thr))
            self.frag_spin.setValue(int(fr))
        except Exception:
            pass
        self._append_log(f"Profil '{name}' wczytany.")

    def _list_named_profiles(self) -> None:
        """D: list known profiles from settings (scan for PROFILE_ keys)."""
        try:
            settings_path = self.settings.settings_file
            if settings_path.exists():
                data = json.loads(settings_path.read_text(encoding="utf-8"))
                profiles = set()
                for k in data:
                    if k.startswith("DOWNLOADER_PROFILE_") and k.endswith("_FORMAT"):
                        name = k.replace("DOWNLOADER_PROFILE_", "").replace("_FORMAT", "").lower()
                        profiles.add(name)
                if "LAST" in [k for k in data if "LAST_FORMAT" in k]:
                    profiles.add("last")
                self._append_log("Dostępne profile: " + ", ".join(sorted(profiles)) if profiles else "Brak zapisanych profili (użyj Zapisz).")
            else:
                self._append_log("Brak pliku settings.")
        except Exception as e:
            self._append_log(f"Błąd listowania profili: {e}")

    def _show_history(self) -> None:
        """Sugestia F: richer historia z checkpoint files + details (count, mtime, ids sample) per 'dalej' enhancements.
        Per SZPIEG research + consolidated raw + detailed prompt 2026-06-27 + CHECKLIST_Downloader_AI_Panel.md + PLAN + 'dalej' (F richer history) ... must document identical.
        """
        out_dir = Path(self.dir_edit.text().strip() or ".")
        cps = sorted(out_dir.glob(".lumbago_dl_checkpoint_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:5]
        if not cps:
            self._append_log("Brak historii pobrań w folderze.")
            return
        self._append_log("Ostatnie checkpointy (z details):")
        for cp in cps:
            try:
                data = json.loads(cp.read_text())
                ids = len(data.get("downloaded_ids", []))
                mtime = cp.stat().st_mtime
                sample = (data.get("downloaded_ids", []) or [])[:2]
                self._append_log(f"  {cp.name} (mtime {mtime:.0f}): {ids} pobranych, sample: {sample}")
            except:
                self._append_log(f"  {cp.name}")

    def _resume_last(self) -> None:
        """
        Wznów ostatnie pobieranie z checkpointu (JSON).
        Ulepszone: szczegółowe logi + heuristic sugestia URL + przygotowanie do wznowienia workera.
        Per NOWA_LISTA item 9/26 (UI polish + real wiring) + SZPIEG/Plan Faza4.
        W pełnej wersji: wczytuje downloaded_ids do worker i pomija je przy starcie.
        """
        out_dir = Path(self.dir_edit.text().strip() or ".")
        cps = sorted(out_dir.glob(".lumbago_dl_checkpoint_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if cps:
            cp = cps[0]
            self._append_log(f"Wznawiam z {cp.name}")
            try:
                data = json.loads(cp.read_text())
                downloaded = data.get("downloaded_ids", []) or []
                total = data.get("total", "?")
                url = data.get("url", "")
                self._append_log(f"  Checkpoint: {len(downloaded)} / {total} pobranych.")
                if url:
                    self._append_log(f"  Oryginalny URL: {url}")
                    # heuristic prefill jeśli pasuje
                    if not self.url_edit.text().strip():
                        self.url_edit.setText(url)
                if 'playlist' in cp.name.lower() or (isinstance(url, str) and 'playlist' in url.lower()):
                    self._append_log("  Wskazówka: dla playlisty wklej URL aby kontynuować z pominiętymi ID.")
                # TODO dalsze: przekazać do DownloadWorker via checkpoint path (Faza4 edge)
            except Exception as e:
                self._append_log(f"  Błąd odczytu checkpoint: {e}")
        else:
            self._append_log("Brak checkpoint do wznowienia w wybranym katalogu.")

    def _load_prefs(self) -> None:
        s = self.settings
        self.fmt_combo.setCurrentText(normalize_format(getattr(s, "downloader_default_format", "mp3")))
        self.profile_combo.setCurrentText(normalize_profile(getattr(s, "downloader_default_quality", "BALANCE")))
        self.throttle_spin.setValue(float(getattr(s, "downloader_throttle_seconds", 1.5)))
        self.frag_spin.setValue(int(getattr(s, "downloader_max_fragments", 4)))
        if getattr(s, "downloader_output_dir", None):
            self.dir_edit.setText(s.downloader_output_dir)
        else:
            self.dir_edit.setText(str(Path.home() / "Music" / "LumbagoDownloads"))

    def set_prefill(self, url: str, fmt: str = None, quality: str = None, auto_start: bool = False) -> None:
        """Prefill from AI or other (for E integration and suggestions).
        If auto_start, trigger after (with safety est in _start). Enhancements to E: auto_start in prefill + trigger for pobierz.
        Per SZPIEG research + consolidated raw + detailed prompt 2026-06-27 + CHECKLIST_Downloader_AI_Panel.md + PLAN + 'dalej' (E auto_start) ... must document identical.
        """
        if url:
            self.url_edit.setText(url)
        if fmt:
            self.fmt_combo.setCurrentText(normalize_format(fmt))
        if quality:
            self.profile_combo.setCurrentText(normalize_profile(quality))
        self._append_log("Prefilled from AI command.")
        if auto_start:
            self._append_log("Auto-start from AI pobierz - performing explicit safety est first (per E enhancement + 'dalej do konca').")
            try:
                # quick pre-est for safety before auto
                ydl_opts = {"quiet": True, "extract_flat": "in_playlist", "playlist_items": "1-5"}
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(self.url_edit.text().strip(), download=False)
                    entries = list(playlist_manager.iter_playlist_entries(info or {}))[:5]
                    total = len(list(playlist_manager.iter_playlist_entries(info or {}))) if info and info.get("entries") else 1
                    est = playlist_manager.estimate_playlist_size(entries, total)
                    if est.get("warning"):
                        self._append_log("Large playlist / size detected by pre-est - disabling auto-start for safety. User will be prompted in _start if proceeds.")
                        auto_start = False
            except Exception:
                pass
            if auto_start:
                self._append_log("Safety est passed - auto-starting worker.")
                self._start()

    def _save_prefs(self) -> None:
        vals = {
            "DOWNLOADER_DEFAULT_FORMAT": self.fmt_combo.currentText(),
            "DOWNLOADER_DEFAULT_QUALITY": self.profile_combo.currentText(),
            "DOWNLOADER_THROTTLE_SECONDS": str(self.throttle_spin.value()),
            "DOWNLOADER_MAX_FRAGMENTS": str(self.frag_spin.value()),
            "DOWNLOADER_OUTPUT_DIR": self.dir_edit.text().strip(),
        }
        save_settings(vals)

    def _append_log(self, text: str) -> None:
        self.log_edit.appendPlainText(text)
        # item 7 polish: limit log lines for very long runs (large playlists)
        doc = self.log_edit.document()
        if doc.blockCount() > 200:
            cursor = self.log_edit.textCursor()
            cursor.movePosition(cursor.Start)
            cursor.movePosition(cursor.Down, cursor.KeepAnchor, 50)
            cursor.removeSelectedText()
        self.log_edit.verticalScrollBar().setValue(self.log_edit.verticalScrollBar().maximum())

    def _update_overall(self, cur: int, tot: int, title: str) -> None:
        self.overall_label.setText(f"{cur} / {tot} — {title[:60]}")
        if tot > 0:
            self.overall_bar.setValue(int(cur / tot * 100))

    def _update_file(self, pct: int, name: str) -> None:
        self.file_bar.setValue(pct)
        self.file_label.setText(f"{name} — {pct}%")

    def _start(self) -> None:
        url = self.url_edit.text().strip()
        if not url:
            QtWidgets.QMessageBox.warning(self, "Brak URL", "Wklej link do filmu lub playlisty.")
            return

        out_dir = Path(self.dir_edit.text().strip())
        if not out_dir.exists():
            try:
                out_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Błąd folderu", str(e))
                return

        if not _has_ffmpeg():
            QtWidgets.QMessageBox.warning(self, "ffmpeg", "ffmpeg nie znaleziony. Pobierz z videolan.org lub gyan.dev i dodaj do PATH.")
            # kontynuujemy — worker może działać dla części

        # Preflight est for large playlists (Plan list P0 #2 + prompt C + SZPIEG)
        try:
            ydl_opts = {"quiet": True, "extract_flat": "in_playlist", "playlist_items": "1-5"}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                entries = list(playlist_manager.iter_playlist_entries(info or {}))[:5]
                total = len(list(playlist_manager.iter_playlist_entries(info or {}))) if info and info.get("entries") else 1
                est = playlist_manager.estimate_playlist_size(entries, total)
                self._append_log(f"Estymacja: ~{est.get('approx_duration_sec',0)//60} min, ~{est.get('approx_size_mb',0)} MB (sample {est.get('sample_used',0)})")
                if est.get("warning"):
                    self._append_log(est["warning"])
                    reply = QtWidgets.QMessageBox.question(
                        self, "Duża playlista / duży rozmiar",
                        est["warning"] + "\n\nKontynuować pobieranie?",
                        QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
                    )
                    if reply == QtWidgets.QMessageBox.No:
                        self._append_log("Anulowano przez użytkownika po estymacji.")
                        return
                # Dodatkowy check dysku dla C/P0#2
                try:
                    free_mb = shutil.disk_usage(out_dir).free // (1024*1024)
                    needed = est.get('approx_size_mb', 0)
                    if free_mb < needed * 1.1:
                        QtWidgets.QMessageBox.warning(self, "Za mało miejsca na dysku", f"Potrzebne ~{needed} MB, wolne {free_mb} MB. Anuluj lub zwolnij miejsce.")
                        self._append_log("Za mało miejsca — anulowano.")
                        return
                except Exception:
                    pass
        except Exception as e:
            self._append_log(f"Estymacja pominięta: {e}")

        self._save_prefs()

        # Bridge + worker
        self._bridge = ProgressBridge(self)
        self._bridge.playlist_progress.connect(self._update_overall)
        self._bridge.file_progress.connect(self._update_file)
        self._bridge.log_message.connect(self._append_log)
        self._bridge.error.connect(self._append_log)
        self._bridge.finished.connect(self._on_finished)

        self._worker = DownloadWorker(
            url=url,
            output_dir=out_dir,
            out_format=self.fmt_combo.currentText(),
            quality_profile=self.profile_combo.currentText(),
            throttle_seconds=self.throttle_spin.value(),
            max_fragments=self.frag_spin.value(),
            bridge=self._bridge,
            add_to_library_after=self.import_cb.isChecked(),
        )

        self._append_log("Uruchamiam worker...")
        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.overall_bar.setValue(0)
        self.file_bar.setValue(0)
        self.log_edit.clear()

        self._worker.start()

    def _cancel(self) -> None:
        if self._worker:
            self._worker.stop()
            self._append_log("Anulowanie...")

    def _on_finished(self, ok: bool, msg: str) -> None:
        self._append_log(f"[KONIEC] {msg}")
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        if ok and self.import_cb.isChecked():
            self._append_log("Dodaj do biblioteki po pobraniu — trigger skan.")
            if hasattr(self.parent(), "_scan_folder_for_library"):
                self.parent()._scan_folder_for_library(self.dir_edit.text().strip())

        if self._worker:
            self._worker.quit()
            self._worker.wait(2000)
            self._worker = None

    def closeEvent(self, event: QtCore.QEvent) -> None:
        if self._worker and self._worker.isRunning():
            self._worker.stop()
            self._worker.wait(1500)
        super().closeEvent(event)
