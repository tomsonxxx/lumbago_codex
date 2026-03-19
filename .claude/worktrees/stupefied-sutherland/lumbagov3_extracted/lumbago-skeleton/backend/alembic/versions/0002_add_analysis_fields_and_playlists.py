# Alembic migration: add analysis fields to tracks and create playlists table (sqlite compatible SQL)
def upgrade():
    import sqlite3
    conn = sqlite3.connect('lumbago.db')
    c = conn.cursor()
    try:
        c.execute('ALTER TABLE tracks ADD COLUMN fingerprint TEXT')
    except Exception:
        pass
    try:
        c.execute('ALTER TABLE tracks ADD COLUMN waveform_path TEXT')
    except Exception:
        pass
    try:
        c.execute('ALTER TABLE tracks ADD COLUMN features JSON')
    except Exception:
        pass
    try:
        c.execute('CREATE TABLE IF NOT EXISTS playlists (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, description TEXT)')
    except Exception:
        pass
    conn.commit()
    conn.close()

def downgrade():
    print('downgrade not supported for sqlite in this script')
