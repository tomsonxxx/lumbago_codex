from backend.app.duplicate_finder import find_duplicates

def make_track(id, title, artist, duration, file_hash=None, fingerprint=None):
    return {
        'id': id,
        'title': title,
        'artist': artist,
        'duration': duration,
        'file_hash': file_hash,
        'fingerprint': fingerprint
    }

def test_hash_duplication():
    t1 = make_track(1, 'Deep Voyage', 'DJ Tom', 372, file_hash='abc123')
    t2 = make_track(2, 'Deep Voyage', 'DJ Tom', 372, file_hash='abc123')
    groups = find_duplicates([t1,t2])
    assert len(groups) == 1
    assert len(groups[0]['tracks']) == 2
    assert groups[0]['matches'][0]['method'] == 'hash'

def test_tag_similarity_dup():
    t1 = make_track(1, 'Harmonic Shift', 'Bass Agent', 345, fingerprint=None)
    t2 = make_track(2, 'Harmonic Shift (Remastered)', 'Bass Agent', 346, fingerprint=None)
    groups = find_duplicates([t1,t2])
    assert len(groups) == 1
    assert groups[0]['matches'][0]['method'] == 'tag'

def test_fingerprint_similarity():
    t1 = make_track(1, 'Track One', 'Artist', 200, fingerprint='fp_abcdef123456')
    t2 = make_track(2, 'Track One (copy)', 'Artist', 200, fingerprint='fp_abcxyz123456')
    groups = find_duplicates([t1,t2])
    assert len(groups) == 1
    assert groups[0]['matches'][0]['method'] in ('fingerprint','tag')
