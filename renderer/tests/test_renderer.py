import xml.etree.cElementTree as et
import imghdr

from time import sleep
from PyPDF2 import PdfFileReader
from io import BytesIO
from tests.fixtures import *
from tests.utils import post, get, wait_until_finished, reset_map_folder


VERSION = 'c8bbde29fa1cfd1109fae1835fcc1ea1f92f4e31292c1b3d338c782f18333605'


def setup_function(function):
    reset_map_folder()


def tast_png(client, sample):
    job_id = None

    # Request rendering of a png
    with post(client, '/render/png:small', sample) as (resp, json):
        assert json['status'] == 'queued'
        assert json['map_id'] == 'test123'
        assert json['file_type'] == 'png:small'
        assert json['version'] == VERSION
        assert 'job_id' in json
        job_id = json['job_id']

    # seems we need to wait a bit so it has been queued
    sleep(0.1)

    # Check if render of same data is not done twice
    with post(client, '/render/png:small', sample) as (resp, json):
        assert 'job_id' in json
        assert job_id == json['job_id']

    assert wait_until_finished(client, job_id)

    # Retry - Check if finished (and is reuses old job - not enqeueud as new
    # job)
    with post(client, '/render/png:small', sample) as (resp, json):
        assert 'job_id' in json
        assert job_id == json['job_id']
        assert json['status'] == 'finished'

    # Download with version
    url = '/download/test123_{}.png:small'.format(VERSION)
    with get(client, url) as (resp, data):
        assert resp.status_code == 200

    # Download latest (without version)
    with get(client, '/download/test123.png:small') as (resp, data):
        assert resp.status_code == 200
        assert len(data) > 0
        assert imghdr.what(None, data) == 'png'


def test_pdf(client, sample):
    job_id = None

    # Request rendering of a pdf
    with post(client, '/render/pdf', sample) as (resp, json):
        assert json['status'] == 'queued'
        job_id = json['job_id']

    assert wait_until_finished(client, job_id)

    # Download with version
    url = '/download/test123_{}.pdf'.format(VERSION)
    with get(client, url) as (resp, data):
        assert resp.status_code == 200
        assert len(data) > 0
        with BytesIO(data) as f:
            PdfFileReader(f)


def tast_svg(client, sample):
    job_id = None

    # Request rendering of a svg
    with post(client, '/render/svg', sample) as (resp, json):
        assert json['status'] == 'queued'
        job_id = json['job_id']

    assert wait_until_finished(client, job_id)

    # Download with version
    url = '/download/test123_{}.svg'.format(VERSION)
    with get(client, url) as (resp, data):
        with open('/tmp/foo.svg', 'wb') as f:
            f.write(data)
        assert et.fromstring(data).tag == '{http://www.w3.org/2000/svg}svg'
        assert len(data) > 0
        assert resp.status_code == 200


def tast_status(client, sample):
    job_id = None

    # Request rendering of a svg
    with post(client, '/render/svg', sample) as (resp, json):
        assert json['status'] == 'queued'
        job_id = json['job_id']

    # wait until job has been started
    sleep(0.1)

    # status_by_job
    with get(client, '/status/'+job_id) as (resp, json):
        assert json['status'] == 'started'
        assert resp.status_code == 200

    assert wait_until_finished(client, job_id)

    # status_by_job
    with get(client, '/status/'+job_id) as (resp, json):
        assert json['status'] == 'finished'
        assert resp.status_code == 200


def tast_invalid_download(client):
    with get(client, '/download/INVALID.png:small') as (resp, data):
        assert resp.status_code == 404


def tast_invalid_status_by_job(client):
    # status_by_job
    with get(client, '/status/INVALID') as (resp, data):
        assert resp.status_code == 404


def tast_invalid_status_by_map(client, sample):
    # status_by_map - invalid file_type
    url = '/status/INVALID_MAP_NAME/INVALID_VERSION/INVALID_FILE_TYPE'
    with get(client, url) as (resp, data):
        assert resp.status_code == 400  # unsupported file type

    # status_by_map - invalid map
    url = '/status/INVALID_MAP_NAME/INVALID_VERSION/pdf'
    with get(client, url) as (resp, _):
        assert resp.status_code == 404

    # Request rendering of a pdf
    job_id = None
    with post(client, '/render/png:small', sample) as (resp, json):
        assert resp.status_code == 200
        assert json['status'] == 'queued'
        job_id = json['job_id']

    assert wait_until_finished(client, job_id)

    # status_by_map - invalid version
    url = '/status/test123/INVALID_VERSION/pdf'
    with get(client, url) as (resp, _):
        assert resp.status_code == 404
