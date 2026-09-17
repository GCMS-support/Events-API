from datetime import datetime
from models import User, Event, RSVP


def test_password_hash_and_verification():
    user = User(username='test')
    user.set_password('a-long-test-password')
    assert user.password_hash != 'a-long-test-password'
    assert user.check_password('a-long-test-password')
    assert not user.check_password('wrong')


def test_salts_are_unique():
    first, second = User(username='first'), User(username='second')
    first.set_password('same-password')
    second.set_password('same-password')
    assert first.password_hash != second.password_hash


def test_user_serialization_never_exposes_password():
    user = User(id=7, username='test', is_admin=False,
                created_at=datetime(2027, 1, 1))
    user.set_password('private-password')
    assert user.to_dict() == {'id': 7, 'username': 'test', 'is_admin': False,
                              'created_at': '2027-01-01T00:00:00'}


def test_event_serialization_counts_rsvps_and_only_named_attendees():
    event = Event(id=3, title='Concert', date=datetime(2027, 6, 1, 18))
    event.rsvps = [RSVP(user_id=7, attending=True),
                   RSVP(user_id=8, attending=False),
                   RSVP(user_id=None, attending=True)]
    result = event.to_dict()
    assert result['date'] == '2027-06-01T18:00:00'
    assert result['rsvp_count'] == 3
    assert result['attendees'] == [7]


def test_rsvp_serialization():
    rsvp = RSVP(id=2, event_id=3, user_id=None, attending=False)
    assert rsvp.to_dict() == {'id': 2, 'event_id': 3, 'user_id': None,
                              'attending': False, 'created_at': None}
