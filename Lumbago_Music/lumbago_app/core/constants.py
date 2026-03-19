"""
Lumbago Music AI — Stałe aplikacji
=====================================
Formaty audio, koło Camelota, poziomy energii, koszty AI.
"""

from typing import Final

# ------------------------------------------------------------------ #
# Obsługiwane formaty audio
# ------------------------------------------------------------------ #
SUPPORTED_FORMATS: Final[frozenset[str]] = frozenset({
    ".mp3", ".flac", ".wav", ".aiff", ".aif", ".ogg",
    ".m4a", ".aac", ".opus", ".wma", ".mp4", ".alac",
})

LOSSLESS_FORMATS: Final[frozenset[str]] = frozenset({
    ".flac", ".wav", ".aiff", ".aif", ".alac",
})

# ------------------------------------------------------------------ #
# Koło Camelota — pełna tablica 24 tonacji
# Format: klucz muzyczny -> (numer Camelot, litera A/B)
# A = molowa, B = durowa
# ------------------------------------------------------------------ #
CAMELOT_WHEEL: Final[dict[str, str]] = {
    # Dur (B)
    "C major":   "8B",
    "Db major":  "3B",
    "D major":   "10B",
    "Eb major":  "5B",
    "E major":   "12B",
    "F major":   "7B",
    "F# major":  "2B",
    "Gb major":  "2B",
    "G major":   "9B",
    "Ab major":  "4B",
    "A major":   "11B",
    "Bb major":  "6B",
    "B major":   "1B",
    # Moll (A)
    "A minor":   "8A",
    "Bb minor":  "3A",
    "B minor":   "10A",
    "C minor":   "5A",
    "C# minor":  "12A",
    "D minor":   "7A",
    "Eb minor":  "2A",
    "D# minor":  "2A",
    "E minor":   "9A",
    "F minor":   "4A",
    "F# minor":  "11A",
    "G minor":   "6A",
    "G# minor":  "1A",
    "Ab minor":  "1A",
}

# Odwrotna mapa: Camelot -> klucz muzyczny (pierwsze dopasowanie)
CAMELOT_TO_KEY: Final[dict[str, str]] = {
    v: k for k, v in reversed(list(CAMELOT_WHEEL.items()))
}

# Sąsiedzi harmoniczni w kole Camelota (kompatybilne przejścia)
CAMELOT_COMPATIBLE: Final[dict[str, list[str]]] = {
    "1A":  ["1A", "1B", "12A", "2A"],
    "2A":  ["2A", "2B", "1A", "3A"],
    "3A":  ["3A", "3B", "2A", "4A"],
    "4A":  ["4A", "4B", "3A", "5A"],
    "5A":  ["5A", "5B", "4A", "6A"],
    "6A":  ["6A", "6B", "5A", "7A"],
    "7A":  ["7A", "7B", "6A", "8A"],
    "8A":  ["8A", "8B", "7A", "9A"],
    "9A":  ["9A", "9B", "8A", "10A"],
    "10A": ["10A", "10B", "9A", "11A"],
    "11A": ["11A", "11B", "10A", "12A"],
    "12A": ["12A", "12B", "11A", "1A"],
    "1B":  ["1B", "1A", "12B", "2B"],
    "2B":  ["2B", "2A", "1B", "3B"],
    "3B":  ["3B", "3A", "2B", "4B"],
    "4B":  ["4B", "4A", "3B", "5B"],
    "5B":  ["5B", "5A", "4B", "6B"],
    "6B":  ["6B", "6A", "5B", "7B"],
    "7B":  ["7B", "7A", "6B", "8B"],
    "8B":  ["8B", "8A", "7B", "9B"],
    "9B":  ["9B", "9A", "8B", "10B"],
    "10B": ["10B", "10A", "9B", "11B"],
    "11B": ["11B", "11A", "10B", "12B"],
    "12B": ["12B", "12A", "11B", "1B"],
}

# ------------------------------------------------------------------ #
# Poziomy energii DJ (1-10)
# ------------------------------------------------------------------ #
ENERGY_LEVELS: Final[dict[int, str]] = {
    1:  "Ambient / Chill-out",
    2:  "Deep / Mellow",
    3:  "Laid-back / Groovy",
    4:  "Smooth / Mid-tempo",
    5:  "Uplifting / Building",
    6:  "Driving / Energetic",
    7:  "Peak-time / Club",
    8:  "High Energy / Pumping",
    9:  "Hard / Intense",
    10: "Extreme / Rave",
}

# ------------------------------------------------------------------ #
# Koszty AI (USD za 1000 tokenów — wejście/wyjście)
# Używane przez LLM Router do wyboru najtańszego providera
# ------------------------------------------------------------------ #
AI_PROVIDERS_COST: Final[dict[str, dict[str, float]]] = {
    "openai": {
        "model": "gpt-4o-mini",
        "input_per_1k":  0.00015,
        "output_per_1k": 0.00060,
        "priority": 2,
    },
    "deepseek": {
        "model": "deepseek-chat",
        "input_per_1k":  0.00014,
        "output_per_1k": 0.00028,
        "priority": 1,   # najtańszy
    },
    "gemini": {
        "model": "gemini-1.5-flash",
        "input_per_1k":  0.00007,
        "output_per_1k": 0.00021,
        "priority": 0,   # najnajtańszy (bezpłatny tier)
    },
    "anthropic": {
        "model": "claude-3-haiku-20240307",
        "input_per_1k":  0.00025,
        "output_per_1k": 0.00125,
        "priority": 3,
    },
    "grok": {
        "model": "grok-beta",
        "input_per_1k":  0.00500,
        "output_per_1k": 0.01500,
        "priority": 4,   # najdroższy
    },
}

# ------------------------------------------------------------------ #
# Stałe UI
# ------------------------------------------------------------------ #
APP_NAME: Final[str] = "Lumbago Music AI"
APP_VERSION: Final[str] = "1.0.0"
APP_ORG: Final[str] = "LumbagoMusic"

# Kolory tematyczne
COLOR_ACCENT_CYBER: Final[str] = "#00f5ff"
COLOR_BG_CYBER: Final[str] = "#0d0d0f"
COLOR_ACCENT_FLUENT: Final[str] = "#60cdff"
COLOR_BG_FLUENT: Final[str] = "#202020"

# ------------------------------------------------------------------ #
# Stałe analizy audio
# ------------------------------------------------------------------ #
DEFAULT_SAMPLE_RATE: Final[int] = 44100
WAVEFORM_CHUNK_SIZE: Final[int] = 2048
MAX_CUE_POINTS: Final[int] = 8

# Zakresy BPM dla gatunków
BPM_RANGES: Final[dict[str, tuple[int, int]]] = {
    "ambient":    (60, 100),
    "hip_hop":    (75, 115),
    "house":      (120, 130),
    "techno":     (130, 160),
    "dnb":        (160, 180),
    "hardcore":   (150, 200),
}

# ------------------------------------------------------------------ #
# Gatunki muzyczne
# ------------------------------------------------------------------ #
MUSIC_GENRES: Final[list[str]] = [
    "Ambient", "Bass House", "Breakbeat", "Breaks", "Deep House",
    "Drum and Bass", "Dubstep", "Electro", "Funk", "Garage",
    "Hard Techno", "Hardcore", "Hip Hop", "House", "Industrial",
    "Jungle", "Melodic Techno", "Minimal", "Nu-Disco", "Organic House",
    "Progressive House", "Psytrance", "R&B", "Reggaeton", "Techno",
    "Trance", "Trap", "Tribal", "UK Garage", "Other",
]
