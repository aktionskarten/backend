from geoalchemy2 import Geometry
from geoalchemy2.shape import from_shape
from app.utils import parse_bbox_string
from .exts import db


class Map(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    features = db.relationship("Feature", backref="map")
    bbox = db.Column(Geometry('POLYGON', srid=4326))
    public = db.Column(db.Boolean, default=False)
    editable = db.Column(db.Boolean, default=True)

    def set_bbox(self, bbox_string):
        self.bbox = from_shape(parse_bbox_string(bbox_string))


class Feature(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    geo = db.Column(Geometry(srid=4326))
    map_id = db.Column(db.Integer, db.ForeignKey('map.id'))


