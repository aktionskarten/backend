import json
import os
import mimetypes

from hashlib import sha256
from flask import current_app, has_app_context
from app.render import MapRenderer
from app.utils import InvalidUsage

class UnsupportedFileType(Exception):
    pass

def _get_img_type(file_type):
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
    file_info['dir'] = os.path.join('maps', dirname)

    extension, *args = _get_img_type(file_type)
    file_info['extension'] = extension

    try:
        file_info['mimetype'] = mimetypes.types_map['.' + extension]
    except KeyError:
        raise UnsupportedFileType

    suffix = ''
    if len(args) > 0:
        scale, size = args
        file_info['scale'] = scale
        file_info['size'] = scale
        suffix = '_' + size

    file_info['suffix'] = suffix + '.' + extension
    file_info['name'] = version + file_info['suffix']
    file_info['path'] = os.path.join(file_info['dir'], file_info['name'])

    return file_info


def file_exists(file_info):
    file_name = os.path.join(current_app.static_folder, file_info['path'])
    return os.path.exists(file_name)


def get_version(data):
    raw = json.dumps(data, separators=(',', ':'), sort_keys=True)
    return sha256(raw.encode()).hexdigest()


def render_map(data, file_type, force=False):
    if not has_app_context():
        from app import app
        app.app_context().push()

    if ('grid' not in data or 'features' not in data):
        raise InvalidUsage('invalid data')

    map_id = data['id']
    version = get_version(data)
    file_info = get_file_info(map_id, version, file_type)

    # if map already is rendered, do nothing
    if not force and file_exists(file_info):
        return

    static_dir = current_app.static_folder
    map_dir = os.path.join(static_dir, file_info['dir'])
    if not os.path.exists(map_dir):
        os.makedirs(map_dir)

    # render map and save as file
    path = os.path.join(static_dir, file_info['path'])
    with open(path, 'wb') as f:
        m = MapRenderer(data)
        f.write(m.render(file_info['mimetype']).read())

    # update latest symlink to this
    symlink_name = 'LATEST'+file_info['suffix']
    path_latest = os.path.join(static_dir, file_info['dir'], symlink_name)
    try:
        os.symlink(path, path_latest)
    except FileExistsError:
        os.unlink(path_latest)
        os.symlink(path, path_latest)
