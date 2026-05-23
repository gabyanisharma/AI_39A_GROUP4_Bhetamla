from flask import Blueprint, redirect, url_for

place_bp = Blueprint('place', __name__, url_prefix='/place')

# ── Routes ────────────────────────────────────────────
@place_bp.route('/saved')
def saved():
    return redirect(url_for('user.dashboard'))  # placeholder