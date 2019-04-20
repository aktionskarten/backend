from flask import Flask
from os import environ

import rq
from redis import Redis

#from live import socketio
from app.api import api
from render import render
from models import db


def create_app():
    app = Flask(__name__)

    app.config.from_object('app.settings_default')
    if 'SETTINGS' in environ:
        app.config.from_envvar('SETTINGS')

    db.init_app(app)
    #socketio.init_app(app)

    app.task_queue = rq.Queue(connection=Redis())

    for blueprint in [render, api]:
        app.register_blueprint(blueprint)

    return app


app = create_app()

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run()
    #socketio.run(app)
