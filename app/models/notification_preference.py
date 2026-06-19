from datetime import datetime, date, time, timedelta

from app.database import execute_query


# Sensible defaults used when a user has no saved preferences yet.
DEFAULT_PREFERENCES = {
    'smart_alerts_enabled': True,
    'meetup_reminders': True,
    'invite_alerts': True,
    'trending_alerts': True,
    'reminder_lead_hours': 24,
    'quiet_hours_start': None,
    'quiet_hours_end': None,
}


# ── Pure helpers (no DB — unit testable) ───────────────────────────
def _as_date(value):
    """Coerce a date/datetime/ISO-string into a date, or None."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return datetime.strptime(value[:10], '%Y-%m-%d').date()
        except ValueError:
            return None
    return None


def _as_time(value):
    """Coerce a time/timedelta/string into a time, or None."""
    if value is None:
        return None
    if isinstance(value, time):
        return value
    if isinstance(value, timedelta):
        secs = int(value.total_seconds()) % 86400
        return time(secs // 3600, (secs % 3600) // 60, secs % 60)
    if isinstance(value, str):
        parts = value.split(':')
        try:
            nums = [int(p) for p in parts[:3]]
            while len(nums) < 3:
                nums.append(0)
            return time(nums[0] % 24, nums[1], nums[2])
        except ValueError:
            return None
    return None


def _in_quiet_hours(hour, start, end):
    """True if `hour` falls inside the quiet window [start, end)."""
    if start is None or end is None:
        return False
    start, end = int(start), int(end)
    if start == end:
        return False
    if start < end:
        return start <= hour < end
    # Window wraps past midnight, e.g. 22:00 → 07:00.
    return hour >= start or hour < end


def build_smart_alerts(meetups, pending_invites, prefs, now, trending_count=0):
    """
    Decide which smart alerts should fire for a user.

    Pure function: takes plain data and returns a list of alert dicts of the
    shape {key, title, message, type, link}. The ``key`` is a stable
    idempotency token so the engine never fires the same alert twice.
    """
    prefs = {**DEFAULT_PREFERENCES, **(prefs or {})}
    if not prefs['smart_alerts_enabled']:
        return []

    if _in_quiet_hours(now.hour, prefs['quiet_hours_start'], prefs['quiet_hours_end']):
        return []

    alerts = []
    today = now.date()
    lead_hours = int(prefs['reminder_lead_hours'] or 24)

    if prefs['meetup_reminders']:
        for m in meetups or []:
            if m.get('status') in ('completed', 'cancelled'):
                continue
            mdate = _as_date(m.get('meetup_date'))
            if not mdate:
                continue
            title = m.get('title', 'your meetup')
            link = f"/meetup/view/{m.get('id')}"

            if mdate == today:
                when = _as_time(m.get('meetup_time'))
                when_txt = when.strftime('%I:%M %p').lstrip('0') if when else 'today'
                alerts.append({
                    'key': f"meetup_today:{m.get('id')}:{today.isoformat()}",
                    'title': '📅 Meetup Today',
                    'message': f'"{title}" is happening today{" at " + when_txt if when else ""}. See you there!',
                    'type': 'reminder',
                    'link': link,
                })
            elif mdate > today:
                meetup_dt = datetime.combine(mdate, _as_time(m.get('meetup_time')) or time(9, 0))
                delta_hours = (meetup_dt - now).total_seconds() / 3600
                if 0 <= delta_hours <= lead_hours:
                    alerts.append({
                        'key': f"meetup_reminder:{m.get('id')}:{mdate.isoformat()}",
                        'title': '⏰ Upcoming Meetup',
                        'message': (
                            f'"{title}" is coming up on '
                            f'{mdate.strftime("%a, %b %d")}. Get ready!'
                        ),
                        'type': 'reminder',
                        'link': link,
                    })

    if prefs['invite_alerts']:
        for inv in pending_invites or []:
            inviter = inv.get('inviter_name', 'Someone')
            mtitle = inv.get('title', 'a meetup')
            alerts.append({
                'key': f"invite_pending:{inv.get('invite_id')}",
                'title': '✉️ Invite Awaiting Response',
                'message': f'{inviter} invited you to "{mtitle}". Tap to respond.',
                'type': 'meetup',
                'link': f"/meetup/view/{inv.get('meetup_id')}",
            })

    if prefs['trending_alerts'] and trending_count and trending_count > 0:
        iso_year, iso_week, _ = now.isocalendar()
        alerts.append({
            'key': f"trending_digest:{iso_year}-W{iso_week}",
            'title': '🔥 Trending This Week',
            'message': (
                f'{trending_count} spots are trending in Kathmandu right now. '
                f'See where everyone is meeting up.'
            ),
            'type': 'general',
            'link': '/explore/',
        })

    return alerts


# ── Persistence layer ──────────────────────────────────────────────
class NotificationPreference:

    @staticmethod
    def get(user_id):
        rows = execute_query(
            "SELECT * FROM notification_preferences WHERE user_id = %s",
            (user_id,), fetch=True
        )
        return rows[0] if rows else None

    @staticmethod
    def get_or_create(user_id):
        prefs = NotificationPreference.get(user_id)
        if prefs:
            return prefs
        execute_query(
            "INSERT IGNORE INTO notification_preferences (user_id) VALUES (%s)",
            (user_id,)
        )
        return NotificationPreference.get(user_id) or {
            'user_id': user_id, **DEFAULT_PREFERENCES
        }

    @staticmethod
    def update(user_id, fields):
        """Upsert the given preference fields for a user."""
        allowed = (
            'smart_alerts_enabled', 'meetup_reminders', 'invite_alerts',
            'trending_alerts', 'reminder_lead_hours',
            'quiet_hours_start', 'quiet_hours_end',
        )
        data = {k: fields[k] for k in allowed if k in fields}
        if not data:
            return None
        NotificationPreference.get_or_create(user_id)
        set_clause = ", ".join(f"{k} = %s" for k in data)
        params = list(data.values()) + [user_id]
        return execute_query(
            f"UPDATE notification_preferences SET {set_clause} WHERE user_id = %s",
            tuple(params)
        )


class SmartAlertEngine:
    """Runs the pure alert builder and persists deduped notifications."""

    @staticmethod
    def _already_fired(user_id, alert_key):
        return bool(execute_query(
            "SELECT 1 FROM smart_alert_log WHERE user_id = %s AND alert_key = %s",
            (user_id, alert_key), fetch=True
        ))

    @staticmethod
    def run(user_id, now=None):
        """
        Generate any due smart alerts for the user and persist them as
        notifications. Returns the number of new alerts created.
        """
        from app.models.meetup import Meetup
        from app.models.notification import Notification

        now = now or datetime.now()
        prefs = NotificationPreference.get_or_create(user_id)

        meetups = Meetup.get_by_user(user_id) or []

        pending_invites = execute_query(
            """SELECT mm.id AS invite_id, m.id AS meetup_id, m.title,
                      u.full_name AS inviter_name
               FROM meetup_members mm
               JOIN meetups m ON m.id = mm.meetup_id
               JOIN users u   ON u.id = m.created_by
               WHERE mm.user_id = %s AND mm.status = 'invited'
               LIMIT 20""",
            (user_id,), fetch=True
        ) or []

        trending_count = 0
        if prefs.get('trending_alerts'):
            row = execute_query(
                "SELECT COUNT(*) AS cnt FROM trending_spots WHERE is_active = TRUE",
                fetch=True
            )
            trending_count = row[0]['cnt'] if row else 0

        alerts = build_smart_alerts(meetups, pending_invites, prefs, now, trending_count)

        created = 0
        for alert in alerts:
            if SmartAlertEngine._already_fired(user_id, alert['key']):
                continue
            notif_id = Notification.create(
                user_id, alert['title'], alert['message'],
                type=alert.get('type', 'general'), link=alert.get('link')
            )
            execute_query(
                "INSERT IGNORE INTO smart_alert_log (user_id, alert_key, notification_id) "
                "VALUES (%s, %s, %s)",
                (user_id, alert['key'], notif_id)
            )
            created += 1

        return created
