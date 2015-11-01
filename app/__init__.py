from flask import Flask
from flask_restful import Resource, Api
from .exts import db

class Maps(Resource):
    def get(self, name):
        return { 'name': name }

def create_app(config=None):
    """Creates the Flask app."""
    app = Flask(__name__)

    # load config - http://flask.pocoo.org/docs/config/#instance-folders
    app.config.from_pyfile('../config.cfg', silent=True)

    # init flask-sqlalchemy
    db.init_app(app)

    # add flask-restful to app
    api = Api(app)
    api.add_resource(Maps, '/maps/<string:name>')

    return app

if __name__ == '__main__':
    manager.run()
