from __future__ import annotations

"""
ChatWidget — zwijany panel czatu AI (pomocnik komendami).

Wspiera WSZYSTKIE aktywne providery (gemini, openai, grok, deepseek)
tak jak Autotager — automatyczny wybór lub ręczny.

- Provider selector (Auto / konkretny)
- Historia
- Dispatch do registry + sandbox
- "Myślę..." + chunk streaming support
- Ambiguity: system prosi o doprecyzowanie (per prompt)

Per SZPIEG research + ... 2026-06-27 + "kontynuuj" ... must document identical.
"""

from PyQt6 import QtCore, QtWidgets

from ai_panel.gemini_client import AIChatClient
from ai_panel.command_dispatcher import CommandDispatcher
from ai_panel.command_registry import list_commands
from ai_panel.sandbox_runner import run_in_sandbox


class ChatWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(340)
        self.dispatcher = CommandDispatcher()
        self._history: list[str] = []
        self._client: AIChatClient | None = None
        self._build_ui()
        self._refresh_client()

    def _build_ui(self):
        v = QtWidgets.QVBoxLayout(self)
        v.setContentsMargins(8, 8, 8, 8)
        v.setSpacing(6)

        # Provider row
        prov_row = QtWidgets.QHBoxLayout()
        prov_row.addWidget(QtWidgets.QLabel("Provider:"))
        self.provider_combo = QtWidgets.QComboBox()
        self.provider_combo.addItem("Auto (najszybszy działający)")
        self.provider_combo.currentTextChanged.connect(self._on_provider_changed)
        prov_row.addWidget(self.provider_combo, 1)
        self.refresh_btn = QtWidgets.QPushButton("↻")
        self.refresh_btn.setFixedWidth(28)
        self.refresh_btn.clicked.connect(self._refresh_client)
        prov_row.addWidget(self.refresh_btn)
        v.addLayout(prov_row)

        self.toggle_btn = QtWidgets.QPushButton("🤖 AI Pomocnik (kliknij aby rozwinąć)")
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.toggled.connect(self._toggle)
        v.addWidget(self.toggle_btn)

        self.content = QtWidgets.QWidget()
        cv = QtWidgets.QVBoxLayout(self.content)
        cv.setContentsMargins(0, 0, 0, 0)

        self.history = QtWidgets.QTextBrowser()
        self.history.setOpenExternalLinks(False)
        cv.addWidget(self.history, 1)

        row = QtWidgets.QHBoxLayout()
        self.input = QtWidgets.QLineEdit()
        self.input.setPlaceholderText("Np: pobierz https://... jako MP3 | duplikaty | pomoc")
        self.input.returnPressed.connect(self._send)
        self.send_btn = QtWidgets.QPushButton("Wyślij")
        self.send_btn.clicked.connect(self._send)
        row.addWidget(self.input, 1)
        row.addWidget(self.send_btn)
        cv.addLayout(row)

        self.status = QtWidgets.QLabel("")
        cv.addWidget(self.status)

        v.addWidget(self.content)
        self.content.setVisible(False)

        # Załaduj help
        self._append("System", "Witaj! Dostępne komendy: " + ", ".join(c.name for c in list_commands()))
        self._append("System", "Czat używa dowolnego aktywnego API (jak Autotager). Wybierz provider powyżej.")

    def _toggle(self, checked: bool):
        self.content.setVisible(checked)
        self.toggle_btn.setText("🤖 AI Pomocnik (ukryj)" if checked else "🤖 AI Pomocnik (kliknij aby rozwinąć)")

    def _refresh_client(self):
        explicit = None
        current = self.provider_combo.currentText()
        if current and not current.startswith("Auto"):
            explicit = current.lower()

        self._client = AIChatClient(explicit_provider=explicit)

        # Odśwież listę providerów w combo
        self.provider_combo.blockSignals(True)
        current_text = self.provider_combo.currentText()
        self.provider_combo.clear()
        self.provider_combo.addItem("Auto (najszybszy działający)")
        for p in self._client.available_providers:
            self.provider_combo.addItem(p.capitalize())
        # Przywróć wybór jeśli nadal dostępny
        idx = self.provider_combo.findText(current_text)
        if idx >= 0:
            self.provider_combo.setCurrentIndex(idx)
        self.provider_combo.blockSignals(False)

        if self._client.provider:
            self.status.setText(f"Aktywny: {self._client.provider} / {self._client.model}")
        else:
            self.status.setText("Brak skonfigurowanego API (Ustawienia → Cloud AI)")

    def _on_provider_changed(self, text: str):
        self._refresh_client()

    def _append(self, who: str, text: str):
        self._history.append(f"[{who}] {text}")
        self.history.append(f"<b>{who}:</b> {text}")

    def _send(self):
        if not self._client:
            self._append("System", "Brak klienta AI.")
            return
        txt = self.input.text().strip()
        if not txt:
            return
        self.input.clear()
        self._append("Ty", txt)
        self.status.setText("Myślę...")  # indicator for streaming / long AI response (per E polish + "kontynuuj")

        QtCore.QTimer.singleShot(30, lambda: self._process(txt))

    def _process(self, user_msg: str):
        system = (
            "Jesteś pomocnikiem Lumbago Music AI (desktop). "
            "Użytkownik wydaje komendy po polsku. Odpowiadaj TYLKO poprawnym JSON: "
            "{\"command\": \"nazwa\", \"params\": {...}}. "
            "Dostępne komendy: pobierz, duplikaty, otaguj, pomoc. "
            "Dla 'pobierz' podaj url i fmt (mp3/wav/m4a). "
            "Jeśli niepewny — poproś o doprecyzowanie w zwykłym tekście."
        )

        reply = self._client.chat(system, user_msg)
        if isinstance(reply, str):
            self._append("AI", reply[:700])
            res = self.dispatcher.parse_and_dispatch(reply)
            self._handle_result(res)
        else:
            full = ""
            for chunk in reply:
                full += chunk
            self._append("AI", full[:700])
            res = self.dispatcher.parse_and_dispatch(full)
            self._handle_result(res)

        self.status.setText("")

    def _handle_result(self, res: dict):
        if res.get("ok"):
            self._append("System", f"OK: {res.get('command')} — {res.get('effect', '')}")
            if res.get("command") == "pomoc":
                for name, desc, eff in res.get("result", {}).get("commands", []):
                    self._append("Komenda", f"{name}: {desc} | {eff}")
            # AI → Downloader full E wiring (per Plan + "dalej" enhancements): prefill + auto_start=True for "pobierz"
            result = res.get("result", {})
            if isinstance(result, dict) and result.get("action") == "open_downloader":
                url = result.get("url", "")
                fmt = result.get("fmt", "")
                if hasattr(self.parent(), "_open_downloader"):
                    self.parent()._open_downloader(url, fmt, auto_start=True)
                    self._append("System", "Otwarto i uruchomiono Downloader z AI (auto-start z safety).")
        else:
            self._append("System", f"Błąd: {res.get('error')}")
