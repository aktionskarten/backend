class DefaultConfig(object):
    """Base config, uses staging database server."""
    DEBUG = False
    TESTING = False

    MAPNIK_OSM_XML = "libs/openstreetmap-carto/style.xml"
    SECRET_KEY = "GENERATE SUPER SECRET KEY"

    DB_HOST = 'localhost'
    DB_USER = 'maps'
    DB_PASS = 'maps'
    DB_NAME = 'maps'

    OSM_DB_HOST = 'localhost'
    OSM_DB_USER = 'maps'
    OSM_DB_PASS = 'maps'
    OSM_DB_NAME = 'osm'

    REDIS_HOST = 'localhost'

    # needed for events
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    DEJAVU_FONT_PATH = '/usr/share/fonts/TTF/DejaVuSansCondensed.ttf'

    @property
    def SQLALCHEMY_DATABASE_URI(self):
        return 'postgres://{}:{}@{}/{}'.format(self.DB_USER, self.DB_PASS,
                                               self.DB_HOST, self.DB_NAME)

class DevelopmentConfig(DefaultConfig):
    DEBUG = True

class TestingConfig(DevelopmentConfig):
    TESTING = True
    DB_HOST = 'db'
    OSM_DB_HOST = 'db'
    REDIS_HOST = 'redis'
