from flask import current_app
from flask.cli import with_appcontext
from dotenv import load_dotenv
from functools import wraps
from os import environ


def try_with_appcontext(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            load_dotenv('.flaskenv')
            return with_appcontext(f)(*args, **kwargs)
        except:
            return f(*args, **kwargs)
    return decorated


@try_with_appcontext
def get_default_option(name):
    if current_app:
        return current_app.config[name]
    return None


def default_option(*args, **kwargs):
    return lambda: get_default_option(*args, **kwargs)
