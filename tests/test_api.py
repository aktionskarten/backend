import datetime
import pytz
from tests.fixtures import *
from tests.utils import db_reset
from json import dumps as json_dump
from geojson import Feature as GeoFeature, Point as GeoPoint
from app.models import Map, Feature, db as _db

def setup_function(function):
    db_reset()

def _count_maps(app):
    with app.test_client() as client:
        resp = client.get('/api/maps')
        assert(resp.status_code == 200)
        assert(isinstance(resp.json, list))
        return len(resp.json)

def _get_map(app, uuid, token=None):
    with app.test_client() as client:
        url = '/api/maps/{}'.format(uuid)
        if token:
            headers = {'X-MAP': uuid, 'X-TOKEN': token}
            return client.get(url, headers=headers)
        return client.get(url)

def _login(app, uuid, secret):
    token = None
    with app.test_client() as client:
        url = '/api/maps/{}/auth'.format(uuid)
        headers = {'X-SECRET': secret}
        resp = client.get(url, headers=headers)
        token = resp.json['token']
    assert(token)
    return token

def _create_map(app, data):
    uuid = None
    secret = None
    token = None

    with app.test_client() as client:
        url = '/api/maps'
        resp = client.post(url, json=data)

        assert(resp.status_code == 201)

        for k, v in data.items():
            assert(resp.json[k] == v)

        uuid = resp.json['id']
        secret = resp.json['secret']

    # auth
    token = _login(app, uuid, secret)

    return (uuid, token)


def _update_map(app, uuid, token, data):
    with app.test_client() as client:
        url = '/api/maps/{}'.format(uuid)
        headers = {'X-MAP': uuid, 'X-TOKEN': token}
        return client.patch(url, json=data, headers=headers)


def test_maps_list(app, db):
    assert(len(Map.all()) == 0)
    assert(_count_maps(app) == 0)

    db.session.add(Map('foo-list', published=True, bbox=[1, 1, 1, 1]))
    db.session.commit()

    assert(len(Map.all()) == 1)
    assert(_count_maps(app) == 1)


def test_maps_new_private(app, db):
    name = 'foo-new-private'
    uuid, token = _create_map(app, {'name': name})

    m = Map.get(uuid)
    assert(m)
    assert(m.name == name)
    assert(m.check_token(token))
    assert(not m.published)
    assert(not m.outdated)

    # FORBIDDEN is 404 not 403 (to prevent leak of sensitive data)
    resp = _get_map(app, uuid)
    assert(resp.status_code == 404)

    for t in ['WRONG_TOKEN', 'undefined', 'NULL', None, [], {}]:
        resp = _get_map(app, uuid, t)
        assert(resp.status_code == 404)

    resp = _get_map(app, uuid, token)
    assert(resp.status_code == 200)


def test_maps_new_public(app, db):
    m = Map('foo-new-public', bbox=[1, 1, 1, 1])
    db.session.add(m)
    db.session.commit()

    assert(not m.published)

    m.published = True
    db.session.add(m)
    db.session.commit()

    resp = _get_map(app, m.uuid)
    assert(resp.status_code == 200)

    resp = _get_map(app, m.uuid, m.gen_token())
    assert(resp.status_code == 200)

def test_maps_new_datetime(app, db):
    name = 'foo-new-private'
    now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
    uuid, token = _create_map(app, {'name': name, 'datetime': now.isoformat()})

    m = Map.get(uuid)
    assert(m)
    assert(m.datetime == now)
    assert(not m.outdated)

    resp = _get_map(app, m.uuid, token)
    assert(resp.status_code == 200)
    assert(resp.json['datetime'] == now.isoformat())


def test_map_delete_private(app, db):
    m = Map('foo', bbox=[1, 1, 1, 1])
    db.session.add(m)
    db.session.commit()

    token = m.gen_token()
    resp = _get_map(app, m.uuid, token)
    assert(resp.status_code == 200)

    with app.test_client() as client:
        point = GeoFeature(geometry=GeoPoint([1, 1]))
        f = Feature(point)
        m.features.append(f)
        db.session.add(m)
        db.session.commit()

        url = '/api/maps/{}'.format(m.uuid)
        resp = client.delete(url)
        assert(resp.status_code == 401) # TODO: should be 404 for private maps

        headers = {'X-MAP': m.uuid, 'X-TOKEN': token}
        resp = client.delete(url, headers=headers)
        assert(resp.status_code == 204)

    assert(not Map.get(m.uuid))
    resp = _get_map(app, m.uuid, token)
    assert(resp.status_code == 404)


def test_map_lifespan(app, db):
    now = datetime.datetime.utcnow()
    m = Map('foo-lifespan', datetime=now, published=True, bbox=[1, 1, 1, 1])
    db.session.add(m)
    db.session.commit()
    assert(not m.outdated)

    token = m.gen_token()
    resp = _get_map(app, m.uuid, token)
    assert(resp.status_code == 200)

    m.datetime = now - datetime.timedelta(days=31)
    db.session.add(m)
    db.session.commit()

    assert(m.outdated)

    resp = _get_map(app, m.uuid, token)
    assert(resp.status_code == 404)


def test_feature(app, db):
    assert(_count_maps(app) == 0)
    name = 'foo'
    uuid, token = _create_map(app, {'name': name, 'bbox': [1,1,1,1]})
    assert(_count_maps(app) == 0)

    # add feature
    with app.test_client() as client:
        url = '/api/maps/{}/features'.format(uuid)
        json = GeoFeature(geometry=GeoPoint([1,1]))
        headers = {'X-MAP': uuid, 'X-TOKEN': token}
        resp = client.post(url, json=json, headers=headers)
        assert(resp.status_code == 201)

    resp = _update_map(app, uuid, token, {'published':True})
    assert(resp.json['published'])

    assert(_count_maps(app) == 1)


def test_live(app, db):
    with app.test_client() as client:
        m = Map('foo', bbox=[1, 1, 1, 1])
        db.session.add(m)
        db.session.commit()
        uuid = m.uuid.hex

        from app.live import socketio
        socketio_client = socketio.test_client(app, flask_test_client=client)
        socketio_client.emit('join', uuid)
        assert socketio_client.is_connected()

        r = socketio_client.get_received()
        assert(len(r) == 1)
        assert(r[0]['name'] == 'message')
        assert(r[0]['args'] == 'user joined')

        m.name = 'bar'
        db.session.add(m)
        db.session.commit()

        r = socketio_client.get_received()
        assert(len(r) == 1)
        assert(r[0]['name'] == 'map-updated')

        point = GeoFeature(geometry=GeoPoint([1, 1]))
        f = Feature(point)
        db.session.add(m)
        m.features.append(f)
        db.session.commit()

        r = socketio_client.get_received()
        assert(len(r) == 1)
        assert(r[0]['name'] == 'feature-created')

        f.style = {'color': 'red'}
        db.session.add(f)
        db.session.commit()

        r = socketio_client.get_received()
        assert(len(r) == 1)
        assert(r[0]['name'] == 'feature-updated')

        db.session.delete(m)
        db.session.commit()

        r = socketio_client.get_received()
        assert(len(r) == 2)
        assert(r[0]['name'] == 'map-deleted')
        assert(r[1]['name'] == 'feature-deleted')
