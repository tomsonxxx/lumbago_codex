"""add metadata consensus core tables

Revision ID: 0003_metadata_consensus_core
Revises: 002_lumbago_v2
Create Date: 2026-05-16
"""

from alembic import op
import sqlalchemy as sa


revision = "0003_metadata_consensus_core"
down_revision = "002_lumbago_v2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "metadata_field_evidence",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("track_id", sa.Integer(), sa.ForeignKey("tracks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("field_name", sa.Text(), nullable=False),
        sa.Column("value", sa.Text(), nullable=True),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("observed_at", sa.DateTime(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
    )
    op.create_index(
        "ix_metadata_field_evidence_track_field",
        "metadata_field_evidence",
        ["track_id", "field_name"],
    )
    op.create_index("ix_metadata_field_evidence_source", "metadata_field_evidence", ["source"])

    op.create_table(
        "metadata_conflicts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("track_id", sa.Integer(), sa.ForeignKey("tracks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("field_name", sa.Text(), nullable=False),
        sa.Column("chosen_value", sa.Text(), nullable=True),
        sa.Column("chosen_source", sa.Text(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="open"),
        sa.Column("variants_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("detected_at", sa.DateTime(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_metadata_conflicts_track_field", "metadata_conflicts", ["track_id", "field_name"])
    op.create_index("ix_metadata_conflicts_status", "metadata_conflicts", ["status"])

    op.create_table(
        "metadata_history",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("track_id", sa.Integer(), sa.ForeignKey("tracks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("field_name", sa.Text(), nullable=False),
        sa.Column("old_value", sa.Text(), nullable=True),
        sa.Column("new_value", sa.Text(), nullable=True),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("operation", sa.Text(), nullable=False, server_default="consensus"),
        sa.Column("changed_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_metadata_history_track_field", "metadata_history", ["track_id", "field_name"])


def downgrade() -> None:
    op.drop_index("ix_metadata_history_track_field", table_name="metadata_history")
    op.drop_table("metadata_history")
    op.drop_index("ix_metadata_conflicts_status", table_name="metadata_conflicts")
    op.drop_index("ix_metadata_conflicts_track_field", table_name="metadata_conflicts")
    op.drop_table("metadata_conflicts")
    op.drop_index("ix_metadata_field_evidence_source", table_name="metadata_field_evidence")
    op.drop_index("ix_metadata_field_evidence_track_field", table_name="metadata_field_evidence")
    op.drop_table("metadata_field_evidence")
