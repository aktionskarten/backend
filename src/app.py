from flask import Flask
from os import environ

from routes import renderer


def create_app():
    app = Flask(__name__)

    app.config.from_object('settings_default')
    if 'SETTINGS' in environ:
        app.config.from_envvar('SETTINGS')

    for blueprint in [renderer]:
        app.register_blueprint(blueprint)

    return app


app = create_app()


if __name__ == "__main__":
    app.run()
