import flask_sqlalchemy
import geojson
import os
import json
import datetime
import string
import random

from uuid import uuid4
from hashlib import sha256
from geoalchemy2.shape import from_shape, to_shape
from sqlalchemy import desc
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.dialects.postgresql import JSONB
from shapely.geometry import shape, mapping, box
from itsdangerous import TimedJSONWebSignatureSerializer, BadSignature,\
                         SignatureExpired
from geoalchemy2 import Geometry
from blinker import Namespace
from sqlalchemy import event
from slugify import slugify
from grid import Grid
from flask import url_for


db = flask_sqlalchemy.SQLAlchemy()
db_signals = Namespace()


def _gen_secret(length=24):
    chars = string.ascii_letters + string.digits
    return ''.join(random.SystemRandom().choice(chars) for _ in range(length))


class Map(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.Unicode)
    secret = db.Column(db.Unicode, default=_gen_secret)
    name = db.Column(db.Unicode)
    description = db.Column(db.Unicode)
    place = db.Column(db.Unicode)
    datetime = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    _bbox = db.Column(Geometry('POLYGON'))
    features = db.relationship('Feature', backref='map', lazy=True, order_by="Feature.id", cascade="all, delete-orphan")
    attributes = db.Column(JSONB)

    on_created = db_signals.signal('map-created')
    on_updated = db_signals.signal('map-updated')
    on_deleted = db_signals.signal('map-deleted')

    def __init__(self, name):
        self.name = name

    @property
    def serializer(self):
        if not hasattr(self, '_serializer'):
            self._serializer = TimedJSONWebSignatureSerializer(self.secret,
                                                               expires_in=60*60*2)
        return self._serializer

    @classmethod
    def all(cls):
        return db.session.query(Map).filter(Map._bbox.isnot(None), Map.features.any()) \
                                    .order_by(desc(Map.datetime)) \
                                    .all()

    @classmethod
    def get(cls, name_or_slug):
        slug = slugify(name_or_slug)
        return db.session.query(Map).filter(Map.slug == slug).first()

    @classmethod
    def delete(cls, slug):
        db.session.delete(cls.get(slug))
        db.session.commit()

    @property
    def grid(self):
        if (self.bbox):
            return Grid(*self.bbox).generate()
        return None

    @property
    def hash(self):
        data = self.to_dict(False)
        data['features'] = [f.to_dict() for f in self.features]
        raw = json.dumps(data, separators=(',', ':'), sort_keys=True)
        return sha256(raw.encode()).hexdigest()

    @hybrid_property
    def time(self):
        return self.datetime.time()

    @time.setter
    def time(self, t):
        args = {'hour': t.hour, 'minute': t.minute, 'second': t.second}
        if self.datetime:
            self.datetime.replace(**args)
        else:
            self.datetime = datetime.datetime(**args)

    @hybrid_property
    def date(self):
        return self.datetime.date()

    @date.setter
    def date(self, value):
        args = [value.year, value.month, value.day]
        if self.datetime:
            self.datetime.replace(*args)
        else:
            self.datetime = datetime.datetime(*args)

    @hybrid_property
    def bbox(self):
        if (self._bbox is None):
            return None
        return to_shape(self._bbox).bounds

    @bbox.setter
    def bbox(self, value):
        self._bbox = from_shape(box(*value))

    def to_dict(self, hash_included=True, secret_included=False):
        data = {
            'id': self.slug,
            'name': self.name,
            'description': self.description,
            'datetime': self.datetime.strftime('%Y-%m-%d %H:%M'),
            'attributes': self.attributes if self.attributes else [],
            'bbox': self.bbox,
            'place': self.place,
            'thumbnail': url_for('Render.map_export_png', map_id=self.slug, size='small', _external=True),
            'exports': {
                'pdf': url_for('Render.map_export_pdf', map_id=self.slug, _external=True),
                'svg': url_for('Render.map_export_svg', map_id=self.slug, _external=True),
                'png': url_for('Render.map_export_png', map_id=self.slug, _external=True)
            }
        }

        if hash_included:
            data['hash'] = self.hash

        if secret_included:
            data['secret'] = self.secret

        return data

    def gen_token(self):
        return self.serializer.dumps(self.id).decode('utf-8')

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
    if value and value != oldvalue:
        target.slug = slugify(value)


class Feature(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    map_id = db.Column(db.Integer, db.ForeignKey('map.id'), nullable=False)
    _geo = db.Column(Geometry())
    style = db.Column(JSONB)

    on_created = db_signals.signal('feature-created')
    on_updated = db_signals.signal('feature-updated')
    on_deleted = db_signals.signal('feature-deleted')

    def __init__(self, feature):
        if 'geometry' in feature:
            self.geo = feature['geometry']

        if 'properties' in feature:
            self.style = feature['properties']

    @classmethod
    def get(cls, id):
        return db.session.query(Feature).get(id)

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

        properties['id'] = self.id
        properties['map_id'] = self.map.slug

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
