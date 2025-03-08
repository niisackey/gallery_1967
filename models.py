from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_bcrypt import Bcrypt
from flask import current_app

db = SQLAlchemy()
bcrypt = Bcrypt()

PREDEFINED_USERS = {
    "admin": {
        "email": "admin@bci.org",
        "password": bcrypt.generate_password_hash("adminpass").decode("utf-8"),
        "is_admin": True
    },
    "user": {
        "email": "user1@example.org",
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

class Media(db.Model):  # ✅ Supports images, audio, and video
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    filename = db.Column(db.String(255), unique=True, nullable=False)
    media_type = db.Column(db.String(10), nullable=False)  # ✅ "image", "audio", "video"
    price = db.Column(db.Float, nullable=False)

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    media_id = db.Column(db.Integer, db.ForeignKey('media.id'))
    reference = db.Column(db.String(100), unique=True)
    status = db.Column(db.String(50))
    downloaded = db.Column(db.Boolean, default=False)  # ✅ Track download status


def seed_users():
    """ ✅ Insert predefined users into the database if they do not exist """
    with current_app.app_context():
        for username, user_data in PREDEFINED_USERS.items():
            existing_user = User.query.filter_by(email=user_data["email"]).first()
            if not existing_user:
                new_user = User(
                    username=username,
                    email=user_data["email"],
                    is_admin=user_data["is_admin"]
                )
                new_user.set_password(user_data["password"])  # ✅ Hash the password
                db.session.add(new_user)

        db.session.commit()