from flask import Blueprint, redirect, url_for, render_template, session
from functools import wraps
from app.auth import is_logged_in

user_bp = Blueprint('user', __name__, url_prefix='/user')

# ── Login required decorator ──────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not is_logged_in():
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

# ── Routes ────────────────────────────────────────────
@user_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('user/dashboard.html')

@user_bp.route('/profile')
@login_required
def profile():
    return render_template('user/dashboard.html')  # placeholder

@user_bp.route('/settings')
@login_required
def settings():
    return render_template('user/dashboard.html')  # placeholder

@user_bp.route('/safety')
@login_required
def safety():
    return render_template('user/dashboard.html')  # placeholder

@user_bp.route('/notifications')
@login_required
def notifications():
    return render_template('user/dashboard.html')  # placeholder

@user_bp.route('/support')
@login_required
def support():
    return render_template('user/dashboard.html')  # placeholder