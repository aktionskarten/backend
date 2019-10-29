"""lifespan as interval

Revision ID: 39128f82b57f
Revises: b69a101b0e01
Create Date: 2019-10-15 21:06:50.405302

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '39128f82b57f'
down_revision = 'b69a101b0e01'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('map', 'lifespan',
               existing_type=sa.INTEGER(),
               type_=sa.Interval(),
               existing_nullable=True,
               postgresql_using="(lifespan || ' days')::interval"
               )
    op.drop_column('map', 'slug')


def downgrade():
    op.add_column('map', sa.Column('slug', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.alter_column('map', 'lifespan',
               existing_type=sa.Interval(),
               type_=sa.INTEGER(),
               existing_nullable=True,
               postgresql_using="EXTRACT(DAY FROM lifespan)")
