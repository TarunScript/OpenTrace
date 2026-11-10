"""Initial schema

Revision ID: 02ee95d937a3
Revises: 
Create Date: 2026-11-10 22:49:35.337299

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '02ee95d937a3'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Creates core OpenTrace tables and indexes."""
    # 1. users
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('is_verified', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # 2. investigations
    op.create_table(
        'investigations',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('search_type', sa.String(32), nullable=False, server_default='username'),
        sa.Column('target_value', sa.String(255), nullable=False),
        sa.Column('status', sa.String(32), nullable=False, server_default='queued'),
        sa.Column('options_json', sa.Text(), nullable=True),
        sa.Column('total_sites_checked', sa.Integer(), server_default='0'),
        sa.Column('verified_count', sa.Integer(), server_default='0'),
        sa.Column('inconclusive_count', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_investigations_user_id', 'investigations', ['user_id'])
    op.create_index('ix_investigations_status', 'investigations', ['status'])
    op.create_index('ix_investigations_user_created', 'investigations', ['user_id', 'created_at'])

    # 3. search_inputs
    op.create_table(
        'search_inputs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('investigation_id', sa.String(64), sa.ForeignKey('investigations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('encrypted_value', sa.Text(), nullable=False),
        sa.Column('input_type', sa.String(32), nullable=False, server_default='username'),
    )
    op.create_index('ix_search_inputs_investigation_id', 'search_inputs', ['investigation_id'])

    # 4. profiles
    op.create_table(
        'profiles',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('investigation_id', sa.String(64), sa.ForeignKey('investigations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('platform', sa.String(64), nullable=False),
        sa.Column('category', sa.String(32), nullable=False, server_default='other'),
        sa.Column('username', sa.String(128), nullable=False),
        sa.Column('profile_url', sa.String(512), nullable=False),
        sa.Column('display_name', sa.String(255), nullable=True),
        sa.Column('biography', sa.Text(), nullable=True),
        sa.Column('public_website', sa.String(512), nullable=True),
        sa.Column('profile_image_url', sa.String(512), nullable=True),
        sa.Column('location', sa.String(255), nullable=True),
        sa.Column('confidence_existence', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('confidence_data', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('identity_confidence', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('first_seen_at', sa.DateTime(), nullable=False),
        sa.Column('last_checked_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_profiles_investigation_id', 'profiles', ['investigation_id'])
    op.create_index('ix_profiles_platform', 'profiles', ['platform'])
    op.create_index('ix_profiles_username', 'profiles', ['username'])

    # 5. evidence
    op.create_table(
        'evidence',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('profile_id', sa.String(36), sa.ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('source_url', sa.String(512), nullable=False),
        sa.Column('evidence_type', sa.String(64), nullable=False, server_default='profile_probe'),
        sa.Column('detection_method', sa.String(64), nullable=False),
        sa.Column('verification_status', sa.String(32), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('adapter_version', sa.String(32), nullable=False, server_default='1.0.0'),
        sa.Column('observed_at', sa.DateTime(), nullable=False),
        sa.Column('match_evidence', sa.Text(), nullable=True),
        sa.Column('raw_data_json', sa.Text(), nullable=True),
    )
    op.create_index('ix_evidence_profile_id', 'evidence', ['profile_id'])

    # 6. identifiers
    op.create_table(
        'identifiers',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('identifier_type', sa.String(32), nullable=False),
        sa.Column('identifier_value', sa.String(255), nullable=False),
        sa.Column('visibility', sa.String(32), nullable=False, server_default='public'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_identifiers_value', 'identifiers', ['identifier_value'])

    # 7. profile_identifiers
    op.create_table(
        'profile_identifiers',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('profile_id', sa.String(36), sa.ForeignKey('profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('identifier_id', sa.String(36), sa.ForeignKey('identifiers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('evidence_id', sa.String(36), sa.ForeignKey('evidence.id', ondelete='SET NULL'), nullable=True),
    )

    # 8. relationships
    op.create_table(
        'relationships',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('investigation_id', sa.String(64), sa.ForeignKey('investigations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('source_profile_id', sa.String(64), nullable=False),
        sa.Column('target_profile_id', sa.String(64), nullable=False),
        sa.Column('relationship_type', sa.String(64), nullable=False),
        sa.Column('confidence_tier', sa.String(32), nullable=False, server_default='possible'),
        sa.Column('confidence_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('evidence_reason', sa.Text(), nullable=False),
    )
    op.create_index('ix_relationships_investigation_id', 'relationships', ['investigation_id'])

    # 9. site_modules
    op.create_table(
        'site_modules',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('platform', sa.String(64), nullable=False, unique=True),
        sa.Column('module_name', sa.String(64), nullable=False),
        sa.Column('category', sa.String(32), nullable=False, server_default='other'),
        sa.Column('enabled', sa.Boolean(), server_default='1'),
        sa.Column('version', sa.String(32), server_default='1.0.0'),
        sa.Column('last_tested_at', sa.DateTime(), nullable=True),
    )

    # 10. audit_events
    op.create_table(
        'audit_events',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('investigation_id', sa.String(64), sa.ForeignKey('investigations.id', ondelete='SET NULL'), nullable=True),
        sa.Column('action', sa.String(64), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema: Drops tables in reverse order."""
    op.drop_table('audit_events')
    op.drop_table('site_modules')
    op.drop_table('relationships')
    op.drop_table('profile_identifiers')
    op.drop_table('identifiers')
    op.drop_table('evidence')
    op.drop_table('profiles')
    op.drop_table('search_inputs')
    op.drop_table('investigations')
    op.drop_table('users')
