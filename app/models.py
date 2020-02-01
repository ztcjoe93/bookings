from .extensions import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

def attr_expr(model_class):
    attr_list = []
    for attr in dir(model_class):
        val = getattr(model_class, attr)
        if not attr.startswith("__") and not callable(val):
            attr_list.append(f'{attr} = {val}')

    return attr_list

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(128), unique=True, nullable=False)
    pwd_hash = db.Column(db.String(128))
    bookings = db.relationship("Booking", backref="users")
    su_rights = db.Column(db.Boolean, default=False, nullable=False)
    verification = db.Column(db.Boolean, default=False)

    def set_pwd(self, password):
            self.pwd_hash = generate_password_hash(password)
    def check_pwd(self, password):
            return check_password_hash(self.pwd_hash, password)

class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'))
    quantity = db.Column(db.Integer, nullable=False)
    book_time = db.Column(db.DateTime, nullable=True)
    last_modified = db.Column(db.DateTime, nullable=True)

class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    max_capacity = db.Column(db.Integer, nullable=False)
    start = db.Column(db.DateTime, nullable=False)
    end = db.Column(db.DateTime, nullable=False)
    img_name = db.Column(db.String(128), nullable=True)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    description = db.Column(db.String(1024), nullable=True)
    
    bookings = db.relationship("Booking", backref="events")

class Location(db.Model):
    __tablename__ = 'locations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False, unique=True)
    address = db.Column(db.String(512), nullable=True)
    
    events = db.relationship("Event", backref="locations")

