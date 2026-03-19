from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0002_track_metadata_and_tag_history"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("tracks") as batch:
        batch.add_column(sa.Column("danceability", sa.Float()))
        batch.add_column(sa.Column("track_number", sa.Text()))
        batch.add_column(sa.Column("disc_number", sa.Text()))
        batch.add_column(sa.Column("album_artist", sa.Text()))
        batch.add_column(sa.Column("composer", sa.Text()))
        batch.add_column(sa.Column("copyright", sa.Text()))
        batch.add_column(sa.Column("encoded_by", sa.Text()))
        batch.add_column(sa.Column("original_artist", sa.Text()))
        batch.add_column(sa.Column("comments", sa.Text()))
        batch.add_column(sa.Column("isrc", sa.Text()))
        batch.add_column(sa.Column("release_type", sa.Text()))
        batch.add_column(sa.Column("record_label", sa.Text()))

    op.create_table(
        "metadata_cache",
        sa.Column("key", sa.Text(), primary_key=True),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("source", sa.Text()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_metadata_cache_created", "metadata_cache", ["created_at"])

    op.create_table(
        "tag_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("track_id", sa.Integer(), sa.ForeignKey("tracks.id"), nullable=False),
        sa.Column("field", sa.Text(), nullable=False),
        sa.Column("old_value", sa.Text()),
        sa.Column("new_value", sa.Text()),
        sa.Column("source", sa.Text(), server_default="user"),
        sa.Column("changed_by", sa.Text()),
        sa.Column("changed_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_tag_history_track_changed", "tag_history", ["track_id", "changed_at"])
    op.create_index("ix_tag_history_field", "tag_history", ["field"])


def downgrade() -> None:
    op.drop_index("ix_tag_history_field", table_name="tag_history")
    op.drop_index("ix_tag_history_track_changed", table_name="tag_history")
    op.drop_table("tag_history")
    op.drop_index("ix_metadata_cache_created", table_name="metadata_cache")
    op.drop_table("metadata_cache")
