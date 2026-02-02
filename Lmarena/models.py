from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# Пользователи
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    role = db.Column(db.String(50)) # manager, admin

# Комментарии к заявкам (НОВОЕ)
class BookingNote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'))
    author = db.Column(db.String(50), default="System")

# Заявки
class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_name = db.Column(db.String(100))
    client_phone = db.Column(db.String(20))
    tour_type = db.Column(db.String(100))
    status = db.Column(db.String(20), default='new')
    priority = db.Column(db.String(10), default='medium')
    price = db.Column(db.Float, default=0.0)
    cost = db.Column(db.Float, default=0.0)
    tour_date = db.Column(db.DateTime)
    
    # Ответственный менеджер
    manager_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    manager = db.relationship('User', backref='bookings')

    # Связь с заметками (НОВОЕ)
    notes = db.relationship('BookingNote', backref='booking', lazy=True)

# Остальные модели (оставляем как были, чтобы не ломать логику)
class Guide(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
class Transport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    model = db.Column(db.String(100))
class Supplier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(100))
class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(50))
    text = db.Column(db.String(500))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    channel = db.Column(db.String(50))