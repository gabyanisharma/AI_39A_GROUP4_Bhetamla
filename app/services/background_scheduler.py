"""Lightweight background scheduler for proactive notifications.

Runs in a daemon thread (no external dependency) and periodically:
  • runs the SmartAlertEngine for every user — meeting reminders (F5) and
    smart departure/arrival alerts (F22), deduped via smart_alert_log;
  • re-checks every active fare-drop alert and notifies on a drop (F10).

It is intentionally simple: a single loop with per-task interval gating. All
DB work happens inside an app context. Failures in one cycle never kill the
thread — they are logged and the loop continues.
"""

import threading
import time as _time
import traceback
from datetime import datetime

# Run cadence (seconds). Smart alerts every 30 min, fare checks every 15 min.
SMART_ALERT_INTERVAL = 30 * 60
FARE_CHECK_INTERVAL = 15 * 60
_TICK = 60  # how often the loop wakes to decide what is due

_started = False
_lock = threading.Lock()


def _run_smart_alerts_for_all():
    from app.database import execute_query
    from app.models.notification_preference import SmartAlertEngine

    users = execute_query("SELECT id FROM users WHERE is_verified = TRUE", fetch=True) or []
    total = 0
    for u in users:
        try:
            total += SmartAlertEngine.run(u['id']) or 0
        except Exception as e:
            print(f"[scheduler] smart alert failed for user {u['id']}: {e}")
    if total:
        print(f"[scheduler] generated {total} smart alert(s) at {datetime.now():%H:%M}")


def _run_fare_checks():
    from app.models.fare_alert_model import (
        get_pending_alert_targets, get_distance, estimate_fare,
        record_fare_history, check_and_trigger_alerts, get_meetup,
    )
    from app.controllers.notification_controller import fare_drop_notification

    targets = get_pending_alert_targets()
    fired = 0
    title_cache = {}
    for t in targets:
        meetup_id, user_id, mode = t['meetupID'], t['userID'], t['mode']
        try:
            distance = get_distance(meetup_id, user_id)
            fare = estimate_fare(distance, mode)
            record_fare_history(meetup_id, mode, fare)
            if meetup_id not in title_cache:
                m = get_meetup(meetup_id)
                title_cache[meetup_id] = m['title'] if m else None
            for alert in check_and_trigger_alerts(meetup_id, mode, fare):
                fare_drop_notification(
                    user_id=alert['userID'], mode=alert['mode'], fare=alert['fare'],
                    target_fare=alert['targetFare'], saving=alert['saving'],
                    meetup_id=meetup_id, meetup_title=title_cache[meetup_id],
                )
                fired += 1
        except Exception as e:
            print(f"[scheduler] fare check failed for meetup {meetup_id}: {e}")
    if fired:
        print(f"[scheduler] fired {fired} fare-drop alert(s) at {datetime.now():%H:%M}")


def _loop(app):
    last_smart = 0.0
    last_fare = 0.0
    while True:
        now = _time.monotonic()
        try:
            with app.app_context():
                if now - last_smart >= SMART_ALERT_INTERVAL:
                    _run_smart_alerts_for_all()
                    last_smart = now
                if now - last_fare >= FARE_CHECK_INTERVAL:
                    _run_fare_checks()
                    last_fare = now
        except Exception:
            traceback.print_exc()
        _time.sleep(_TICK)


def start(app):
    """Start the scheduler once per process. Safe to call from create_app."""
    global _started
    with _lock:
        if _started:
            return
        _started = True
    thread = threading.Thread(target=_loop, args=(app,), daemon=True,
                              name='bhetamla-scheduler')
    thread.start()
    print('[scheduler] background notification scheduler started')
