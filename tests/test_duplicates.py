from core.models import Track
from core.services import find_duplicates_by_tags


def test_find_duplicates_by_tags_groups_tracks():
    tracks = [
        Track(path="a.mp3", title="Song", artist="Artist", duration=180),
        Track(path="b.mp3", title="Song", artist="Artist", duration=180),
        Track(path="c.mp3", title="Other", artist="Artist", duration=200),
    ]
    result = find_duplicates_by_tags(tracks)
    assert len(result.groups) == 1
    assert len(result.groups[0].track_ids) == 2
