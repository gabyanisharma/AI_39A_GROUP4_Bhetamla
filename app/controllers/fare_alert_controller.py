"""
controllers/fare_alert_controller.py
Bhetamल — Fare Drop Alert Feature
------------------------------------
Flask Blueprint — handles HTTP only.
All DB / business logic is delegated to fare_alert_model.
All rendering is delegated to Jinja2 templates (the View layer).

Routes
  GET  /fare-alert/                        → list all alerts for current user
  GET  /fare-alert/meetup/<id>             → alert dashboard for one meetup
  POST /fare-alert/create                  → create / update an alert
  POST /fare-alert/delete/<alert_id>       → deactivate an alert
  GET  /fare-alert/check/<meetup_id>       → simulate a fare refresh (AJAX)
  GET  /fare-alert/history/<meetup_id>     → sparkline data (AJAX, JSON)
"""

from flask import (
    Blueprint, render_template, request,
    redirect, url_for, session, jsonify, flash
)
from datetime import datetime
from app.models.fare_alert_model import (
    estimate_fare,
    get_distance,
    get_alerts_for_user,
    get_alert_for_meetup,
    create_alert,
    deactivate_alert,
    get_meetup,
    get_fare_history,
    record_fare_history,
    check_and_trigger_alerts,
    group_history_by_mode,
    FARE_MODES,
)
from app.controllers.notification_controller import send_notification, fare_drop_notification

fare_alert_bp = Blueprint('fare_alert', __name__)


# ── Session helper ────────────────────────────────────────────────────────────
def _current_user_id() -> int:
    return session.get('user_id', 1)   # default 1 for dev


# ─────────────────────────────────────────────────────────────────────────────
#  LIST — all active alerts for the logged-in user
# ─────────────────────────────────────────────────────────────────────────────
@fare_alert_bp.route('/')
def index():
    user_id = _current_user_id()
    alerts  = get_alerts_for_user(user_id)

    # Enrich each alert with live fare + saving amount
    for a in alerts:
        distance      = get_distance(a['meetupID'], user_id)
        a['liveFare'] = estimate_fare(distance, a['mode'])
        a['targetFare'] = float(a['targetFare'])
        a['saving']   = round(a['targetFare'] - a['liveFare'], 2)
        a['triggered']= a['liveFare'] <= a['targetFare']

    return render_template(
        'meetup/fare_alert.html',
        alerts=alerts,
        meetup=None,
        fares=None,
        distance=None,
        existing_alert=None,
        history=None,
        page='fare_alert',
    )


# ─────────────────────────────────────────────────────────────────────────────
#  MEETUP DASHBOARD — fare alerts for one specific meetup
# ─────────────────────────────────────────────────────────────────────────────
@fare_alert_bp.route('/meetup/<int:meetup_id>')
def meetup_alerts(meetup_id):
    meetup = get_meetup(meetup_id)
    if not meetup:
        flash('Meetup not found.', 'error')
        return redirect(url_for('fare_alert.index'))

    user_id  = _current_user_id()
    distance = get_distance(meetup_id, user_id)

    # Current fare estimates for all modes
    fares = {mode: estimate_fare(distance, mode) for mode in FARE_MODES}

    # Existing alert (if any) for this user + meetup
    existing_alert = get_alert_for_meetup(user_id, meetup_id)
    if existing_alert:
        existing_alert['targetFare'] = float(existing_alert['targetFare'])
        if existing_alert.get('currentFare') is not None:
            existing_alert['currentFare'] = float(existing_alert['currentFare'])

    # Fare history for sparkline (last 40 rows, grouped by mode)
    raw_history = get_fare_history(meetup_id, limit=40)
    history     = group_history_by_mode(raw_history)

    return render_template(
        'meetup/fare_alert.html',
        meetup=meetup,
        fares=fares,
        distance=round(distance, 1),
        existing_alert=existing_alert,
        history=history,
        alerts=None,
        page='fare_alert',
    )


# ─────────────────────────────────────────────────────────────────────────────
#  CREATE — set or update a fare-drop alert
# ─────────────────────────────────────────────────────────────────────────────
@fare_alert_bp.route('/create', methods=['POST'])
def create():
    meetup_id   = int(request.form.get('meetup_id', 0))
    mode        = request.form.get('mode', 'car')
    target_fare = float(request.form.get('target_fare', 0))
    if mode not in FARE_MODES:
        mode = 'car'

    if not meetup_id or target_fare <= 0:
        flash('Please fill in all fields.', 'error')
        return redirect(url_for('fare_alert.meetup_alerts', meetup_id=meetup_id))

    user_id      = _current_user_id()
    distance     = get_distance(meetup_id, user_id)
    current_fare = estimate_fare(distance, mode)

    create_alert(user_id, meetup_id, mode, target_fare, current_fare)

    flash(f"Alert set! We'll notify you when the fare drops to NPR {target_fare:.0f}.", 'success')
    return redirect(url_for('fare_alert.meetup_alerts', meetup_id=meetup_id))


# ─────────────────────────────────────────────────────────────────────────────
#  DELETE — soft-delete (deactivate) an alert
# ─────────────────────────────────────────────────────────────────────────────
@fare_alert_bp.route('/delete/<int:alert_id>', methods=['POST'])
def delete(alert_id):
    deactivate_alert(alert_id, _current_user_id())
    flash('Alert removed.', 'success')
    return redirect(url_for('fare_alert.index'))


# ─────────────────────────────────────────────────────────────────────────────
#  CHECK — AJAX: refresh live fares, persist history, fire alerts
# ─────────────────────────────────────────────────────────────────────────────
@fare_alert_bp.route('/check/<int:meetup_id>')
def check_fare(meetup_id):
    user_id  = _current_user_id()
    distance = get_distance(meetup_id, user_id)

    # Fetch meetup title for richer notifications
    meetup = get_meetup(meetup_id)
    meetup_title = meetup['title'] if meetup else None

    fares             = {}
    triggered_alerts  = []

    for mode in FARE_MODES:
        fare          = estimate_fare(distance, mode)
        fares[mode]   = fare

        record_fare_history(meetup_id, mode, fare)
        alerts = check_and_trigger_alerts(meetup_id, mode, fare)
        for alert in alerts:
            # Use the rich fare-drop notification helper
            fare_drop_notification(
                user_id=alert['userID'],
                mode=alert['mode'],
                fare=alert['fare'],
                target_fare=alert['targetFare'],
                saving=alert['saving'],
                meetup_id=meetup_id,
                meetup_title=meetup_title,
            )
        triggered_alerts.extend(alerts)

    return jsonify({
        'fares':     fares,
        'distance':  round(distance, 1),
        'alerts':    triggered_alerts,
        'checkedAt': datetime.now().strftime('%H:%M:%S'),
    })


# ─────────────────────────────────────────────────────────────────────────────
#  HISTORY — AJAX: sparkline JSON data
# ─────────────────────────────────────────────────────────────────────────────
@fare_alert_bp.route('/history/<int:meetup_id>')
def fare_history(meetup_id):
    raw_history = get_fare_history(meetup_id, limit=60)
    history     = group_history_by_mode(raw_history)
    return jsonify(history)
