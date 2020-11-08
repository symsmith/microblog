"""
Configuration for the app
"""

import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config():
    """
    Configuration variables for the app
    """
    SECRET_KEY = os.environ.get('SECRET_KEY') or '9C6D72F31E4289DCCE1020FA11D'\
        'C267B81E9C9F803C47000529FB2AFD4C8EE5DB26FAF234A875D75B4C0AA8B65D8103'\
        '1874B800E37C0AE6EBB9EB4E09A2DB709'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['test@mail.com']
    POSTS_PER_PAGE = 10
    # available: mp, identicon, monsterid, wavatar, retro, robohash, blank
    AVATAR_STYLE = 'retro'
    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL')
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
