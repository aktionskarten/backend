import re

from flask import Blueprint, request, jsonify, abort, redirect, url_for
from flask_cors import CORS
from werkzeug.security import safe_str_cmp
from models import db, Map, Feature
from grid import Grid
from geojson import FeatureCollection
from datetime import datetime


api = Blueprint('API', __name__)
CORS(api)


@api.route('/api/maps/<string:map_id>/auth')
def auth(map_id):
    secret = request.headers.get('X-Secret', '')
    obj = Map.get(map_id)

    if not obj or not secret:
        abort(400)  # bad request - invalid input

    if not safe_str_cmp(secret, obj.secret):
        abort(401)  # forbidden - secrets do not match

    return jsonify(token=obj.gen_token())


def verify_token():
    map_id = request.headers.get('X-Map').encode()
    token = request.headers.get('X-Token').encode()

    if not map_id or not token:
        abort(400)

    obj = Map.get(map_id)
    if not obj or not obj.check_token(token):
        abort(401)


@api.route('/api/maps/', methods=['GET', 'POST'])
@api.route('/api/maps', methods=['GET', 'POST'])
def maps():
    if request.method == 'POST':
        if ('name' not in request.json):
            abort(400)

        name = request.json['name']

        m = Map.get(name)
        if (m):
            abort(400)

        m = Map(name)

        for key in ['name', 'bbox', 'description', 'place']:
            if key in request.json:
                setattr(m, key, request.json[key])

        if 'date' in request.json and 'time' in request.json:
            date_str = "{} {}".format(request.json['date'], request.json['time'])
            m.datetime = datetime.strptime(date_str, '%Y-%m-%d %H:%M')

        if 'keys' in request.json and 'values' in request.json:
            keys = request.json['keys']
            values = request.json['values']
            if len(keys) == len(values):
                m.attributes = dict(zip(keys, values))

        db.session.add(m)
        db.session.commit()

        return redirect(url_for('.map_get', code=303, map_id=m.slug))

    return jsonify([m.to_dict() for m in Map.all()])


@api.route('/api/maps/<string:map_id>/', methods=['GET', 'PATCH'])
@api.route('/api/maps/<string:map_id>', methods=['GET', 'PATCH'])
def map_get(map_id):
    m = Map.get(map_id)

    if not m:
        abort(404)

    if request.method == 'PATCH':
        for key in ['name', 'bbox', 'description', 'place']:
            if key in request.json:
                setattr(m, key, request.json[key])

        if 'date' in request.json and 'time' in request.json:
            date_str = "{} {}".format(request.json['date'], request.json['time'])
            m.datetime = datetime.strptime(date_str, '%Y-%m-%d %H:%M')

        if 'keys' in request.json and 'values' in request.json:
            keys = request.json['keys']
            values = request.json['values']
            if len(keys) == len(values):
                m.attributes = dict(zip(keys, values))
        else:
            m.attributes = {}

        db.session.add(m)
        db.session.commit()

    return jsonify(m.to_dict())


@api.route('/api/maps/<string:map_id>/features', methods=['GET', 'POST'])
def map_features(map_id):
    m = Map.get(map_id)
    if not m:
        abort(404)

    if request.method == 'POST':
        if not request.json:
            abort(400)

        feature = Feature(request.json)
        m.features.append(feature)
        db.session.add(m)
        db.session.commit()
        return jsonify(feature.to_dict())

    features = [f.to_dict() for f in m.features]
    return jsonify(FeatureCollection(features))


@api.route('/api/maps/<string:map_id>/features/<int:feature_id>',
           methods=['PUT', 'PATCH', 'DELETE'])
def map_feature_get(map_id, feature_id):
    f = Feature.get(feature_id)
    if not f:
        abort(404)

    if request.method == 'DELETE':
        db.session.delete(f)
        db.session.commit()
        return ('', 200)

    if not request.json:
        abort(400)

    # it's PUT or PATCH now
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
