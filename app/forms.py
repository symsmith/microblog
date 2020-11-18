"""
Definition of forms in the app
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField,\
    TextAreaField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo,\
    Length
from app.models import User
from flask import request
import re


class LoginForm(FlaskForm):
    """
    Login form
    """
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    """
    Registration/user creation form
    """
    username = StringField('Username', validators=[
                           DataRequired(), Length(min=1, max=24)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[
                             DataRequired(), Length(min=6)])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        """
        Checks if the username isn't already used
        """
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')
        if re.fullmatch(r"[a-z0-9_]+", username.data) is None:
            raise ValidationError('Please only use a-z, 0-9 and _')

    def validate_email(self, email):
        """
        Checks if the email isn't already used
        """
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')


class EditProfileForm(FlaskForm):
    """
    Profile editor form
    """
    username = StringField('Username', validators=[
                           DataRequired(), Length(min=1, max=24)])
    about_me = TextAreaField('About me', validators=[Length(min=0, max=140)])
    submit = SubmitField('Edit')

    def __init__(self, original_username, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        """
        Checks if the username isn't already used
        """
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username.')
            if re.fullmatch(r"[a-z0-9_]+", username.data) is None:
                raise ValidationError('Please only use a-z, 0-9 and _')


class PostForm(FlaskForm):
    """
    Posting form
    """
    post = TextAreaField('Say something',
                         validators=[DataRequired(), Length(min=1, max=140)])
    submit = SubmitField('Post')


class SearchForm(FlaskForm):
    """
    Post search form
    """
    q = StringField('Search', validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        if 'formdata' not in kwargs:
            kwargs['formdata'] = request.args
        if 'csrf_enabled' not in kwargs:
            kwargs['csrf_enabled'] = False
        super().__init__(*args, **kwargs)


class EmptyForm(FlaskForm):
    """
    Empty form (single button)
    """
    submit = SubmitField('Submit')


class ResetPasswordRequestForm(FlaskForm):
    """
    Password reset request form
    """
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Reset Password')


class ResetPasswordForm(FlaskForm):
    """
    Password reset form
    """
    password = PasswordField('New Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat New Password',
        validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')
