import pytest
from app import create_app
from models import db


@pytest.fixture
def app():
    application = create_app({
        'TESTING': True,
        'FIRST_USER_ADMIN': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite://',
        'SECRET_KEY': 'test-only-secret-key-not-for-production',
        'JWT_SECRET_KEY': 'test-only-jwt-secret-key-not-for-production',
    })
    yield application
    with application.app_context():
        db.session.remove()
        db.drop_all()
        db.engine.dispose()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def accounts(client):
    result = {}
    for username in ('admin', 'member'):
        credentials = {'username': username, 'password': 'test-password-123!'}
        response = client.post('/api/auth/register', json=credentials)
        assert response.status_code == 201
        login = client.post('/api/auth/login', json=credentials)
        assert login.status_code == 200
        result[username] = {
            'headers': {'Authorization': f"Bearer {login.json['access_token']}"},
            'user': response.json['user'],
        }
    return result


@pytest.fixture
def make_event(client, accounts):
    def create(**overrides):
        payload = {'title': 'Test concert', 'date': '2027-06-01T18:00:00',
                   'location': 'Berlin', 'is_public': True}
        payload.update(overrides)
        response = client.post('/api/events', json=payload,
                               headers=accounts['admin']['headers'])
        assert response.status_code == 201, response.get_data(as_text=True)
        return response.json
    return create
