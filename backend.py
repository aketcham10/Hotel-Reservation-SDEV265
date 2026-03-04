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
