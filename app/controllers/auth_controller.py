from flask import render_template, request, redirect, url_for, flash, session
from app.models.user import User
from app.auth import login_user, logout_user
from app import mail
from flask_mail import Message
from config import Config

def register():
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email     = request.form.get('email', '').strip()
        phone     = request.form.get('phone', '').strip()
        password  = request.form.get('password', '')
        confirm   = request.form.get('confirm_password', '')

        # Basic validation
        if not all([full_name, email, phone, password, confirm]):
            flash('All fields are required.', 'error')
            return render_template('auth/register.html')

        if password != confirm:
            flash('Passwords do not match.', 'error')
            return render_template('auth/register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return render_template('auth/register.html')

        if User.email_exists(email):
            flash('Email is already registered.', 'error')
            return render_template('auth/register.html')

        user_id = User.create(full_name, email, phone, password)
        if not user_id:
            flash('Registration failed. Please try again.', 'error')
            return render_template('auth/register.html')

        # Auto-verify immediately (email not configured)
        User.verify_email(user_id)

        flash('Account created! You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


def login():
    if request.method == 'POST':
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        # Block empty fields
        if not email or not password:
            flash('Please enter your email and password.', 'error')
            return render_template('auth/login.html')

        user = User.get_by_email(email)

        # Block wrong credentials
        if not user or not User.check_password(user['password_hash'], password):
            flash('Invalid email or password.', 'error')
            return render_template('auth/login.html')

        # Block unverified accounts
        if not user['is_verified']:
            flash('Please verify your email before logging in.', 'error')
            return render_template('auth/login.html')

        login_user(user)
        flash(f"Welcome back, {user['full_name']}!", 'success')
        # Honour a pending meetup invite link opened while logged out.
        invite_code = session.pop('next_invite', None)
        if invite_code:
            return redirect(url_for('meetup.join_via_invite', code=invite_code))
        return redirect(url_for('user.dashboard'))

    return render_template('auth/login.html')


def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


def verify_email(token):
    user = User.get_by_verification_token(token)
    if not user:
        flash('Invalid or expired verification link.', 'error')
        return redirect(url_for('auth.login'))

    User.verify_email(user['id'])
    flash('Email verified! You can now log in.', 'success')
    return redirect(url_for('auth.login'))


def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        user  = User.get_by_email(email)

        if user:
            token = User.set_reset_token(user['id'])
            _send_reset_email(user, token)
            # Print link to terminal for dev use
            from flask import current_app
            with current_app.test_request_context():
                pass
            reset_link = url_for('auth.reset_password', token=token, _external=True)
            print(f"\n[DEV] Password reset link for {user['email']}:\n{reset_link}\n")

        # Always show this message (don't reveal if email exists)
        flash('If that email exists, a reset link has been sent.', 'info')
        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html')


def reset_password(token):
    user = User.get_by_reset_token(token)
    if not user:
        flash('Invalid or expired reset link.', 'error')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')

        if password != confirm:
            flash('Passwords do not match.', 'error')
            return render_template('auth/reset_password.html', token=token)

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return render_template('auth/reset_password.html', token=token)

        User.reset_password(user['id'], password)
        flash('Password reset successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', token=token)


# ─── Private email helpers ─────────────────────────────────────────────────

def _send_verification_email(user):
    if not Config.MAIL_USERNAME or not Config.MAIL_PASSWORD:
        print('Mail skipped: MAIL_USERNAME / MAIL_PASSWORD not configured.')
        return

    token = user['verification_token']
    link  = url_for('auth.verify_email', token=token, _external=True)
    msg   = Message('Verify your Bhetamल account', recipients=[user['email']])
    msg.html = f"""
        <h2>Welcome to Bhetamल, {user['full_name']}!</h2>
        <p>Click the link below to verify your email address:</p>
        <a href="{link}">{link}</a>
        <p>This link expires in 24 hours.</p>
    """
    try:
        mail.send(msg)
    except Exception as e:
        print(f"Mail error: {e}")


def _send_reset_email(user, token):
    if not Config.MAIL_USERNAME or not Config.MAIL_PASSWORD:
        print('Mail skipped: MAIL_USERNAME / MAIL_PASSWORD not configured.')
        return

    link = url_for('auth.reset_password', token=token, _external=True)
    msg  = Message('Reset your Bhetamल password', recipients=[user['email']])
    msg.html = f"""
        <h2>Password Reset Request</h2>
        <p>Click the link below to reset your password:</p>
        <a href="{link}">{link}</a>
        <p>This link expires in 24 hours. If you did not request this, ignore this email.</p>
    """
    try:
        mail.send(msg)
    except Exception as e:
        print(f"Mail error: {e}")
