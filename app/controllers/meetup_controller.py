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


def delete_availability(slot_id):
    if not is_logged_in():
        return redirect(url_for('auth.login'))

    AvailabilitySlot.delete(slot_id, get_current_user_id())
    flash('Slot removed.', 'info')
    return redirect(url_for('meetup.scheduler_page'))


def search_users():
    if not is_logged_in():
        return jsonify([])

    query   = request.args.get('q', '').strip()
    if len(query) < 2:
        return jsonify([])

    results = Friend.search_users(query, get_current_user_id())
    return jsonify([{
        'id':       u['id'],
        'name':     u['full_name'],
        'email':    u['email']
    } for u in results])


def send_friend_request():
    if not is_logged_in():
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        friend_id = request.form.get('friend_id')
        if not friend_id:
            flash('Invalid user.', 'error')
            return redirect(url_for('meetup.scheduler_page'))

        friend = User.get_by_id(friend_id)
        if not friend:
            flash('User not found.', 'error')
            return redirect(url_for('meetup.scheduler_page'))

        Friend.send_request(get_current_user_id(), int(friend_id))
        flash(f'Friend request sent to {friend["full_name"]}!', 'success')

    return redirect(url_for('meetup.scheduler_page'))


def respond_friend_request(request_id):
    if not is_logged_in():
        return redirect(url_for('auth.login'))

    action = request.form.get('action')
    if action == 'accept':
        Friend.accept_request(request_id, get_current_user_id())
        flash('Friend request accepted!', 'success')
    elif action == 'reject':
        Friend.reject_request(request_id, get_current_user_id())
        flash('Friend request declined.', 'info')

    return redirect(url_for('meetup.scheduler_page'))


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