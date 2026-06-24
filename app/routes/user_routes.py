from flask import Blueprint, redirect, url_for, render_template, session
from functools import wraps
from app.auth import is_logged_in
from app.controllers.user_controller import (
    profile, settings, support, submit_feedback
)
from app.controllers.notification_controller import safety
from datetime import datetime
from app.models.meetup import Meetup
from app.models.meetup_preference import MeetupPlanPreference
from app.database import execute_query

user_bp = Blueprint('user', __name__, url_prefix='/user')

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not is_logged_in():
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@user_bp.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']

    # ── Core meetup data ──────────────────────────────────────────────────────
    meetups = Meetup.get_by_user(user_id) or []
    for meetup in meetups:
        prefs = MeetupPlanPreference.get_for_meetup(meetup['id'])
        selected_pref = next(
            (p for p in prefs if p.get('selected_venue')),
            None
        )
        meetup['dashboard_venue'] = (
            meetup.get('winning_venue_name')
            or (selected_pref.get('selected_venue') if selected_pref else None)
            or ''
        )

    # ── Today's meetups (status active OR date = today) ───────────────────────
    today_str = datetime.now().strftime('%Y-%m-%d')
    todays_meetups = [
        m for m in meetups
        if (m.get('meetup_date') and str(m['meetup_date']) == today_str)
        or m.get('status') == 'active'
    ]

    # ── Pending invites (meetup_members rows where this user was invited) ─────
    pending_invites = execute_query(
        """SELECT mm.id AS invite_id,
                  m.id AS meetup_id,
                  m.title,
                  u.full_name AS inviter_name,
                  m.meetup_date,
                  m.meetup_time
           FROM meetup_members mm
           JOIN meetups m ON m.id = mm.meetup_id
           JOIN users u   ON u.id = m.created_by
           WHERE mm.user_id = %s
             AND mm.status  = 'invited'
           ORDER BY mm.joined_at DESC
           LIMIT 10""",
        (user_id,), fetch=True
    ) or []

    # ── Stats: saved places ───────────────────────────────────────────────────
    saved_count_row = execute_query(
        "SELECT COUNT(*) AS cnt FROM saved_places WHERE user_id = %s",
        (user_id,), fetch=True
    )
    saved_count = saved_count_row[0]['cnt'] if saved_count_row else 0

    # ── Stats: active friends ─────────────────────────────────────────────────
    friends_count_row = execute_query(
        """SELECT COUNT(*) AS cnt FROM friends
           WHERE (user_id = %s OR friend_id = %s)
             AND status = 'accepted'""",
        (user_id, user_id), fetch=True
    )
    friends_count = friends_count_row[0]['cnt'] if friends_count_row else 0

    # ── Stats: badges earned ──────────────────────────────────────────────────
    from app.models.achievement import Achievement
    badges_count = Achievement.count_for_user(user_id)

    # ── Meetup member avatars (first 6 meetups, up to 5 members each) ─────────
    meetup_member_map = {}
    for m in meetups[:6]:
        mid = m['id']
        members = execute_query(
            """SELECT u.full_name, mm.status
               FROM meetup_members mm
               JOIN users u ON u.id = mm.user_id
               WHERE mm.meetup_id = %s
                 AND mm.status != 'declined'
               LIMIT 5""",
            (mid,), fetch=True
        ) or []
        meetup_member_map[mid] = members

    today_display = datetime.now().strftime('%A, %B %Y')
    today_iso     = datetime.now().strftime('%Y-%m-%d')

    return render_template(
        'user/dashboard.html',
        meetups=meetups,
        today=today_display,
        today_iso=today_iso,
        todays_meetups=todays_meetups,
        pending_invites=pending_invites,
        saved_count=saved_count,
        friends_count=friends_count,
        badges_count=badges_count,
        meetup_member_map=meetup_member_map,
    )

@user_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile_page():
    return profile()

@user_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings_page():
    return settings()


@user_bp.route('/safety')
@login_required
def safety_page():
    return safety()

@user_bp.route('/notifications')
@login_required
def notifications_page():
    from app.controllers.notification_controller import notifications
    return notifications()

@user_bp.route('/support', methods=['GET', 'POST'])
@login_required
def support_page():
    return support()


@user_bp.route('/feedback', methods=['POST'])
@login_required
def feedback_submit():
    return submit_feedback()
