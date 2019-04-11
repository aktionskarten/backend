from flask import Blueprint, request, jsonify
from render import send_map
from utils import InvalidUsage


render = Blueprint('Render', __name__)


def _parse_request():
    if not request.is_json:
        raise InvalidUsage("invalid request")

    content = request.get_json()
    if 'name' not in content:
        raise InvalidUsage("no name given")

    return content


@render.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error=error.message)
    response.status_code = error.status_code
    return response


@render.route('/svg', methods=['POST'])
def render_svg():
    return send_map(_parse_request(), 'svg')


@render.route('/pdf', methods=['POST'])
def render_pdf():
    return send_map(_parse_request(), 'pdf')


@render.route('/png', methods=['POST'])
@render.route('/png:<string:size>', methods=['POST'])
def render_png(size='large'):
    if size == 'large':
        scale = 1
    elif size == 'small':
        scale = 0.5
    else:
        size = 'medium'
        scale = 0.75

    return send_map(_parse_request(), 'png', scale, size)
