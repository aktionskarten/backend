from os import path

class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code


def get_xml(filename):
    path_abs = path.join(path.dirname(__file__), "..", filename)
    with open(path_abs, 'r') as f:
        return f.read()


def strip(feature):
    props = feature['properties']
    # dashArray="1" results in Leaflet as a straight line but in mapnik as
    # strokes. In mapnik to render a straight line, you don't provide any
    # dashArray. To have the same render result, delete it here.
    if 'dashArray' in props and props['dashArray'] == "1":
        del props['dashArray']

    if 'iconSize' in props:
        props['scale'] = (20/150) * (props['iconSize'][0]/20) * 2

    return feature
