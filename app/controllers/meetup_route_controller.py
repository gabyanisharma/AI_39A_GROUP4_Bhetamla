from flask import jsonify, request

from app.auth import get_current_user_id, is_logged_in
from app.models.meetup import Meetup
from app.models.meetup_route import MeetupRoute, validate_route_payload


def _error(message, status=400, errors=None):
    payload = {'success': False, 'message': message}
    if errors:
        payload['errors'] = errors
    return jsonify(payload), status


def get_meetup_route(meetup_id):
    if not is_logged_in():
        return _error('Login required.', 401)

    user_id = get_current_user_id()
    if not Meetup.get_by_id(meetup_id):
        return _error('Meetup not found.', 404)

    if not MeetupRoute.user_can_access(meetup_id, user_id):
        return _error('You do not have access to this meetup route.', 403)

    route = MeetupRoute.get_by_meetup(meetup_id)
    return jsonify({
        'success': True,
        'route': route,
        'waypoints': route['waypoints'] if route else [],
    })


def save_meetup_route(meetup_id):
    if not is_logged_in():
        return _error('Login required.', 401)

    user_id = get_current_user_id()
    if not Meetup.get_by_id(meetup_id):
        return _error('Meetup not found.', 404)

    if not MeetupRoute.user_can_edit(meetup_id, user_id):
        return _error('Only the creator or accepted members can edit this route.', 403)

    route_data, errors = validate_route_payload(request.get_json(silent=True) or {})
    if errors:
        return _error(errors[0], 400, errors)

    route_id = MeetupRoute.replace_for_meetup(meetup_id, user_id, route_data)
    route = MeetupRoute.get_by_meetup(meetup_id)

    return jsonify({
        'success': True,
        'message': 'Route saved successfully.',
        'route_id': route_id,
        'route': route,
        'waypoints': route['waypoints'] if route else [],
    })


def delete_meetup_route(meetup_id):
    if not is_logged_in():
        return _error('Login required.', 401)

    user_id = get_current_user_id()
    if not Meetup.get_by_id(meetup_id):
        return _error('Meetup not found.', 404)

    if not MeetupRoute.user_can_edit(meetup_id, user_id):
        return _error('Only the creator or accepted members can clear this route.', 403)

    MeetupRoute.delete_for_meetup(meetup_id, user_id)
    return jsonify({
        'success': True,
        'message': 'Route cleared successfully.',
        'waypoints': [],
    })
