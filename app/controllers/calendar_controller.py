import re

from flask import Response, flash, redirect, render_template, request, url_for

from app.auth import get_current_user_id, is_logged_in
from app.models.calendar_sync import (
    CalendarAccount,
    CalendarEvent,
    build_meetups_ics,
    find_calendar_conflicts,
    parse_ics_events,
)
from app.models.meetup import Meetup


EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


def _calendar_redirect():
    return redirect(url_for('calendar.sync_page'))


def _current_user_or_login():
    if not is_logged_in():
        return None, redirect(url_for('auth.login'))
    return get_current_user_id(), None


def sync_page():
    user_id, login_redirect = _current_user_or_login()
    if login_redirect:
        return login_redirect

    accounts = CalendarAccount.get_by_user(user_id)
    imported_events = CalendarEvent.get_by_user(user_id)
    meetups = Meetup.get_by_user(user_id)
    conflicts = find_calendar_conflicts(meetups, imported_events)

    return render_template(
        'user/calendar_sync.html',
        accounts=accounts,
        imported_events=imported_events,
        meetups=meetups,
        conflicts=conflicts,
    )


def connect_account():
    user_id, login_redirect = _current_user_or_login()
    if login_redirect:
        return login_redirect

    provider = request.form.get('provider', 'other')
    account_email = (request.form.get('account_email') or '').strip().lower()
    display_name = (request.form.get('display_name') or '').strip()
    permission_scope = request.form.get('permission_scope') or 'read_write'
    consent_given = request.form.get('permission_consent') == '1'

    if not EMAIL_RE.match(account_email):
        flash('Enter a valid calendar account email.', 'error')
        return _calendar_redirect()

    if permission_scope not in {'read', 'write', 'read_write'}:
        permission_scope = 'read_write'

    if not consent_given:
        flash('Calendar connection needs your permission before syncing.', 'error')
        return _calendar_redirect()

    CalendarAccount.connect(
        user_id,
        provider,
        account_email,
        display_name,
        permission_scope,
    )
    flash('Calendar account connected.', 'success')
    return _calendar_redirect()


def disconnect_account(account_id):
    user_id, login_redirect = _current_user_or_login()
    if login_redirect:
        return login_redirect

    CalendarAccount.disconnect(account_id, user_id)
    flash('Calendar account disconnected.', 'info')
    return _calendar_redirect()


def import_events():
    user_id, login_redirect = _current_user_or_login()
    if login_redirect:
        return login_redirect

    try:
        account_id = int(request.form.get('account_id', ''))
    except (TypeError, ValueError):
        account_id = 0

    account = CalendarAccount.get_for_user(account_id, user_id)
    if not account or not account.get('is_active'):
        flash('Choose an active calendar account before importing events.', 'error')
        return _calendar_redirect()

    ics_text = (request.form.get('ics_text') or '').strip()
    upload = request.files.get('ics_file')
    if upload and upload.filename:
        ics_text = upload.read().decode('utf-8', errors='replace')

    if not ics_text:
        flash('Upload an .ics file or paste calendar data to import.', 'error')
        return _calendar_redirect()

    events = parse_ics_events(ics_text)
    if not events:
        flash('No calendar events were found in that import.', 'error')
        return _calendar_redirect()

    imported_count = CalendarEvent.import_events(user_id, account_id, events)
    CalendarAccount.touch_sync(account_id, user_id)
    flash(f'Imported {imported_count} calendar event(s).', 'success')
    return _calendar_redirect()


def sync_now(account_id):
    user_id, login_redirect = _current_user_or_login()
    if login_redirect:
        return login_redirect

    account = CalendarAccount.get_for_user(account_id, user_id)
    if not account or not account.get('is_active'):
        flash('Calendar account not found.', 'error')
        return _calendar_redirect()

    CalendarAccount.touch_sync(account_id, user_id)
    flash('Calendar sync refreshed. Conflicts are up to date.', 'success')
    return _calendar_redirect()


def delete_event(event_id):
    user_id, login_redirect = _current_user_or_login()
    if login_redirect:
        return login_redirect

    CalendarEvent.delete(event_id, user_id)
    flash('Imported event removed.', 'info')
    return _calendar_redirect()


def export_calendar():
    user_id, login_redirect = _current_user_or_login()
    if login_redirect:
        return login_redirect

    meetups = Meetup.get_by_user(user_id)
    ics = build_meetups_ics(meetups)

    return Response(
        ics,
        mimetype='text/calendar',
        headers={
            'Content-Disposition': 'attachment; filename="bhetamla-meetups.ics"'
        },
    )
