from .db import engine, Base
from .models_sql import Track
from .models_user import User
from .models_playlists import Playlist

def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == '__main__':
    init_db()
    print('Database initialized')
