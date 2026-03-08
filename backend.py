from dbm import sqlite3

from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
from decimal import Decimal
import os
import logging

logging.basicConfig(filename='app.log', level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s: %(message)s')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this in production

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db/sdev265.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.app_context().push()

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Guest.query.get(int(user_id))

class Guest(db.Model, UserMixin):
    guest_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        # Flask-Login expects a string ID; override to use guest_id
        return str(self.guest_id)

class Room(db.Model):
    room_id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.String(10), unique=True, nullable=False)
    room_type = db.Column(db.String(30), nullable=False)
    rate = db.Column(db.Numeric(10,2), nullable=False)
    status = db.Column(db.String(20), default='available')

class Reservation(db.Model):
    reservation_id = db.Column(db.Integer, primary_key=True)
    guest_id = db.Column(db.Integer, db.ForeignKey('guest.guest_id'))
    room_id = db.Column(db.Integer, db.ForeignKey('room.room_id'))
    check_in_date = db.Column(db.Date, nullable=False)
    check_out_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='booked')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    guest = db.relationship('Guest', backref='reservations')
    room = db.relationship('Room', backref='reservations')


def seed_default_rooms():
    """Add a default set of rooms if the rooms table is empty.

    Creates 3 singles @150, 3 doubles @200, and 2 suites @300. Called
    during database initialization.
    """
    if Room.query.count() == 0:
        defaults = []
        # using simple numbering; adjust as needed
        for i in range(1, 4):
            defaults.append(Room(room_number=f'S{i:03}', room_type='Single', rate=150.00))
        for i in range(1, 4):
            defaults.append(Room(room_number=f'D{i:03}', room_type='Double', rate=200.00))
        for i in range(1, 3):
            defaults.append(Room(room_number=f'SU{i:03}', room_type='Suite', rate=300.00))
        db.session.add_all(defaults)
        db.session.commit()

@app.route('/')
def index():
    # render the frontend home page with a list of rooms
    """
    Render the frontend home page with a list of rooms.

    Returns:
        Rendered HTML page
    """
    rooms = Room.query.all()
    return render_template('index.html', rooms=rooms)

@app.route('/rooms')
def rooms():
    # page listing rooms; if check-in/check-out provided, filter by availability
    """
    Page listing rooms; if check-in/check-out provided, filter by availability.

    Returns:
        Rendered HTML page
    """

    check_in = request.args.get('check_in')
    check_out = request.args.get('check_out')

    if check_in and check_out:
        try:
            ci = datetime.strptime(check_in, '%Y-%m-%d').date()
            co = datetime.strptime(check_out, '%Y-%m-%d').date()
        except ValueError:
            # invalid dates; fall back to showing all rooms
            rooms = Room.query.all()
            return render_template('rooms.html', rooms=rooms, check_in=None, check_out=None)

        # overlapping reservation exists when: res.check_in_date < co and res.check_out_date > ci
        overlapping = db.session.query(Reservation).filter(
            Reservation.room_id == Room.room_id,
            Reservation.status != 'cancelled' ,
            Reservation.check_in_date < co,
            Reservation.check_out_date > ci
        ).exists()

        available_rooms = Room.query.filter(~overlapping).all()
        return render_template('rooms.html', rooms=available_rooms, check_in=check_in, check_out=check_out)

    # no dates provided: show all rooms
    rooms = Room.query.all()
    return render_template('rooms.html', rooms=rooms, check_in=None, check_out=None)

@app.route('/about')
def about():
    # static about us page
    """
    Static about us page.

    Returns:
        Rendered HTML page
    """
    return render_template('about.html')

@app.route('/contact')
def contact():
    # static contact page
    """
    Static contact page.

    Returns:
        Rendered HTML page
    """
    return render_template('contact.html')

@app.route('/send-message', methods=['POST'])
def send_message():
    # dummy handler for contact form submissions
    # grab form data; in real world we'd save or email it
    """
    Dummy handler for contact form submissions.

    Grabs form data from the request object and logs it for debugging purposes.

    Returns:
        Rendered HTML page
    """
    name = request.form.get('name')
    email = request.form.get('email')
    subject = request.form.get('subject')
    message = request.form.get('message')
    # log for debugging
    app.logger.info(f"Contact message from {name} <{email}> subject={subject}")
    return render_template('contact_success.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')

        if not all([name, email, password]):
            flash('Name, email, and password are required.')
            return redirect(url_for('register'))

        if Guest.query.filter_by(email=email).first():
            flash('Email already registered.')
            return redirect(url_for('register'))

        guest = Guest(name=name, email=email, phone=phone)
        guest.set_password(password)
        db.session.add(guest)
        db.session.commit()

        login_user(guest)
        return redirect(url_for('dashboard'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        guest = Guest.query.filter_by(email=email).first()
        if guest and guest.check_password(password):
            login_user(guest)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    reservations = Reservation.query.filter_by(guest_id=current_user.guest_id).all()
    return render_template('dashboard.html', reservations=reservations)

@app.route('/room-details/<int:room_id>')
def room_details(room_id):
    # show detailed information about a specific room
    """
    Show detailed information about a specific room.

    Args:
        room_id (int): The room number to show details for.

    Returns:
        Rendered HTML page
    """
    session = db.session
    room = session.get(Room, room_id)
    if not room:
        return "Room not found", 404
    return render_template('room_details.html', room=room)

@app.route('/reserve/<int:room_id>')
@login_required
def reserve(room_id):
    # show reservation form for a specific room
    """
    Show reservation form for a specific room.

    Args:
        room_id (int): The room number to show the reservation form for.

    Returns:
        Rendered HTML page

    Raises:
        404: If the room is not found
        400: If the date format is invalid or if the check-out date is not after the check-in date
    """
    session = db.session
    room = session.get(Room, room_id)
    if not room:
        return "Room not found", 404

    check_in = request.args.get('check_in')
    check_out = request.args.get('check_out')

    # if dates are missing, render template without booking details, showing date selection form
    if not check_in or not check_out:
        return render_template('reservation.html', 
                             room=room, 
                             check_in=None, 
                             check_out=None,
                             nights=None,
                             total_cost=None)

    try:
        ci = datetime.strptime(check_in, '%Y-%m-%d').date()
        co = datetime.strptime(check_out, '%Y-%m-%d').date()
    except ValueError:
        return "Invalid date format", 400

    nights = (co - ci).days
    if nights <= 0:
        return "Check-out must be after check-in", 400

    total_cost = float(room.rate) * nights

    return render_template('reservation.html', 
                         room=room, 
                         check_in=check_in, 
                         check_out=check_out,
                         nights=nights,
                         total_cost=total_cost)
# Make reservation route
@app.route('/make-reservation', methods=['POST'])
@login_required
def make_reservation():
    # create reservation for current user
    """
    Create a reservation for the current logged-in user.

    Args:
        room_id (int): Room ID to book
        check_in_str (str): Check-in date in YYYY-MM-DD format
        check_out_str (str): Check-out date in YYYY-MM-DD format

    Returns:
        Rendered HTML page
    Raises:
        400: If any of the form fields are missing, or if the date format is invalid
        404: If the room is not found
    """
    room_id = request.form.get('room_id', type=int)
    check_in_str = request.form.get('check_in')
    check_out_str = request.form.get('check_out')

    if not all([room_id, check_in_str, check_out_str]):
        return "All fields are required", 400

    try:
        check_in = datetime.strptime(check_in_str, '%Y-%m-%d').date()
        check_out = datetime.strptime(check_out_str, '%Y-%m-%d').date()
    except ValueError:
        return "Invalid date format", 400

    session = db.session
    room = session.get(Room, room_id)
    if not room:
        return "Room not found", 404

    # use current user as guest
    guest = current_user

    # create reservation
    reservation = Reservation(
        guest_id=guest.guest_id,
        room_id=room_id,
        check_in_date=check_in,
        check_out_date=check_out,
        status='booked'
    )
    db.session.add(reservation)
    db.session.commit()

    return render_template('confirmation.html', 
                         guest=guest, 
                         room=room, 
                         reservation=reservation)

@app.route('/api/rooms')
def get_rooms():
    # simple JSON endpoint for rooms data
    """
    Return a JSON object containing all rooms data.

    Returns:
        A JSON object containing a list of room data objects with the following keys:
            room_id (int): Unique identifier for the room.
            room_number (str): Room number as displayed on the hotel's website.
            room_type (str): Type of room (Single, Double, Suite).
            rate (float): Room rate per night.
            status (str): Room status (booked, available).
    """
    rooms = Room.query.all()
    return jsonify([
        {
            'room_id': r.room_id,
            'room_number': r.room_number,
            'room_type': r.room_type,
            'rate': float(r.rate),
            'status': r.status
        }
        for r in rooms
    ])

# Admin routes for rooms
@app.route('/admin/rooms')
def admin_rooms():
    rooms = Room.query.all()
    return render_template('admin_rooms.html', rooms=rooms)

@app.route('/admin/rooms/new', methods=['GET', 'POST'])
def admin_rooms_new():
    if request.method == 'POST':
        room_number = request.form.get('room_number')
        room_type = request.form.get('room_type')
        rate = float(request.form.get('rate'))
        status = request.form.get('status', 'available')
        room = Room(room_number=room_number, room_type=room_type, rate=rate, status=status)
        db.session.add(room)
        db.session.commit()
        return redirect(url_for('admin_rooms'))
    return render_template('admin_rooms_form.html', room=None)

@app.route('/admin/rooms/<int:room_id>/edit', methods=['GET', 'POST'])
def admin_rooms_edit(room_id):
    room = Room.query.get_or_404(room_id)
    if request.method == 'POST':
        room.room_number = request.form.get('room_number')
        room.room_type = request.form.get('room_type')
        room.rate = float(request.form.get('rate'))
        room.status = request.form.get('status')
        db.session.commit()
        return redirect(url_for('admin_rooms'))
    return render_template('admin_rooms_form.html', room=room)

@app.route('/admin/rooms/<int:room_id>/delete', methods=['POST'])
def admin_rooms_delete(room_id):
    room = Room.query.get_or_404(room_id)
    db.session.delete(room)
    db.session.commit()
    return redirect(url_for('admin_rooms'))

# Admin routes for reservations
@app.route('/admin/reservations')
def admin_reservations():
    reservations = Reservation.query.all()
    return render_template('admin_reservations.html', reservations=reservations)

@app.route('/admin/reservations/new', methods=['GET', 'POST'])
def admin_reservations_new():
    if request.method == 'POST':
        guest_id = int(request.form.get('guest_id'))
        room_id = int(request.form.get('room_id'))
        check_in = datetime.strptime(request.form.get('check_in'), '%Y-%m-%d').date()
        check_out = datetime.strptime(request.form.get('check_out'), '%Y-%m-%d').date()
        status = request.form.get('status', 'booked')
        reservation = Reservation(guest_id=guest_id, room_id=room_id, check_in_date=check_in, check_out_date=check_out, status=status)
        db.session.add(reservation)
        db.session.commit()
        return redirect(url_for('admin_reservations'))
    guests = Guest.query.all()
    rooms = Room.query.all()
    return render_template('admin_reservations_form.html', reservation=None, guests=guests, rooms=rooms)

@app.route('/admin/reservations/<int:reservation_id>/edit', methods=['GET', 'POST'])
def admin_reservations_edit(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    if request.method == 'POST':
        reservation.guest_id = int(request.form.get('guest_id'))
        reservation.room_id = int(request.form.get('room_id'))
        reservation.check_in_date = datetime.strptime(request.form.get('check_in'), '%Y-%m-%d').date()
        reservation.check_out_date = datetime.strptime(request.form.get('check_out'), '%Y-%m-%d').date()
        reservation.status = request.form.get('status')
        db.session.commit()
        return redirect(url_for('admin_reservations'))
    guests = Guest.query.all()
    rooms = Room.query.all()
    return render_template('admin_reservations_form.html', reservation=reservation, guests=guests, rooms=rooms)

@app.route('/admin/reservations/<int:reservation_id>/delete', methods=['POST'])
def admin_reservations_delete(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    db.session.delete(reservation)
    db.session.commit()
    return redirect(url_for('admin_reservations'))

# Admin routes for guests
@app.route('/admin/guests')
def admin_guests():
    guests = Guest.query.all()
    return render_template('admin_guests.html', guests=guests)

@app.route('/admin/guests/new', methods=['GET', 'POST'])
def admin_guests_new():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        guest = Guest(name=name, phone=phone, email=email)
        db.session.add(guest)
        db.session.commit()
        return redirect(url_for('admin_guests'))
    return render_template('admin_guests_form.html', guest=None)

@app.route('/admin/guests/<int:guest_id>/edit', methods=['GET', 'POST'])
def admin_guests_edit(guest_id):
    guest = Guest.query.get_or_404(guest_id)
    if request.method == 'POST':
        guest.name = request.form.get('name')
        guest.phone = request.form.get('phone')
        guest.email = request.form.get('email')
        db.session.commit()
        return redirect(url_for('admin_guests'))
    return render_template('admin_guests_form.html', guest=guest)

@app.route('/admin/guests/<int:guest_id>/delete', methods=['POST'])
def admin_guests_delete(guest_id):
    guest = Guest.query.get_or_404(guest_id)
    db.session.delete(guest)
    db.session.commit()
    return redirect(url_for('admin_guests'))

if __name__ == '__main__':
    db.create_all()
    # seed default rooms on first run
    seed_default_rooms()
    app.run(debug=True)
