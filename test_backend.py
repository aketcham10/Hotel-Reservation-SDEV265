import pytest
from backend import app, db, Room, Guest, Reservation
from datetime import date

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.app_context():
        db.create_all()
        # Add some test data
        room1 = Room(room_number='101', room_type='Single', rate=100.00, status='available')
        room2 = Room(room_number='102', room_type='Double', rate=150.00, status='available')
        db.session.add(room1)
        db.session.add(room2)
        db.session.commit()
        yield app.test_client()
        db.drop_all()

def test_index(client):
    response = client.get('/')
    assert response.status_code == 200
    # Since it renders template, just check status

def test_rooms_no_dates(client):
    response = client.get('/rooms')
    assert response.status_code == 200

def test_rooms_with_dates(client):
    response = client.get('/rooms?check_in=2023-01-01&check_out=2023-01-02')
    assert response.status_code == 200

def test_rooms_invalid_dates(client):
    response = client.get('/rooms?check_in=invalid&check_out=2023-01-02')
    assert response.status_code == 200  # Falls back to all rooms

def test_about(client):
    response = client.get('/about')
    assert response.status_code == 200

def test_contact(client):
    response = client.get('/contact')
    assert response.status_code == 200

def test_send_message(client):
    response = client.post('/send-message', data={
        'name': 'Test User',
        'email': 'test@example.com',
        'subject': 'Test Subject',
        'message': 'Test Message'
    })
    assert response.status_code == 200

def test_room_details_existing(client):
    response = client.get('/room-details/1')
    assert response.status_code == 200

def test_room_details_not_found(client):
    response = client.get('/room-details/999')
    assert response.status_code == 404

def test_reserve_no_dates(client):
    response = client.get('/reserve/1')
    assert response.status_code == 200

def test_reserve_with_dates(client):
    response = client.get('/reserve/1?check_in=2023-01-01&check_out=2023-01-02')
    assert response.status_code == 200

def test_reserve_invalid_dates(client):
    response = client.get('/reserve/1?check_in=invalid&check_out=2023-01-02')
    assert response.status_code == 400

def test_reserve_checkout_before_checkin(client):
    response = client.get('/reserve/1?check_in=2023-01-02&check_out=2023-01-01')
    assert response.status_code == 400

def test_reserve_room_not_found(client):
    response = client.get('/reserve/999?check_in=2023-01-01&check_out=2023-01-02')
    assert response.status_code == 404

def test_make_reservation_success(client):
    response = client.post('/make-reservation', data={
        'name': 'John Doe',
        'email': 'john@example.com',
        'phone': '123-456-7890',
        'room_id': '1',
        'check_in': '2023-01-01',
        'check_out': '2023-01-02'
    })
    assert response.status_code == 200

def test_make_reservation_missing_fields(client):
    response = client.post('/make-reservation', data={
        'name': 'John Doe',
        # missing email, etc.
    })
    assert response.status_code == 400

def test_make_reservation_invalid_date(client):
    response = client.post('/make-reservation', data={
        'name': 'John Doe',
        'email': 'john@example.com',
        'phone': '123-456-7890',
        'room_id': '1',
        'check_in': 'invalid',
        'check_out': '2023-01-02'
    })
    assert response.status_code == 400

def test_make_reservation_room_not_found(client):
    response = client.post('/make-reservation', data={
        'name': 'John Doe',
        'email': 'john@example.com',
        'phone': '123-456-7890',
        'room_id': '999',
        'check_in': '2023-01-01',
        'check_out': '2023-01-02'
    })
    assert response.status_code == 404

def test_get_rooms(client):
    response = client.get('/api/rooms')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 2  # We added 2 rooms
    assert data[0]['room_number'] == '101'