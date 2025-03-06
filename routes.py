from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory, current_app
from flask_login import login_user, logout_user, login_required, current_user
from models import User, PREDEFINED_USERS, db, Image, Payment
import requests
import os
from flask import send_from_directory
from flask import send_file
from flask_login import login_required

# Define Blueprints
app_routes = Blueprint("app_routes", __name__)
auth = Blueprint("auth", __name__)

@app_routes.route("/")
@login_required
def index():
    images = Image.query.all()

    # ✅ Set of purchased images (Tracks purchases)
    purchased_images = {payment.image_id for payment in Payment.query.filter_by(user_id=current_user.id, status="paid").all()}

    return render_template("index.html", images=images, purchased_images=purchased_images)


@app_routes.route("/secure_image/<filename>")
@login_required
def secure_image(filename):
    """ ✅ Serve image ONLY to logged-in users securely """
    file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)

    if not os.path.exists(file_path):
        flash("Image not found!", "danger")
        return redirect(url_for("app_routes.index"))

    return send_file(file_path, mimetype="image/jpeg")  # Adjust for PNG if needed



    

@app_routes.route("/download/<int:image_id>")
@login_required
def download(image_id):
    # ✅ Check if the user has purchased the image
    payment = Payment.query.filter_by(user_id=current_user.id, image_id=image_id, status="paid").first()
    
    if not payment:
        flash("You need to purchase this image first.", "danger")
        return redirect(url_for("app_routes.index"))

    # ✅ Remove payment record to reset the purchase status
    db.session.delete(payment)
    db.session.commit()

    # ✅ Refresh the page so "Buy" button returns
    flash("Download successful! You can now re-purchase if needed.", "success")
    return redirect(url_for("app_routes.index"))









# ✅ Route for Editing Image
@app_routes.route("/edit_image/<int:image_id>", methods=["GET", "POST"])
@login_required
def edit_image(image_id):
    if not current_user.is_admin:
        flash("Access Denied!", "danger")
        return redirect(url_for("app_routes.index"))

    image = Image.query.get_or_404(image_id)

    if request.method == "POST":
        image.title = request.form["title"]
        image.price = request.form["price"]
        db.session.commit()
        flash("Image details updated successfully!", "success")
        return redirect(url_for("app_routes.admin"))

    return render_template("edit_image.html", image=image)

# ✅ Route for Deleting Image
@app_routes.route("/delete_image/<int:image_id>", methods=["POST"])
@login_required
def delete_image(image_id):
    if not current_user.is_admin:
        flash("Access Denied!", "danger")
        return redirect(url_for("app_routes.index"))

    image = Image.query.get_or_404(image_id)

    # Delete image file from static/uploads/
    file_path = os.path.join(current_app.root_path, "static", "uploads", image.filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    # Remove from database
    db.session.delete(image)
    db.session.commit()
    flash("Image deleted successfully!", "success")

    return redirect(url_for("app_routes.admin"))

@auth.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))


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

        if file:
            filename = file.filename
            base, ext = os.path.splitext(filename)

            # ✅ Auto-rename file if it exists
            counter = 1
            while Image.query.filter_by(filename=filename).first():
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
            new_image = Image(title=title, filename=filename, price=price)
            db.session.add(new_image)
            db.session.commit()
            flash("Image uploaded successfully!", "success")

    images = Image.query.all()
    return render_template("admin.html", images=images)




@app_routes.route("/pay/<int:image_id>")
@login_required
def pay(image_id):
    image = Image.query.get_or_404(image_id)
    paystack_url = "https://api.paystack.co/transaction/initialize"
    
    headers = {"Authorization": f"Bearer {current_app.config['PAYSTACK_SECRET_KEY']}"}
    data = {
        "email": current_user.email,
        "amount": int(image.price * 100),
        "callback_url": url_for("app_routes.confirm_payment", image_id=image.id, _external=True)
    }

    response = requests.post(paystack_url, headers=headers, json=data)
    response_data = response.json()

    if response_data.get("status"):
        return redirect(response_data["data"]["authorization_url"])
    else:
        flash("Payment initialization failed.", "danger")
        return redirect(url_for("app_routes.index"))

@app_routes.route("/confirm/<int:image_id>")
@login_required
def confirm_payment(image_id):
    reference = request.args.get("reference")
    verify_url = f"https://api.paystack.co/transaction/verify/{reference}"
    
    headers = {"Authorization": f"Bearer {current_app.config['PAYSTACK_SECRET_KEY']}"}
    response = requests.get(verify_url, headers=headers)
    response_data = response.json()
    
    if response_data["data"]["status"] == "success":
        new_payment = Payment(user_id=current_user.id, image_id=image_id, reference=reference, status="paid")
        db.session.add(new_payment)
        db.session.commit()
        flash("Payment successful! You can now download the image.", "success")
    else:
        flash("Payment failed.", "danger")
    
    return redirect(url_for("app_routes.index"))


