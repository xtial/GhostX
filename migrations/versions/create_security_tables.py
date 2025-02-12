"""create security tables

Revision ID: create_security_tables
Revises: 
Create Date: 2024-02-12 22:22:14.631935

"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Create sessions table
    op.create_table('sessions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=False),
        sa.Column('user_agent', sa.String(255)),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('last_active', sa.DateTime(), nullable=False)
    )

    # Create login_attempts table
    op.create_table('login_attempts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('username', sa.String(255), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=False),
        sa.Column('success', sa.Boolean(), default=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('user_agent', sa.String(255))
    )

    # Create api_requests table
    op.create_table('api_requests',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('endpoint', sa.String(255), nullable=False),
        sa.Column('method', sa.String(10), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('ip_address', sa.String(45), nullable=False),
        sa.Column('status_code', sa.Integer()),
        sa.Column('timestamp', sa.DateTime(), nullable=False)
    )

    # Create security_logs table
    op.create_table('security_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('timestamp', sa.DateTime(), nullable=False)
    )

def downgrade():
    op.drop_table('security_logs')
    op.drop_table('api_requests')
    op.drop_table('login_attempts')
    op.drop_table('sessions') 