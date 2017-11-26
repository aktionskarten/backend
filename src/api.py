import re

from flask import Blueprint, request, jsonify, abort
from flask_cors import CORS
from werkzeug.security import safe_str_cmp
from models import db, Map, Feature
from geojson import FeatureCollection


api = Blueprint('API', __name__)
CORS(api)


@api.route('/api/maps/<string:map_id>/auth')
def auth(map_id):
    secret = request.headers.get('X-Secret', '')
    obj = db.session.query(Map).get(map_id)

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

    obj = db.session.query(Map).get(map_id)
    if not obj or not obj.check_token(token):
        abort(401)


@api.route('/api/maps/', methods=['GET', 'POST'])
@api.route('/api/maps', methods=['GET', 'POST'])
def maps():
    if request.method == 'POST':
        if ('bbox' not in request.json):
            abort(400)

        m = Map(request.json['bbox'])
        db.session.add(m)
        db.session.commit()
        return jsonify(m.to_dict())
    return jsonify([m.to_dict() for m in db.session.query(Map).all()])


@api.route('/api/maps/<string:map_id>/')
@api.route('/api/maps/<string:map_id>')
def map_get(map_id):
    m = db.session.query(Map).get(map_id)
    if not m:
        abort(404)
    return jsonify(m.to_dict())


@api.route('/api/maps/<string:map_id>/features', methods=['GET', 'POST'])
def map_features(map_id):
    m = db.session.query(Map).get(map_id)
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
    f = db.session.query(Feature).get(feature_id)
    if not f:
        abort(404)

    if request.method == 'DELETE':
        db.session.delete(f)
        db.session.commit()
        return ('', 200)

    if not request.json:
        abort(400)

    if request.method == 'PATCH':
        if 'style' in request.json:
            style = request.json['style']
            if 'iconColor' in style:
                # ensure that we deal with hex values (not rgb(r,g,b))
                if style['iconColor'].startswith('rgb'):
                    rgb = re.findall(r'\d+', style['iconColor'])
                    iconColor = ''.join([('%02x' % int(x)) for x in rgb])
                    style['iconColor'] = '#' + iconColor
            f.style = style
        if 'geo' in request.json:
            f.geo = request.json['geo']
    else:
        f.geo = request.json

    db.session.add(f)
    db.session.commit()
    return jsonify(f.to_dict())


@api.route('/api/maps/<string:map_id>/grid')
def map_get_grid(map_id):
    m = db.session.query(Map).get(map_id)
    if not m:
        abort(404)
    return jsonify(m.grid)
