"""Calendar (.ics) import + conflict detection for the scheduler (F29).

No external dependency: a small, tolerant iCalendar VEVENT parser that pulls
out date/start/end/summary, plus helpers to detect clashes against a user's
existing meetups and availability slots.
"""

from datetime import datetime, time

from app.database import execute_query


def _unfold(text):
    """Join RFC 5545 folded lines (continuations begin with space/tab)."""
    out = []
    for raw in text.replace('\r\n', '\n').replace('\r', '\n').split('\n'):
        if raw[:1] in (' ', '\t') and out:
            out[-1] += raw[1:]
        else:
            out.append(raw)
    return out


def _parse_dt(value):
    """Parse an iCal DATE or DATE-TIME value -> (date, time|None)."""
    value = value.strip().rstrip('Z')
    if 'T' in value:
        d, t = value.split('T', 1)
        try:
            dd = datetime.strptime(d, '%Y%m%d').date()
            tt = datetime.strptime(t[:6].ljust(6, '0'), '%H%M%S').time()
            return dd, tt
        except ValueError:
            return None, None
    try:
        return datetime.strptime(value, '%Y%m%d').date(), None
    except ValueError:
        return None, None


def parse_ics(text):
    """Return a list of events: {summary, date, start_time, end_time}."""
    events = []
    cur = None
    for line in _unfold(text):
        if line.startswith('BEGIN:VEVENT'):
            cur = {}
        elif line.startswith('END:VEVENT'):
            if cur and cur.get('date'):
                events.append(cur)
            cur = None
        elif cur is not None and ':' in line:
            key, val = line.split(':', 1)
            name = key.split(';', 1)[0].upper()
            if name == 'SUMMARY':
                cur['summary'] = val.strip()
            elif name == 'DTSTART':
                d, t = _parse_dt(val)
                if d:
                    cur['date'] = d
                    cur['start_time'] = t or time(0, 0)
            elif name == 'DTEND':
                d, t = _parse_dt(val)
                if t:
                    cur['end_time'] = t
    # Default a 1h-ish end where none was given.
    for e in events:
        e.setdefault('summary', 'Imported event')
        e.setdefault('start_time', time(0, 0))
        if not e.get('end_time') or e['end_time'] <= e['start_time']:
            h = e['start_time'].hour
            e['end_time'] = time(23, 59) if h >= 23 else time(h + 1, e['start_time'].minute)
    return events


def _overlaps(s1, e1, s2, e2):
    return s1 < e2 and s2 < e1


def find_conflicts(user_id, event):
    """Return a list of human-readable conflicts for one event against the
    user's meetups and availability slots on the same date."""
    conflicts = []
    d, s, e = event['date'], event['start_time'], event['end_time']

    meetups = execute_query(
        """
        SELECT m.title, m.meetup_time
        FROM meetups m
        LEFT JOIN meetup_members mm ON mm.meetup_id = m.id AND mm.user_id = %s
        WHERE (m.created_by = %s OR mm.user_id = %s)
          AND m.meetup_date = %s AND m.meetup_time IS NOT NULL
        """,
        (user_id, user_id, user_id, d), fetch=True
    ) or []
    for m in meetups:
        mt = m['meetup_time']
        if isinstance(mt, datetime):
            mt = mt.time()
        elif hasattr(mt, 'total_seconds'):  # timedelta from MySQL TIME
            secs = int(mt.total_seconds())
            mt = time((secs // 3600) % 24, (secs % 3600) // 60)
        if mt and s <= mt < e:
            conflicts.append(f"Meetup \"{m['title']}\" at {mt.strftime('%H:%M')}")

    slots = execute_query(
        "SELECT label, start_time, end_time FROM availability_slots WHERE user_id = %s AND date = %s",
        (user_id, d), fetch=True
    ) or []
    for sl in slots:
        def _t(v):
            if hasattr(v, 'total_seconds'):
                secs = int(v.total_seconds())
                return time((secs // 3600) % 24, (secs % 3600) // 60)
            return v
        ss, se = _t(sl['start_time']), _t(sl['end_time'])
        if ss and se and _overlaps(s, e, ss, se):
            conflicts.append(f"Availability {ss.strftime('%H:%M')}–{se.strftime('%H:%M')}")

    return conflicts
