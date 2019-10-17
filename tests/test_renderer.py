from time import sleep
from imghdr import what as img_what
from PyPDF2 import PdfFileReader
from io import BytesIO
from xml.etree import cElementTree as et
from tests.fixtures import *
from tests.utils import db_reset


def setup_function(function):
    db_reset()


def test_invalid_map(client):
    url = '/api/maps/INVALID/render/png'
    resp = client.json_get(url)
    assert(resp.status_code == 404)


def test_invalid_file_type(client, uuid):
    url = '/api/maps/{}/render/INVALID_FILE_TYPE'.format(uuid)
    resp = client.json_get(url)
    assert(resp.status_code == 400)


def test_invalid_status_by_job(client, uuid):
    url = '/api/maps/{}/png:small/INVALID/status'.format(uuid)
    resp = client.json_get(url)
    assert(resp.status_code == 404)


def test_png(client, uuid, worker):
    url = '/api/maps/{}/render/png:small'.format(uuid)
    resp = client.json_get(url)
    assert(resp.status_code == 202)
    assert resp.json['status'] == 'queued'
    assert resp.json['file_type'] == 'png:small'
    job_id = resp.json['job_id']
    version = resp.json['version']

    # Check if render of same data is not done twice (same job_id)
    url = '/api/maps/{}/render/png:small'.format(uuid)
    resp = client.json_get(url)
    assert(resp.status_code == 202)
    assert(resp.json['job_id'] == job_id)

    # do work (as we don't have a worker process)
    worker.work(burst=True)
    sleep(0.5)

    # check if finished
    url = '/api/maps/{}/png:small/{}/status'.format(uuid, version)
    resp = client.json_get(url)
    assert(resp.json['status'] == 'finished')

    # Download without version
    url = '/maps/{}/png:small'.format(uuid)
    resp = client.get(url)
    assert resp.status_code == 200
    assert len(resp.data) > 0
    assert img_what(None, resp.data) == 'png'

    # Download with version
    url = '/maps/{}/png:small/{}'.format(uuid, version)
    resp = client.get(url)
    assert resp.status_code == 200


def test_pdf(client, uuid, worker):
    url = '/api/maps/{}/render/pdf'.format(uuid)
    resp = client.json_get(url)
    assert(resp.status_code == 202)
    assert resp.json['status'] == 'queued'
    assert resp.json['file_type'] == 'pdf'
    version = resp.json['version']

    # do work (as we don't have a worker process)
    worker.work(burst=True)
    sleep(0.5)

    # Download without version
    url = '/maps/{}/pdf'.format(uuid)
    resp = client.get(url)
    assert resp.status_code == 200
    assert len(resp.data) > 0
    with BytesIO(resp.data) as f:
        PdfFileReader(f)

    # Download with version
    url = '/maps/{}/pdf/{}'.format(uuid, version)
    resp = client.get(url)
    assert resp.status_code == 200


def test_svg(client, uuid, worker):
    url = '/api/maps/{}/render/svg'.format(uuid)
    resp = client.json_get(url)
    assert(resp.status_code == 202)
    assert resp.json['status'] == 'queued'
    assert resp.json['file_type'] == 'svg'
    version = resp.json['version']

    # do work (as we don't have a worker process)
    worker.work(burst=True)
    sleep(0.5)

    # Download without version
    url = '/maps/{}/svg'.format(uuid)
    resp = client.get(url)
    assert resp.status_code == 200
    assert len(resp.data) > 0
    assert et.fromstring(resp.data).tag == '{http://www.w3.org/2000/svg}svg'

    # Download with version
    url = '/maps/{}/svg/{}'.format(uuid, version)
    resp = client.get(url)
    assert resp.status_code == 200
