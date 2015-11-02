from geoalchemy2 import Geometry, Raster, functions as func
from .exts import db

class Map(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    features = db.relationship("Feature", backref="map")

class Feature(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    geo = db.Column(Geometry(srid=4326))

