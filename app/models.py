"""
Database models
"""
from datetime import datetime
from time import time
from werkzeug.security import generate_password_hash, check_password_hash
from hashlib import md5
import jwt
from flask_login import UserMixin
from app import app, db, login
from app.search import add_to_index, remove_from_index, query_index

"""
Association table between followers and followed
"""
followers = db.Table('followers',
                     db.Column('follower_id',
                               db.Integer,
                               db.ForeignKey('user.id')),
                     db.Column('followed_id',
                               db.Integer,
                               db.ForeignKey('user.id')))


class SearchableMixin:
    """
    Mixin for searchable objects
    """
    @classmethod
    def search(cls, expression, page, per_page):
        """
        Replaces the list of ids found by objects
        """
        ids, total = query_index(cls.__tablename__, expression, page, per_page)
        if len(ids) == 0:
            return cls.query.filter_by(id=0), 0
        when = []
        for i in range(len(ids)):
            when.append((ids[i], i))
        return cls.query.filter(cls.id.in_(ids)).order_by(
            db.case(when, value=cls.id)), total

    @classmethod
    def before_commit(cls, session):
        """
        Save changes before we commit to the database
        """
        session._changes = {
            'add': list(session.new),
            'update': list(session.dirty),
            'delete': list(session.deleted)
        }

    @classmethod
    def after_commit(cls, session):
        """
        Pass the changes made by the commit to the search index
        """
        for obj in session._changes['add']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['update']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['delete']:
            if isinstance(obj, SearchableMixin):
                remove_from_index(obj.__tablename__, obj)
        session._changes = None

    @classmethod
    def reindex(cls):
        """
        Refresh an index with all the data from the relational side
        """
        for obj in cls.query:
            add_to_index(cls.__tablename__, obj)


db.event.listen(db.session, 'before_commit', SearchableMixin.before_commit)
db.event.listen(db.session, 'after_commit', SearchableMixin.after_commit)


class User(UserMixin, db.Model):
    """
    User database model
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

    followed = db.relationship(
        # 'what is followed' ('what follows' is defined by the parent class)
        'User',
        # association table
        secondary=followers,
        # condition that links the the follower with the association table
        primaryjoin=(followers.c.follower_id == id),
        # condition that links the the followed with the association table
        secondaryjoin=(followers.c.followed_id == id),
        # how the relationship will be accessed by the followed
        backref=db.backref('followers', lazy='dynamic'),
        # execution mode of the query
        lazy='dynamic')

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        """
        Hashes the given password and adds it to the user
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """
        Checks if the given password matches the database entry
        """
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        """
        Returns the avatar of the user using Gravatar with a specific size
        """
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f"//www.gravatar.com/avatar/{digest}?s={size}"\
            f"&d={app.config['AVATAR_STYLE']}"

    def follow(self, user):
        """
        Follows the user
        """
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        """
        Unfollows the user
        """
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        """
        Checks if the user is followed
        """
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0

    def followed_posts(self):
        """
        Returns the posts of all the followed users + the ones of the user
        """
        followed = Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)).filter(
                followers.c.follower_id == self.id)
        own = Post.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Post.timestamp.desc())

    def get_reset_password_token(self, expires_in=900):
        """
        Returns the password reset token for the user
        By default expires after 15 minutes
        """
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        """
        Returns the user id associated with the token if it is valid
        """
        try:
            user_id = jwt.decode(token, app.config['SECRET_KEY'],
                                 algorithms=['HS256'])['reset_password']
        except:
            return None
        return User.query.get(user_id)


class Post(SearchableMixin, db.Model):
    """
    Post database model
    """
    __searchable__ = ['body']
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return f'<Post {self.body}>'


@login.user_loader
def load_user(user_id):
    """
    Loads the user corresponding to the given id
    """
    return User.query.get(int(user_id))
