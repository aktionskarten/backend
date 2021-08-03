import re

from functools import wraps
from flask import Blueprint, request, jsonify, abort, redirect,\
                  url_for, make_response, Response, current_app, render_template
from flask_cors import CORS
from werkzeug.security import safe_str_cmp
from geojson import Feature, FeatureCollection
from datetime import datetime, timedelta
from app.models import db, Map, Feature as MapFeature
from app.grid import grid_for_bbox
from app.utils import datetime_fromisoformat

api = Blueprint('API', __name__)
CORS(api)


def auth():
    map_id = request.headers.get('X-Map')
    token = request.headers.get('X-Token')

    if not map_id or not token:
        return False

    obj = Map.get(map_id)
    if not obj or not obj.check_token(token):
        return False

    return True


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not auth():
            abort(401)

        return f(*args, **kwargs)

    return decorated_function


@api.route('/api/maps/<string:map_id>/auth')
def gen_auth_token(map_id):
    secret = request.headers.get('X-Secret', '')
    obj = Map.get(map_id)

    if not obj or not secret:
        abort(400)  # bad request - invalid input

    if not safe_str_cmp(secret, obj.secret):
        abort(401)  # forbidden - secrets do not match

    return jsonify(token=obj.gen_token())


@api.route('/api/maps/')
@api.route('/api/maps')
def maps():
    return jsonify([m.to_dict() for m in Map.all()])


@api.route('/api/maps/', methods=['POST'])
@api.route('/api/maps', methods=['POST'])
def maps_new():
    if ('name' not in request.json):
        abort(400)

    json = request.json
    name = json['name']

    m = Map(name)
    for key in ['name', 'bbox', 'description', 'place', 'attributes', 'published', 'theme']:
        if key in json:
            setattr(m, key, json[key])

    if 'theme' in json and json['theme'] in current_app.config['MAP_RENDERER']:
        m.theme = json['theme']

    if 'datetime' in json:
        m.datetime = datetime_fromisoformat(request.json['datetime'])

    if 'lifespan' in json:
        m.lifespan = timedelta(days=request.json['lifspan'])

    db.session.add(m)
    db.session.commit()

    return make_response(jsonify(m.to_dict(secret_included=True)), 201)


@api.route('/api/maps/<uuid:map_id>/')
@api.route('/api/maps/<uuid:map_id>')
def map_get(map_id):
    m = Map.get(map_id.hex)
    if not m or not (auth() or m.published) or m.outdated:
        abort(404)
    return jsonify(m.to_dict())


@api.route('/api/maps/<string:map_id>/', methods=['PATCH'])
@api.route('/api/maps/<string:map_id>', methods=['PATCH'])
@login_required
def map_edit(map_id):
    m = Map.get(map_id)

    if not m:
        abort(404)

    json = request.json

    for key in ['name', 'bbox', 'description', 'place', 'attributes', 'published']:
        if key in json:
            setattr(m, key, json[key])


    if 'theme' in json and json['theme'] in current_app.config['MAP_RENDERER']:
        m.theme = json['theme']

    if 'datetime' in json:
        m.datetime = datetime_fromisoformat(request.json['datetime'])

    if 'lifespan' in json:
        m.lifespan = timedelta(days=request.json['lifespan'])

    db.session.add(m)
    db.session.commit()

    return jsonify(m.to_dict())


@api.route('/api/maps/<string:map_id>/', methods=['DELETE'])
@api.route('/api/maps/<string:map_id>', methods=['DELETE'])
@login_required
def map_delete(map_id):
    Map.delete(map_id)
    return ('', 204)


@api.route('/api/maps/<string:map_id>/features')
def map_features(map_id):
    m = Map.get(map_id)

    if not m or not (m.published or auth()):
        abort(404)

    features = [f.to_dict() for f in m.features]
    return jsonify(FeatureCollection(features))


@api.route('/api/maps/<string:map_id>/features', methods=['POST'])
@login_required
def map_features_new(map_id):
    m = Map.get(map_id)
    if not m:
        abort(404)

    if not request.json or not Feature(request.json).is_valid:
        abort(400)

    # TODO: strip input data
    feature = MapFeature(request.json)
    m.features.append(feature)
    db.session.add(m)
    db.session.commit()

    return make_response(jsonify(feature.to_dict()), 201)


@api.route('/api/maps/<string:map_id>/features/<int:feature_id>',
           methods=['DELETE'])
@login_required
def map_feature_delete(map_id, feature_id):
    f = MapFeature.get(feature_id)
    if not f:
        abort(404)

    db.session.delete(f)
    db.session.commit()

    return ('', 200)


@api.route('/api/maps/<string:map_id>/features/<int:feature_id>',
           methods=['PUT', 'PATCH'])
@login_required
def map_feature_edit(map_id, feature_id):
    f = MapFeature.get(feature_id)
    if not f:
        abort(404)

    if not request.json or not Feature(request.json).is_valid:
        abort(400)

    if 'properties' in request.json:
        props = request.json['properties']
        if 'iconColor' in props:
            # ensure that we deal with hex values (not rgb(r,g,b))
            if props['iconColor'].startswith('rgb'):
                rgb = re.findall(r'\d+', props['iconColor'])
                iconColor = ''.join([('%02x' % int(x)) for x in rgb])
                props['iconColor'] = '#' + iconColor
        f.style = props

    if 'geometry' in request.json:
        f.geo = request.json['geometry']

    db.session.add(f)
    db.session.commit()

    return jsonify(f.to_dict())


@api.route('/api/grid/<string:bbox>')
def grid_get(bbox):
    cells = {
        '': [5, 5],
        'landscape': [5, 3],
        'portrait': [3, 5],
    }
    bbox = list(map(float, bbox.split(',')))
    orientation = orientation_for_bbox(*bbox)
    return grid_for_bbox(*bbox, *cells[orientation])


@api.route('/api/maps/<string:map_id>/grid')
def map_get_grid(map_id):
    m = Map.get(map_id)
    if not m or not (m.published or auth()):
        abort(404)
    return jsonify(m.grid)


@api.route('/api/maps/<string:map_id>/geojson')
def map_export_geojson(map_id):
    m = Map.get(map_id)
    if not m or not (m.published or auth()):
        abort(404)
    features = [f.to_dict() for f in m.features]
    return jsonify(FeatureCollection(features, properties=m.to_dict(False)))
