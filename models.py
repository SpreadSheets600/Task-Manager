from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(256), unique=True, nullable=False)
    email = db.Column(db.String(256), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    tasks = db.relationship("Task", backref="owner", lazy="dynamic")

    def __repr__(self):
        return f"<User {self.username}>"


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    completed = db.Column(db.Boolean, default=False)
    priority = db.Column(db.String(20), default="medium")
    status = db.Column(db.String(20), default="pending")
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"))

    is_recurring = db.Column(db.Boolean, default=False)
    recurrence_type = db.Column(db.String(20))
    recurrence_interval = db.Column(db.Integer, default=1)

    subtasks = db.relationship(
        "SubTask", backref="parent", lazy="dynamic", cascade="all, delete-orphan"
    )
    tags = db.relationship(
        "Tag", secondary="task_tags", backref=db.backref("tasks", lazy="dynamic")
    )

    def __repr__(self):
        return f"<Task {self.title}>"


class SubTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    task_id = db.Column(db.Integer, db.ForeignKey("task.id"))

    def __repr__(self):
        return f"<SubTask {self.title}>"


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(7), default="#607D8B")
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    tasks = db.relationship("Task", backref="category", lazy="dynamic")

    def __repr__(self):
        return f"<Category {self.name}>"


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)

    def __repr__(self):
        return f"<Tag {self.name}>"


task_tags = db.Table(
    "task_tags",
    db.Column("task_id", db.Integer, db.ForeignKey("task.id"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("tag.id"), primary_key=True),
)
