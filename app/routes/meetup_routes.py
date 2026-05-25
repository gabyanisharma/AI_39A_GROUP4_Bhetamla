from flask import Blueprint, redirect, url_for
from app.controllers.meetup_controller import (
    scheduler, add_availability, delete_availability,
    search_users, send_friend_request, respond_friend_request,
    create_schedule, respond_invite, get_common_availability
)

meetup_bp = Blueprint('meetup', __name__, url_prefix='/meetup')

@meetup_bp.route('/plan')
def plan():
    return redirect(url_for('meetup.scheduler_page'))

@meetup_bp.route('/groups')
def groups():
    return redirect(url_for('meetup.scheduler_page'))

@meetup_bp.route('/scheduler')
def scheduler_page():
    return scheduler()

@meetup_bp.route('/add-availability',        methods=['POST'])
def add_availability_route():
    return add_availability()

@meetup_bp.route('/delete-availability/<int:slot_id>')
def delete_availability_route(slot_id):
    return delete_availability(slot_id)

@meetup_bp.route('/search-users')
def search_users_route():
    return search_users()

@meetup_bp.route('/send-friend-request',     methods=['POST'])
def send_friend_request_route():
    return send_friend_request()

@meetup_bp.route('/respond-friend-request/<int:request_id>', methods=['POST'])
def respond_friend_request_route(request_id):
    return respond_friend_request(request_id)

@meetup_bp.route('/create-schedule',         methods=['POST'])
def create_schedule_route():
    return create_schedule()

@meetup_bp.route('/respond-invite/<int:invite_id>', methods=['POST'])
def respond_invite_route(invite_id):
    return respond_invite(invite_id)

@meetup_bp.route('/common-availability')
def common_availability_route():
    return get_common_availability()