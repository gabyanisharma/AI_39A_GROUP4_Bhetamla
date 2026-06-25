import json
import os
from flask import render_template, request, redirect, url_for, flash, jsonify
from app.models.base_model import (
    Friend, AvailabilitySlot, MeetupSchedule, ScheduleInvite
)
from app.models.user import User
from app.auth import get_current_user_id, is_logged_in
from datetime import datetime

def scheduler():
    if not is_logged_in():
        return redirect(url_for('auth.login'))

    user_id  = get_current_user_id()
    friends  = Friend.get_friends(user_id)
    slots    = AvailabilitySlot.get_by_user(user_id)
    schedules = MeetupSchedule.get_by_user(user_id)
    pending  = Friend.get_pending_requests(user_id)
    sent     = Friend.get_sent_requests(user_id)
    invites  = ScheduleInvite.get_pending_by_user(user_id)

    restaurants = get_restaurants_data()

    return render_template('meetup/scheduler.html',
                           friends=friends,
                           slots=slots,
                           schedules=schedules,
                           pending_requests=pending,
                           sent_requests=sent,
                           invites=invites,
                           now=datetime.now())


def add_availability():
    if not is_logged_in():
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        date       = request.form.get('date')
        start_time = request.form.get('start_time')
        end_time   = request.form.get('end_time')
        label      = request.form.get('label', '').strip()

        if not all([date, start_time, end_time]):
            flash('Date and times are required.', 'error')
            return redirect(url_for('meetup.scheduler_page'))

        if start_time >= end_time:
            flash('End time must be after start time.', 'error')
            return redirect(url_for('meetup.scheduler_page'))

        AvailabilitySlot.create(get_current_user_id(), date,
                                start_time, end_time, label)
        flash('Availability slot added!', 'success')

    return redirect(url_for('meetup.scheduler_page'))


def import_calendar():
    """Import an uploaded .ics file as availability, detecting conflicts (F29)."""
    if not is_logged_in():
        return redirect(url_for('auth.login'))

    user_id = get_current_user_id()
    file = request.files.get('ics_file')
    if not file or not file.filename:
        flash('Please choose an .ics file to import.', 'error')
        return redirect(url_for('meetup.scheduler_page'))
    if not file.filename.lower().endswith('.ics'):
        flash('Only .ics calendar files are supported.', 'error')
        return redirect(url_for('meetup.scheduler_page'))

    from app.services.calendar_service import parse_ics, find_conflicts
    try:
        text = file.read().decode('utf-8', errors='ignore')
    except Exception:
        flash('Could not read that file.', 'error')
        return redirect(url_for('meetup.scheduler_page'))

    events = parse_ics(text)
    if not events:
        flash('No calendar events found in that file.', 'info')
        return redirect(url_for('meetup.scheduler_page'))

    imported, conflicts = 0, []
    for ev in events:
        clashes = find_conflicts(user_id, ev)
        if clashes:
            conflicts.append(
                f"{ev['summary']} on {ev['date']} — clashes with " + '; '.join(clashes)
            )
            continue  # don't import conflicting events
        AvailabilitySlot.create(
            user_id, ev['date'],
            ev['start_time'].strftime('%H:%M:%S'),
            ev['end_time'].strftime('%H:%M:%S'),
            (ev['summary'] or 'Imported')[:100],
        )
        imported += 1

    if imported:
        flash(f'Imported {imported} event(s) as availability.', 'success')
    if conflicts:
        flash('Skipped ' + str(len(conflicts)) + ' conflicting event(s): '
              + ' | '.join(conflicts[:5]), 'error')
    if not imported and not conflicts:
        flash('Nothing to import.', 'info')
    return redirect(url_for('meetup.scheduler_page'))


def delete_availability(slot_id):
    if not is_logged_in():
        return redirect(url_for('auth.login'))

    AvailabilitySlot.delete(slot_id, get_current_user_id())
    flash('Slot removed.', 'info')
    return redirect(url_for('meetup.scheduler_page'))


def search_users():
    if not is_logged_in():
        return jsonify([])

    query_str = request.args.get('q', '').strip()
    if len(query_str) < 2:
        return jsonify([])

    current_user_id = get_current_user_id()
    results = Friend.search_users(query_str, current_user_id)
    output = []
    for u in results:
        status, fid = Friend.get_friendship_status(current_user_id, u['id'])
        output.append({
            'id':       u['id'],
            'name':     u['full_name'],
            'email':    u['email'],
            'status':   status,       # 'accepted' | 'pending_sent' | 'pending_received' | None
            'fid':      fid           # friendship row id (for respond actions)
        })
    return jsonify(output)


def send_friend_request():
    if not is_logged_in():
        return jsonify({'success': False, 'message': 'Login required.'}), 401

    data      = request.get_json(silent=True) or {}
    friend_id = data.get('friend_id') or request.form.get('friend_id')

    if not friend_id:
        return jsonify({'success': False, 'message': 'Invalid user.'}), 400

    friend_id = int(friend_id)
    current_user_id = get_current_user_id()
    friend = User.get_by_id(friend_id)

    if not friend:
        return jsonify({'success': False, 'message': 'User not found.'}), 404

    if friend_id == current_user_id:
        return jsonify({'success': False, 'message': "Can't add yourself."}), 400

    Friend.send_request(current_user_id, friend_id)

    # Send notification to the recipient
    from app.controllers.notification_controller import send_notification
    current_user = User.get_by_id(current_user_id)
    send_notification(
        friend_id,
        '👥 Friend Request',
        f'{current_user["full_name"]} sent you a friend request.',
        type='friend',
        link='/meetup/groups'
    )

    return jsonify({'success': True, 'message': f'Friend request sent to {friend["full_name"]}!'})


def respond_friend_request(request_id):
    if not is_logged_in():
        return jsonify({'success': False, 'message': 'Login required.'}), 401

    data   = request.get_json(silent=True) or {}
    action = data.get('action') or request.form.get('action')
    current_user_id = get_current_user_id()

    if action == 'accept':
        Friend.accept_request(request_id, current_user_id)
        # Notify the sender that their request was accepted
        from app.database import execute_query as _eq
        row = _eq("SELECT user_id FROM friends WHERE id=%s", (request_id,), fetch=True)
        if row:
            sender_id = row[0]['user_id']
            current_user = User.get_by_id(current_user_id)
            from app.controllers.notification_controller import send_notification
            send_notification(
                sender_id,
                '✅ Friend Request Accepted',
                f'{current_user["full_name"]} accepted your friend request!',
                type='friend',
                link='/meetup/groups'
            )
        return jsonify({'success': True, 'message': 'Friend request accepted!'})

    elif action == 'reject':
        Friend.reject_request(request_id, current_user_id)
        return jsonify({'success': True, 'message': 'Friend request declined.'})

    return jsonify({'success': False, 'message': 'Invalid action.'}), 400


def remove_friend():
    if not is_logged_in():
        return jsonify({'success': False, 'message': 'Login required.'}), 401

    data      = request.get_json(silent=True) or {}
    friend_id = data.get('friend_id')
    if not friend_id:
        return jsonify({'success': False, 'message': 'Missing friend_id.'}), 400

    Friend.remove_friend(get_current_user_id(), int(friend_id))
    return jsonify({'success': True, 'message': 'Friend removed.'})


def create_schedule():
    if not is_logged_in():
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        title         = request.form.get('title', '').strip()
        description   = request.form.get('description', '').strip()
        proposed_date = request.form.get('proposed_date')
        proposed_time = request.form.get('proposed_time')
        invite_ids    = request.form.getlist('invite_friends')

        if not all([title, proposed_date, proposed_time]):
            flash('Title, date and time are required.', 'error')
            return redirect(url_for('meetup.scheduler_page'))

        schedule_id = MeetupSchedule.create(
            get_current_user_id(), title, description,
            proposed_date, proposed_time
        )

        for friend_id in invite_ids:
            ScheduleInvite.create(schedule_id, int(friend_id))

        flash('Meetup scheduled and invites sent!', 'success')

    return redirect(url_for('meetup.scheduler_page'))


def respond_invite(invite_id):
    if not is_logged_in():
        return redirect(url_for('auth.login'))

    action = request.form.get('action')
    if action in ['accepted', 'declined']:
        ScheduleInvite.respond(invite_id, get_current_user_id(), action)
        flash(f'Invite {action}!', 'success')

    return redirect(url_for('meetup.scheduler_page'))


def get_common_availability():
    if not is_logged_in():
        return jsonify([])

    user_id    = get_current_user_id()
    friend_ids = request.args.getlist('friends[]')

    if not friend_ids:
        return jsonify([])

    all_ids = [user_id] + [int(f) for f in friend_ids]
    slots   = AvailabilitySlot.get_common_slots(all_ids)

    return jsonify([{
        'date':       str(s['date']),
        'start_time': str(s['start_time']),
        'end_time':   str(s['end_time']),
        'count':      s['available_count']
    } for s in slots])

def get_restaurants_data():
    file_path = os.path.join(os.getcwd(), 'data', 'restaurants.json')
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []
    
