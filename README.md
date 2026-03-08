HOTEL RESERVATION SYSTEM 

SDEV265 Software Development Project 

 

PROJECT OVERVIEW 

The Hotel Reservation System is a web-based application designed to help hotels, inns, and small lodging businesses manage room reservations in a simple and organized way. The system allows users to browse available rooms, view room details, and create reservations through an intuitive interface. 


The primary goal of this project is to demonstrate the design and development of a complete software solution using modern development practices. The application emphasizes usability, reliability, and efficient reservation management while preventing duplicate or overlapping bookings. 

 
This project was developed as part of the SDEV265 Software Development course and simulates a real-world development workflow including planning, design, implementation, testing, and documentation. 

 
TEAM MEMBERS 

Michael Moore – Programmer 

Zane Ketcham – Programmer 

Jesus Quirarte – Project Organizer 

Jasmine Reacco – Designer 

Xavier Randolph – Tester 

 

TECHNOLOGIES USED 

 

Backend 

Python 

Flask 

SQLAlchemy 

 

Database 

SQLite 

 

Frontend 

HTML 

CSS 

JavaScript 

Jinja2 Templates 

 

Development Tools 

Visual Studio Code 

Git 

GitHub 

Figma 

Canva 

GIMP 

 

FEATURES 

The application includes the following functionality: 

 

• View available hotel rooms 

• Filter rooms by check-in and check-out dates 

• Display room details 

• Calculate reservation cost automatically 

• Create guest reservations 

• Prevent overlapping room bookings 

• Store guest information 

• Reservation confirmation page 

• Contact form for customer inquiries 

• API endpoint for retrieving room information 

 

SYSTEM ARCHITECTURE 

The application follows a three-layer web architecture. 

 

User Browser 

HTML / CSS / JavaScript (Jinja2 Templates) 

Flask Web Application (Python Backend) 

SQLAlchemy ORM 

SQLite Database 

 

DATABASE DESIGN 

The system uses a relational database structure with the following core entities: 

 

Guest – Stores guest contac t information 

Room – Stores room number, type, rate, and availability 

Reservation – Tracks guest bookings 

Stay – Records actual check-in and check-out times 

Charge – Tracks additional service charges 

Payment – Records reservation payments 

 

RESERVATION LOGIC 

The system prevents double bookings by checking for overlapping reservations. 

 

A reservation conflict occurs when: 

existing.check_in_date < requested_check_out 

AND 

existing.check_out_date > requested_check_in 

 

INSTALLATION 

 

1. Clone the repository 

git clone https://github.com/aketcham10/Hotel-Reservation-SDEV265.git 

 

2. Navigate to the project directory 

cd Hotel-Reservation-SDEV265 

 

3. Create a virtual environment 

python -m venv venv 

 

4. Activate the virtual environment 

Windows: 

venv\Scripts\activate 

 

Mac/Linux: 

source venv/bin/activate 

 

5. Install dependencies 

pip install flask flask_sqlalchemy 

 

6. Run the application 

python app.py 

 

Open in browser: 

http://127.0.0.1:5000 

 

API ENDPOINT 

 

GET /api/rooms 

 

Returns a JSON list of all rooms stored in the system. 

 

TESTING 

Testing included reservation workflow validation, room availability filtering, database record verification, and integration testing between the frontend, backend, and database. 

 

FUTURE IMPROVEMENTS 

Possible future improvements include: 

 

• User authentication system 

• Online payment integration 

• Administrative dashboard 

• Reservation management tools 

• Reporting and analytics 

• Mobile responsive interface 

• Cloud deployment 

 

LICENSE 

This project was developed for educational purposes as part of the SDEV265 Software Development course. 
