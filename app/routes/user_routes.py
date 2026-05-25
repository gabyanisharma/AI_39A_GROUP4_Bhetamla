from flask import Blueprint, redirect, url_for, render_template, session
from functools import wraps
from app.auth import is_logged_in
from app.controllers.user_controller import (
    profile, settings, notifications, support
)
from app.controllers.notification_controller import safety

user_bp = Blueprint('user', __name__, url_prefix='/user')

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not is_logged_in():
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@user_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('user/dashboard.html')

@user_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile_page():
    return profile()

@user_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings_page():
    return settings()

@user_bp.route('/safety')
@login_required
def safety_page():
    return safety()

@user_bp.route('/notifications')
@login_required
def notifications_page():
    return notifications()

@user_bp.route('/support', methods=['GET', 'POST'])
@login_required
def support_page():
    return support()