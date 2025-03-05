import os
from datetime import datetime, timedelta

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    abort,
)
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
)

from werkzeug.security import generate_password_hash, check_password_hash
from urllib.parse import urlparse

from forms import LoginForm, RegistrationForm, TaskForm, CategoryForm, SubTaskForm
from models import db, User, Task, SubTask, Category, Tag
from config import Config

app = Flask(__name__)
app.config.from_object(Config)


db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Please log in to access this page"
login_manager.login_message_category = "info"


@app.before_request
def ensure_tables_exist():
    if not getattr(app, "_tables_created", False):
        print("Creating tables")

        with app.app_context():
            db.create_all()

            default_user = User.query.first()
            if not default_user:
                default_user = User(
                    username="SOHAM",
                    email="SOHAM@SOHAM.com",
                    password_hash="SOHAM",
                )
                db.session.add(default_user)
                db.session.commit()

            app._tables_created = True
            app.default_user_id = default_user.id


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.route("/login", methods=["GET", "POST"])
def login():
    return render_template("auth/login.html", title="Sign In")


@app.route("/register", methods=["GET", "POST"])
def register():
    return render_template("auth/register.html", title="Register")


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/")
def index():
    default_user = User.query.first()

    today = datetime.utcnow().date()
    today_tasks = (
        Task.query.filter_by(user_id=default_user.id)
        .filter(db.func.date(Task.due_date) == today)
        .order_by(Task.priority.desc())
        .all()
    )

    upcoming_tasks = (
        Task.query.filter_by(user_id=default_user.id)
        .filter(db.func.date(Task.due_date) > today)
        .order_by(Task.due_date)
        .limit(5)
        .all()
    )

    overdue_tasks = (
        Task.query.filter_by(user_id=default_user.id)
        .filter(Task.due_date < datetime.utcnow(), Task.completed == False)
        .order_by(Task.due_date)
        .all()
    )

    return render_template(
        "index.html",
        title="Dashboard",
        today_tasks=today_tasks,
        upcoming_tasks=upcoming_tasks,
        overdue_tasks=overdue_tasks,
        today=today,
    )


@app.route("/tasks/daily")
def daily_tasks():
    default_user = User.query.first()

    today = datetime.utcnow().date()
    tasks = (
        Task.query.filter_by(user_id=default_user.id)
        .filter(db.func.date(Task.due_date) == today)
        .order_by(Task.priority.desc())
        .all()
    )

    categories = Category.query.filter_by(user_id=default_user.id).all()

    return render_template(
        "tasks/daily.html",
        title="Daily Tasks",
        tasks=tasks,
        categories=categories,
        view_mode="daily",
    )


@app.route("/tasks/weekly")
def weekly_tasks():
    default_user = User.query.first()

    today = datetime.utcnow().date()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    tasks = (
        Task.query.filter_by(user_id=default_user.id)
        .filter(
            db.func.date(Task.due_date) >= start_of_week,
            db.func.date(Task.due_date) <= end_of_week,
        )
        .order_by(Task.due_date, Task.priority.desc())
        .all()
    )

    tasks_by_day = {}
    for i in range(7):
        day = start_of_week + timedelta(days=i)
        tasks_by_day[day] = []

    for task in tasks:
        if task.due_date:
            day = task.due_date.date()
            if day in tasks_by_day:
                tasks_by_day[day].append(task)

    categories = Category.query.filter_by(user_id=default_user.id).all()

    return render_template(
        "tasks/weekly.html",
        title="Weekly Tasks",
        tasks_by_day=tasks_by_day,
        days_of_week=list(tasks_by_day.keys()),
        categories=categories,
        view_mode="weekly",
    )


@app.route("/tasks/monthly")
def monthly_tasks():
    default_user = User.query.first()

    today = datetime.utcnow().date()
    year, month = today.year, today.month

    first_day = datetime(year, month, 1).date()
    if month == 12:
        last_day = datetime(year + 1, 1, 1).date() - timedelta(days=1)
    else:
        last_day = datetime(year, month + 1, 1).date() - timedelta(days=1)

    tasks = (
        Task.query.filter_by(user_id=default_user.id)
        .filter(
            db.func.date(Task.due_date) >= first_day,
            db.func.date(Task.due_date) <= last_day,
        )
        .order_by(Task.due_date)
        .all()
    )

    calendar_days = []
    month_start_weekday = first_day.weekday()

    for _ in range(month_start_weekday):
        calendar_days.append({"day": None, "tasks": []})

    tasks_by_day = {}
    for task in tasks:
        if task.due_date:
            day = task.due_date.day
            if day not in tasks_by_day:
                tasks_by_day[day] = []
            tasks_by_day[day].append(task)

    for day in range(1, last_day.day + 1):
        calendar_days.append({"day": day, "tasks": tasks_by_day.get(day, [])})

    categories = Category.query.filter_by(user_id=default_user.id).all()

    return render_template(
        "tasks/monthly.html",
        title="Monthly Tasks",
        calendar_days=calendar_days,
        month_name=first_day.strftime("%B"),
        year=year,
        categories=categories,
        view_mode="monthly",
    )


@app.route("/task/new", methods=["GET", "POST"])
def new_task():
    default_user = User.query.first()

    form = TaskForm()
    form.category_id.choices = [
        (c.id, c.name) for c in Category.query.filter_by(user_id=default_user.id).all()
    ]
    form.category_id.choices.insert(0, (0, "No Category"))

    if form.validate_on_submit():
        task = Task(
            title=form.title.data,
            description=form.description.data,
            due_date=form.due_date.data,
            priority=form.priority.data,
            status=form.status.data,
            user_id=default_user.id,
            is_recurring=form.is_recurring.data,
            recurrence_type=form.recurrence_type.data
            if form.is_recurring.data
            else None,
            recurrence_interval=form.recurrence_interval.data
            if form.is_recurring.data
            else None,
        )

        if form.category_id.data > 0:
            task.category_id = form.category_id.data

        if form.tags.data:
            tag_names = [tag.strip() for tag in form.tags.data.split(",")]
            for tag_name in tag_names:
                if tag_name:
                    tag = Tag.query.filter_by(name=tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name)
                        db.session.add(tag)
                    task.tags.append(tag)

        db.session.add(task)
        db.session.commit()
        flash("Task created successfully!", "success")
        return redirect(url_for("index"))

    return render_template("tasks/task_form.html", title="New Task", form=form)


@app.route("/task/<int:id>/edit", methods=["GET", "POST"])
def edit_task(id):
    default_user = User.query.first()

    task = Task.query.get_or_404(id)

    if task.user_id != default_user.id:
        abort(403)

    form = TaskForm(obj=task)
    form.category_id.choices = [
        (c.id, c.name) for c in Category.query.filter_by(user_id=default_user.id).all()
    ]
    form.category_id.choices.insert(0, (0, "No Category"))

    if task.tags:
        form.tags.data = ", ".join([tag.name for tag in task.tags])

    if form.validate_on_submit():
        task.title = form.title.data
        task.description = form.description.data
        task.due_date = form.due_date.data
        task.priority = form.priority.data
        task.status = form.status.data
        task.is_recurring = form.is_recurring.data
        task.recurrence_type = (
            form.recurrence_type.data if form.is_recurring.data else None
        )
        task.recurrence_interval = (
            form.recurrence_interval.data if form.is_recurring.data else None
        )

        if form.category_id.data > 0:
            task.category_id = form.category_id.data
        else:
            task.category_id = None

        task.tags = []
        if form.tags.data:
            tag_names = [tag.strip() for tag in form.tags.data.split(",")]
            for tag_name in tag_names:
                if tag_name:
                    tag = Tag.query.filter_by(name=tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name)
                        db.session.add(tag)
                    task.tags.append(tag)

        db.session.commit()
        flash("Task updated successfully!", "success")
        return redirect(url_for("index"))

    return render_template(
        "tasks/task_form.html", title="Edit Task", form=form, task=task
    )


@app.route("/task/<int:id>/toggle", methods=["POST"])
def toggle_task(id):
    default_user = User.query.first()

    task = Task.query.get_or_404(id)

    if task.user_id != default_user.id:
        return jsonify({"success": False, "error": "Unauthorized"}), 403

    task.completed = not task.completed
    if task.completed and task.status != "completed":
        task.status = "completed"
    elif not task.completed and task.status == "completed":
        task.status = "pending"

    db.session.commit()
    return jsonify({"success": True, "completed": task.completed})


@app.route("/task/<int:id>/delete", methods=["POST"])
def delete_task(id):
    default_user = User.query.first()

    task = Task.query.get_or_404(id)

    if task.user_id != default_user.id:
        return jsonify({"success": False, "error": "Unauthorized"}), 403

    db.session.delete(task)
    db.session.commit()
    flash("Task deleted successfully!", "success")
    return jsonify({"success": True})


@app.route("/categories", methods=["GET", "POST"])
def categories():
    default_user = User.query.first()

    form = CategoryForm()
    if form.validate_on_submit():
        category = Category(
            name=form.name.data, color=form.color.data, user_id=default_user.id
        )
        db.session.add(category)
        db.session.commit()
        flash("Category created successfully!", "success")
        return redirect(url_for("categories"))

    categories = Category.query.filter_by(user_id=default_user.id).all()
    return render_template(
        "categories.html", title="Categories", categories=categories, form=form
    )


if __name__ == "__main__":
    app.run(debug=True)
