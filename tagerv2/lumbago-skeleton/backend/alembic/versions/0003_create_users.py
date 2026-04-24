def upgrade():
    import sqlite3
    conn = sqlite3.connect('lumbago.db')
    c = conn.cursor()
    try:
        c.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE, hashed_password TEXT, display_name TEXT, is_active INTEGER, created_at TEXT)')
    except Exception:
        pass
    conn.commit(); conn.close()
def downgrade():
    print('downgrade not implemented')
