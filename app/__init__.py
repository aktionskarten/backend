from flask import Flask
from os import environ
from flask_migrate import Migrate
import rq
from redis import Redis
from werkzeug.utils import import_string

from app.live import socketio
from app.api import api
from app.test import test
from app.models import db
from app.render import renderer
from app.settings import DefaultConfig
from app.cli import pymapnik_cli, osm_cli, postgres_cli, clear_maps,\
                    create_tables, gen_markers, remove_outdated_maps

from uuid import UUID
from werkzeug.routing import BaseConverter, ValidationError
class UUIDConverter(BaseConverter):
    def to_python(self, value):
        try:
            return UUID(value)
        except:
            raise ValidationError()

    def to_url(self, uuid):
        return uuid.hex

def create_app():
    app = Flask(__name__)

    app.config.from_object(DefaultConfig())
    if app.env == 'testing':
        cfg = import_string('app.settings.TestingConfig')()
        app.config.from_object(cfg)
        print("it's testing")
    else:
        print("it's not testing")

    db.init_app(app)
    Migrate(app, db)
    socketio.init_app(app, cors_allowed_origins="*")

    app.task_queue = rq.Queue(connection=Redis(app.config['REDIS_HOST']))
    app.url_map.converters['uuid'] = UUIDConverter

    blueprints = [renderer, api]
    if app.config['TESTING']:
        blueprints.append(test)
        with app.app_context():
            db.create_all()

    for blueprint in blueprints:
        app.register_blueprint(blueprint)

    cmds = [clear_maps, create_tables, gen_markers, remove_outdated_maps]
    for command in [pymapnik_cli, osm_cli, postgres_cli] + cmds:
        app.cli.add_command(command)

    return app


if __name__ == "__main__":
    socketio.run(create_app())
