import pytest
from app import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    client = app.test_client()
    yield client


@pytest.fixture
def sample():
    test_data = 'tests/data/test_map.json'
    with open(test_data, 'r') as f:
        yield f.read()
