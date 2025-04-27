from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required
from werkzeug.security import check_password_hash
from models import User, db

auth_bp = Blueprint("auth", __name__)
login_mgr = LoginManager()

@login_mgr.user_loader
def load_user(uid):
    return User.query.get(int(uid))

@auth_bp.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        u = request.form["username"]
        p = request.form["password"]
        user = User.query.filter_by(username=u).first()
        if user and check_password_hash(user.password, p):
            login_user(user)
            return redirect(url_for("index"))
        flash("Bad creds")
    return render_template("login.html")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
