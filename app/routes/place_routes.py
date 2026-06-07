from flask import Blueprint, render_template, session, redirect, url_for
from app.controllers.place_controller import restaurants, api_filter_restaurants
from app.routes.user_routes import login_required

place_bp = Blueprint('place', __name__, url_prefix='/place')

@place_bp.route('/saved')
@login_required
def saved():
    return redirect(url_for('user.dashboard'))  # placeholder§