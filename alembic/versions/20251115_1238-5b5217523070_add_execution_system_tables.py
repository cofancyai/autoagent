"""Add execution system tables

Revision ID: 5b5217523070
Revises: 
Create Date: 2025-11-15 12:38:43.474025

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5b5217523070'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create execution_projects table
    op.create_table(
        'execution_projects',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('project_name', sa.String(length=255), nullable=False),
        sa.Column('business_type', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('total_budget', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('spent_amount', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='planning'),
        sa.Column('progress_percentage', sa.Numeric(precision=5, scale=2), nullable=False, server_default='0'),
        sa.Column('estimated_completion_date', sa.DateTime(), nullable=True),
        sa.Column('actual_completion_date', sa.DateTime(), nullable=True),
        sa.Column('requirements', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column('execution_plan', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column('results', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_execution_projects_session_id'), 'execution_projects', ['session_id'], unique=False)

    # Create execution_tasks table
    op.create_table(
        'execution_tasks',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('project_id', sa.UUID(), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('task_name', sa.String(length=255), nullable=False),
        sa.Column('task_type', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('assigned_agent', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('progress_percentage', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('dependencies', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column('blocking_tasks', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column('task_config', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column('execution_logs', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('estimated_duration_hours', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['project_id'], ['execution_projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_execution_tasks_project_id'), 'execution_tasks', ['project_id'], unique=False)
    op.create_index(op.f('ix_execution_tasks_session_id'), 'execution_tasks', ['session_id'], unique=False)

    # Create created_assets table
    op.create_table(
        'created_assets',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('project_id', sa.UUID(), nullable=False),
        sa.Column('task_id', sa.UUID(), nullable=True),
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('asset_name', sa.String(length=255), nullable=False),
        sa.Column('asset_type', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('url', sa.Text(), nullable=True),
        sa.Column('file_path', sa.Text(), nullable=True),
        sa.Column('credentials', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column('asset_metadata', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column('deployment_status', sa.String(length=50), nullable=False, server_default='draft'),
        sa.Column('external_id', sa.String(length=255), nullable=True),
        sa.Column('external_service', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['project_id'], ['execution_projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['task_id'], ['execution_tasks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_created_assets_project_id'), 'created_assets', ['project_id'], unique=False)
    op.create_index(op.f('ix_created_assets_task_id'), 'created_assets', ['task_id'], unique=False)
    op.create_index(op.f('ix_created_assets_session_id'), 'created_assets', ['session_id'], unique=False)

    # Create service_integrations table
    op.create_table(
        'service_integrations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('project_id', sa.UUID(), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('service_name', sa.String(length=100), nullable=False),
        sa.Column('service_category', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('api_key', sa.Text(), nullable=True),
        sa.Column('api_credentials', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column('config', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column('webhooks', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('usage_stats', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.String(length=50), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['project_id'], ['execution_projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_service_integrations_project_id'), 'service_integrations', ['project_id'], unique=False)
    op.create_index(op.f('ix_service_integrations_session_id'), 'service_integrations', ['session_id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order (respecting foreign keys)
    op.drop_index(op.f('ix_service_integrations_session_id'), table_name='service_integrations')
    op.drop_index(op.f('ix_service_integrations_project_id'), table_name='service_integrations')
    op.drop_table('service_integrations')

    op.drop_index(op.f('ix_created_assets_session_id'), table_name='created_assets')
    op.drop_index(op.f('ix_created_assets_task_id'), table_name='created_assets')
    op.drop_index(op.f('ix_created_assets_project_id'), table_name='created_assets')
    op.drop_table('created_assets')

    op.drop_index(op.f('ix_execution_tasks_session_id'), table_name='execution_tasks')
    op.drop_index(op.f('ix_execution_tasks_project_id'), table_name='execution_tasks')
    op.drop_table('execution_tasks')

    op.drop_index(op.f('ix_execution_projects_session_id'), table_name='execution_projects')
    op.drop_table('execution_projects')
