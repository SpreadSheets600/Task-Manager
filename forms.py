from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    TextAreaField,
    BooleanField,
    SelectField,
    DateTimeField,
    PasswordField,
    EmailField,
    IntegerField,
)
from wtforms.validators import DataRequired, Email, Length, Optional, EqualTo


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember Me")


class RegistrationForm(FlaskForm):
    username = StringField(
        "Username", validators=[DataRequired(), Length(min=3, max=64)]
    )
    email = EmailField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password")]
    )


class TaskForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=100)])
    description = TextAreaField("Description", validators=[Optional(), Length(max=500)])
    due_date = DateTimeField(
        "Due Date", validators=[Optional()], format="%Y-%m-%dT%H:%M"
    )
    priority = SelectField(
        "Priority",
        choices=[
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
            ("urgent", "Urgent"),
        ],
    )
    status = SelectField(
        "Status",
        choices=[
            ("pending", "Pending"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("archived", "Archived"),
        ],
    )
    category_id = SelectField("Category", coerce=int)
    is_recurring = BooleanField("Recurring Task")
    recurrence_type = SelectField(
        "Recurrence Type",
        choices=[
            ("", "None"),
            ("daily", "Daily"),
            ("weekly", "Weekly"),
            ("monthly", "Monthly"),
        ],
    )
    recurrence_interval = IntegerField("Every", default=1)
    tags = StringField("Tags (comma separated)", validators=[Optional()])


class CategoryForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=50)])
    color = StringField("Color", validators=[DataRequired()], default="#607D8B")


class SubTaskForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=100)])
