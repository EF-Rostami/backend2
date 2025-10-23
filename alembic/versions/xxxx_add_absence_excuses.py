"""add absence excuses table

Revision ID: add_absence_excuses
Revises: [YOUR_PREVIOUS_REVISION]
Create Date: 2025-10-20

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_absence_excuses'
down_revision = None  # TODO: Replace with your latest revision ID
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types
    excuse_status_enum = postgresql.ENUM('pending', 'approved', 'rejected', name='excusestatus')
    excuse_status_enum.create(op.get_bind(), checkfirst=True)
    
    absence_reason_enum = postgresql.ENUM('illness', 'medical_appointment', 'family_emergency', 'family_event', 'other', name='absencereason')
    absence_reason_enum.create(op.get_bind(), checkfirst=True)
    
    # Create absence_excuses table
    op.create_table(
        'absence_excuses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('reason', sa.Enum('illness', 'medical_appointment', 'family_emergency', 'family_event', 'other', name='absencereason'), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('status', sa.Enum('pending', 'approved', 'rejected', name='excusestatus'), nullable=False, server_default='pending'),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reviewed_by', sa.Integer(), nullable=True),
        sa.Column('admin_notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_id'], ['parents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_absence_excuses_id', 'absence_excuses', ['id'])
    op.create_index('ix_absence_excuses_student_id', 'absence_excuses', ['student_id'])
    op.create_index('ix_absence_excuses_parent_id', 'absence_excuses', ['parent_id'])
    op.create_index('ix_absence_excuses_status', 'absence_excuses', ['status'])
    op.create_index('ix_absence_excuses_submitted_at', 'absence_excuses', ['submitted_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_absence_excuses_submitted_at', table_name='absence_excuses')
    op.drop_index('ix_absence_excuses_status', table_name='absence_excuses')
    op.drop_index('ix_absence_excuses_parent_id', table_name='absence_excuses')
    op.drop_index('ix_absence_excuses_student_id', table_name='absence_excuses')
    op.drop_index('ix_absence_excuses_id', table_name='absence_excuses')
    
    # Drop table
    op.drop_table('absence_excuses')
    
    # Drop enum types
    sa.Enum(name='excusestatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='absencereason').drop(op.get_bind(), checkfirst=True)