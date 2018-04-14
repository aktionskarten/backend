from flask import Flask
from os import environ

from live import socketio
from api import api
from render import render
from models import db


def create_app():
    app = Flask(__name__)

    app.config.from_object('settings')
    if 'SETTINGS' in environ:
        app.config.from_envvar('SETTINGS')

    db.init_app(app)

    socketio.init_app(app)

    for blueprint in [api, render]:
        app.register_blueprint(blueprint)

    return app


app = create_app()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    socketio.run(app)
