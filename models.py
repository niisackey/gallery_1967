from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()

PREDEFINED_USERS = {
    "admin": {
        "email": "admin@example.com",
        "password": bcrypt.generate_password_hash("adminpass").decode("utf-8"),
        "is_admin": True
    },
    "user": {
        "email": "user1@example.com",
        "password": bcrypt.generate_password_hash("userpass").decode("utf-8"),
        "is_admin": False
    }
}


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # ✅ Cannot be NULL
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        """ ✅ Hash password before storing """
        if password and not password.startswith("$2b$"):  # ✅ Avoid re-hashing
            self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        """ ✅ Check hashed password """
        return bcrypt.check_password_hash(self.password, password)


class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    filename = db.Column(db.String(100), unique=True, nullable=False)
    price = db.Column(db.Float, nullable=False)


class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    image_id = db.Column(db.Integer, db.ForeignKey('image.id'))
    reference = db.Column(db.String(100), unique=True)
    status = db.Column(db.String(50))
    downloaded = db.Column(db.Boolean, default=False)  # ✅ Track download status