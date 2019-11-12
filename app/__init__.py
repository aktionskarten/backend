from flask import Flask
from os import environ
from flask_migrate import Migrate
import rq
from redis import Redis

from app.live import socketio
from app.api import api
from app.models import db
from app.render import renderer
from app.cli import pymapnik_cli, osm_cli, postgres_cli, clear_maps,\
                    gen_markers, remove_outdated_maps

from uuid import UUID
from werkzeug.routing import BaseConverter
class UUIDConverter(BaseConverter):
    def to_python(self, value):
        return UUID(value)
    def to_url(self, uuid):
        return uuid.hex

def create_app():
    app = Flask(__name__)

    app.config.from_object('app.settings_default')
    if 'SETTINGS' in environ:
        app.config.from_envvar('SETTINGS')

    db.init_app(app)
    Migrate(app, db)
    socketio.init_app(app)

    app.task_queue = rq.Queue(connection=Redis())
    app.url_map.converters['uuid'] = UUIDConverter

    for blueprint in [renderer, api]:
        app.register_blueprint(blueprint)

    cmds = [clear_maps, gen_markers, remove_outdated_maps]
    for command in [pymapnik_cli, osm_cli, postgres_cli] + cmds:
        app.cli.add_command(command)

    return app


if __name__ == "__main__":
    socketio.run(create_app())
