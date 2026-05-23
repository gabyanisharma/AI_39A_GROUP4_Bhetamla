from flask import Blueprint, redirect, url_for

meetup_bp = Blueprint('meetup', __name__, url_prefix='/meetup')

# ── Routes ────────────────────────────────────────────
@meetup_bp.route('/plan')
def plan():
    return redirect(url_for('user.dashboard'))  # placeholder

@meetup_bp.route('/groups')
def groups():
    return redirect(url_for('user.dashboard'))  # placeholder