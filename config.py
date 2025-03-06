import os

class Config:
    SECRET_KEY = "bcimedia"
    SQLALCHEMY_DATABASE_URI = "sqlite:///db.sqlite3"
    UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
    PAYSTACK_SECRET_KEY = "sk_live_6f60c764e38038f0bc777e7b496a4ce46b13c36d"
    PAYSTACK_PUBLIC_KEY = "pk_live_d557af373af964934115b37d627faf36d2eb9573"
