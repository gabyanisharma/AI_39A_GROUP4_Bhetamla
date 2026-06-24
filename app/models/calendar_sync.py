from datetime import date, datetime, time, timedelta

from app.database import execute_query


SUPPORTED_PROVIDERS = {
    'google': ('google', 'google calendar', 'gmail'),
    'outlook': ('outlook', 'microsoft', 'office 365', 'hotmail'),
    'apple': ('apple', 'icloud', 'ical', 'apple ical'),
}


def normalize_provider(provider):
    """Return the canonical provider key for UI labels and storage."""
    value = (provider or '').strip().lower()
    for canonical, aliases in SUPPORTED_PROVIDERS.items():
        if value in aliases:
            return canonical
    return 'other'


def _unfold_ics_lines(ics_text):
    lines = []
    for raw_line in (ics_text or '').replace('\r\n', '\n').replace('\r', '\n').split('\n'):
        if not raw_line:
            continue
        if raw_line.startswith((' ', '\t')) and lines:
            lines[-1] += raw_line[1:]
        else:
            lines.append(raw_line.strip())
    return lines


def _split_ics_line(line):
    if ':' not in line:
        return '', {}, ''
    left, value = line.split(':', 1)
    parts = left.split(';')
    name = parts[0].upper()
    params = {}
    for part in parts[1:]:
        if '=' in part:
            key, param_value = part.split('=', 1)
            params[key.upper()] = param_value
    return name, params, _ics_unescape(value)


def _ics_unescape(value):
    return (str(value or '')
            .replace('\\n', '\n')
            .replace('\\N', '\n')
            .replace('\\,', ',')
            .replace('\\;', ';')
            .replace('\\\\', '\\'))


def ics_escape(value):
    """Escape text per RFC 5545 for simple VEVENT fields."""
    return (str(value or '')
            .replace('\\', '\\\\')
            .replace(';', '\\;')
            .replace(',', '\\,')
            .replace('\r\n', '\\n')
            .replace('\n', '\\n'))


def _parse_ics_datetime(value, params=None):
    params = params or {}
    value = (value or '').strip()
    if not value:
        return None, False

    if params.get('VALUE', '').upper() == 'DATE' or (len(value) == 8 and 'T' not in value):
        return datetime.strptime(value[:8], '%Y%m%d'), True

    if value.endswith('Z'):
        value = value[:-1]

    if 'T' in value:
        fmt = '%Y%m%dT%H%M%S' if len(value.split('T', 1)[1]) >= 6 else '%Y%m%dT%H%M'
        return datetime.strptime(value[:15] if fmt.endswith('%S') else value[:13], fmt), False

    return datetime.strptime(value[:8], '%Y%m%d'), True


def parse_ics_events(ics_text):
    """Parse VEVENT entries from an uploaded ICS string.

    This intentionally supports the common subset exported by Google Calendar,
    Outlook, Apple Calendar, and school calendars.
    """
    events = []
    current = None

    for line in _unfold_ics_lines(ics_text):
        name, params, value = _split_ics_line(line)
        if name == 'BEGIN' and value.upper() == 'VEVENT':
            current = {'raw': {}}
            continue
        if name == 'END' and value.upper() == 'VEVENT':
            if current:
                events.append(_event_from_raw(current['raw']))
            current = None
            continue
        if current is not None and name:
            current['raw'][name] = {'value': value, 'params': params}

    return [event for event in events if event is not None]


def _event_from_raw(raw):
    start_field = raw.get('DTSTART')
    if not start_field:
        return None

    end_field = raw.get('DTEND')
    starts_at, is_all_day = _parse_ics_datetime(
        start_field['value'], start_field.get('params')
    )
    if not starts_at:
        return None

    if end_field:
        ends_at, _ = _parse_ics_datetime(end_field['value'], end_field.get('params'))
    elif is_all_day:
        ends_at = starts_at + timedelta(days=1)
    else:
        ends_at = starts_at + timedelta(hours=1)

    if ends_at <= starts_at:
        ends_at = starts_at + (timedelta(days=1) if is_all_day else timedelta(hours=1))

    return {
        'external_uid': raw.get('UID', {}).get('value') or f'imported-{starts_at.isoformat()}',
        'title': raw.get('SUMMARY', {}).get('value') or 'Untitled event',
        'description': raw.get('DESCRIPTION', {}).get('value') or '',
        'location': raw.get('LOCATION', {}).get('value') or '',
        'starts_at': starts_at,
        'ends_at': ends_at,
        'is_all_day': is_all_day,
    }


def _coerce_date(value):
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


def _coerce_time(value):
    if value is None:
        return None
    if isinstance(value, time):
        return value
    if isinstance(value, timedelta):
        seconds = int(value.total_seconds()) % 86400
        return time(seconds // 3600, (seconds % 3600) // 60, seconds % 60)
    if isinstance(value, str):
        parts = value.split('.')[0].split(':')
        try:
            hour = int(parts[0])
            minute = int(parts[1]) if len(parts) > 1 else 0
            second = int(parts[2]) if len(parts) > 2 else 0
            return time(hour, minute, second)
        except (TypeError, ValueError):
            return None
    return None


def meetup_time_window(meetup, default_hours=2):
    day = _coerce_date(meetup.get('meetup_date'))
    if not day:
        return None

    clock = _coerce_time(meetup.get('meetup_time'))
    if clock:
        start = datetime.combine(day, clock)
        return start, start + timedelta(hours=default_hours)

    start = datetime.combine(day, time.min)
    return start, start + timedelta(days=1)


def _events_overlap(left_start, left_end, right_start, right_end):
    return left_start < right_end and right_start < left_end


def find_calendar_conflicts(meetups, imported_events):
    """Return imported calendar events that overlap existing meetups."""
    conflicts = []
    for meetup in meetups or []:
        window = meetup_time_window(meetup)
        if not window:
            continue
        meetup_start, meetup_end = window
        for event in imported_events or []:
            event_start = event.get('starts_at')
            event_end = event.get('ends_at')
            if not event_start or not event_end:
                continue
            if _events_overlap(meetup_start, meetup_end, event_start, event_end):
                conflicts.append({
                    'meetup_id': meetup.get('id'),
                    'meetup_title': meetup.get('title') or 'Untitled meetup',
                    'meetup_start': meetup_start,
                    'meetup_end': meetup_end,
                    'event_id': event.get('id'),
                    'event_title': event.get('title') or 'Untitled event',
                    'event_start': event_start,
                    'event_end': event_end,
                    'account_email': event.get('account_email') or '',
                })
    return conflicts


def _ics_datetime(value):
    return value.strftime('%Y%m%dT%H%M%S')


def _meetup_vevent(meetup, stamp):
    window = meetup_time_window(meetup)
    if not window:
        return None

    starts_at, ends_at = window
    location = meetup.get('winning_venue_name') or meetup.get('midpoint_address') or ''
    description = meetup.get('description') or 'Planned with Bhetamla.'

    return [
        'BEGIN:VEVENT',
        f"UID:meetup-{meetup.get('id')}@bhetamla",
        f'DTSTAMP:{stamp}',
        f'DTSTART:{_ics_datetime(starts_at)}',
        f'DTEND:{_ics_datetime(ends_at)}',
        'SUMMARY:' + ics_escape(meetup.get('title') or 'Bhetamla Meetup'),
        'DESCRIPTION:' + ics_escape(description),
        'LOCATION:' + ics_escape(location),
        'STATUS:CONFIRMED',
        'END:VEVENT',
    ]


def build_meetups_ics(meetups, now=None, calendar_name='Bhetamla Meetups'):
    now = now or datetime.utcnow()
    stamp = now.strftime('%Y%m%dT%H%M%SZ')
    lines = [
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//Bhetamla//Calendar Sync//EN',
        'CALSCALE:GREGORIAN',
        'METHOD:PUBLISH',
        'X-WR-CALNAME:' + ics_escape(calendar_name),
    ]

    for meetup in meetups or []:
        vevent = _meetup_vevent(meetup, stamp)
        if vevent:
            lines.extend(vevent)

    lines.append('END:VCALENDAR')
    return '\r\n'.join(lines) + '\r\n'


class CalendarAccount:
    @staticmethod
    def connect(user_id, provider, account_email, display_name='', permission_scope='read_write'):
        provider_key = normalize_provider(provider)
        account_email = (account_email or '').strip().lower()
        display_name = (display_name or account_email).strip()
        return execute_query(
            """
            INSERT INTO calendar_accounts
                (user_id, provider, account_email, display_name, permission_scope, is_active)
            VALUES (%s, %s, %s, %s, %s, TRUE)
            ON DUPLICATE KEY UPDATE
                provider = VALUES(provider),
                display_name = VALUES(display_name),
                permission_scope = VALUES(permission_scope),
                is_active = TRUE,
                updated_at = CURRENT_TIMESTAMP
            """,
            (user_id, provider_key, account_email, display_name, permission_scope)
        )

    @staticmethod
    def get_by_user(user_id):
        return execute_query(
            """
            SELECT *
            FROM calendar_accounts
            WHERE user_id=%s
            ORDER BY is_active DESC, updated_at DESC
            """,
            (user_id,), fetch=True
        )

    @staticmethod
    def get_active_by_user(user_id):
        return execute_query(
            """
            SELECT *
            FROM calendar_accounts
            WHERE user_id=%s AND is_active=TRUE
            ORDER BY updated_at DESC
            """,
            (user_id,), fetch=True
        )

    @staticmethod
    def get_for_user(account_id, user_id):
        rows = execute_query(
            "SELECT * FROM calendar_accounts WHERE id=%s AND user_id=%s",
            (account_id, user_id), fetch=True
        )
        return rows[0] if rows else None

    @staticmethod
    def disconnect(account_id, user_id):
        return execute_query(
            """
            UPDATE calendar_accounts
            SET is_active=FALSE, updated_at=CURRENT_TIMESTAMP
            WHERE id=%s AND user_id=%s
            """,
            (account_id, user_id)
        )

    @staticmethod
    def touch_sync(account_id, user_id):
        return execute_query(
            """
            UPDATE calendar_accounts
            SET last_sync_at=CURRENT_TIMESTAMP, updated_at=CURRENT_TIMESTAMP
            WHERE id=%s AND user_id=%s
            """,
            (account_id, user_id)
        )


class CalendarEvent:
    @staticmethod
    def import_events(user_id, account_id, events):
        saved = 0
        for event in events:
            execute_query(
                """
                INSERT INTO imported_calendar_events
                    (user_id, account_id, external_uid, title, description, location,
                     starts_at, ends_at, is_all_day, source)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'ics_upload')
                ON DUPLICATE KEY UPDATE
                    title = VALUES(title),
                    description = VALUES(description),
                    location = VALUES(location),
                    starts_at = VALUES(starts_at),
                    ends_at = VALUES(ends_at),
                    is_all_day = VALUES(is_all_day),
                    imported_at = CURRENT_TIMESTAMP
                """,
                (
                    user_id,
                    account_id,
                    event['external_uid'],
                    event['title'][:255],
                    event.get('description', ''),
                    event.get('location', '')[:255],
                    event['starts_at'],
                    event['ends_at'],
                    bool(event.get('is_all_day')),
                )
            )
            saved += 1
        return saved

    @staticmethod
    def get_by_user(user_id):
        return execute_query(
            """
            SELECT ice.*, ca.account_email, ca.provider
            FROM imported_calendar_events ice
            JOIN calendar_accounts ca ON ca.id = ice.account_id
            WHERE ice.user_id=%s AND ca.is_active=TRUE
            ORDER BY ice.starts_at ASC
            """,
            (user_id,), fetch=True
        )

    @staticmethod
    def delete(event_id, user_id):
        return execute_query(
            "DELETE FROM imported_calendar_events WHERE id=%s AND user_id=%s",
            (event_id, user_id)
        )
