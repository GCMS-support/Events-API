"""HTTP verification. Mutating demo checks require explicit --exercise."""
import argparse
import secrets
import time
import requests


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('base_url')
    parser.add_argument('--exercise', action='store_true')
    parser.add_argument('--revision')
    parser.add_argument('--wait', type=int, default=90)
    args = parser.parse_args()
    base = args.base_url.rstrip('/')
    session = requests.Session()
    deadline = time.monotonic() + args.wait
    while True:
        try:
            health = session.get(base + '/api/health', timeout=10)
            health.raise_for_status()
            assert health.json()['status'] == 'healthy'
            root = session.get(base + '/', timeout=10)
            root.raise_for_status()
            assert root.json()['name'] == 'Evently API'
            if args.revision:
                assert root.json()['revision'] == args.revision
            break
        except (requests.RequestException, AssertionError, ValueError, KeyError):
            if time.monotonic() >= deadline:
                raise RuntimeError('API did not become healthy with the expected revision') from None
            time.sleep(3)
    for path in ('/api/events', '/api/openapi.yaml', '/apidocs/'):
        response = session.get(base + path, timeout=10)
        response.raise_for_status()
    if args.exercise:
        credentials = {'username': 'smoke-' + secrets.token_hex(6),
                       'password': secrets.token_urlsafe(24)}
        response = session.post(base + '/api/auth/register', json=credentials, timeout=10)
        assert response.status_code == 201
        response = session.post(base + '/api/auth/login', json=credentials, timeout=10)
        assert response.status_code == 200
        headers = {'Authorization': 'Bearer ' + response.json()['access_token']}
        response = session.post(base + '/api/events', headers=headers, timeout=10,
            json={'title': 'Container smoke test', 'date': '2027-06-01T18:00:00',
                  'is_public': False, 'capacity': 1})
        assert response.status_code == 201
        event_id = response.json()['id']
        path = base + f'/api/rsvps/event/{event_id}'
        assert session.post(path, json={}, timeout=10).status_code == 401
        assert session.post(path, headers=headers, json={}, timeout=10).status_code == 201
        assert session.post(path, headers=headers, json={'attending': False}, timeout=10).status_code == 200
    print('PASS: health, revision, events and API documentation' +
          ('; registration, login, event creation and RSVP flow' if args.exercise else ''))


if __name__ == '__main__':
    main()
