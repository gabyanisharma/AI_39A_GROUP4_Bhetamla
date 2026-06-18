from flask import session, redirect, url_for
from functools import wraps

def login_user(user):
    """Save user info to session after login."""
    session['user_id'] = user['id']
    session['user_name'] = user['username']
    session['user_email'] = user['email']

def logout_user():
    """Clear the session."""
    session.clear()

def get_current_user_id():
    """Return logged-in user's ID or None."""
    return session.get('user_id')

def is_logged_in():
    """Return True if a user is in session."""
    return 'user_id' in session

def login_required(f):
    """Decorator to enforce login on routes."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not is_logged_in():
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated