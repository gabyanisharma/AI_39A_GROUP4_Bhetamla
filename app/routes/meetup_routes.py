from flask import Blueprint, request, render_template, session, redirect, url_for
from app.routes.user_routes import login_required
from app.controllers.meetup_controller import (
    scheduler, add_availability, delete_availability,
    search_users, send_friend_request, respond_friend_request,
    remove_friend, create_schedule, respond_invite, get_common_availability,
    get_restaurants_data
)
from app.controllers.place_controller import (
    plan_meetup, create_meetup, view_meetup as view_meetup_ctrl,
    update_location, get_midpoint, add_suggestion,
    respond_meetup, confirm_meetup_plan, delete_meetup_plan,
    complete_meetup_plan, save_plan_preferences, get_plan_preferences,
    meetup_calendar
)
from app.controllers.meetup_route_controller import (
    get_meetup_route, save_meetup_route, delete_meetup_route
)
from app.controllers.group_features_controller import (
    groups_page, hide_from_groups, start_vote, cast_vote, vote_results,
    upload_gallery, gallery_list, delete_gallery_photo, toggle_gallery_like,
    gallery_comment, gallery_privacy, chat_messages, record_budget_split,
    translate_message, gallery_page,
)

meetup_bp = Blueprint('meetup', __name__, url_prefix='/meetup')

@meetup_bp.route('/plan')
@login_required
def plan():
    meetup_id = request.args.get('meetup_id')
    return plan_meetup(created_meetup_id=meetup_id)

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

@meetup_bp.route('/delete/<int:meetup_id>', methods=['POST'])
@login_required
def delete_plan(meetup_id):
    return delete_meetup_plan(meetup_id)

@meetup_bp.route('/confirm-plan/<int:meetup_id>', methods=['POST'])
@login_required
def confirm_plan(meetup_id):
    return confirm_meetup_plan(meetup_id)


@meetup_bp.route('/complete-plan/<int:meetup_id>', methods=['POST'])
@login_required
def complete_plan(meetup_id):
    return complete_meetup_plan(meetup_id)


@meetup_bp.route('/<int:meetup_id>/preferences', methods=['POST'])
@login_required
def save_preferences(meetup_id):
    return save_plan_preferences(meetup_id)


@meetup_bp.route('/<int:meetup_id>/preferences', methods=['GET'])
@login_required
def load_preferences(meetup_id):
    return get_plan_preferences(meetup_id)


@meetup_bp.route('/<int:meetup_id>/calendar.ics', methods=['GET'])
@login_required
def calendar_ics(meetup_id):
    return meetup_calendar(meetup_id)


@meetup_bp.route('/gallery')
@login_required
def gallery_page_route():
    return gallery_page()


@meetup_bp.route('/groups')
@login_required
def groups():
    return groups_page()


@meetup_bp.route('/groups/hide/<int:meetup_id>', methods=['POST'])
@login_required
def remove_from_groups(meetup_id):
    return hide_from_groups(meetup_id)


@meetup_bp.route('/<int:meetup_id>/vote/start', methods=['POST'])
@login_required
def vote_start(meetup_id):
    return start_vote(meetup_id)


@meetup_bp.route('/<int:meetup_id>/vote/cast', methods=['POST'])
@login_required
def vote_cast(meetup_id):
    return cast_vote(meetup_id)


@meetup_bp.route('/<int:meetup_id>/vote/results')
@login_required
def vote_results_route(meetup_id):
    return vote_results(meetup_id)


@meetup_bp.route('/<int:meetup_id>/gallery/list')
@login_required
def gallery_list_route(meetup_id):
    return gallery_list(meetup_id)


@meetup_bp.route('/<int:meetup_id>/gallery/upload', methods=['POST'])
@login_required
def gallery_upload(meetup_id):
    return upload_gallery(meetup_id)


@meetup_bp.route('/gallery/<int:photo_id>/delete', methods=['POST'])
@login_required
def gallery_delete(photo_id):
    return delete_gallery_photo(photo_id)


@meetup_bp.route('/gallery/<int:photo_id>/like', methods=['POST'])
@login_required
def gallery_like(photo_id):
    return toggle_gallery_like(photo_id)


@meetup_bp.route('/gallery/<int:photo_id>/comment', methods=['POST'])
@login_required
def gallery_comment_route(photo_id):
    return gallery_comment(photo_id)


@meetup_bp.route('/gallery/<int:photo_id>/privacy', methods=['POST'])
@login_required
def gallery_privacy_route(photo_id):
    return gallery_privacy(photo_id)


@meetup_bp.route('/chat/<int:group_id>/messages')
@login_required
def chat_messages_route(group_id):
    return chat_messages(group_id)


@meetup_bp.route('/chat/<int:group_id>/send', methods=['POST'])
@login_required
def chat_send_route(group_id):
    from app.controllers.group_features_controller import send_chat_message
    return send_chat_message(group_id)


@meetup_bp.route('/chat/translate', methods=['POST'])
@login_required
def chat_translate():
    return translate_message()


@meetup_bp.route('/budget-split/<int:meetup_id>/record', methods=['POST'])
@login_required
def budget_split_record(meetup_id):
    return record_budget_split(meetup_id)

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


@meetup_bp.route('/friend/remove', methods=['POST'])
@login_required
def remove_friend_route():
    return remove_friend()

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


@meetup_bp.route('/invite/<code>')
@login_required
def join_via_invite(code):
    """Join a meetup using an invite code"""
    from app.models.meetup import Meetup
    meetup = Meetup.get_by_invite_code(code)
    
    if not meetup:
        return render_template('errors/404.html'), 404
    
    user_id = session.get('user_id')
    # Add user to the meetup
    Meetup.accept(meetup['id'], user_id)
    
    return redirect(url_for('meetup.view_meetup', meetup_id=meetup['id']))
