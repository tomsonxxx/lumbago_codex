"""
ui/dj/booth_svg_icons.py

SVG ikony transportu booth (play/pause/stop/cue) ze skalą DPI.
Fallback na tekst Unicode gdy PyQt6.QtSvg niedostępne.
Per SZPIEG Build Spec 2026-06-15 iteracja 4.
"""

from __future__ import annotations

from PyQt6 import QtCore, QtGui, QtWidgets

from ui.dj.styles import BoothMetrics, booth_transport_label, booth_transport_text

_HAS_QT_SVG = False
try:
    from PyQt6.QtSvg import QSvgRenderer

    _HAS_QT_SVG = True
except ImportError:
    QSvgRenderer = None  # type: ignore[misc, assignment]

_ICON_COLOR = "#f0f4f8"

_SVG_TEMPLATES: dict[str, str] = {
    "play": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
        '<polygon points="8,5 19,12 8,19" fill="{color}"/></svg>'
    ),
    "pause": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
        '<rect x="6" y="5" width="4" height="14" fill="{color}"/>'
        '<rect x="14" y="5" width="4" height="14" fill="{color}"/></svg>'
    ),
    "stop": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
        '<rect x="6" y="6" width="12" height="12" rx="1.5" fill="{color}"/></svg>'
    ),
    "cue": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
        '<text x="12" y="16" text-anchor="middle" font-family="Segoe UI,Arial,sans-serif" '
        'font-weight="900" font-size="11" fill="{color}">CUE</text></svg>'
    ),
}

_icon_cache: dict[tuple[str, bool, int], QtGui.QIcon] = {}


def svg_available() -> bool:
    return _HAS_QT_SVG


def _svg_key(role: str, *, playing: bool) -> str:
    if role == "play":
        return "pause" if playing else "play"
    return role


def _render_svg_icon(svg_xml: str, size_px: int) -> QtGui.QIcon | None:
    if not _HAS_QT_SVG or QSvgRenderer is None:
        return None
    renderer = QSvgRenderer(QtCore.QByteArray(svg_xml.encode("utf-8")))
    if not renderer.isValid():
        return None
    pixmap = QtGui.QPixmap(size_px, size_px)
    pixmap.fill(QtCore.Qt.GlobalColor.transparent)
    painter = QtGui.QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QtGui.QIcon(pixmap)


def booth_transport_icon(
    metrics: BoothMetrics,
    role: str,
    *,
    playing: bool = False,
) -> QtGui.QIcon | None:
    """Skalowana ikona transportu; None gdy SVG niedostępne."""
    if not _HAS_QT_SVG:
        return None
    key = _svg_key(role, playing=playing)
    size_px = max(12, metrics.px(18))
    cache_key = (key, playing, size_px)
    cached = _icon_cache.get(cache_key)
    if cached is not None:
        return cached
    template = _SVG_TEMPLATES.get(key)
    if template is None:
        return None
    icon = _render_svg_icon(template.format(color=_ICON_COLOR), size_px)
    if icon is not None:
        _icon_cache[cache_key] = icon
    return icon


def apply_transport_button_content(
    metrics: BoothMetrics,
    cue_btn: QtWidgets.QPushButton,
    play_btn: QtWidgets.QPushButton,
    stop_btn: QtWidgets.QPushButton,
    *,
    playing: bool = False,
    compact: bool = False,
) -> None:
    """
    Ustaw ikony SVG + etykiety na przyciskach transportu.
    Compact: tylko ikona. Normal: ikona + tekst bez duplikatu Unicode.
    """
    icon_size = QtCore.QSize(metrics.px(18), metrics.px(18))
    pairs: list[tuple[QtWidgets.QPushButton, str, bool]] = [
        (cue_btn, "cue", False),
        (play_btn, "play", playing),
        (stop_btn, "stop", False),
    ]
    for btn, role, is_playing in pairs:
        icon = booth_transport_icon(metrics, role, playing=is_playing)
        if icon is not None:
            btn.setIcon(icon)
            btn.setIconSize(icon_size)
            btn.setText("" if compact else booth_transport_label(role, playing=is_playing))
        else:
            btn.setIcon(QtGui.QIcon())
            btn.setText(
                booth_transport_text(role, playing=is_playing, compact=compact)
            )
    _apply_transport_tooltips(cue_btn, play_btn, stop_btn)


def _apply_transport_tooltips(
    cue_btn: QtWidgets.QPushButton,
    play_btn: QtWidgets.QPushButton,
    stop_btn: QtWidgets.QPushButton,
) -> None:
    cue_btn.setToolTip(
        "CUE — trzymaj: podgląd od CUE. Zwolnij: stop na CUE. Shift+trzymaj: ustaw CUE."
    )
    play_btn.setToolTip("Play / Pauza — PPM: odtwórz od CUE, początku lub bieżącej pozycji")
    stop_btn.setToolTip("Stop — PPM: powrót do CUE, do 0 lub tylko zatrzymaj")