from datetime import datetime, date

from app.database import execute_query


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


def _is_past(meetup, today):
    """A meetup is 'past' if completed/cancelled or its date has gone by."""
    status = meetup.get('status')
    if status in ('completed', 'cancelled'):
        return True
    mdate = _as_date(meetup.get('meetup_date'))
    if mdate is None:
        return False
    return mdate < today


def split_upcoming_past(meetups, today):
    """Partition meetups into (upcoming, past), each sorted sensibly."""
    upcoming, past = [], []
    for m in meetups or []:
        (past if _is_past(m, today) else upcoming).append(m)

    upcoming.sort(key=lambda m: (_as_date(m.get('meetup_date')) or date.max))
    past.sort(key=lambda m: (_as_date(m.get('meetup_date')) or date.min), reverse=True)
    return upcoming, past


def build_monthly_activity(meetups, today, months=6):
    """
    Bucket meetups into the trailing ``months`` calendar months.

    Returns a chronologically-ordered list of
    {year, month, label, count} so the template can draw a bar chart.
    """
    # Build the ordered list of (year, month) buckets ending at `today`.
    buckets = []
    y, mo = today.year, today.month
    for _ in range(months):
        buckets.append((y, mo))
        mo -= 1
        if mo == 0:
            mo = 12
            y -= 1
    buckets.reverse()

    counts = {key: 0 for key in buckets}
    for m in meetups or []:
        mdate = _as_date(m.get('meetup_date'))
        if mdate is None:
            continue
        key = (mdate.year, mdate.month)
        if key in counts:
            counts[key] += 1

    month_names = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    return [
        {'year': y, 'month': mo, 'label': month_names[mo], 'count': counts[(y, mo)]}
        for (y, mo) in buckets
    ]


def summarize(meetups, today, user_id=None):
    """Compute headline analytics from a user's meetup rows."""
    meetups = meetups or []
    upcoming, past = split_upcoming_past(meetups, today)

    completed = sum(1 for m in meetups if m.get('status') == 'completed')
    cancelled = sum(1 for m in meetups if m.get('status') == 'cancelled')
    hosted = sum(1 for m in meetups if user_id is not None and m.get('created_by') == user_id)

    this_month = sum(
        1 for m in meetups
        if (_as_date(m.get('meetup_date')) or date.min).replace(day=1)
        == today.replace(day=1)
    )

    # Completion rate among meetups that have actually concluded.
    concluded = completed + cancelled
    completion_rate = round((completed / concluded) * 100) if concluded else 0

    return {
        'total': len(meetups),
        'upcoming': len(upcoming),
        'past': len(past),
        'completed': completed,
        'cancelled': cancelled,
        'hosted': hosted,
        'joined': len(meetups) - hosted,
        'this_month': this_month,
        'completion_rate': completion_rate,
    }


# ── Persistence layer ──────────────────────────────────────────────
class MeetingAnalytics:

    @staticmethod
    def get_overview(user_id, today=None):
        """Return stats + monthly activity + upcoming/past splits for a user."""
        from app.models.meetup import Meetup

        today = today or date.today()
        meetups = Meetup.get_by_user(user_id) or []
        upcoming, past = split_upcoming_past(meetups, today)

        return {
            'stats': summarize(meetups, today, user_id),
            'monthly': build_monthly_activity(meetups, today, months=6),
            'upcoming': upcoming,
            'past': past,
        }

    @staticmethod
    def get_top_companions(user_id, limit=5):
        """People this user shares the most meetups with."""
        query = """
            SELECT u.id, u.full_name, u.profile_pic,
                   COUNT(DISTINCT mm.meetup_id) AS shared_meetups
            FROM meetup_members mm
            JOIN meetup_members me
              ON me.meetup_id = mm.meetup_id AND me.user_id = %s
            JOIN users u ON u.id = mm.user_id
            WHERE mm.user_id <> %s
              AND mm.status IN ('accepted', 'invited')
            GROUP BY u.id, u.full_name, u.profile_pic
            ORDER BY shared_meetups DESC, u.full_name ASC
            LIMIT %s
        """
        return execute_query(query, (user_id, user_id, int(limit)), fetch=True) or []
