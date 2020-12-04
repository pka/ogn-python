"""Added ReceiverStatusStatistic

Revision ID: 0dff4f629978
Revises: 7f5b8f65a977
Create Date: 2020-12-04 18:36:12.884785

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0dff4f629978'
down_revision = '7f5b8f65a977'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('receiver_status_statistics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('version', sa.String(), nullable=False),
        sa.Column('platform', sa.String(), nullable=False),
        sa.Column('messages_count', sa.Integer(), nullable=True),
        sa.Column('receiver_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['receiver_id'], ['receivers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_receiver_status_statistics_uc', 'receiver_status_statistics', ['date', 'receiver_id', 'version', 'platform'], unique=True)
    op.create_index(op.f('ix_receiver_status_statistics_receiver_id'), 'receiver_status_statistics', ['receiver_id'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_receiver_status_statistics_receiver_id'), table_name='receiver_status_statistics')
    op.drop_index('idx_receiver_status_statistics_uc', table_name='receiver_status_statistics')
    op.drop_table('receiver_status_statistics')
    # ### end Alembic commands ###