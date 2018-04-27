import re

from functools import wraps
from flask import Blueprint, request, jsonify, abort, redirect, url_for, make_response
from flask_cors import CORS
from werkzeug.security import safe_str_cmp
from models import db, Map, Feature
from grid import Grid
from geojson import FeatureCollection
from datetime import datetime


api = Blueprint('API', __name__)
CORS(api)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):

        print(request.headers)
        if 'X-Map' not in request.headers or 'X-Token' not in request.headers:
            abort(401)

        map_id = request.headers.get('X-Map').encode()
        token = request.headers.get('X-Token').encode()

        if not map_id or not token:
            abort(400)

        obj = Map.get(map_id)
        if not obj or not obj.check_token(token):
            abort(401)

        return f(*args, **kwargs)

    return decorated_function


@api.route('/api/maps/<string:map_id>/auth')
def auth(map_id):
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
    print(request.json)
    if ('name' not in request.json):
        abort(400)

    name = request.json['name']

    m = Map.get(name)
    if (m):
        return make_response(jsonify(error='Map already exists'), 400)

    m = Map(name)

    for key in ['name', 'bbox', 'description', 'place', 'attributes']:
        if key in request.json and request.json[key]:
            setattr(m, key, request.json[key])

    if 'date' in request.json and 'time' in request.json:
        date_str = "{} {}".format(request.json['date'], request.json['time'])
        m.datetime = datetime.strptime(date_str, '%Y-%m-%d %H:%M')

    db.session.add(m)
    db.session.commit()

    return make_response(jsonify(m.to_dict(secret_included=True)), 201)


@api.route('/api/maps/<string:map_id>/')
@api.route('/api/maps/<string:map_id>')
def map_get(map_id):
    m = Map.get(map_id)
    if not m:
        abort(404)
    return jsonify(m.to_dict())


@api.route('/api/maps/<string:map_id>/', methods=['PATCH'])
@api.route('/api/maps/<string:map_id>', methods=['PATCH'])
@login_required
def map_edit(map_id):
    m = Map.get(map_id)

    if not m:
        abort(404)

    print(request.json)
    for key in ['name', 'bbox', 'description', 'place', 'attributes']:
        if key in request.json and request.json[key]:
                setattr(m, key, request.json[key])

    if 'date' in request.json and 'time' in request.json:
        date_str = "{} {}".format(request.json['date'], request.json['time'])
        m.datetime = datetime.strptime(date_str, '%Y-%m-%d %H:%M')

    db.session.add(m)
    db.session.commit()

    return jsonify(m.to_dict())


@api.route('/api/maps/<string:map_id>/', methods=['DELETE'])
@api.route('/api/maps/<string:map_id>', methods=['DELETE'])
def map_delete(map_id):
    Map.delete(map_id)
    return ('', 204)


@api.route('/api/maps/<string:map_id>/features')
def map_features(map_id):
    m = Map.get(map_id)

    if not m:
        abort(404)

    features = [f.to_dict() for f in m.features]
    return jsonify(FeatureCollection(features))


@api.route('/api/maps/<string:map_id>/features', methods=['POST'])
@login_required
def map_features_new(map_id):
    m = Map.get(map_id)
    if not m:
        abort(404)

    if not request.json:
        abort(400)

    feature = Feature(request.json)
    m.features.append(feature)
    db.session.add(m)
    db.session.commit()
    return make_response(jsonify(feature.to_dict()), 201)


@api.route('/api/maps/<string:map_id>/features/<int:feature_id>',
           methods=['DELETE'])
@login_required
def map_feature_delete(map_id, feature_id):
    f = Feature.get(feature_id)
    if not f:
        abort(404)

    if request.method == 'DELETE':
        db.session.delete(f)
        db.session.commit()
        return ('', 200)


@api.route('/api/maps/<string:map_id>/features/<int:feature_id>',
           methods=['PUT', 'PATCH'])
@login_required
def map_feature_edit(map_id, feature_id):
    f = Feature.get(feature_id)
    if not f:
        abort(404)

    if not request.json:
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
    return jsonify(Grid(*map(float, bbox.split(','))).generate())


@api.route('/api/maps/<string:map_id>/grid')
def map_get_grid(map_id):
    m = Map.get(map_id)
    if not m:
        abort(404)
    return jsonify(m.grid)
