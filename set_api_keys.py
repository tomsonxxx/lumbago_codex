"""
Skrypt ustawiający klucze API dla aplikacji Lumbago Music AI.

Zapisuje klucze w trzech miejscach (od najwyższego priorytetu):
  1. %APPDATA%\LumbagoMusicAI\settings.json  (najwyższy priorytet w aplikacji)
  2. .env w katalogu projektu
  3. Windows Registry: HKCU\SOFTWARE\LumbagoMusicAI

UWAGA: Ten plik zawiera tajne klucze – nie dodawaj go do repozytorium git!
"""

import json
import os
import sys
from pathlib import Path

# ── Klucze API ──────────────────────────────────────────────────────────────

KEYS: dict[str, str] = {
    "GROK_API_KEY":       "xai-WPflSMVYp1fX0FrKOLXMQMip2BniESeG0WkmqqRpAcYcPhNnE88MH3QfwJJza38agmHdcuMrrIO4httt",
    "OPENAI_API_KEY":     "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",
    "DEEPSEEK_API_KEY":   "sk-a102187e7d2f44db8c45eb54a635e10a",
    "CLOUD_AI_API_KEY":   "AIzaSyCi-f8N6a-ePrRN5X5K3yWPD0Po_tyQ350",  # Google Gemini
    "GEMINI_API_KEY":     "AIzaSyCi-f8N6a-ePrRN5X5K3yWPD0Po_tyQ350",  # alias
}

# ── Ścieżki ─────────────────────────────────────────────────────────────────

APPDATA = Path(os.getenv("APPDATA") or Path.home() / "AppData" / "Roaming")
SETTINGS_JSON = APPDATA / "LumbagoMusicAI" / "settings.json"
DOTENV_FILE   = Path(__file__).parent / ".env"


# ── 1. settings.json ────────────────────────────────────────────────────────

def save_to_settings_json(keys: dict[str, str]) -> None:
    SETTINGS_JSON.parent.mkdir(parents=True, exist_ok=True)
    existing: dict = {}
    if SETTINGS_JSON.exists():
        try:
            existing = json.loads(SETTINGS_JSON.read_text(encoding="utf-8"))
        except Exception:
            existing = {}
    merged = {**existing, **keys}
    SETTINGS_JSON.write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[OK] settings.json  →  {SETTINGS_JSON}")


# ── 2. .env ─────────────────────────────────────────────────────────────────

def save_to_dotenv(keys: dict[str, str]) -> None:
    lines: list[str] = []
    existing_keys: set[str] = set()

    if DOTENV_FILE.exists():
        for line in DOTENV_FILE.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and "=" in stripped:
                var = stripped.split("=", 1)[0].strip()
                if var in keys:
                    existing_keys.add(var)
                    lines.append(f"{var}={keys[var]}")
                    continue
            lines.append(line)

    for var, val in keys.items():
        if var not in existing_keys:
            lines.append(f"{var}={val}")

    DOTENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[OK] .env           →  {DOTENV_FILE}")


# ── 3. Windows Registry ──────────────────────────────────────────────────────

def save_to_registry(keys: dict[str, str]) -> None:
    if not sys.platform.startswith("win"):
        print("[--] Registry       →  pominięto (nie Windows)")
        return
    try:
        import winreg
        reg_path = r"SOFTWARE\LumbagoMusicAI"
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, reg_path)
        for name, value in keys.items():
            winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)
        winreg.CloseKey(key)
        print(f"[OK] Registry       →  HKCU\\{reg_path}")
    except Exception as e:
        print(f"[!!] Registry       →  błąd: {e}")


# ── main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Ustawianie kluczy API dla Lumbago Music AI...\n")
    save_to_settings_json(KEYS)
    save_to_dotenv(KEYS)
    save_to_registry(KEYS)
    print("\nGotowe! Uruchom aplikację ponownie, aby zmiany zostały wczytane.")
