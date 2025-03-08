from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, 
    send_file, current_app, after_this_request
)
from flask_login import login_user, logout_user, login_required, current_user
from models import User, PREDEFINED_USERS, db, Media, Payment
import requests
import os

# Define Blueprints
app_routes = Blueprint("app_routes", __name__)
auth = Blueprint("auth", __name__)

@app_routes.route("/")
@login_required
def index():
    category = request.args.get("category", "all")  # Get category from URL

    if category == "all":
        media_files = Media.query.all()
    else:
        media_files = Media.query.filter_by(media_type=category).all()

    purchased_media = {
        payment.media_id for payment in Payment.query.filter_by(user_id=current_user.id, status="paid").all()
    }

    return render_template("index.html", media_files=media_files, purchased_media=purchased_media, category=category)


@app_routes.route("/delete_media/<int:media_id>", methods=["POST"])
@login_required
def delete_media(media_id):
    if not current_user.is_admin:
        flash("Access Denied!", "danger")
        return redirect(url_for("app_routes.admin"))

    media = Media.query.get_or_404(media_id)

    # Delete media file from static/uploads/
    file_path = os.path.join(current_app.root_path, "static", "uploads", media.filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    # Remove from database
    db.session.delete(media)
    db.session.commit()
    flash("Media deleted successfully!", "success")

    return redirect(url_for("app_routes.admin"))



@app_routes.route("/secure_media/<filename>")
@login_required
def secure_media(filename):
    """ ✅ Serve media (images, videos, or audio) ONLY to logged-in users securely """
    file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)

    if not os.path.exists(file_path):
        flash("Media not found!", "danger")
        return redirect(url_for("app_routes.index"))

    return send_file(file_path)

@app_routes.route("/edit_media/<int:media_id>", methods=["GET", "POST"])
@login_required
def edit_media(media_id):
    media = Media.query.get_or_404(media_id)

    if request.method == "POST":
        media.title = request.form["title"]
        media.price = request.form["price"]
        media.media_type = request.form["media_type"]  # ✅ Update media type
        db.session.commit()
        flash("Media updated successfully!", "success")
        return redirect(url_for("app_routes.admin"))

    return render_template("edit_media.html", media=media)




@app_routes.route("/download/<int:media_id>")
@login_required
def download(media_id):
    """Serve media for download and reset purchase status only after download."""
    payment = Payment.query.filter_by(user_id=current_user.id, media_id=media_id, status="paid").first()

    if not payment:
        flash("You need to purchase this media first.", "danger")
        return redirect(url_for("app_routes.index"))

    media = Media.query.get_or_404(media_id)
    file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], media.filename)

    if not os.path.exists(file_path):
        flash("File not found!", "danger")
        return redirect(url_for("app_routes.index"))

    # ✅ Detect MIME type dynamically
    ext = media.filename.lower().split(".")[-1]
    mimetype_map = {
        "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
        "gif": "image/gif", "webp": "image/webp", "bmp": "image/bmp",
        "tiff": "image/tiff", "tif": "image/tiff",
        "mp4": "video/mp4", "mkv": "video/x-matroska", "avi": "video/x-msvideo",
        "mov": "video/quicktime", "wmv": "video/x-ms-wmv",
        "mp3": "audio/mpeg", "wav": "audio/wav", "ogg": "audio/ogg", "flac": "audio/flac"
    }
    mimetype = mimetype_map.get(ext, "application/octet-stream")

    # ✅ Reset purchase status **AFTER** the file is sent successfully
    @after_this_request
    def remove_purchase(response):
        db.session.delete(payment)
        db.session.commit()
        return response

    return send_file(file_path, as_attachment=True, mimetype=mimetype, download_name=media.filename)


@app_routes.route("/admin", methods=["GET", "POST"])
@login_required
def admin():
    if not current_user.is_admin:
        flash("Access Denied! Admins only.", "danger")
        return redirect(url_for("app_routes.index"))  # ✅ Prevent unauthorized access

    if request.method == "POST":
        title = request.form["title"]
        price = request.form["price"]
        file = request.files["file"]
        media_type = request.form["media_type"]  # ✅ Type: 'image', 'audio', 'video'

        if file:
            filename = file.filename
            base, ext = os.path.splitext(filename)

            # ✅ Auto-rename file if it exists
            counter = 1
            while Media.query.filter_by(filename=filename).first():
                filename = f"{base}_{counter}{ext}"
                counter += 1

            # ✅ Ensure upload directory exists
            upload_folder = os.path.join(current_app.root_path, "static", "uploads")
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)

            # ✅ Save file
            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)

            # ✅ Store in database
            new_media = Media(title=title, filename=filename, price=price, media_type=media_type)
            db.session.add(new_media)
            db.session.commit()
            flash("Media uploaded successfully!", "success")

    media_files = Media.query.all()
    return render_template("admin.html", media_files=media_files)


@app_routes.route("/pay/<int:media_id>")
@login_required
def pay(media_id):
    media = Media.query.get_or_404(media_id)
    paystack_url = "https://api.paystack.co/transaction/initialize"

    headers = {"Authorization": f"Bearer {current_app.config['PAYSTACK_SECRET_KEY']}"}
    data = {
        "email": current_user.email,
        "amount": int(media.price * 100),
        "callback_url": url_for("app_routes.confirm_payment", media_id=media.id, _external=True)
    }

    response = requests.post(paystack_url, headers=headers, json=data)
    response_data = response.json()

    if response_data.get("status"):
        return redirect(response_data["data"]["authorization_url"])
    else:
        flash("Payment initialization failed.", "danger")
        return redirect(url_for("app_routes.index"))


@app_routes.route("/confirm/<int:media_id>")
@login_required
def confirm_payment(media_id):
    reference = request.args.get("reference")
    verify_url = f"https://api.paystack.co/transaction/verify/{reference}"

    headers = {"Authorization": f"Bearer {current_app.config['PAYSTACK_SECRET_KEY']}"}
    response = requests.get(verify_url, headers=headers)
    response_data = response.json()

    if response_data["data"]["status"] == "success":
        new_payment = Payment(user_id=current_user.id, media_id=media_id, reference=reference, status="paid")
        db.session.add(new_payment)
        db.session.commit()
        flash("Payment successful! You can now download the media.", "success")
    else:
        flash("Payment failed.", "danger")

    return redirect(url_for("app_routes.index"))


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))
