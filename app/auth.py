from flask import session

def login_user(user):
    """Save user info to session after login."""
    session['user_id'] = user['id']
    session['user_name'] = user['full_name']
    session['user_email'] = user['email']
    session['user_pic'] = user['profile_pic']
    session['theme'] = user['theme_preference']
    session['language'] = user['language_preference']

def logout_user():
    """Clear the session."""
    session.clear()

def get_current_user_id():
    """Return logged-in user's ID or None."""
    return session.get('user_id')

def is_logged_in():
    """Return True if a user is in session."""
    return 'user_id' in session