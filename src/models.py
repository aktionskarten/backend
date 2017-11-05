import flask_sqlalchemy
import itertools
import geojson
import os

from geoalchemy2.shape import from_shape, to_shape
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.dialects.postgresql import JSON
from shapely.geometry import shape, mapping, box
from itsdangerous import TimedJSONWebSignatureSerializer, BadSignature,\
                         SignatureExpired
from geoalchemy2 import Geometry
from blinker import Namespace
from sqlalchemy import event
from slugify import slugify
from grid import Grid


db = flask_sqlalchemy.SQLAlchemy()
db_signals = Namespace()


class Map(db.Model):
    id = db.Column(db.Unicode, primary_key=True)
    name = db.Column(db.Unicode)
    secret = db.Column(db.Binary, default=lambda: os.urandom(24))
    public = db.Column(db.Boolean, default=True)
    _bbox = db.Column(Geometry('POLYGON'))
    features = db.relationship('Feature', backref='map', lazy=True)

    on_created = db_signals.signal('map-created')
    on_updated = db_signals.signal('map-updated')
    on_deleted = db_signals.signal('map-deleted')

    def __init__(self, name, bbox):
        self.name = name
        self._bbox = from_shape(box(*bbox))
        self.serializer = TimedJSONWebSignatureSerializer(self.secret,
                                                          expires_in=600)

    @property
    def legend(self):
        return {
            'Twitter': '@foo',
            'EA': '030 69 55555',
            'Datum': '30.06.2018'
        }

    @property
    def grid(self):
        return Grid(*self.bbox).generate(cells=12)

    @hybrid_property
    def bbox(self):
        return to_shape(self._bbox).bounds

    @bbox.setter
    def bbox(self, value):
        self._bbox = from_shape(shape(value))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'public': self.public,
            'bbox': self.bbox
        }

    def gen_token(self):
        return self.serializer.dumps(self.id)

    def check_token(self, token):
        try:
            self.serializer.loads(token)
        except SignatureExpired:
            return False  # valid token, but expired
        except BadSignature:
            return False  # invalid token

        return True


@event.listens_for(Map.name, 'set')
def generate_slug(target, value, oldvalue, initiator):
    if value and (not target.id or value != oldvalue):
        target.id = slugify(value)


class Feature(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    map_id = db.Column(db.Unicode, db.ForeignKey('map.id'), nullable=False)
    _geo = db.Column(Geometry())
    style = db.Column(JSON)

    on_created = db_signals.signal('feature-created')
    on_updated = db_signals.signal('feature-updated')
    on_deleted = db_signals.signal('feature-deleted')

    def __init__(self, data):
        self.geo = data

    @hybrid_property
    def geo(self):
        data = mapping(to_shape(self._geo))
        return data

    @geo.setter
    def geo(self, value):
        if 'properties' in value:
            self.style = value['properties']

        self._geo = from_shape(shape(value))

    def to_dict(self):
        properties = self.style.copy() if self.style else {}

        # scale is needed for rendering images in mapnik
        if 'iconSize' in properties:
            properties['scale'] = (20/150) * (properties['iconSize'][0]/20) * 2

        properties['id'] = self.id
        properties['map_id'] = self.map_id

        return geojson.Feature(geometry=self.geo, properties=properties)


@event.listens_for(db.session, 'after_commit')
def receive_after_commit(session):
    for action in ['created', 'updated', 'deleted']:
        if action in session.info:
            for (cls, data) in session.info[action]:
                getattr(cls, 'on_' + action).send(data)


@event.listens_for(db.session, 'before_flush')
def receive_before_flush(session, flush_context, instances):
    events = [('created', session.new), ('updated', session.dirty),
              ('deleted', session.deleted)]
    for (action, instances) in events:
        session.info[action] = [obj for obj in instances
                                if action == 'deleted' or
                                session.is_modified(obj, False)]


@event.listens_for(db.session, 'after_flush')
def receive_after_flush(session, flush_context):
    for action in ['created', 'updated', 'deleted']:
        if action in session.info:
            session.info[action] = [(obj.__class__, obj.to_dict())
                                    for obj in session.info[action]]
