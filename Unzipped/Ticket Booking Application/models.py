from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class USER(db.Model):
    __tablename__="USER"
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), nullable=False)

class Theatre(db.Model):
    __tablename__="Theatre"
    theatre_id=db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer,db.ForeignKey("USER.user_id"),nullable=False)
    name = db.Column(db.String(100), nullable=False)
    place = db.Column(db.String(100), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    trend=db.Column(db.String)

class Show(db.Model):
    __tablename__="Show"
    show_id = db.Column(db.Integer, primary_key=True)
    theatre_id=db.Column(db.Integer,db.ForeignKey("Theatre.theatre_id"),nullable=False)
    name = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Float, nullable=False)
    tags = db.Column(db.String(100), nullable=True)
    ticket_price = db.Column(db.Float, nullable=False)
    num_tickets = db.Column(db.Integer, nullable=False)
    datetime = db.Column(db.String(100), nullable=False)


class Ticket(db.Model):
    _tablename_ = "Ticket"
    ticket_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("USER.user_id"), nullable=False)
    show_id = db.Column(db.Integer, db.ForeignKey("Show.show_id"), nullable=False)
    booked_tickets = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    total = db.Column(db.Integer, nullable=False)