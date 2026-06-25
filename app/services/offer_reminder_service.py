import logging
from app.database import execute_query

logger = logging.getLogger(__name__)


def check_expiring_offers(app=None):
    """
    Background job: find restaurant offers expiring within 24 hours where the
    user opted in for reminders (remind_me=1) and hasn't been notified yet.
    Insert a notification per match and mark the row as notified.
    """
    def _run():
        try:
            query = """
                SELECT uso.user_id,
                       uso.offer_id,
                       o.title        AS offer_title,
                       o.valid_until,
                       r.name         AS restaurant_name
                FROM user_saved_offers uso
                JOIN restaurant_offers o  ON uso.offer_id       = o.id
                JOIN restaurants       r  ON o.restaurant_id    = r.id
                WHERE uso.remind_me   = 1
                  AND uso.notified    = 0
                  AND o.is_active     = 1
                  AND o.valid_until  >= CURDATE()
                  AND o.valid_until  <= DATE_ADD(CURDATE(), INTERVAL 1 DAY)
            """
            rows = execute_query(query, fetch=True)

            if not rows:
                return

            for row in rows:
                user_id         = row['user_id']
                offer_id        = row['offer_id']
                offer_title     = row['offer_title']
                restaurant_name = row['restaurant_name']
                valid_until     = row['valid_until']

                notif_query = """
                    INSERT INTO notifications (user_id, title, message, type, link)
                    VALUES (%s, %s, %s, %s, %s)
                """
                message = (
                    f"\"{offer_title}\" at {restaurant_name} expires on {valid_until}. "
                    f"Don\u2019t miss out!"
                )
                execute_query(
                    notif_query,
                    (user_id, "Offer Expiring Soon!", message, "reminder", "/places/saved"),
                )

                mark_query = """
                    UPDATE user_saved_offers
                    SET notified = 1
                    WHERE user_id = %s AND offer_id = %s
                """
                execute_query(mark_query, (user_id, offer_id))

            logger.info("Offer reminder check complete — %d notification(s) sent.", len(rows))

        except Exception as exc:
            logger.error("Error in check_expiring_offers: %s", exc)

    if app is not None:
        with app.app_context():
            _run()
    else:
        _run()


def check_meeting_reminders(app):
    """Check all users for upcoming meetups and create reminder notifications."""
    with app.app_context():
        from app.database import execute_query
        from app.models.notification import Notification
        from datetime import datetime, timedelta

        try:
            # Get all users with their reminder preferences
            users = execute_query(
                "SELECT user_id, reminder_lead_hours FROM notification_preferences "
                "WHERE meetup_reminders = 1 AND smart_alerts_enabled = 1",
                fetch=True
            )
            if not users:
                # Fallback: all users with default 24h lead
                users = execute_query(
                    "SELECT id AS user_id, 24 AS reminder_lead_hours FROM users",
                    fetch=True
                )

            for user in users:
                try:
                    user_id = user['user_id']
                    lead_hours = user.get('reminder_lead_hours', 24) or 24
                    now = datetime.now()
                    window_end = now + timedelta(hours=int(lead_hours))

                    # Find meetups this user is part of, happening within the reminder window
                    meetups = execute_query("""
                        SELECT m.id, m.title, m.meetup_date, m.meetup_time, m.midpoint_address
                        FROM meetups m
                        JOIN meetup_members mm ON mm.meetup_id = m.id
                        WHERE mm.user_id = %s
                          AND m.meetup_date BETWEEN %s AND %s
                          AND m.status != 'cancelled'
                    """, (user_id, now.date(), window_end.date()), fetch=True)

                    if meetups:
                        for meetup in meetups:
                            # Deduplicate using smart_alert_log
                            alert_key = f"reminder_meetup_{meetup['id']}"
                            already = execute_query(
                                "SELECT id FROM smart_alert_log WHERE user_id=%s AND alert_key=%s",
                                (user_id, alert_key), fetch=True
                            )
                            if not already:
                                location = meetup.get('midpoint_address') or 'TBD'
                                scheduled = meetup.get('meetup_date', '')
                                notif_id = Notification.create(
                                    user_id,
                                    f"\u23f0 Upcoming: {meetup['title']}",
                                    f"Your meetup at {location} is coming up on {scheduled}",
                                    'reminder',
                                    f"/meetup/view/{meetup['id']}")
                                execute_query(
                                    "INSERT INTO smart_alert_log (user_id, alert_key, notification_id) VALUES (%s, %s, %s)",
                                    (user_id, alert_key, notif_id)
                                )
                except Exception as inner:
                    logger.error("Error in check_meeting_reminders for user %s: %s", user.get('user_id'), inner)

            logger.info("Meeting reminder check complete.")
        except Exception as exc:
            logger.error("Error in check_meeting_reminders: %s", exc)


def check_fare_alerts(app):
    """Check all active fare alerts and notify users if fare dropped below threshold."""
    with app.app_context():
        from app.database import execute_query
        from app.models.notification import Notification
        from app.models.fare_alert_model import estimate_fare, get_distance

        try:
            # Get all active, untriggered alerts
            alerts = execute_query(
                "SELECT * FROM fare_alert WHERE isActive = 1 AND isTriggered = 0",
                fetch=True
            )
            if not alerts:
                return

            for alert in alerts:
                try:
                    user_id = alert['userID']
                    meetup_id = alert['meetupID']
                    mode = alert.get('mode', 'car')
                    base_fare = float(alert['currentFare']) if alert.get('currentFare') else 0

                    # Get current fare estimate
                    distance = get_distance(meetup_id, user_id)
                    current_fare = estimate_fare(distance, mode)

                    if base_fare > 0:
                        drop_pct = ((base_fare - current_fare) / base_fare) * 100
                        if drop_pct >= 10:
                            # Check dedup
                            alert_key = f"fare_drop_{alert['alertID']}_{int(drop_pct)}"
                            already = execute_query(
                                "SELECT id FROM smart_alert_log WHERE user_id=%s AND alert_key=%s",
                                (user_id, alert_key), fetch=True
                            )
                            if not already:
                                notif_id = Notification.create(
                                    user_id,
                                    f"\U0001f4b0 Fare Dropped {int(drop_pct)}%!",
                                    f"Ride fare for your meetup dropped by {int(drop_pct)}%. Book now to save!",
                                    'fare_alert',
                                    f"/fare-alert/meetup/{meetup_id}")
                                execute_query(
                                    "INSERT INTO smart_alert_log (user_id, alert_key, notification_id) VALUES (%s, %s, %s)",
                                    (user_id, alert_key, notif_id)
                                )
                except Exception as inner:
                    logger.error("Error in check_fare_alerts for alert %s: %s", alert.get('alertID'), inner)

            logger.info("Fare alert check complete.")
        except Exception as exc:
            logger.error("Error in check_fare_alerts: %s", exc)


def check_smart_alerts(app):
    """Run SmartAlertEngine for all users periodically."""
    with app.app_context():
        try:
            from app.models.notification_preference import SmartAlertEngine
            users = execute_query("SELECT id FROM users", fetch=True)
            if not users:
                return
            for u in users:
                try:
                    SmartAlertEngine.run(u['id'])
                except Exception as inner:
                    logger.error("SmartAlertEngine error for user %s: %s", u['id'], inner)
            logger.info("Smart alerts check complete for %d users.", len(users))
        except Exception as exc:
            logger.error("Error in check_smart_alerts: %s", exc)
