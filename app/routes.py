"""
Routes for the app
"""

from flask import render_template, flash, redirect, url_for, request, g
from flask_login import current_user, login_user, logout_user, login_required
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, EmptyForm,\
    PostForm, ResetPasswordRequestForm, ResetPasswordForm, SearchForm
from app.models import User, Post
from app.email import send_password_reset_email
from werkzeug.urls import url_parse
from datetime import datetime


def post(form):
    """
    Creates a post using the submitted form
    """
    created_post = Post(body=form.post.data, author=current_user)
    db.session.add(created_post)
    db.session.commit()
    flash('Posted!')


@app.route('/', methods=['POST', 'GET'])
@login_required
def index():
    """
    Main page
    """
    post_form = PostForm()
    delete_form = EmptyForm()
    page = request.args.get('page', 1, type=int)
    if post_form.validate_on_submit():
        post(post_form)
        return redirect(redirect_url())
    posts = current_user.followed_posts().paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('index',
                       page=posts.prev_num if posts.prev_num > 1 else None) \
        if posts.has_prev else None
    return render_template('index.html',
                           form=post_form,
                           posts=posts.items,
                           next_url=next_url,
                           prev_url=prev_url,
                           delete_form=delete_form)


@app.route('/explore', methods=['GET', 'POST'])
@login_required
def explore():
    """
    Explore all posts
    """
    post_form = PostForm()
    delete_form = EmptyForm()
    page = request.args.get('page', 1, type=int)
    if post_form.validate_on_submit():
        post(post_form)
        return redirect(redirect_url())
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('explore', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('explore',
                       page=posts.prev_num if posts.prev_num > 1 else None) \
        if posts.has_prev else None
    return render_template('index.html',
                           title='All posts',
                           form=post_form,
                           posts=posts.items,
                           next_url=next_url,
                           prev_url=prev_url,
                           delete_form=delete_form)


@app.route('/search')
@login_required
def search():
    """
    Search results page
    """
    delete_form = EmptyForm()
    if not g.search_form.validate():
        return redirect(url_for('explore'))
    query = g.search_form.q.data
    page = request.args.get('page', 1, type=int)
    if page <= 0:
        return redirect(url_for('index'))
    posts, total = Post.search(query,
                               page,
                               app.config['POSTS_PER_PAGE'])
    next_url = url_for('search', q=query, page=page + 1) \
        if total > page * app.config['POSTS_PER_PAGE'] else None
    prev_url = url_for('search', q=query, page=page - 1) \
        if page > 1 else None
    return render_template('search.html',
                           title=query,
                           total=total,
                           posts=posts,
                           next_url=next_url,
                           prev_url=prev_url,
                           delete_form=delete_form)


@app.route('/delete/<post_id>', methods=['POST', 'GET'])
@login_required
def delete_post(post_id):
    """
    Delete post
    """
    form = EmptyForm()
    if form.validate_on_submit():
        target_post = Post.query.filter_by(id=post_id).first_or_404()
        if target_post.author == current_user:
            db.session.delete(target_post)
            db.session.commit()
            flash('Post deleted')
    return redirect(redirect_url())


@app.route('/login', methods=['POST', 'GET'])
def login():
    """
    Login page
    """
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()

    if form.validate_on_submit():
        user_to_log = User.query.filter_by(username=form.username.data).first()

        if (user_to_log is None or
                not user_to_log.check_password(form.password.data)):
            flash('Invalid username or password', 'error')
            return redirect(url_for('login'))

        login_user(user_to_log, remember=form.remember_me.data)

        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')

        return redirect(next_page)

    return render_template('login.html', form=form, title='Login')


@app.route('/logout')
def logout():
    """
    Logout page
    """
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['POST', 'GET'])
def register():
    """
    Account creation page
    """
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = RegistrationForm()

    if form.validate_on_submit():
        new_user = User(username=form.username.data, email=form.email.data)
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created!')
        return redirect(url_for('login'))

    return render_template('register.html', title='Register', form=form)


@app.route('/forgotten', methods=['GET', 'POST'])
def reset_password_request():
    """
    Password reset request page
    """
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        target_user = User.query.filter_by(email=form.email.data).first()
        if target_user:
            send_password_reset_email(target_user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title='Reset password',
                           form=form)


@app.route('/reset/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """
    Password reset page
    """
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    target_user = User.verify_reset_password_token(token)
    if not target_user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        target_user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)


@app.route('/user/<username>', methods=['POST', 'GET'])
@login_required
def user(username):
    """
    User profile page
    """
    post_form = PostForm()
    delete_form = EmptyForm()
    follow_form = EmptyForm()
    profile_user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    if post_form.validate_on_submit():
        post(post_form)
        return redirect(redirect_url())
    posts = profile_user.posts.order_by(Post.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('user',
                       username=profile_user.username,
                       page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('user',
                       username=profile_user.username,
                       page=posts.prev_num if posts.prev_num > 1 else None) \
        if posts.has_prev else None
    return render_template('user.html',
                           title=profile_user.username,
                           user=profile_user,
                           posts=posts.items,
                           follow_form=follow_form,
                           delete_form=delete_form,
                           post_form=post_form,
                           next_url=next_url,
                           prev_url=prev_url)


@app.route('/edit', methods=['POST', 'GET'])
@login_required
def edit_profile():
    """
    Profile edition page
    """
    form = EditProfileForm(current_user.username)
    delete_form = EmptyForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved')
        return redirect(url_for('user', username=current_user.username))
    if request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html',
                           title='Edit profile',
                           form=form,
                           delete_form=delete_form)


@app.route('/delete-account', methods=['GET', 'POST'])
@login_required
def delete_account():
    """
    Delete account processing
    """
    delete_form = EmptyForm()
    if delete_form.validate_on_submit():
        user = User.query.filter_by(username=current_user.username).first()
        for post in user.posts:
            db.session.delete(post)
        db.session.delete(user)
        db.session.commit()
        flash('Your account was deleted')
        return redirect(url_for('login'))
    return redirect(redirect_url())


@app.route('/user/<username>/popup')
@login_required
def user_popup(username):
    """
    Profile page popup
    """
    target_user = User.query.filter_by(username=username).first_or_404()
    form = EmptyForm()
    return render_template('user_popup.html', user=target_user, form=form)


@app.before_request
def before_request():
    """
    Logic happening before the request
    """
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
        g.search_form = SearchForm()


@app.route('/toggle-follow/<username>', methods=['POST', 'GET'])
@login_required
def toggle_follow(username):
    """
    Follow or unfollow user
    """
    form = EmptyForm()
    if form.validate_on_submit():
        target_user = User.query.filter_by(username=username).first()
        if target_user is None:
            flash(f'User {username} not found', 'error')
            return redirect(url_for('index'))

        if target_user == current_user:
            flash('You cannot follow or unfollow yourself', 'error')
            return redirect(url_for('user', username=username))

        if current_user.is_following(target_user):
            current_user.unfollow(target_user)
            flash(f'You unfollowed {username}!')
        else:
            current_user.follow(target_user)
            flash(f'You followed {username}!')

        db.session.commit()
        return redirect(redirect_url())
    return redirect(url_for('index'))


@app.errorhandler(404)
def not_found_error(error):
    """
    Handles 404 error
    """
    return render_template('404.html', title='Not found'), 404


@app.errorhandler(500)
def internal_error(error):
    """
    Handles 500 error
    """
    db.session.rollback()
    return render_template('500.html', title='Internal error'), 500


def redirect_url(default='index'):
    """
    Returns the previous url visited
    """
    return request.args.get('next') or request.referrer or url_for(default)
