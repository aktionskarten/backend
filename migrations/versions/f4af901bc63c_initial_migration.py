"""Initial migration.

Revision ID: f4af901bc63c
Revises: 
Create Date: 2021-08-04 12:01:04.836639

"""
from alembic import op
import sqlalchemy as sa
from geoalchemy2 import types as gsa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'f4af901bc63c'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('map',
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('secret', sa.Unicode(), nullable=True),
        sa.Column('name', sa.Unicode(), nullable=True),
        sa.Column('description', sa.Unicode(), nullable=True),
        sa.Column('place', sa.Unicode(), nullable=True),
        sa.Column('_datetime', sa.DateTime(timezone=True), nullable=True),
        sa.Column('_bbox', gsa.Geometry(geometry_type='POLYGON', from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
        sa.Column('attributes', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('published', sa.Boolean(), nullable=True),
        sa.Column('lifespan', sa.Interval(), nullable=True),
        sa.Column('theme', sa.Unicode(), nullable=True),
        sa.PrimaryKeyConstraint('uuid')
    )
    op.create_table('feature',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('map_uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('_geo', gsa.Geometry(from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
        sa.Column('style', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['map_uuid'], ['map.uuid'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('feature')
    op.drop_table('map')
