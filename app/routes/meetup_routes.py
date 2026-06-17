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
from app.controllers.meetup_route_controller import (
    get_meetup_route, save_meetup_route, delete_meetup_route
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
    from app.auth import get_current_user_id
    from app.models.meetup import Meetup
    from app.database import execute_query
    user_id = get_current_user_id()
    meetups = Meetup.get_by_user(user_id)
    friends = execute_query(
        """SELECT u.id, u.full_name, u.email
           FROM friends f
           JOIN users u ON (
               CASE WHEN f.user_id = %s THEN f.friend_id = u.id
               ELSE f.user_id = u.id END
           )
           WHERE (f.user_id = %s OR f.friend_id = %s)
           AND f.status = 'accepted'""",
        (user_id, user_id, user_id), fetch=True
    ) or []
    return render_template('meetup/groups.html', meetups=meetups, friends=friends)

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

@meetup_bp.route('/<int:meetup_id>/route', methods=['GET'])
@login_required
def route_detail(meetup_id):
    return get_meetup_route(meetup_id)

@meetup_bp.route('/<int:meetup_id>/route', methods=['POST'])
@login_required
def route_save(meetup_id):
    return save_meetup_route(meetup_id)

@meetup_bp.route('/<int:meetup_id>/route', methods=['DELETE'])
@login_required
def route_delete(meetup_id):
    return delete_meetup_route(meetup_id)