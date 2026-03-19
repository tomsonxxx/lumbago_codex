"""Add Lumbago_Music v2 tables

Revision ID: 002_lumbago_v2
Revises: 0002_track_metadata_and_tag_history
Create Date: 2026-03-19
"""
from alembic import op
import sqlalchemy as sa

revision = '002_lumbago_v2'
down_revision = '0002_track_metadata_and_tag_history'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('cue_points',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('track_id', sa.Integer, sa.ForeignKey('tracks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('time_ms', sa.Integer, nullable=False),
        sa.Column('cue_type', sa.String(20), nullable=False, server_default='hotcue'),
        sa.Column('hotcue_index', sa.Integer, nullable=True),
        sa.Column('loop_end_ms', sa.Integer, nullable=True),
        sa.Column('label', sa.String(100), nullable=True),
        sa.Column('color', sa.String(10), nullable=True),
    )
    op.create_index('ix_cue_points_track', 'cue_points', ['track_id', 'hotcue_index'])

    op.create_table('beat_markers',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('track_id', sa.Integer, sa.ForeignKey('tracks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('time_ms', sa.Float, nullable=False),
        sa.Column('beat_number', sa.Integer, nullable=False),
        sa.Column('bar_number', sa.Integer, nullable=False),
    )
    op.create_index('ix_beat_markers_track_time', 'beat_markers', ['track_id', 'time_ms'])

    op.create_table('analysis_jobs',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('track_id', sa.Integer, sa.ForeignKey('tracks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('job_type', sa.String(30), nullable=False),
        sa.Column('priority', sa.Integer, nullable=False, server_default='5'),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime, nullable=True),
        sa.Column('updated_at', sa.DateTime, nullable=True),
        sa.Column('error_msg', sa.Text, nullable=True),
    )
    op.create_index('ix_analysis_jobs_status_prio', 'analysis_jobs', ['status', 'priority'])

    op.create_table('audio_features',
        sa.Column('id', sa.Integer, sa.ForeignKey('tracks.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('mfcc_json', sa.Text, nullable=False, server_default='[]'),
        sa.Column('tempo', sa.Float, nullable=True),
        sa.Column('spectral_centroid', sa.Float, nullable=True),
        sa.Column('spectral_rolloff', sa.Float, nullable=True),
        sa.Column('brightness', sa.Float, nullable=True),
        sa.Column('roughness', sa.Float, nullable=True),
        sa.Column('waveform_blob', sa.LargeBinary, nullable=True),
    )

    op.create_table('watch_folders',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('path', sa.String(1024), nullable=False, unique=True),
        sa.Column('active', sa.Boolean, nullable=False, server_default='1'),
    )


def downgrade() -> None:
    op.drop_table('watch_folders')
    op.drop_table('audio_features')
    op.drop_index('ix_analysis_jobs_status_prio', 'analysis_jobs')
    op.drop_table('analysis_jobs')
    op.drop_index('ix_beat_markers_track_time', 'beat_markers')
    op.drop_table('beat_markers')
    op.drop_index('ix_cue_points_track', 'cue_points')
    op.drop_table('cue_points')
