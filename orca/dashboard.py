from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from werkzeug.exceptions import abort

from orca.auth import login_required, admin_required, student_required
from orca.db import get_db

from orca.validator import is_valid_email

bp = Blueprint("dashboard", __name__)


@bp.route("/")
@login_required
def index():
    return render_template("dashboard/index.html")


@bp.route("/course")
@login_required
def course():
    db = get_db()
    courses = db.execute("SELECT * FROM course ORDER BY course_name DESC").fetchall()
    return render_template("dashboard/course.html", courses=courses)


@bp.route("/create_course", methods=("GET", "POST"))
@admin_required
def create_course():
    if request.method == "POST":
        course_id = request.form["course_id"]
        course_name = request.form["course_name"]
        error = None

        if not course_id:
            error = "Course ID is required."
        elif not course_name:
            error = "Course Name is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "INSERT INTO course (course_id, course_name)" " VALUES (?, ?)",
                (course_id, course_name),
            )
            db.commit()
            return redirect(url_for("dashboard.course"))

    return render_template("dashboard/create_course.html")


def get_course(id, check_author=True):
    course = get_db().execute("SELECT * FROM course" " WHERE id = ?", (id,)).fetchone()

    if course is None:
        abort(404, f"Course id {id} doesn't exist.")

    if check_author and g.user_type != "admin":
        abort(403)

    return course


@bp.route("/<int:id>/update_course", methods=("GET", "POST"))
@admin_required
def update_course(id):
    course = get_course(id)

    if request.method == "POST":
        course_id = request.form["course_id"]
        course_name = request.form["course_name"]
        error = None

        if not course_id:
            error = "Course ID is required."
        elif not course_name:
            error = "Course Name is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "UPDATE course SET course_id = ?, course_name = ?" " WHERE id = ?",
                (course_id, course_name, id),
            )
            db.commit()
            return redirect(url_for("dashboard.course"))

    return render_template("dashboard/update_course.html", course=course)


@bp.route("/<int:id>/delete_course", methods=("POST",))
@admin_required
def delete_course(id):
    get_course(id)
    db = get_db()
    db.execute("DELETE FROM course WHERE id = ?", (id,))
    db.commit()

    return redirect(url_for("dashboard.course"))


@bp.route("/assessment")
@student_required
def assessment():
    db = get_db()
    assessments = db.execute(
        "SELECT * FROM assessment WHERE student_id = ?", (str(g.user["id"]))
    ).fetchall()

    return render_template("dashboard/assessment.html", assessments=assessments)


@bp.route("/create_assessment", methods=("GET", "POST"))
@student_required
def create_assessment():
    db = get_db()
    courses = db.execute("SELECT * FROM course").fetchall()

    if request.method == "POST":
        course_id = request.form["course_id"]
        name = request.form["name"]
        weight = request.form["weight"]
        score = request.form["score"]

        error = None

        if not course_id:
            error = "Course ID is required."
        elif not name:
            error = "Name is required."
        elif not weight:
            error = "Weight is required."
        elif not score:
            error = "Score is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "INSERT INTO assessment (student_id, course_id, name, weight, score)"
                " VALUES (?, ?, ?, ?, ?)",
                (g.user["id"], course_id, name, weight, score),
            )
            db.commit()
            return redirect(url_for("dashboard.assessment"))

    return render_template("dashboard/create_assessment.html", courses=courses)


def get_assessment(id, check_author=True):
    assessment = (
        get_db().execute("SELECT * FROM assessment" " WHERE id = ?", (id,)).fetchone()
    )

    if assessment is None:
        abort(404, f"Assessment id {id} doesn't exist.")

    if check_author and assessment["student_id"] != g.user["id"]:
        abort(403)

    return assessment


@bp.route("/<int:id>/update_assessment", methods=("GET", "POST"))
@student_required
def update_assessment(id):
    assessment = get_assessment(id)

    if request.method == "POST":
        course_id = request.form["course_id"]
        name = request.form["name"]
        weight = request.form["weight"]
        score = request.form["score"]

        error = None

        if not course_id:
            error = "Course ID is required."
        elif not name:
            error = "Name is required."
        elif not weight:
            error = "Weight is required."
        elif not score:
            error = "Score is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "UPDATE assessment SET course_id = ?, name = ?, weight = ?, score = ?"
                " WHERE id = ?",
                (course_id, name, weight, score, id),
            )
            db.commit()
            return redirect(url_for("dashboard.assessment"))

    return render_template("dashboard/update_assessment.html", assessment=assessment)


@bp.route("/<int:id>/delete_assessment", methods=("POST",))
@login_required
def delete_assessment(id):
    get_assessment(id)
    db = get_db()
    db.execute("DELETE FROM assessment WHERE id = ?", (id,))
    db.commit()
    return redirect(url_for("dashboard.assessment"))


@bp.route("/prediction")
@student_required
def prediction():
    db = get_db()
    courses = db.execute("SELECT * FROM course").fetchall()
    predictions = []

    for course in courses:
        assessments = db.execute(
            "SELECT weight, score FROM assessment WHERE student_id = ? AND course_id = ?",
            (g.user["id"], course["course_id"]),
        ).fetchall()

        total_weight = sum(
            a["weight"] or 0 for a in assessments if a["score"] is not None
        )
        weighted_score = sum(
            (a["score"] or 0) * (a["weight"] or 0)
            for a in assessments
            if a["score"] is not None
        )

        current_grade = (weighted_score / total_weight) if total_weight else None
        print(weighted_score)
        print(total_weight)

        predictions.append(
            {
                "course": course["course_name"],
                "current_grade": current_grade,
                "total_weight": total_weight,
                "remaining": 1 - total_weight,
            }
        )

    print(predictions)

    return render_template("dashboard/prediction.html", predictions=predictions)


@bp.route("/student")
@admin_required
def student():
    db = get_db()
    students = db.execute("SELECT *" " FROM student" " ORDER BY name DESC").fetchall()
    return render_template("dashboard/student.html", students=students)


def get_student(id, check_author=True):
    student = (
        get_db().execute("SELECT *" " FROM student" " WHERE id = ?", (id,)).fetchone()
    )

    if student is None:
        abort(404, f"Student id {id} doesn't exist.")

    if check_author and g.user_type != "admin":
        abort(403)

    return student


@bp.route("/<int:id>/update_student", methods=("GET", "POST"))
@admin_required
def update_student(id):
    student = get_student(id)

    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]

        error = None

        if not name:
            error = "Name is required."
        elif not email:
            error = "Email is required."
        elif not is_valid_email(email):
            error = "Email is invalid."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "UPDATE student SET name = ?, email = ?" " WHERE id = ?",
                (name, email, id),
            )
            db.commit()
            return redirect(url_for("dashboard.student"))

    return render_template("dashboard/update_student.html", student=student)


@bp.route("/<int:id>/delete_student", methods=("POST",))
@login_required
def delete_student(id):
    get_student(id)
    db = get_db()
    db.execute("DELETE FROM student WHERE id = ?", (id,))
    db.commit()
    return redirect(url_for("dashboard.student"))
