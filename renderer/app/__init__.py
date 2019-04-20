from flask import Flask
from os import environ
from app.routes import renderer

import rq
from redis import Redis


def create_app():
    app = Flask(__name__)

    app.config.from_object('app.settings_default')
    if 'SETTINGS' in environ:
        app.config.from_envvar('SETTINGS')

    for blueprint in [renderer]:
        app.register_blueprint(blueprint)

    app.task_queue = rq.Queue(connection=Redis())

    return app


app = create_app()


if __name__ == "__main__":
    app.run()
