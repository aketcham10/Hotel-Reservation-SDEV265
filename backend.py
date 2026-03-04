from dbm import sqlite3

from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from decimal import Decimal
import os
import logging

logging.basicConfig(filename='app.log', level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s: %(message)s')

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db/sdev265.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.app_context().push()

db = SQLAlchemy(app)
def get_db_connection():
    conn = sqlite3.connect('db/sdev265.db')
    conn.row_factory = sqlite3.Row
    return conn

class Guest(db.Model):
    guest_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))

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

class Stay(db.Model):
    stay_id = db.Column(db.Integer, primary_key=True)
    reservation_id = db.Column(db.Integer, db.ForeignKey('reservation.reservation_id'))
    actual_check_in = db.Column(db.DateTime)
    actual_check_out = db.Column(db.DateTime)

class Charge(db.Model):
    charge_id = db.Column(db.Integer, primary_key=True)
    stay_id = db.Column(db.Integer, db.ForeignKey('stay.stay_id'))
    description = db.Column(db.String(200))
    amount = db.Column(db.Numeric(10,2))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Payment(db.Model):
    payment_id = db.Column(db.Integer, primary_key=True)
    reservation_id = db.Column(db.Integer, db.ForeignKey('reservation.reservation_id'))
    amount = db.Column(db.Numeric(10,2))
    method = db.Column(db.String(20))
    status = db.Column(db.String(20))
    paid_at = db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/')
def index():
    # render the frontend home page with a list of rooms
    rooms = Room.query.all()
    return render_template('index.html', rooms=rooms)

@app.route('/rooms')
def rooms():
    # page listing rooms; if check-in/check-out provided, filter by availability
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
    return render_template('about.html')

@app.route('/contact')
def contact():
    # static contact page
    return render_template('contact.html')

@app.route('/reserve/<int:room_id>')
def reserve(room_id):
    # show reservation form for a specific room
    room = Room.query.get(room_id)
    if not room:
        return "Room not found", 404

    check_in = request.args.get('check_in')
    check_out = request.args.get('check_out')

    if not check_in or not check_out:
        return "Check-in and check-out dates are required", 400

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

@app.route('/make-reservation', methods=['POST'])
def make_reservation():
    # create guest and reservation
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    room_id = request.form.get('room_id', type=int)
    check_in_str = request.form.get('check_in')
    check_out_str = request.form.get('check_out')

    if not all([name, email, phone, room_id, check_in_str, check_out_str]):
        return "All fields are required", 400

    try:
        check_in = datetime.strptime(check_in_str, '%Y-%m-%d').date()
        check_out = datetime.strptime(check_out_str, '%Y-%m-%d').date()
    except ValueError:
        return "Invalid date format", 400

    room = Room.query.get(room_id)
    if not room:
        return "Room not found", 404

    # create guest
    guest = Guest(name=name, email=email, phone=phone)
    db.session.add(guest)
    db.session.flush()  # flush to get the guest_id without committing

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

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
