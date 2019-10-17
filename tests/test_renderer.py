from imghdr import what as img_what
from PyPDF2 import PdfFileReader
from io import BytesIO
from xml.etree import cElementTree as et
from tests.fixtures import *
from tests.utils import db_reset


def setup_function(function):
    db_reset()


def test_invalid_map(app):
    with app.test_client() as client:
        url = '/api/maps/INVALID/render/png'
        resp = client.get(url)
        assert(resp.status_code == 404)


def test_invalid_file_type(app, uuid):
    with app.test_client() as client:
        url = '/api/maps/{}/render/INVALID_FILE_TYPE'.format(uuid)
        resp = client.get(url)
        assert(resp.status_code == 400)


def test_invalid_status_by_job(app, uuid):
    with app.test_client() as client:
        url = '/api/maps/{}.png:small/INVALID/status'.format(uuid)
        resp = client.get(url)
        assert(resp.status_code == 404)


def test_png(app, uuid, worker):
    with app.test_client() as client:
        url = '/api/maps/{}/render/png:small'.format(uuid)
        headers = {'Accept': 'application/json'}
        resp = client.get(url, headers=headers)
        assert(resp.status_code == 202)
        assert resp.json['status'] == 'queued'
        assert resp.json['file_type'] == 'png:small'
        job_id = resp.json['job_id']
        version = resp.json['version']

    # Check if render of same data is not done twice (same job_id)
    with app.test_client() as client:
        url = '/api/maps/{}/render/png:small'.format(uuid)
        headers = {'Accept': 'application/json'}
        resp = client.get(url, headers=headers)
        assert(resp.status_code == 202)
        assert(resp.json['job_id'] == job_id)

    # do work (as we don't have a worker process)
    worker.work(burst=True)

    # check if finished
    with app.test_client() as client:
        url = '/api/maps/{}.png:small/{}/status'.format(uuid, version)
        headers = {'Accept': 'application/json'}
        resp = client.get(url, headers=headers)
        assert(resp.json['status'] == 'finished')

    # Download without version
    with app.test_client() as client:
        url = '/maps/{}.png:small'.format(uuid)
        resp = client.get(url)
        assert resp.status_code == 200
        assert len(resp.data) > 0
        assert img_what(None, resp.data) == 'png'

    # Download with version
    with app.test_client() as client:
        url = '/maps/{}.png:small/{}'.format(uuid, version)
        resp = client.get(url)
        assert resp.status_code == 200


def test_pdf(app, uuid, worker):
    with app.test_client() as client:
        url = '/api/maps/{}/render/pdf'.format(uuid)
        headers = {'Accept': 'application/json'}
        resp = client.get(url, headers=headers)
        assert(resp.status_code == 202)
        assert resp.json['status'] == 'queued'
        assert resp.json['file_type'] == 'pdf'
        version = resp.json['version']

    # do work (as we don't have a worker process)
    worker.work(burst=True)

    # Download without version
    with app.test_client() as client:
        url = '/maps/{}.pdf'.format(uuid)
        resp = client.get(url)
        assert resp.status_code == 200
        assert len(resp.data) > 0
        with BytesIO(resp.data) as f:
            PdfFileReader(f)

    # Download with version
    with app.test_client() as client:
        url = '/maps/{}.pdf/{}'.format(uuid, version)
        resp = client.get(url)
        assert resp.status_code == 200


def test_svg(app, uuid, worker):
    with app.test_client() as client:
        url = '/api/maps/{}/render/svg'.format(uuid)
        headers = {'Accept': 'application/json'}
        resp = client.get(url, headers=headers)
        assert(resp.status_code == 202)
        assert resp.json['status'] == 'queued'
        assert resp.json['file_type'] == 'svg'
        version = resp.json['version']

    # do work (as we don't have a worker process)
    worker.work(burst=True)

    # Download without version
    with app.test_client() as client:
        url = '/maps/{}.svg'.format(uuid)
        resp = client.get(url)
        assert resp.status_code == 200
        assert len(resp.data) > 0
        assert et.fromstring(resp.data).tag == '{http://www.w3.org/2000/svg}svg'

    # Download with version
    with app.test_client() as client:
        url = '/maps/{}.svg/{}'.format(uuid, version)
        resp = client.get(url)
        assert resp.status_code == 200
