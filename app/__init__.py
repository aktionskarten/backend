from flask import Flask
from flask_restful import Api
from .exts import db


def create_app(config=None):
    """Creates the Flask app."""
    app = Flask(__name__)

    # load config - http://flask.pocoo.org/docs/config/#instance-folders
    app.config.from_pyfile('../config.cfg', silent=True)

    # init flask-sqlalchemy
    db.init_app(app)

    # add rest endpoints
    api = Api(app)
    from resources import Maps
    api.add_resource(Maps, '/maps/<string:name>')

    # TODO: integrate better
    @app.before_first_request
    def enable_spatialite():
        conn = db.engine.connect()
        raw = conn.connection.connection

        # extension
        raw.enable_load_extension(True)
        raw.execute("select load_extension('/usr/lib/mod_spatialite.so')")

        # init
        cursor = raw.execute("PRAGMA table_info(geometry_columns);")
        if cursor.fetchall() == 0:
            raw.execute("SELECT InitSpatialMetaData();")
        conn.close()

    return app

if __name__ == '__main__':
    manager.run()
