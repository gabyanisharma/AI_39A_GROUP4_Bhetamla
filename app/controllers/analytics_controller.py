from datetime import date

from flask import render_template, redirect, url_for, jsonify
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
