"""Testy DuplicateService (bazowe)."""

import pytest


def test_duplicate_service_imports():
    """DuplicateService importuje się bez błędów."""
    from lumbago_app.services.duplicate_service import DuplicateService, DuplicateGroup
    assert DuplicateService is not None
    assert DuplicateGroup is not None


def test_duplicate_group_dataclass():
    """DuplicateGroup jest poprawnym dataclassem."""
    from lumbago_app.services.duplicate_service import DuplicateGroup
    g = DuplicateGroup(method="hash", track_ids=[1, 2], similarity=1.0)
    assert g.method == "hash"
    assert len(g.track_ids) == 2
    assert g.similarity == 1.0
