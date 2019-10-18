from shutil import rmtree
from app.models import Map, Feature, db

def db_reset():
    db.session.execute(Feature.__table__.delete())
    db.session.execute(Map.__table__.delete())
