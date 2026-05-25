from flask import render_template, request, redirect, url_for, flash, session
from app.models.user import User
from app.models.notification import SOSAlert

def profile():
    user_id = session.get('user_id')
    user = User.get_by_id(user_id)
    
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('auth.login'))
        
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        if not full_name:
            flash('Full name is required.', 'error')
        else:
            user.full_name = full_name
            user.update_profile()
            session['user_name'] = full_name
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('user.profile_page'))
            
    return render_template('user/profile.html', user=user)

def settings():
    if request.method == 'POST':
        theme = request.form.get('theme', 'light')
        language = request.form.get('language', 'en')
        
        session['theme'] = theme
        session['language'] = language
        
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('user.settings_page'))
        
    return render_template('user/settings.html')

def notifications():
    user_id = session.get('user_id')
    alerts = SOSAlert.get_all_by_user(user_id) if user_id else []
    return render_template('user/notifications.html', alerts=alerts)

def support():
    if request.method == 'POST':
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()
        
        if not subject or not message:
            flash('All fields are required.', 'error')
        else:
            flash('Your message has been sent to our support team. We will get back to you shortly!', 'success')
            return redirect(url_for('user.support_page'))
            
    return render_template('user/support.html')
