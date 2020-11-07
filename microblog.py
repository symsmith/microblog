"""
Application instance for the microblog app
"""

from app import app, db
from app.models import User, Post


@app.shell_context_processor
def make_shell_context():
    """
    Commands for `flask shell`
    """
    return {'db': db, 'User': User, 'Post': Post}
