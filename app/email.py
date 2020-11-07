"""
Simple email framework
"""
from threading import Thread
from flask import render_template
from flask_mail import Message
from app import mail, app


def send_async_email(application, msg):
    """
    Sends an email asynchroneously
    """
    with application.app_context():
        mail.send(msg)


def send_email(subject, sender, recipients, text_body, html_body):
    """
    Sends an email using flask-mail
    """
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    Thread(target=send_async_email, args=(app, msg)).start()


def send_password_reset_email(user):
    """
    Sends an email to reset the password of the user
    """
    token = user.get_reset_password_token()
    subject = 'Microblog - Reset your password'
    body = render_template('email/reset_password.txt', user=user, token=token)
    html = render_template('email/reset_password.html', user=user, token=token)
    send_email(subject, app.config['ADMINS'][0], [user.email], body, html)
