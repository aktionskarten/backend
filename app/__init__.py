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

    return app

if __name__ == '__main__':
    manager.run()
