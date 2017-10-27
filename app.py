import flask_sqlalchemy
import models
import render
import json

from flask import Flask, abort, jsonify, request, send_file
from werkzeug.security import safe_str_cmp
from geojson import FeatureCollection
from flask_cors import CORS


app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:@localhost/test_geoalchemy2"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = flask_sqlalchemy.SQLAlchemy(app)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})


@app.route('/api/maps/<int:map_id>/auth')
def auth(map_id):
    secret = request.headers.get('X-Secret', '')
    obj = db.session.query(models.Map).get(map_id)

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

    obj = db.session.query(models.Map).get(map_id)
    if not obj or not obj.check_token(token):
        abort(401)


@app.route('/api/maps/', methods=['GET', 'POST'])
@app.route('/api/maps', methods=['GET', 'POST'])
def maps():
    if request.method == 'POST':
        if ('name' not in request.json or 'bbox' not in request.json):
            abort(400)

        m = models.Map(request.json['name'], request.json['bbox'])
        db.session.add(m)
        db.session.commit()
        return jsonify(m.to_dict())

    return jsonify([m.to_dict() for m in db.session.query(models.Map).all()])


@app.route('/api/maps/<int:map_id>/')
@app.route('/api/maps/<int:map_id>')
def map_get(map_id):
    m = db.session.query(models.Map).get(map_id)
    return jsonify(m.to_dict())


@app.route('/api/maps/<int:map_id>/features', methods=['GET', 'POST'])
def map_features(map_id):
    m = db.session.query(models.Map).get(map_id)
    if not m:
        abort(404)

    if request.method == 'POST':
        if not request.json:
            abort(400)

        feature = models.Feature(request.json)
        m.features.append(feature)
        db.session.add(m)
        db.session.commit()
        return jsonify(feature.to_dict())

    features = [f.to_dict() for f in m.features]
    return jsonify(FeatureCollection(features))


@app.route('/api/maps/<int:map_id>/features/<int:feature_id>', methods=['PUT', 'PATCH', 'DELETE'])
def map_feature_get(map_id, feature_id):
    f = db.session.query(models.Feature).get(feature_id)
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
            f.style = request.json['style']
        if 'geo' in request.json:
            f.geo = request.json['geo']
    else:
        f.geo = request.json

    db.session.add(f)
    db.session.commit()
    return jsonify(f.to_dict())


@app.route('/api/maps/<int:map_id>/grid')
def map_get_grid(map_id):
    m = db.session.query(models.Map).get(map_id)
    return jsonify(m.grid)


@app.route('/api/maps/<int:map_id>/export/svg')
def map_export_svg(map_id):
    m = db.session.query(models.Map).get(map_id)
    mimetype = 'image/svg+xml'
    return send_file(render.render_map(m, mimetype),
                     attachment_filename='map.svg',
                     mimetype=mimetype)


@app.route('/api/maps/<int:map_id>/export/pdf')
def map_export_pdf(map_id):
    m = db.session.query(models.Map).get(map_id)
    mimetype = 'application/pdf'
    return send_file(render.render_map(m, mimetype),
                     attachment_filename='map.pdf',
                     mimetype=mimetype)


@app.route('/api/maps/<int:map_id>/export/png')
def map_export_png(map_id):
    m = db.session.query(models.Map).get(map_id)
    mimetype = 'image/png'
    return send_file(render.render_map(m, mimetype),
                     attachment_filename='map.png',
                     mimetype=mimetype)


if __name__ == "__main__":
    app.run()

