from flask import render_template, request, redirect, url_for, flash, session, jsonify
from app.models.notification import EmergencyContact, SOSAlert, Notification
from app.models.user import User
from app.auth import get_current_user_id, is_logged_in
from app import mail
from flask_mail import Message
from config import Config
import secrets

def safety():
    if not is_logged_in():
        return redirect(url_for('auth.login'))

    user_id  = get_current_user_id()
    contacts = EmergencyContact.get_by_user(user_id)
    alerts   = SOSAlert.get_all_by_user(user_id)
    active   = SOSAlert.get_active(user_id)
    user     = User.get_by_id(user_id)

    return render_template('user/safety.html',
                           contacts=contacts,
                           alerts=alerts,
                           active_alert=active,
                           user=user)


def add_contact():
    if not is_logged_in():
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        name         = request.form.get('name', '').strip()
        phone        = request.form.get('phone', '').strip()
        relationship = request.form.get('relationship', '').strip()

        if not name or not phone:
            flash('Name and phone are required.', 'error')
            return redirect(url_for('user.safety_page'))

        contacts = EmergencyContact.get_by_user(get_current_user_id())
        if len(contacts) >= 3:
            flash('Maximum 3 emergency contacts allowed.', 'error')
            return redirect(url_for('user.safety_page'))

        EmergencyContact.create(get_current_user_id(), name, phone, relationship)
        flash('Emergency contact added!', 'success')

    return redirect(url_for('user.safety_page'))


def delete_contact(contact_id):
    if not is_logged_in():
        return redirect(url_for('auth.login'))

    EmergencyContact.delete(contact_id, get_current_user_id())
    flash('Contact removed.', 'info')
    return redirect(url_for('user.safety_page'))


def trigger_sos():
    if not is_logged_in():
        return jsonify({'success': False, 'message': 'Not logged in'}), 401

    user_id  = get_current_user_id()
    user     = User.get_by_id(user_id)
    contacts = EmergencyContact.get_by_user(user_id)

    # Get location from request
    data      = request.get_json(silent=True) or {}
    latitude  = data.get('latitude')
    longitude = data.get('longitude')
    message   = data.get('message', 'I need help! This is an emergency.')

    # Generate a 4-digit cancel PIN
    cancel_pin = str(secrets.randbelow(9000) + 1000)

    # Save alert to database
    alert_id = SOSAlert.create(user_id, latitude, longitude, message, cancel_pin)

    # Send email to all emergency contacts
    maps_link = f"https://maps.google.com/?q={latitude},{longitude}" if latitude else "Location unavailable"

    if not Config.MAIL_USERNAME or not Config.MAIL_PASSWORD:
        print('Mail skipped: MAIL_USERNAME / MAIL_PASSWORD not configured.')
        return jsonify({
            'success':    True,
            'alert_id':   alert_id,
            'cancel_pin': cancel_pin,
            'message':    'SOS alert saved successfully!'
        })

    for contact in contacts:
        try:
            msg = Message(
                subject=f'🚨 SOS Alert from {user["full_name"]}',
                recipients=[user['email']]  # send to user's email for now
            )
            msg.html = f"""
                <h2>🚨 Emergency Alert</h2>
                <p><strong>{user['full_name']}</strong> has triggered an SOS alert!</p>
                <p><strong>Contact:</strong> {contact['name']} ({contact['relationship']})</p>
                <p><strong>Phone:</strong> {contact['phone']}</p>
                <p><strong>Message:</strong> {message}</p>
                <p><strong>Location:</strong> <a href="{maps_link}">{maps_link}</a></p>
                <p><strong>Time:</strong> Just now</p>
                <hr>
                <p style="color:red;">Please check on them immediately!</p>
            """
            mail.send(msg)
        except Exception as e:
            print(f"SOS email error: {e}")

    return jsonify({
        'success':    True,
        'alert_id':   alert_id,
        'cancel_pin': cancel_pin,
        'message':    'SOS alert sent successfully!'
    })


def cancel_sos():
    if not is_logged_in():
        return jsonify({'success': False}), 401

    user_id  = get_current_user_id()
    data     = request.get_json(silent=True) or {}
    pin      = data.get('pin', '')
    alert    = SOSAlert.get_active(user_id)

    if not alert:
        return jsonify({'success': False, 'message': 'No active alert found.'})

    if str(alert['cancel_pin']) != str(pin):
        return jsonify({'success': False, 'message': 'Incorrect PIN.'})

    SOSAlert.cancel(alert['id'], user_id)
    return jsonify({'success': True, 'message': 'SOS alert cancelled.'})


def send_notification(user_id, title, message, type='general', link=None):
    """Create a database-backed notification for a user."""
    return Notification.create(user_id, title, message, type, link)


MODE_ICONS = {'car': '🚗', 'bike': '🛵', 'public': '🚌', 'walk': '🚶'}


def fare_drop_notification(user_id, mode, fare, target_fare, saving, meetup_id, meetup_title=None):
    """
    Create a rich fare-drop notification with saving details.
    Returns the new notification row ID.
    """
    icon = MODE_ICONS.get(mode, '🚗')
    title = f"📉 Fare Drop Alert — {icon} {mode.capitalize()}"
    message = (
        f"Great news! The {mode.capitalize()} fare for "
        f"{'your meetup «' + meetup_title + '»' if meetup_title else 'your meetup'} "
        f"has dropped to NPR {fare:,.0f} "
        f"(target was NPR {target_fare:,.0f}). "
        f"You save NPR {saving:,.0f}! 🎉"
    )
    link = f"/fare-alert/meetup/{meetup_id}"
    return Notification.create(user_id, title, message, type='reminder', link=link)


def get_unread_count():
    if not is_logged_in():
        return jsonify({'count': 0})
    count = Notification.get_unread_count(get_current_user_id())
    return jsonify({'count': count})

def notifications():
    if not is_logged_in():
        return redirect(url_for('auth.login'))

    user_id = get_current_user_id()
    notifs  = Notification.get_by_user(user_id)
    Notification.mark_all_read(user_id)

    return render_template('user/notifications.html',
                           notifications=notifs)


def mark_read(notification_id):
    if not is_logged_in():
        return jsonify({'success': False})
    Notification.mark_read(notification_id, get_current_user_id())
    return jsonify({'success': True})


def delete_notification(notification_id):
    if not is_logged_in():
        return redirect(url_for('auth.login'))
    Notification.delete(notification_id, get_current_user_id())
    return redirect(url_for('user.notifications_page'))


def clear_all_notifications():
    if not is_logged_in():
        return redirect(url_for('auth.login'))
    Notification.delete_all(get_current_user_id())
    flash('All notifications cleared.', 'info')
    return redirect(url_for('user.notifications_page'))