import sqlite3
from flask_bcrypt import Bcrypt
import os

bcrypt = Bcrypt()

# ✅ Generate hashed passwords
admin_password = bcrypt.generate_password_hash("adminpass").decode("utf-8")
user_password = bcrypt.generate_password_hash("userpass").decode("utf-8")

# ✅ Define the correct database path
db_path = os.path.join("instance", "db.sqlite3")  # ✅ Updated to match your database name

# ✅ Ensure the database file exists
if not os.path.exists(db_path):
    print(f"❌ ERROR: Database not found at {db_path}")
    exit()

# ✅ Connect to the existing SQLite database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # ✅ Check if user already exists to prevent duplicate entries
    cursor.execute("SELECT COUNT(*) FROM user WHERE email = ?", ("admin@bci.org",))
    if cursor.fetchone()[0] == 0:
        # ✅ Insert Users
        cursor.executemany(
            "INSERT INTO user (username, email, password, is_admin) VALUES (?, ?, ?, ?)",
            [
                ("admin", "admin@bci.org", admin_password, 1),
                ("user", "user1@example.org", user_password, 0),
            ],
        )
        conn.commit()
        print("✅ Users inserted successfully into instance/db.sqlite3!")
    else:
        print("⚠ Users already exist. Skipping insertion.")
except sqlite3.Error as e:
    print(f"❌ Database Error: {e}")
finally:
    conn.close()
