from __future__ import annotations

"""
CommandDispatcher — Gemini JSON → wywołanie zarejestrowanej komendy.

Oczekiwany output od LLM (przykład):
{"command": "pobierz", "params": {"url": "...", "fmt": "mp3"}}

Bezpieczna walidacja + fallback na ambiguity.
"""

import json
import re
from ai_panel.command_registry import get_command, list_commands


class CommandDispatcher:
    def __init__(self, registry_get=get_command):
        self._get = registry_get

    def parse_and_dispatch(self, llm_text: str) -> dict:
        """Parsuje JSON z odpowiedzi LLM i dispatchuje."""
        try:
            # Wyodrębnij pierwszy {...} jeśli LLM dodał markdown
            m = re.search(r"\{.*\}", llm_text, re.DOTALL)
            raw = m.group(0) if m else llm_text
            data = json.loads(raw)
            cmd_name = (data.get("command") or "").strip().lower()
            params = data.get("params") or data.get("arguments") or {}
            cmd = self._get(cmd_name)
            if not cmd:
                return {"ok": False, "error": "Nieznana komenda. Użyj 'pomoc'.", "suggestion": "help"}
            result = cmd.handler(**params)
            return {"ok": True, "command": cmd_name, "result": result, "effect": cmd.effect}
        except Exception as e:
            return {"ok": False, "error": f"Nie udało się zrozumieć komendy: {e}. Podaj więcej szczegółów.", "raw": llm_text[:300]}
