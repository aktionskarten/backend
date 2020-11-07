import mimetypes

from os import path
from flask import current_app
from hashlib import sha256
from math import floor, log10
from haversine import haversine, Unit

from datetime import datetime
try:
    from backports.datetime_fromisoformat import MonkeyPatch
    MonkeyPatch.patch_fromisoformat()
except ImportError:
    pass

class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code

class UnsupportedFileType(InvalidUsage):
    pass


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


def file_exists(file_info):
    file_name = path.join(current_app.static_folder, file_info['path'])
    return path.exists(file_name)

def get_img_type(file_type):
    if ':' in file_type:
        img_type, size = file_type.split(':')
        scale = 0.75
        if size == 'large':
            scale = 1
        elif size == 'small':
            scale = 0.5
        return (img_type, scale, size)
    return (file_type,)


def get_file_info(map_id, version, file_type):
    file_info = {
        'map_id': map_id,
        'file_type': file_type,
        'version': version
    }

    dirname = sha256(map_id.encode()).hexdigest()
    file_info['dir'] = path.join('maps', dirname)

    extension, *args = get_img_type(file_type)
    file_info['extension'] = extension

    try:
        file_info['mimetype'] = mimetypes.types_map['.' + extension]
    except KeyError:
        raise UnsupportedFileType('unsuported file type')

    suffix = ''
    if len(args) > 0:
        scale, size = args
        file_info['scale'] = scale
        file_info['size'] = scale
        suffix = '_' + size

    file_info['suffix'] = suffix + '.' + extension
    file_info['name'] = version + file_info['suffix']
    file_info['path'] = path.join(file_info['dir'], file_info['name'])

    return file_info


def datetime_fromisoformat(isoformat):
    return datetime.fromisoformat(isoformat)


def nearest_n(x):
    if x < 50:
        return 50
    n = 5*(10**floor(log10(x/5.)))
    return round(x/float(n))*n


def orientation_for_bbox(minx, miny, maxx, maxy):
        width = haversine((miny, minx), (miny,maxx), Unit.METERS)
        height = haversine((miny, minx), (maxy,minx), Unit.METERS)
        ratio = height/width

        if abs(ratio - 1240/1754) < 0.1:
            return 'landscape'
        elif abs(ratio - 1754/1240) < 0.1:
            return 'portrait'
        return ''
