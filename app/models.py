from geoalchemy2 import Geometry
from geoalchemy2.shape import from_shape
from app.utils import parse_bbox_string
from .exts import db


class Map(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    _bbox = db.Column(Geometry('POLYGON', srid=4326))
    public = db.Column(db.Boolean, default=False)
    editable = db.Column(db.Boolean, default=True)
    features = db.relationship("Feature", backref="map")

    @property
    def bbox(self):
        return self._bbox;

    @bbox.setter
    def bbox(self, bbox_string):
        self._bbox = from_shape(parse_bbox_string(bbox_string), 4326)

class Feature(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    geo = db.Column(Geometry(srid=4326))
    map_id = db.Column(db.Integer, db.ForeignKey('map.id'))


