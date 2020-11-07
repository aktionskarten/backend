import os
import flask_sqlalchemy
import geojson
import json
import datetime as _datetime
import string
import random

from uuid import uuid4
from hashlib import sha256
from geoalchemy2.shape import from_shape, to_shape
from sqlalchemy import desc, inspect, text, func
from sqlalchemy.sql.functions import concat
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.dialects.postgresql import JSONB, UUID, INTERVAL
from shapely.geometry import shape, mapping, box
from itsdangerous import TimedJSONWebSignatureSerializer, BadSignature,\
                         SignatureExpired
from geoalchemy2 import Geometry
from blinker import Namespace
from sqlalchemy import event
from flask import url_for
from app.grid import grid_for_bbox
from app.utils import orientation_for_bbox


db = flask_sqlalchemy.SQLAlchemy()
db_signals = Namespace()


def _gen_secret(length=24):
    chars = string.ascii_letters + string.digits
    return ''.join(random.SystemRandom().choice(chars) for _ in range(length))


class Map(db.Model):
    uuid = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    secret = db.Column(db.Unicode, default=_gen_secret)
    name = db.Column(db.Unicode)
    description = db.Column(db.Unicode)
    place = db.Column(db.Unicode)
    datetime = db.Column(db.DateTime, default=_datetime.datetime.utcnow)
    _bbox = db.Column(Geometry('POLYGON'))
    features = db.relationship('Feature', backref='map', lazy=True, order_by="Feature.id", cascade="all, delete-orphan")
    attributes = db.Column(JSONB)
    published = db.Column(db.Boolean, default=False)
    lifespan = db.Column(db.Interval, default=_datetime.timedelta(days=30))

    on_created = db_signals.signal('map-created')
    on_updated = db_signals.signal('map-updated')
    on_deleted = db_signals.signal('map-deleted')

    def __init__(self, name, **kwargs):
        self.name = name

        for k,v in kwargs.items():
            setattr(self, k,v)

    @property
    def serializer(self):
        if not hasattr(self, '_serializer'):
            self._serializer = TimedJSONWebSignatureSerializer(self.secret,
                                                               expires_in=60*60*2)
        return self._serializer

    @classmethod
    def all(cls):
        return db.session.query(Map).filter(Map._bbox.isnot(None),
                                            Map.published.is_(True), \
                                            Map.outdated.is_(False)) \
                                    .order_by(desc(Map.datetime))    \
                                    .all()

    @classmethod
    def get(cls, uuid):
        try:
            return db.session.query(Map).filter(Map.uuid == uuid).first()
        except:
            pass
        return None

    @classmethod
    def find(cls, name):
        try:
            return db.session.query(Map).filter(Map.name == name).first()
        except:
            pass
        return None

    @classmethod
    def delete(cls, uuid):
        db.session.delete(cls.get(uuid))
        db.session.commit()

    @hybrid_property
    def outdated(self):
        now = _datetime.datetime.utcnow()
        return self.datetime < (now - self.lifespan)

    @outdated.expression
    def outdated(cls):
        return cls.datetime < (func.now()-cls.lifespan)

    @property
    def orientation(self):
        if self._bbox is None:
            return ''
        return orientation_for_bbox(*self.bbox)

    @property
    def grid(self):
        if (self.bbox):
            cells = {
                '': [5, 5],
                'landscape': [5, 3],
                'portrait': [3, 5],
            }
            return grid_for_bbox(*self.bbox, *cells[self.orientation])
        return None

    @property
    def version(self):
        data = self.to_dict(False, features_included=True)
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
            self.datetime = _datetime.datetime(**args)

    @hybrid_property
    def date(self):
        return self.datetime.date()

    @date.setter
    def date(self, value):
        args = [value.year, value.month, value.day]
        if self.datetime:
            self.datetime.replace(*args)
        else:
            self.datetime = _datetime.datetime(*args)

    @hybrid_property
    def bbox(self):
        if (self._bbox is None):
            return None
        return to_shape(self._bbox).bounds

    @bbox.setter
    def bbox(self, value):
        if (value is not None):
            self._bbox = from_shape(box(*value))

    def to_dict(self, version_included=True, secret_included=False, grid_included=False, features_included=False):
        data = {
            'id': self.uuid.hex,
            'name': self.name,
            'description': self.description,
            'datetime': self.datetime.isoformat(),
            'attributes': self.attributes if self.attributes else [],
            'bbox': self.bbox,
            'place': self.place,
            'lifespan': self.lifespan.days,
            'published': self.published,
        }

        if version_included:
            data['version'] = self.version

        if secret_included:
            data['secret'] = self.secret

        if grid_included:
            data['grid'] = self.grid

        if features_included:
            data['features'] = [f.to_dict() for f in self.features]

        return data

    def gen_token(self):
        return self.serializer.dumps(self.uuid.hex).decode('utf-8')

    def check_token(self, token):
        try:
            self.serializer.loads(token)
        except SignatureExpired:
            return False  # valid token, but expired
        except BadSignature:
            return False  # invalid token

        return True

    def publish(self):
        self.published = True
        db.session.add(self)
        db.session.commit()


class Feature(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    map_uuid = db.Column(UUID(as_uuid=True), db.ForeignKey('map.uuid'), nullable=False)
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
        return mapping(to_shape(self._geo))

    @geo.setter
    def geo(self, value):
        if 'properties' in value:
            self.style = value['properties']

        self._geo = from_shape(shape(value))

    def to_dict(self):
        properties = self.style.copy() if self.style else {}

        properties['id'] = self.id
        properties['map_id'] = self.map.uuid.hex

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


def _get_history(obj):
    hist = {}
    for attr in inspect(obj).attrs:
        if attr.history.has_changes():
            try:
                hist[attr.key] = attr.history.deleted[-1]
            except IndexError:
                pass
    return hist

@event.listens_for(db.session, 'after_flush')
def receive_after_flush(session, flush_context):
    for action in ['created', 'updated', 'deleted']:
        if action in session.info:
            session.info[action] = [(obj.__class__, {
                'new': obj.to_dict(), 'old': _get_history(obj)
                }) for obj in session.info[action]]
