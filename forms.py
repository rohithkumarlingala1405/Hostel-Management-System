from flask_wtf import FlaskForm
from wtforms import (
    StringField, IntegerField, TextAreaField,
    SelectField, PasswordField, SubmitField
)
from wtforms.validators import (
    DataRequired, Email, Optional,
    Length, NumberRange,InputRequired
)


class LoginForm(FlaskForm):
    """Form for user login."""
    username = StringField('Username', validators=[
        DataRequired(message='Username is required.')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required.')
    ])
    submit = SubmitField('Sign In')


class StudentForm(FlaskForm):
    name = StringField('Full Name', validators=[
        DataRequired(message='Name is required.'),
        Length(min=2, max=100, message='Name must be between 2 and 100 characters.')
    ])
    roll_no = StringField('Roll Number', validators=[
        DataRequired(message='Roll number is required.'),
        Length(min=2, max=20, message='Roll number must be between 2 and 20 characters.')
    ])
    email = StringField('Email', validators=[
        Optional(),
        Email(message='Please enter a valid email address.')
    ])
    gender = SelectField('Gender', choices=[
        ('Male',   'Male'),
        ('Female', 'Female'),
    ], validators=[DataRequired(message='Please select a gender.')])
    room_id = SelectField('Assign Room', coerce=int, validators=[Optional()])
    submit  = SubmitField('Save')


class RoomForm(FlaskForm):
    block = SelectField('Block', choices=[
        ('', '— Select Block —'),
        ('B1', 'B1 — Boys Block 1'),
        ('B2', 'B2 — Boys Block 2'),
        ('B3', 'B3 — Boys Block 3'),
        ('G1', 'G1 — Girls Block 1'),
    ], validators=[DataRequired(message='Please select a block.')])

    room_number = StringField('Room Number', validators=[
        DataRequired(message='Room number is required.'),
        Length(min=1, max=10, message='Room number must be under 10 characters.')
    ])
    floor = IntegerField('Floor', validators=[
        InputRequired(message='Floor is required.'),
        NumberRange(min=0, max=50, message='Floor must be between 0 and 50.')
    ])
    capacity = IntegerField('Capacity', validators=[
        DataRequired(message='Capacity is required.'),
        NumberRange(min=1, max=20, message='Capacity must be between 1 and 20.')
    ])
    submit = SubmitField('Save')


class ComplaintForm(FlaskForm):
    """Form for submitting complaints."""
    student_id = SelectField('Student', coerce=int, validators=[
        DataRequired(message='Please select a student.')
    ])
    title = StringField('Complaint Title', validators=[
        DataRequired(message='Title is required.'),
        Length(min=3, max=200, message='Title must be between 3 and 200 characters.')
    ])
    description = TextAreaField('Description', validators=[
        DataRequired(message='Description is required.'),
        Length(min=10, message='Please describe the issue in at least 10 characters.')
    ])
    submit = SubmitField('Submit Complaint')