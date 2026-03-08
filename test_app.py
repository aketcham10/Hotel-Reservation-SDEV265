import unittest
from backend import app, db, Guest, Room, Reservation
from datetime import date

class HotelAPITestCase(unittest.TestCase):
    def setUp(self):
        # Set up test client and in-memory database
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = app.test_client()
        with app.app_context():
            db.create_all()

    def tearDown(self):
        # Clean up database after each test
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_index_route(self):
        # Test the root route
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome to Novara Luxe', response.data)

    def test_create_guest(self):
        # Test adding a guest
        with app.app_context():
            guest = Guest(name='John Doe', phone='1234567890', email='john@example.com')
            db.session.add(guest)
            db.session.commit()
            
            result = Guest.query.filter_by(name='John Doe').first()
            self.assertIsNotNone(result)
            self.assertEqual(result.email, 'john@example.com')

    def test_create_room(self):
        # Test adding a room
        with app.app_context():
            room = Room(room_number='101', room_type='Single', rate=100.00)
            db.session.add(room)
            db.session.commit()
            
            result = Room.query.filter_by(room_number='101').first()
            self.assertIsNotNone(result)
            self.assertEqual(result.room_type, 'Single')

    def test_create_reservation(self):
        # Test adding a reservation
        with app.app_context():
            guest = Guest(name='Alice', phone='5555555555', email='alice@example.com')
            room = Room(room_number='102', room_type='Double', rate=150.00)
            db.session.add_all([guest, room])
            db.session.commit()

            reservation = Reservation(
                guest_id=guest.guest_id,
                room_id=room.room_id,
                check_in_date=date(2026, 3, 10),
                check_out_date=date(2026, 3, 15)
            )
            db.session.add(reservation)
            db.session.commit()

            result = Reservation.query.filter_by(guest_id=guest.guest_id).first()
            self.assertIsNotNone(result)
            self.assertEqual(result.status, 'booked')

if __name__ == '__main__':
    unittest.main()