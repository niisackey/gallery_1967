from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from models import db, User, bcrypt  # ✅ Import bcrypt from models
from routes import app_routes
from auth import auth
import os
from models import db, seed_users 


app = Flask(__name__)
app.config.from_object("config.Config")  # ✅ Ensure Config is set

# ✅ Set upload folder inside static/uploads/
UPLOAD_FOLDER = os.path.join("static", "uploads")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ✅ Initialize Database & Migrations before registering Blueprints
db.init_app(app)
migrate = Migrate(app, db)

with app.app_context():
    db.create_all()  # ✅ Ensure tables exist
    seed_users()  # ✅ Insert predefined users if missing
    
# ✅ Initialize LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"

# ✅ Register Blueprints AFTER initializing db
app.register_blueprint(app_routes)
app.register_blueprint(auth)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))  # ✅ Load users from the database

# ✅ Ensure database tables are created
with app.app_context():
    db.create_all()


PREDEFINED_USERS = {
    "admin": {
        "email": "admin@example.com",
        "password": "adminpass",  # ✅ Store plain text temporarily
        "is_admin": True
    },
    "user": {
        "email": "user1@example.com",
        "password": "userpass",
        "is_admin": False
    }
}

def insert_predefined_users():
    """ ✅ Insert predefined users into the database if they don't exist. """
    with app.app_context():
        print("🔍 Checking predefined users...")

        for username, user_data in PREDEFINED_USERS.items():
            existing_user = User.query.filter_by(username=username).first()

            if existing_user:
                print(f"⚠️ User {username} already exists, skipping...")
            else:
                print(f"🔄 Inserting user: {username}")

                hashed_password = bcrypt.generate_password_hash(user_data["password"]).decode('utf-8')  # ✅ Hash password
                print(f"🔒 Hashed Password for {username}: {hashed_password}")  # Debugging

                new_user = User(
                    username=username,
                    email=user_data["email"],
                    password=hashed_password,  # ✅ Store hashed password
                    is_admin=user_data["is_admin"]
                )

                db.session.add(new_user)
                db.session.commit()  # ✅ Commit after each user to prevent errors

                print(f"✅ Inserted user: {username}")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # ✅ Ensure tables exist
        print("✅ Checking predefined users...")
        insert_predefined_users()  # ✅ Force insert users
        print(User.query.all())  # ✅ Debugging step to see users
    app.run(debug=True)
