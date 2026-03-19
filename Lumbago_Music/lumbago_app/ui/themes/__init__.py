"""Moduł tematów QSS."""
from lumbago_app.ui.themes.cyber_neon import CYBER_NEON_QSS
from lumbago_app.ui.themes.fluent_dark import FLUENT_DARK_QSS

THEMES: dict[str, str] = {
    "cyber_neon": CYBER_NEON_QSS,
    "fluent_dark": FLUENT_DARK_QSS,
}

__all__ = ["THEMES", "CYBER_NEON_QSS", "FLUENT_DARK_QSS"]
