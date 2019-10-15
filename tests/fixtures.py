import pytest
from app import create_app
from app.models import db as _db


@pytest.fixture(scope="session")
def app(request):
    app = create_app()
    app.config['TESTING'] = True
    return app
    #client = app.test_client()
    #yield client


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
#@pytest.fixture
#def sample():
#    test_data = 'tests/data/test_map.json'
#    with open(test_data, 'r') as f:
#        yield f.read()

@pytest.fixture(scope="session")
def db(app, request):
    """Returns session-wide initialized database"""
    with app.app_context():
        _db.drop_all()
        _db.create_all()
        yield _db