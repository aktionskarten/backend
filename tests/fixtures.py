import pytest
from app import create_app
from app.models import Map, db as _db
from shutil import rmtree
from rq import SimpleWorker
from os import path


@pytest.fixture(scope="session")
def app(request):
    app = create_app()
    app.config['TESTING'] = True
    return app


@pytest.fixture(autouse=True)
def _setup_app_context_for_test(request, app):
    """
    Given app is session-wide, sets up a app context per test to ensure that
    app and request stack is not shared between tests.
    """
    ctx = app.app_context()
    ctx.push()
    yield  # tests will run here
    ctx.pop()


@pytest.fixture(scope="session")
def db(app, request):
    """Returns session-wide initialized database"""
    with app.app_context():
        _db.drop_all()
        _db.create_all()
        yield _db


@pytest.fixture(scope="session")
def worker(app):
    conn = app.task_queue.connection
    yield SimpleWorker([app.task_queue], connection=conn)


@pytest.fixture(scope="function")
def client(app):
    with app.test_client() as client:
        # always add Accept header
        def json_get(*args, **kwargs):
            headers = {'headers': {'Accept': 'application/json'}}
            if kwargs:
                kwargs.update(headers)
            else:
                kwargs = headers
            return client.get(*args, **kwargs)
        client.json_get = json_get
        yield client


@pytest.fixture(scope="function")
def uuid(app, db):
    rmtree(path.join(app.static_folder, 'maps'), ignore_errors=True)
    m = Map('my-new-map', bbox=[1, 1, 1, 1])
    db.session.add(m)
    db.session.commit()
    yield m.uuid.hex
