import time

from shutil import rmtree
from app import app
from os import path
from contextlib import contextmanager
from timeit import default_timer as timer

MAX_WAIT = 100


@contextmanager
def request(client, method, url, data=None):
    content_type = 'application/json'
    kwargs = {
        'path': url, 'method': method, 'content_type': content_type,
        'data': data
    }
    with client.open(**kwargs) as resp:
        if resp.content_type == content_type:
            yield (resp, resp.get_json())
        else:
            yield (resp, resp.get_data())


def get(client, url):
    return request(client, 'GET', url)


def post(client, url, data):
    return request(client, 'POST', url, data)


def wait_until_finished(client, job_id):
    start = end = timer()
    while end-start < MAX_WAIT:
        with get(client, '/status/'+job_id) as (resp, json):
            json = resp.get_json()
            if json['status'] == 'finished':
                return True
            time.sleep(0.1)
        end = timer()
    return False


def reset_map_folder():
    rmtree(path.join(app.static_folder, 'maps'), ignore_errors=True)
