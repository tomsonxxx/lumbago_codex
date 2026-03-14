from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tracks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("path", sa.Text(), nullable=False, unique=True),
        sa.Column("title", sa.Text()),
        sa.Column("artist", sa.Text()),
        sa.Column("album", sa.Text()),
        sa.Column("genre", sa.Text()),
        sa.Column("bpm", sa.Float()),
        sa.Column("key", sa.Text()),
        sa.Column("duration", sa.Integer()),
        sa.Column("file_size", sa.Integer()),
        sa.Column("file_mtime", sa.Float()),
        sa.Column("file_hash", sa.Text()),
        sa.Column("format", sa.Text()),
        sa.Column("bitrate", sa.Integer()),
        sa.Column("sample_rate", sa.Integer()),
        sa.Column("play_count", sa.Integer(), server_default="0"),
        sa.Column("rating", sa.Integer(), server_default="0"),
        sa.Column("energy", sa.Float()),
        sa.Column("mood", sa.Text()),
        sa.Column("fingerprint", sa.Text()),
        sa.Column("waveform_path", sa.Text()),
        sa.Column("artwork_path", sa.Text()),
        sa.Column("date_added", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("date_modified", sa.DateTime()),
    )
    op.create_table(
        "tags",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("track_id", sa.Integer(), sa.ForeignKey("tracks.id"), nullable=False),
        sa.Column("tag", sa.Text(), nullable=False),
        sa.Column("source", sa.Text(), server_default="user"),
        sa.Column("confidence", sa.Float()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_table(
        "playlists",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("modified_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("is_smart", sa.Integer(), server_default="0"),
        sa.Column("rules", sa.Text()),
    )
    op.create_table(
        "playlist_tracks",
        sa.Column("playlist_id", sa.Integer(), sa.ForeignKey("playlists.id"), primary_key=True),
        sa.Column("track_id", sa.Integer(), sa.ForeignKey("tracks.id"), primary_key=True),
        sa.Column("position", sa.Integer(), server_default="0"),
    )
    op.create_table(
        "settings",
        sa.Column("key", sa.Text(), primary_key=True),
        sa.Column("value", sa.Text()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_table(
        "change_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("track_id", sa.Integer(), sa.ForeignKey("tracks.id"), nullable=False),
        sa.Column("field", sa.Text(), nullable=False),
        sa.Column("old_value", sa.Text()),
        sa.Column("new_value", sa.Text()),
        sa.Column("source", sa.Text(), server_default="user"),
        sa.Column("changed_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_tracks_artist", "tracks", ["artist"])
    op.create_index("ix_tracks_title", "tracks", ["title"])
    op.create_index("ix_tracks_album", "tracks", ["album"])
    op.create_index("ix_tracks_genre", "tracks", ["genre"])
    op.create_index("ix_tracks_key", "tracks", ["key"])
    op.create_index("ix_tracks_bpm", "tracks", ["bpm"])
    op.create_index("ix_tags_track", "tags", ["track_id"])
    op.create_index("ix_tags_tag", "tags", ["tag"])
    op.create_index("ix_playlist_tracks_playlist", "playlist_tracks", ["playlist_id", "position"])


def downgrade() -> None:
    op.drop_index("ix_playlist_tracks_playlist", table_name="playlist_tracks")
    op.drop_index("ix_tags_tag", table_name="tags")
    op.drop_index("ix_tags_track", table_name="tags")
    op.drop_index("ix_tracks_bpm", table_name="tracks")
    op.drop_index("ix_tracks_key", table_name="tracks")
    op.drop_index("ix_tracks_genre", table_name="tracks")
    op.drop_index("ix_tracks_album", table_name="tracks")
    op.drop_index("ix_tracks_title", table_name="tracks")
    op.drop_index("ix_tracks_artist", table_name="tracks")
    op.drop_table("change_log")
    op.drop_table("settings")
    op.drop_table("playlist_tracks")
    op.drop_table("playlists")
    op.drop_table("tags")
    op.drop_table("tracks")
