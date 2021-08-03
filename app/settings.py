import os
from dotenv import load_dotenv

load_dotenv()

def get_env_variable(name):
    try:
        return os.environ[name]
    except KeyError:
        message = "Expected env variable '{}' not set.".format(name)
        raise Exception(message)

class DefaultConfig(object):
    """Base config, uses staging database server."""
    DEBUG = False
    TESTING = False

    SECRET_KEY = "GENERATE SUPER SECRET KEY"

    DB_HOST = 'localhost'
    DB_USER = 'maps'
    DB_PASS = 'maps'
    DB_NAME = 'maps'

    REDIS_HOST = 'localhost'

    TILESERVER_HOST = 'localhost:8080'

    # needed for events
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    DEJAVU_FONT_PATH = '/usr/share/fonts/TTF/DejaVuSansCondensed.ttf'

    # url encoded <bbox>,<width>,<height>
    @property
    def MAP_RENDERER(self):
        base_url = 'http://{}/styles/'.format(self.TILESERVER_HOST)
        return {
            'basic': base_url + 'basic-preview/static/{}/{}x{}.png',
            'bright': base_url + 'osm-bright/static/{}/{}x{}.png',
            'positron': base_url + 'positron/static/{}/{}x{}.png'
            #'liberty': 'http://localhost:8080/styles/osm-liberty/static/{}/{}x{}.png',
            #'maptiler-toner': 'http://localhost:8080/styles/maptiler-toner/static/{}/{}x{}.png'
        }

    @property
    def SQLALCHEMY_DATABASE_URI(self):
        return 'postgresql://{}:{}@{}/{}'.format(self.DB_USER, self.DB_PASS,
                                               self.DB_HOST, self.DB_NAME)

class DevelopmentConfig(DefaultConfig):
    DEBUG = True

class TestingConfig(DevelopmentConfig):
    TESTING = True
    DB_HOST = '127.0.0.1'  # db
    DB_USER = 'postgres'
    DB_PASS = 'postgres'
    DB_NAME = 'test'
    #REDIS_HOST = 'redis'

class ProductionConfig(DefaultConfig):
    @property
    def DB_HOST(self):
        return get_env_variable("POSTGRES_HOST")

    @property
    def DB_USER(self):
        return get_env_variable("POSTGRES_USER")

    @property
    def DB_PASS(self):
        return get_env_variable("POSTGRES_PASSWORD")

    @property
    def DB_NAME(self):
        return get_env_variable("POSTGRES_DB")

    @property
    def REDIS_HOST(self):
        return get_env_variable("REDIS_HOS")

    @property
    def TILESERVER_HOST(self):
        return get_env_variable("TILESERVER_HOST")
