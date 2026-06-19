import csv
import io
from datetime import date

from flask import render_template, redirect, url_for, jsonify, Response
from app.auth import get_current_user_id, is_logged_in
from app.models.analytics import MeetingAnalytics


def meeting_history():
    if not is_logged_in():
        return redirect(url_for('auth.login'))

    user_id = get_current_user_id()
    today = date.today()
    overview = MeetingAnalytics.get_overview(user_id, today)
    companions = MeetingAnalytics.get_top_companions(user_id)

    # Max month count drives the bar-chart scaling in the template.
    max_month = max((b['count'] for b in overview['monthly']), default=0)

    return render_template('user/analytics.html',
                           stats=overview['stats'],
                           monthly=overview['monthly'],
                           max_month=max_month,
                           upcoming=overview['upcoming'],
                           past=overview['past'],
                           companions=companions)


def export_history():
    """Export the user's meetup history as a CSV download (F24)."""
    if not is_logged_in():
        return redirect(url_for('auth.login'))

    user_id = get_current_user_id()
    overview = MeetingAnalytics.get_overview(user_id)

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(['Title', 'Date', 'Time', 'Venue', 'Status', 'Role', 'When'])

    def _row(m, bucket):
        venue = m.get('winning_venue_name') or m.get('midpoint_address') or ''
        role = 'Organiser' if m.get('created_by') == user_id else 'Member'
        writer.writerow([
            m.get('title', ''),
            m.get('meetup_date') or '',
            m.get('meetup_time') or '',
            venue,
            m.get('status', ''),
            role,
            bucket,
        ])

    for m in overview['past']:
        _row(m, 'Past')
    for m in overview['upcoming']:
        _row(m, 'Upcoming')

    csv_data = buf.getvalue()
    return Response(
        csv_data,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=bhetamla_meetup_history.csv'},
    )


def analytics_data():
    """JSON endpoint for the analytics overview (for future dashboards)."""
    if not is_logged_in():
        return jsonify({'success': False}), 401

    user_id = get_current_user_id()
    overview = MeetingAnalytics.get_overview(user_id)
    return jsonify({
        'success': True,
        'stats': overview['stats'],
        'monthly': overview['monthly'],
    })
