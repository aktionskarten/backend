from flask import Flask
from os import environ

from api import api
from render import render
from models import db


def create_app():
    app = Flask(__name__)

    app.config.from_object('default_settings')
    if 'SETTINGS' in environ:
        app.config.from_envvar('SETTINGS')

    db.init_app(app)

    app.register_blueprint(api)
    app.register_blueprint(render)

    return app


app = create_app()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run("0.0.0.0")
