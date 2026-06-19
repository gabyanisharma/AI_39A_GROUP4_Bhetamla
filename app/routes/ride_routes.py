from flask import Blueprint
from app.routes.user_routes import login_required
from app.controllers.ride_controller import (
    ride_estimate_page,
    calculate_estimate,
    budget_split,
    route_planner_page,
    save_route,
    delete_route,
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

@ride_bp.route('/planner')
@login_required
def planner():
    return route_planner_page()

@ride_bp.route('/planner/save', methods=['POST'])
@login_required
def planner_save():
    return save_route()

@ride_bp.route('/planner/delete/<int:route_id>', methods=['POST'])
@login_required
def planner_delete(route_id):
    return delete_route(route_id)