import json
from tests import factories


def test_create_map(client, session):
    map_name = 'TestMap'
    response = client.post('/api/maps', data=json.dumps({
        'name': map_name,
        'bbox': [9, 52, 10, 53]
    }), content_type='application/json')
    assert response.status_code == 200
    response = client.get('/api/maps/{}'.format(response.json['id']))
    assert response.status_code == 200
    assert response.json['name'] == map_name


def test_mock_and_get_maps(client, session):
    map_count = 10
    factories.MapFactory.create_batch(map_count)

    response = client.get('/api/maps')

    assert response.status_code == 200
    assert len(response.json) >= map_count
