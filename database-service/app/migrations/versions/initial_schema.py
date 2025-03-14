# database-service/app/migrations/versions/initial_schema.py
"""Initial schema creation

Revision ID: 001
Create Date: 2025-03-14
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# Revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create leads table
    op.create_table(
        'leads',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_name', sa.String(), nullable=False),
        sa.Column('contact_name', sa.String(), nullable=False),
        sa.Column('position', sa.String(), nullable=True),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('revenue', sa.Float(), nullable=True),
        sa.Column('service_type', sa.String(), nullable=True),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.current_timestamp()),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create team_members table
    op.create_table(
        'team_members',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('skills', sqlite.JSON(), nullable=True),
        sa.Column('role', sa.String(), nullable=True),
        sa.Column('expertise_summary', sa.Text(), nullable=True),
        sa.Column('always_notify', sa.Boolean(), default=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    
    # Create analyses table
    op.create_table(
        'analyses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lead_id', sa.Integer(), nullable=False),
        sa.Column('company_details', sqlite.JSON(), nullable=True),
        sa.Column('llm_analysis', sa.Text(), nullable=True),
        sa.Column('final_decision', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), default=sa.func.current_timestamp()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], )
    )
    
    # Create team_matches table
    op.create_table(
        'team_matches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lead_id', sa.Integer(), nullable=False),
        sa.Column('team_member_id', sa.Integer(), nullable=False),
        sa.Column('relevance_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.current_timestamp()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ),
        sa.ForeignKeyConstraint(['team_member_id'], ['team_members.id'], )
    )

def downgrade():
    op.drop_table('team_matches')
    op.drop_table('analyses')
    op.drop_table('team_members')
    op.drop_table('leads')