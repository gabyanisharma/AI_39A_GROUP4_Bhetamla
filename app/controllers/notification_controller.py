from flask import render_template, request, redirect, url_for, flash, jsonify
from app.models.notification import EmergencyContact, SOSAlert
from app.models.user import User
from app import mail
from flask_mail import Message
import secrets



# TEMP USER ID FOR TESTING
# Later replace with login system
TEST_USER_ID = 1


def safety():
    user_id = TEST_USER_ID

    contacts = EmergencyContact.get_by_user(user_id)
    alerts = SOSAlert.get_all_by_user(user_id)
    active = SOSAlert.get_active(user_id)
    user = User.get_by_id(user_id)

    return render_template(
        'user/safety.html',
        contacts=contacts,
        alerts=alerts,
        active_alert=active,
        user=user
    )


def add_contact():
    user_id = TEST_USER_ID

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        relationship = request.form.get('relationship', '').strip()

        if not name or not phone:
            flash('Name and phone are required.', 'error')
            return redirect(url_for('notification.safety'))

        contacts = EmergencyContact.get_by_user(user_id)

        if len(contacts) >= 3:
            flash('Maximum 3 emergency contacts allowed.', 'error')
            return redirect(url_for('notification.safety'))

        EmergencyContact.create(
            user_id,
            name,
            phone,
            relationship
        )

        flash('Emergency contact added!', 'success')

    return redirect(url_for('notification.safety'))


def delete_contact(contact_id):
    user_id = TEST_USER_ID

    EmergencyContact.delete(contact_id, user_id)

    flash('Contact removed.', 'info')

    return redirect(url_for('notification.safety'))


def trigger_sos():
    user_id = TEST_USER_ID

    user = User.get_by_id(user_id)
    contacts = EmergencyContact.get_by_user(user_id)

    # Get location from frontend
    data = request.get_json()

    latitude = data.get('latitude')
    longitude = data.get('longitude')

    message = data.get(
        'message',
        'I need help! This is an emergency.'
    )

    # Generate cancel PIN
    cancel_pin = str(secrets.randbelow(9000) + 1000)

    # Save alert
    alert_id = SOSAlert.create(
        user_id,
        latitude,
        longitude,
        message,
        cancel_pin
    )

    if not user:
        class DummyUser:
            id = TEST_USER_ID
            full_name = "Bipin Maharjan"
            email = "bipin@example.com"
        user = DummyUser()

    maps_link = (
        f"https://maps.google.com/?q={latitude},{longitude}"
        if latitude
        else "Location unavailable"
    )

    # Send email alerts
    for contact in contacts:
        try:
            msg = Message(
                subject=f'🚨 SOS Alert from {user.full_name}',
                recipients=[user.email]
            )

            msg.html = f"""
                <h2>🚨 Emergency Alert</h2>

                <p>
                    <strong>{user.full_name}</strong>
                    has triggered an SOS alert!
                </p>

                <p>
                    <strong>Emergency Contact:</strong>
                    {contact['name']}
                    ({contact['relationship']})
                </p>

                <p>
                    <strong>Phone:</strong>
                    {contact['phone']}
                </p>

                <p>
                    <strong>Message:</strong>
                    {message}
                </p>

                <p>
                    <strong>Location:</strong>
                    <a href="{maps_link}">
                        {maps_link}
                    </a>
                </p>

                <hr>

                <p style="color:red;">
                    Please check on them immediately!
                </p>
            """

            mail.send(msg)

        except Exception as e:
            print(f"SOS email error: {e}")

    return jsonify({
        'success': True,
        'alert_id': alert_id,
        'cancel_pin': cancel_pin,
        'message': 'SOS alert sent successfully!'
    })


def cancel_sos():
    user_id = TEST_USER_ID

    data = request.get_json()

    pin = data.get('pin', '')

    alert = SOSAlert.get_active(user_id)

    if not alert:
        return jsonify({
            'success': False,
            'message': 'No active alert found.'
        })

    if str(alert['cancel_pin']) != str(pin):
        return jsonify({
            'success': False,
            'message': 'Incorrect PIN.'
        })

    SOSAlert.cancel(alert['id'], user_id)

    return jsonify({
        'success': True,
        'message': 'SOS alert cancelled.'
    })