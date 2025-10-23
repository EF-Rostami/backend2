"""add events tables

Revision ID: add_events
Revises: add_absence_excuses
Create Date: 2025-10-21

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_events'
down_revision = 'add_absence_excuses'  # TODO: Replace with your latest revision ID
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types
    event_type_enum = postgresql.ENUM(
        'assembly', 'meeting', 'sports', 'field_trip', 'holiday', 
        'exam', 'workshop', 'celebration', 'other',
        name='eventtype'
    )
    event_type_enum.create(op.get_bind(), checkfirst=True)
    
    event_audience_enum = postgresql.ENUM(
        'all', 'students', 'parents', 'teachers', 'staff',
        name='eventaudience'
    )
    event_audience_enum.create(op.get_bind(), checkfirst=True)
    
    rsvp_status_enum = postgresql.ENUM(
        'pending', 'attending', 'not_attending', 'maybe',
        name='rsvpstatus'
    )
    rsvp_status_enum.create(op.get_bind(), checkfirst=True)
    
    # Create events table
    op.create_table(
        'events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('event_type', sa.Enum(
            'assembly', 'meeting', 'sports', 'field_trip', 'holiday', 
            'exam', 'workshop', 'celebration', 'other',
            name='eventtype'
        ), nullable=False),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('location', sa.String(255), nullable=True),
        sa.Column('target_audience', sa.Enum(
            'all', 'students', 'parents', 'teachers', 'staff',
            name='eventaudience'
        ), nullable=False, server_default='all'),
        sa.Column('target_grade_levels', sa.String(500), nullable=True),
        sa.Column('requires_rsvp', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('max_participants', sa.Integer(), nullable=True),
        sa.Column('registration_deadline', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('organizer_name', sa.String(255), nullable=True),
        sa.Column('organizer_contact', sa.String(255), nullable=True),
        sa.Column('is_published', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_cancelled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('cancellation_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for events
    op.create_index('ix_events_id', 'events', ['id'])
    op.create_index('ix_events_start_date', 'events', ['start_date'])
    op.create_index('ix_events_event_type', 'events', ['event_type'])
    op.create_index('ix_events_target_audience', 'events', ['target_audience'])
    op.create_index('ix_events_is_published', 'events', ['is_published'])
    
    # Create event_rsvps table
    op.create_table(
        'event_rsvps',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.Enum(
            'pending', 'attending', 'not_attending', 'maybe',
            name='rsvpstatus'
        ), nullable=False, server_default='pending'),
        sa.Column('response_date', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('event_id', 'user_id', 'student_id', name='unique_event_user_student_rsvp')
    )
    
    # Create indexes for event_rsvps
    op.create_index('ix_event_rsvps_id', 'event_rsvps', ['id'])
    op.create_index('ix_event_rsvps_event_id', 'event_rsvps', ['event_id'])
    op.create_index('ix_event_rsvps_user_id', 'event_rsvps', ['user_id'])
    op.create_index('ix_event_rsvps_status', 'event_rsvps', ['status'])
    
    # Create event_attachments table
    op.create_table(
        'event_attachments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('uploaded_by', sa.Integer(), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for event_attachments
    op.create_index('ix_event_attachments_id', 'event_attachments', ['id'])
    op.create_index('ix_event_attachments_event_id', 'event_attachments', ['event_id'])


def downgrade() -> None:
    # Drop indexes for event_attachments
    op.drop_index('ix_event_attachments_event_id', table_name='event_attachments')
    op.drop_index('ix_event_attachments_id', table_name='event_attachments')
    
    # Drop indexes for event_rsvps
    op.drop_index('ix_event_rsvps_status', table_name='event_rsvps')
    op.drop_index('ix_event_rsvps_user_id', table_name='event_rsvps')
    op.drop_index('ix_event_rsvps_event_id', table_name='event_rsvps')
    op.drop_index('ix_event_rsvps_id', table_name='event_rsvps')
    
    # Drop indexes for events
    op.drop_index('ix_events_is_published', table_name='events')
    op.drop_index('ix_events_target_audience', table_name='events')
    op.drop_index('ix_events_event_type', table_name='events')
    op.drop_index('ix_events_start_date', table_name='events')
    op.drop_index('ix_events_id', table_name='events')
    
    # Drop tables
    op.drop_table('event_attachments')
    op.drop_table('event_rsvps')
    op.drop_table('events')
    
    # Drop enum types
    sa.Enum(name='rsvpstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='eventaudience').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='eventtype').drop(op.get_bind(), checkfirst=True)