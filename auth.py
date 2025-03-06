from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import User

# Define the Blueprint for authentication routes
auth = Blueprint("auth", __name__)

@auth.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("app_routes.index"))
    
    if request.method == "POST":
        username = request.form.get("username")  # ✅ Use username instead of email
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()  # ✅ Search by username

        if user and user.check_password(password):
            login_user(user)
            flash("Login successful!", "success")

            # ✅ Debugging output (Check console)
            print(f"User logged in: {user.username}, is_admin: {user.is_admin}")

            if user.is_admin:
                print("🔄 Redirecting admin to admin panel...")
                return redirect(url_for("app_routes.admin"))  # ✅ Redirect to admin.html
            
            print("🔄 Redirecting user to gallery...")
            return redirect(url_for("app_routes.index"))  # ✅ Redirect normal users

        # ❌ Incorrect login
        flash("Invalid username or password", "danger")

    return render_template("login.html", hide_navbar=True)


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))
