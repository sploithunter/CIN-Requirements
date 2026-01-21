"""Initial migration

Revision ID: 001_initial
Revises:
Create Date: 2026-01-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('oauth_provider', sa.String(50), nullable=True),
        sa.Column('oauth_id', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # Create sessions table
    op.create_table(
        'sessions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False, default='Untitled Session'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('draft', 'in_progress', 'review', 'completed', 'archived', name='sessionstatus'), nullable=False),
        sa.Column('owner_id', sa.UUID(), nullable=False),
        sa.Column('liveblocks_room_id', sa.String(255), nullable=True),
        sa.Column('system_prompt', sa.Text(), nullable=True),
        sa.Column('context_summary', sa.Text(), nullable=True),
        sa.Column('document_content', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('token_usage', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )

    # Create messages table
    op.create_table(
        'messages',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('role', sa.Enum('user', 'assistant', 'system', name='messagerole'), nullable=False),
        sa.Column('message_type', sa.Enum('text', 'questionnaire', 'requirement', 'voice_transcript', name='messagetype'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('extra_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('input_tokens', sa.Integer(), nullable=False, default=0),
        sa.Column('output_tokens', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )

    # Create media table
    op.create_table(
        'media',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('original_filename', sa.String(255), nullable=False),
        sa.Column('content_type', sa.String(100), nullable=False),
        sa.Column('media_type', sa.Enum('image', 'audio', 'document', 'video', name='mediatype'), nullable=False),
        sa.Column('size_bytes', sa.BigInteger(), nullable=False),
        sa.Column('storage_key', sa.String(500), nullable=False),
        sa.Column('storage_url', sa.String(1000), nullable=True),
        sa.Column('extracted_text', sa.Text(), nullable=True),
        sa.Column('transcript', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('media')
    op.drop_table('messages')
    op.drop_table('sessions')
    op.drop_table('users')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS mediatype')
    op.execute('DROP TYPE IF EXISTS messagetype')
    op.execute('DROP TYPE IF EXISTS messagerole')
    op.execute('DROP TYPE IF EXISTS sessionstatus')
