"""add Map.uuid

Revision ID: b69a101b0e01
Revises: 12fc3bb94002
Create Date: 2019-06-18 21:52:50.474451

"""
from alembic import op
from uuid import uuid4
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session
#from app.models import Map, Feature

# revision identifiers, used by Alembic.
revision = 'b69a101b0e01'
down_revision = '12fc3bb94002'
branch_labels = None
depends_on = None

t_maps = sa.Table(
    'map',
    sa.MetaData(),
    sa.Column('id', sa.Integer),
    sa.Column('uuid', postgresql.UUID(as_uuid=True)),
    sa.Column('name', sa.Unicode),
    )

t_features = sa.Table(
    'feature',
    sa.MetaData(),
    sa.Column('id', sa.Integer),
    sa.Column('map_uuid', postgresql.UUID(as_uuid=True)),
    sa.Column('map_id', sa.Integer),
    )

def upgrade():
    #bind = op.get_bind()
    conn = op.get_bind()
    session = Session(bind=conn)

    # add uuid for each map
    op.add_column('map', sa.Column('uuid', postgresql.UUID(as_uuid=True)))
    results = conn.execute(sa.select([
        t_maps.c.id,
        t_maps.c.uuid,
        t_maps.c.name,
        ])).fetchall()
    for id_, uuid, name in results:
        conn.execute(t_maps.update().where(t_maps.c.id == id_).values(
            uuid=uuid4()
            ))

    # add uuid to each feature
    op.add_column('feature', sa.Column('map_uuid', postgresql.UUID(as_uuid=True)))
    results = conn.execute(sa.select([
        t_features.c.id,
        t_features.c.map_uuid,
        t_maps.c.uuid,
        t_maps.c.name
        ])
        .select_from(
            t_features.outerjoin(t_maps, t_features.c.map_id == t_maps.c.id))
        ).fetchall()
    for id_, map_uuid, uuid, name in results:
        conn.execute(t_features.update().where(t_features.c.id == id_).values(
            map_uuid=uuid
            ))

    # add uuid as new primary key for maps
    #op.execute('ALTER TABLE map DROP CONSTRAINT map_pkey CASCADE')
    op.create_primary_key('map_pkey', 'map', ['uuid'])
    op.drop_constraint('feature_map_id_fkey', 'feature', type_='foreignkey')
    op.create_foreign_key('feature_map_uuid_fkey', 'feature', 'map', ['map_uuid'], ['uuid'], ondelete='CASCADE')
    op.create_unique_constraint('map_uuid', 'map', ['uuid'])

    # commit so our changes are persistent and we can change nullable
    # constraints
    session.commit()

    op.alter_column('feature', 'map_uuid', nullable=False)
    op.alter_column('map', 'uuid', nullable=False)

    # DEBUG OUTPUT
    results = conn.execute(sa.select([
        t_maps.c.id,
        t_maps.c.uuid,
        t_maps.c.name,
        ])).fetchall()
    for id_, uuid, name in results:
        print('MAP CHECK', id_, uuid, name)
    results = conn.execute(sa.select([
        t_features.c.id,
        t_features.c.map_uuid
        ])).fetchall()
    for id_, map_uuid in results:
        print('FEATURE CHECK', id_, uuid)

    op.drop_column('map', 'id')
    op.drop_column('feature', 'map_id')


def downgrade():
    op.execute('ALTER TABLE map DROP CONSTRAINT map_pkey CASCADE')
    op.add_column('map', sa.Column('id', sa.Integer(), primary_key=True))
    op.create_unique_constraint('map_id', 'map', ['id'])

    conn = op.get_bind()
    results = conn.execute(sa.select([
        t_maps.c.id,
        t_maps.c.uuid,
        t_maps.c.name,
        ])).fetchall()
    for id_, uuid, name in results:
        print('DOWNGRADE', id_, uuid, name)

    op.create_foreign_key('feature_map_id_fkey', 'feature', 'map', ['map_id'], ['id'], ondelete='CASCADE')
    op.drop_column('map', 'uuid')
    op.drop_column('feature', 'map_uuid')
