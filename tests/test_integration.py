import pytest


def test_health_and_documentation(client):
    assert client.get('/api/health').json == {'status': 'healthy'}
    assert client.get('/').json['name'] == 'Evently API'
    assert client.get('/apidocs/').status_code == 200
    spec = client.get('/api/openapi.yaml')
    assert spec.status_code == 200
    assert b'/api/events' in spec.data


@pytest.mark.parametrize('payload', [{}, {'username': 'a'}, {'password': 'b'}])
@pytest.mark.parametrize('endpoint', ['register', 'login'])
def test_auth_requires_both_fields(client, endpoint, payload):
    assert client.post(f'/api/auth/{endpoint}', json=payload).status_code == 400


def test_register_roles_duplicate_and_login(client, accounts):
    assert accounts['admin']['user']['is_admin'] is True
    assert accounts['member']['user']['is_admin'] is False
    assert 'password_hash' not in accounts['member']['user']
    assert client.post('/api/auth/register', json={
        'username': 'member', 'password': 'different'}).status_code == 400
    assert client.post('/api/auth/login', json={
        'username': 'member', 'password': 'wrong'}).status_code == 401
    assert client.post('/api/auth/login', json={
        'username': 'unknown', 'password': 'wrong'}).status_code == 401


def test_database_is_empty_for_each_test(client):
    assert client.get('/api/events').json == []


def test_public_deployment_can_disable_first_user_admin(app, client):
    app.config['FIRST_USER_ADMIN'] = False
    response = client.post('/api/auth/register', json={
        'username': 'first-visitor', 'password': 'test-password-123!'})
    assert response.status_code == 201
    assert response.json['user']['is_admin'] is False


def test_create_list_get_event(client, accounts, make_event):
    event = make_event(description='Test concert', capacity=2)
    assert event['created_by'] == accounts['admin']['user']['id']
    assert event['rsvp_count'] == 0
    assert client.get(f"/api/events/{event['id']}").json == event
    assert client.get('/api/events').json == [event]


def test_create_event_requires_valid_token(client):
    payload = {'title': 'Test', 'date': '2027-01-01T12:00:00'}
    assert client.post('/api/events', json=payload).status_code == 401
    assert client.post('/api/events', json=payload, headers={
        'Authorization': 'Bearer invalid'}).status_code == 422


@pytest.mark.parametrize('payload', [{}, {'title': 'Test'},
    {'title': 'Test', 'date': 'not-a-date'}, {'title': 'Test', 'date': 123}])
def test_create_event_validation(client, accounts, payload):
    assert client.post('/api/events', json=payload,
        headers=accounts['member']['headers']).status_code == 400


@pytest.mark.parametrize('path', ['/api/events/999', '/api/rsvps/event/999'])
def test_missing_event(client, path):
    assert client.get(path).status_code == 404


def test_public_anonymous_rsvp_and_statistics(client, make_event):
    event = make_event()
    path = f"/api/rsvps/event/{event['id']}"
    response = client.post(path, json={})
    assert response.status_code == 201
    assert response.json['user_id'] is None
    assert response.json['attending'] is True
    assert client.post(path, json={'attending': False}).status_code == 201
    assert client.get(path).json['stats'] == {
        'attending': 1, 'not_attending': 1, 'total': 2}


def test_protected_rsvp_requires_login(client, accounts, make_event):
    event = make_event(is_public=False)
    path = f"/api/rsvps/event/{event['id']}"
    assert client.post(path, json={}).status_code == 401
    response = client.post(path, json={}, headers=accounts['member']['headers'])
    assert response.status_code == 201
    assert response.json['user_id'] == accounts['member']['user']['id']


@pytest.mark.parametrize('is_public', [True, False])
def test_admin_event_permissions(client, accounts, make_event, is_public):
    event = make_event(is_public=is_public, requires_admin=True)
    path = f"/api/rsvps/event/{event['id']}"
    assert client.post(path, json={}).status_code == 401
    assert client.post(path, json={}, headers=accounts['member']['headers']).status_code == 403
    assert client.post(path, json={}, headers=accounts['admin']['headers']).status_code == 201


def test_existing_rsvp_updates_without_duplicate(client, accounts, make_event):
    event = make_event()
    path = f"/api/rsvps/event/{event['id']}"
    headers = accounts['member']['headers']
    first = client.post(path, json={}, headers=headers)
    update = client.post(path, json={'attending': False}, headers=headers)
    assert update.status_code == 200
    assert update.json['id'] == first.json['id']
    assert client.get(path).json['stats'] == {'attending': 0, 'not_attending': 1, 'total': 1}


def test_capacity_rejects_additional_attendee(client, make_event):
    event = make_event(capacity=1)
    path = f"/api/rsvps/event/{event['id']}"
    assert client.post(path, json={}).status_code == 201
    assert client.post(path, json={}).status_code == 400


def test_full_event_allows_cancellation_and_idempotent_rsvp(client, accounts, make_event):
    event = make_event(capacity=1)
    path = f"/api/rsvps/event/{event['id']}"
    headers = accounts['member']['headers']
    assert client.post(path, json={}, headers=headers).status_code == 201
    assert client.post(path, json={}, headers=headers).status_code == 200
    assert client.post(path, json={'attending': False}, headers=headers).status_code == 200
    assert client.post(path, json={}).status_code == 201
