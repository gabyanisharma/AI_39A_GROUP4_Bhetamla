from flask import Blueprint, render_template, session, redirect, url_for
from app.routes.user_routes import login_required
from app.controllers.meetup_controller import (
    scheduler, add_availability, delete_availability,
    search_users, send_friend_request, respond_friend_request,
    create_schedule, respond_invite, get_common_availability,
    get_restaurants_data
)
from app.controllers.place_controller import (
    plan_meetup, create_meetup, view_meetup as view_meetup_ctrl,
    update_location, get_midpoint, add_suggestion,
    respond_meetup
)

meetup_bp = Blueprint('meetup', __name__, url_prefix='/meetup')

@meetup_bp.route('/plan')
@login_required
def plan():
    return plan_meetup()

@meetup_bp.route('/create', methods=['POST'])
@login_required
def create():
    return create_meetup()

@meetup_bp.route('/view/<int:meetup_id>')
@login_required
def view_meetup(meetup_id):
    return view_meetup_ctrl(meetup_id)

@meetup_bp.route('/update-location/<int:meetup_id>', methods=['POST'])
@login_required
def update_location_route(meetup_id):
    return update_location(meetup_id)

@meetup_bp.route('/midpoint/<int:meetup_id>')
@login_required
def midpoint_route(meetup_id):
    return get_midpoint(meetup_id)

@meetup_bp.route('/suggest/<int:meetup_id>', methods=['POST'])
@login_required
def suggest(meetup_id):
    return add_suggestion(meetup_id)

@meetup_bp.route('/respond/<int:meetup_id>', methods=['POST'])
@login_required
def respond(meetup_id):
    return respond_meetup(meetup_id)

@meetup_bp.route('/groups')
@login_required
def groups():
    return render_template('meetup/groups.html')

@meetup_bp.route('/scheduler')
@login_required
def scheduler_page():
    return scheduler()

@meetup_bp.route('/availability/add', methods=['POST'])
@login_required
def add_availability_route():
    return add_availability()

@meetup_bp.route('/availability/delete/<int:slot_id>')
@login_required
def delete_availability_route(slot_id):
    return delete_availability(slot_id)

@meetup_bp.route('/search-users')
@login_required
def search_users_route():
    return search_users()

@meetup_bp.route('/friend-request/send', methods=['POST'])
@login_required
def send_friend_request_route():
    return send_friend_request()

@meetup_bp.route('/friend-request/respond/<int:request_id>', methods=['POST'])
@login_required
def respond_friend_request_route(request_id):
    return respond_friend_request(request_id)

@meetup_bp.route('/schedule/create', methods=['POST'])
@login_required
def create_schedule_route():
    return create_schedule()

@meetup_bp.route('/invite/respond/<int:invite_id>', methods=['POST'])
@login_required
def respond_invite_route(invite_id):
    return respond_invite(invite_id)

@meetup_bp.route('/common-availability')
@login_required
def common_availability():
    return get_common_availability()
