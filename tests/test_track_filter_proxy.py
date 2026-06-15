from __future__ import annotations

from core.models import Track
from PyQt6 import QtCore

from ui.main_window import ROW_SORT_COLUMN, TrackFilterProxy, _track_sort_key


def test_track_sort_key_numeric_columns():
    t1 = Track(path="a.mp3", bpm=120.0, year="2020")
    t2 = Track(path="b.mp3", bpm=128.0, year="2019")
    assert _track_sort_key(t1, 5) < _track_sort_key(t2, 5)
    assert _track_sort_key(t1, 3) > _track_sort_key(t2, 3)


def test_track_filter_proxy_less_than_sorts_by_title():
    from ui.models import TrackTableModel

    tracks = [
        Track(path="z.mp3", title="Zebra"),
        Track(path="a.mp3", title="Alpha"),
    ]
    model = TrackTableModel(tracks)
    proxy = TrackFilterProxy()
    proxy.setSourceModel(model)
    proxy.sort(0)
    assert proxy.index(0, 0).data() == "Alpha"
    assert "Zebra" in str(proxy.index(1, 0).data())


def test_track_filter_proxy_sorts_by_source_row():
    from ui.models import TrackTableModel

    tracks = [
        Track(path="c.mp3", title="Charlie"),
        Track(path="a.mp3", title="Alpha"),
        Track(path="b.mp3", title="Bravo"),
    ]
    model = TrackTableModel(tracks)
    proxy = TrackFilterProxy()
    proxy.setSourceModel(model)
    proxy.sort(0)
    assert proxy.index(0, 0).data() == "Alpha"

    proxy.sort(ROW_SORT_COLUMN, QtCore.Qt.SortOrder.AscendingOrder)
    assert proxy.is_sorting_by_source_row()
    assert proxy.index(0, 0).data() == "Charlie"
    assert proxy.index(1, 0).data() == "Alpha"
    assert proxy.index(2, 0).data() == "Bravo"

    proxy.sort(ROW_SORT_COLUMN, QtCore.Qt.SortOrder.DescendingOrder)
    assert proxy.index(0, 0).data() == "Bravo"
    assert proxy.index(2, 0).data() == "Charlie"


def test_track_filter_proxy_row_sort_survives_filter_change():
    from ui.models import TrackTableModel

    tracks = [
        Track(path="c.mp3", title="Charlie", genre="House"),
        Track(path="a.mp3", title="Alpha", genre="Techno"),
        Track(path="b.mp3", title="Bravo", genre="House"),
    ]
    model = TrackTableModel(tracks)
    proxy = TrackFilterProxy()
    proxy.setSourceModel(model)
    proxy.sort(ROW_SORT_COLUMN)
    proxy.genre = "house"
    proxy.invalidateFilter()
    assert proxy.is_sorting_by_source_row()
    assert proxy.index(0, 0).data() == "Charlie"
    assert proxy.index(1, 0).data() == "Bravo"