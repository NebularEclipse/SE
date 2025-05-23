import functools

from flask import (
    abort,
    Blueprint,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from orca.db import get_db

from orca.validator import is_valid_email, is_strong_password

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/register", methods=("GET", "POST"))
def register():
    if request.method == "POST":
        user_type = request.form["user_type"]

        db = get_db()
        error = None

        if user_type == "student":
            student_id = request.form["student_id"].strip().lower()
            name = request.form["name"].strip()
            email = request.form["email"].strip()
            password = request.form["password"]

            if not student_id:
                error = "Student ID is required."
            elif not name:
                error = "Name is required."
            elif not email:
                error = "Email is required."
            elif not password:
                error = "Password is required."
            elif not is_valid_email(email):
                error = "Invalid email."
            elif not is_strong_password(password):
                error = "Password isn't strong enough."

            if error is None:
                try:
                    db.execute(
                        "INSERT INTO student (student_id, name, email, password) VALUES (?, ?, ?, ?)",
                        (student_id, name, email, generate_password_hash(password)),
                    )
                    db.commit()
                except db.IntegrityError:
                    error = f"User {student_id} is already registered."
                else:
                    return redirect(url_for("auth.login"))

        elif user_type == "admin":
            username = request.form["username"]
            password = request.form["password"]

            if not username:
                error = "Username is required."
            elif " " in username:
                error = "Username must not contain spaces."
            elif not password:
                error = "Password is required."
            elif not is_strong_password(password):
                error = "Password isn't strong enough."

            if error is None:
                try:
                    db.execute(
                        "INSERT INTO admin (username, password) VALUES (?, ?)",
                        (username, generate_password_hash(password)),
                    )
                    db.commit()
                except db.IntegrityError:
                    error = f"Admin {username} is already registered."
                else:
                    return redirect(url_for("auth.login"))

        flash(error)

    return render_template("auth/register.html")


@bp.route("/login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        user_type = request.form["user_type"]

        db = get_db()
        error = None

        if user_type == "student":
            student_id = request.form["student_id"]
            password = request.form["password"]

            user = db.execute(
                "SELECT * FROM student WHERE student_id = ?", (student_id,)
            ).fetchone()

            if user is None:
                error = "Incorrect Student ID."
            elif not check_password_hash(user["password"], password):
                error = "Incorrect password."

        elif user_type == "admin":
            username = request.form["username"]
            password = request.form["password"]

            user = db.execute(
                "SELECT * FROM admin WHERE username = ?", (username,)
            ).fetchone()

            if user is None:
                error = "Incorrect username."
            elif not check_password_hash(user["password"], password):
                error = "Incorrect password."

        if error is None:
            session.clear()
            session["user_id"] = user["id"]
            session["user_type"] = user_type
            return redirect(url_for("index"))

        flash(error)

    return render_template("auth/login.html")


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get("user_id")
    user_type = session.get("user_type")

    if user_id is None or user_type not in ("student", "admin"):
        g.user = None
    else:
        db = get_db()
        if user_type == "student":
            g.user = db.execute(
                "SELECT * FROM student WHERE id = ?", (user_id,)
            ).fetchone()
        else:
            g.user = db.execute(
                "SELECT * FROM admin WHERE id = ?", (user_id,)
            ).fetchone()
        g.user_type = user_type


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))

        return view(**kwargs)

    return wrapped_view


def admin_required(view):
    @functools.wraps(view)
    def wrapper_view(**kwargs):
        if g.user_type is None:
            return redirect(url_for("auth.login"))
        elif g.user_type != "admin":
            return abort(403)

        return view(**kwargs)

    return wrapper_view


def student_required(view):
    @functools.wraps(view)
    def wrapper_view(**kwargs):
        if g.user_type is None:
            return redirect(url_for("auth.login"))
        elif g.user_type != "student":
            return abort(403)

        return view(**kwargs)

    return wrapper_view
