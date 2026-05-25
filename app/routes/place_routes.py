from flask import Blueprint, render_template, session, redirect, url_for
from app.routes.user_routes import login_required

place_bp = Blueprint('place', __name__, url_prefix='/place')

@place_bp.route('/saved')
@login_required
def saved():
    return render_template('place/saved.html')
