from flask import render_template, request, redirect, url_for, flash, session
from app.models.user import User
from app.models.feedback import Feedback
from app.auth import is_logged_in, get_current_user_id
import os
from werkzeug.utils import secure_filename
from app.models.notification import SOSAlert

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def profile():
    if not is_logged_in():
        return redirect(url_for('auth.login'))

    user = User.get_by_id(get_current_user_id())
    return render_template('user/profile.html', user=user)

def settings():
    if not is_logged_in():
        return redirect(url_for('auth.login'))

    user = User.get_by_id(get_current_user_id())
    user_id = get_current_user_id()

    # Emergency contacts count for the Safety & Privacy card
    from app.models.notification import EmergencyContact
    contacts = EmergencyContact.get_by_user(user_id) or []

    # Notification preferences for the Preferences panel
    from app.models.notification_preference import NotificationPreference
    prefs = NotificationPreference.get_or_create(user_id)

    if request.method == 'POST':
        action = request.form.get('action')
        if not action and ('theme' in request.form or 'language' in request.form):
            action = 'update_preferences'

        if action == 'update_profile':
            full_name          = request.form.get('full_name', '').strip()
            phone              = request.form.get('phone', '').strip()
            budget_preference  = request.form.get('budget_preference', 0)
            cuisine_preference = request.form.get('cuisine_preference', '')
            transport_preference = request.form.get('transport_preference', 'any')

            # Handle profile picture upload
            if 'profile_pic' in request.files:
                file = request.files['profile_pic']
                if file and file.filename != '' and allowed_file(file.filename):
                    filename = secure_filename(f"user_{get_current_user_id()}_{file.filename}")
                    upload_folder = os.path.join('app', 'static', 'uploads', 'profiles')
                    os.makedirs(upload_folder, exist_ok=True)
                    file.save(os.path.join(upload_folder, filename))
                    User.update_profile_pic(get_current_user_id(), filename)
                    session['user_pic'] = filename

            User.update_profile(
                get_current_user_id(),
                full_name, phone,
                budget_preference,
                cuisine_preference,
                transport_preference
            )
            session['user_name'] = full_name
            flash('Profile updated successfully!', 'success')

        elif action == 'update_preferences':
            theme    = request.form.get('theme', 'light')
            language = request.form.get('language', 'en')
            User.update_preferences(get_current_user_id(), theme, language)
            session['theme']    = theme
            session['language'] = language
            flash('Preferences saved!', 'success')

        elif action == 'update_notification_prefs':
            def _cb(name): return 1 if request.form.get(name) else 0
            NotificationPreference.update(user_id, {
                'smart_alerts_enabled': _cb('smart_alerts_enabled'),
                'meetup_reminders':     _cb('meetup_reminders'),
                'invite_alerts':        _cb('invite_alerts'),
                'trending_alerts':      _cb('trending_alerts'),
            })
            flash('Notification preferences saved!', 'success')

        elif action == 'change_password':
            current_password = request.form.get('current_password', '')
            new_password     = request.form.get('new_password', '')
            confirm_password = request.form.get('confirm_password', '')

            if not User.check_password(user['password_hash'], current_password):
                flash('Current password is incorrect.', 'error')
            elif new_password != confirm_password:
                flash('New passwords do not match.', 'error')
            elif len(new_password) < 6:
                flash('Password must be at least 6 characters.', 'error')
            else:
                User.reset_password(get_current_user_id(), new_password)
                flash('Password changed successfully!', 'success')

        return redirect(url_for('user.settings_page'))

    return render_template('user/settings.html', user=user, contacts=contacts, prefs=prefs)

def notifications():
    if not is_logged_in():
        return redirect(url_for('auth.login'))
    user_id = get_current_user_id()
    alerts = SOSAlert.get_all_by_user(user_id)
    
    # Get general notifications and mark them all as read
    from app.models.notification import Notification
    db_notifications = Notification.get_by_user(user_id)
    Notification.mark_all_read(user_id)
    
    return render_template('user/notifications.html', alerts=alerts, db_notifications=db_notifications)

def support():
    if not is_logged_in():
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()
        
        if not subject or not message:
            flash('All fields are required.', 'error')
        else:
            flash('Your message has been sent to our support team. We will get back to you shortly!', 'success')
            return redirect(url_for('user.support_page'))
            
    feedback_summary = Feedback.average_rating()
    my_feedback = Feedback.get_by_user(get_current_user_id())
    return render_template('user/support.html',
                           feedback_summary=feedback_summary,
                           my_feedback=my_feedback)


def submit_feedback():
    """Store an app rating + optional message (US27)."""
    if not is_logged_in():
        return redirect(url_for('auth.login'))

    try:
        rating = int(request.form.get('rating', ''))
    except (TypeError, ValueError):
        rating = 0

    if rating < 1 or rating > 5:
        flash('Please select a rating between 1 and 5 stars.', 'error')
        return redirect(url_for('user.support_page'))

    message = request.form.get('message', '').strip()
    category = (request.form.get('category', 'general').strip() or 'general')[:50]

    Feedback.create(get_current_user_id(), rating, message, category)
    flash('Thanks for your feedback! 🌟', 'success')
    return redirect(url_for('user.support_page'))
