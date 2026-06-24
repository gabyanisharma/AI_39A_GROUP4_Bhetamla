from flask import Blueprint

from app.controllers.calendar_controller import (
    connect_account,
    delete_event,
    disconnect_account,
    export_calendar,
    import_events,
    sync_now,
    sync_page as sync_page_controller,
)
from app.routes.user_routes import login_required


calendar_bp = Blueprint('calendar', __name__, url_prefix='/calendar')


@calendar_bp.route('/')
@login_required
def sync_page():
    return sync_page_controller()


@calendar_bp.route('/connect', methods=['POST'])
@login_required
def connect():
    return connect_account()


@calendar_bp.route('/disconnect/<int:account_id>', methods=['POST'])
@login_required
def disconnect(account_id):
    return disconnect_account(account_id)


@calendar_bp.route('/import', methods=['POST'])
@login_required
def import_ics():
    return import_events()


@calendar_bp.route('/sync/<int:account_id>', methods=['POST'])
@login_required
def sync(account_id):
    return sync_now(account_id)


@calendar_bp.route('/event/<int:event_id>/delete', methods=['POST'])
@login_required
def remove_event(event_id):
    return delete_event(event_id)


@calendar_bp.route('/export.ics')
@login_required
def export_ics():
    return export_calendar()
