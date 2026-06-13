from flask import Blueprint
from app.routes.user_routes import login_required
from app.controllers.ride_controller import (
    ride_estimate_page,
    calculate_estimate,
    budget_split
)

ride_bp = Blueprint('ride', __name__, url_prefix='/ride')

@ride_bp.route('/estimate/<int:meetup_id>')
@login_required
def estimate_page(meetup_id):
    return ride_estimate_page(meetup_id)

@ride_bp.route('/calculate/<int:meetup_id>', methods=['POST'])
@login_required
def calculate(meetup_id):
    return calculate_estimate(meetup_id)

@ride_bp.route('/split/<int:meetup_id>')
@login_required
def split(meetup_id):
    return budget_split(meetup_id)