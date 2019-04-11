import json
import os
import mimetypes

from flask import Blueprint, request, jsonify, send_file, current_app
from render import render_map
from utils import InvalidUsage
from hashlib import sha256


renderer = Blueprint('Renderer', __name__)


def _request_args_restricted(key, whitelist):
    value = request.args.get(key, default=whitelist[0], type=str)
    if value not in whitelist:
        raise InvalidUsage("unsupported " + key + " type")
    return value


def _parse_request():
    if not request.is_json:
        raise InvalidUsage("invalid request")

    content = request.get_json()
    if 'name' not in content:
        raise InvalidUsage("no name given")

    file_type = _request_args_restricted('file_type', ['png', 'pdf', 'svg'])
    return file_type, content


@renderer.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error=error.message)
    response.status_code = error.status_code
    return response


def send_map(content, extension, scale=1, suffix=None):
    if ('grid' not in content or 'features' not in content):
        raise InvalidUsage('invalid data')

    dirname = sha256(content['name'].encode()).hexdigest()
    mimetype = mimetypes.types_map['.' + extension]

    raw = json.dumps(content, separators=(',', ':'), sort_keys=True)
    map_id = sha256(raw.encode()).hexdigest()

    if suffix:
        filename = '{}_{}.{}'.format(map_id, suffix, extension)
    else:
        filename = '{}.{}'.format(map_id, extension)

    static_path = current_app.static_folder
    path = os.path.join(static_path, 'maps', dirname, filename)

    # for development you can disable render caching of maps
    config = current_app.config
    if ('NO_MAP_CACHE' in config and config['NO_MAP_CACHE']) or \
       not os.path.exists(path):
        basename = os.path.dirname(path)
        if not os.path.exists(basename):
            os.makedirs(basename)
        with open(path, 'wb') as f:
            f.write(render_map(content, mimetype, scale).read())

    return send_file(path,
                     attachment_filename=filename,
                     mimetype=mimetype, cache_timeout=0)

@renderer.route('/render', methods=['POST'])
def render():
    file_type, content = _parse_request()
    if file_type == 'png':
        scale = 0.75
        size = _request_args_restricted('size', ['medium', 'small', 'large'])
        if size == 'large':
            scale = 1
        elif size == 'small':
            scale = 0.5

    print("file_type", file_type)
    return send_map(content, file_type, scale, size)
