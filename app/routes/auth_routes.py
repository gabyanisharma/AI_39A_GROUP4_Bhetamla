from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models.user import User

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user_id'):
        return redirect(url_for('user.dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        
        if not email or not password:
            flash('Please enter both email and password.', 'error')
            return render_template('auth/login.html')
            
        user = User.get_by_email(email)
        
        if user and user.password == password:
            session['user_id'] = user.id
            session['user_name'] = user.full_name
            if 'theme' not in session:
                session['theme'] = 'light'
            if 'language' not in session:
                session['language'] = 'en'
                
            flash(f'Welcome back, {user.full_name}!', 'success')
            return redirect(url_for('user.dashboard'))
        else:
            flash('Invalid email or password.', 'error')
            
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if session.get('user_id'):
        return redirect(url_for('user.dashboard'))
        
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        
        if not full_name or not email or not password:
            flash('All fields are required.', 'error')
            return render_template('auth/register.html')
            
        existing_user = User.get_by_email(email)
        if existing_user:
            flash('An account with this email already exists.', 'error')
            return render_template('auth/register.html')
            
        new_user = User(full_name=full_name, email=email, password=password)
        new_user.save()
        
        # Retrieve the newly created user to get their auto-incremented ID
        saved_user = User.get_by_email(email)
        if saved_user:
            session['user_id'] = saved_user.id
            session['user_name'] = saved_user.full_name
            session['theme'] = 'light'
            session['language'] = 'en'
            flash('Your account has been registered successfully!', 'success')
            return redirect(url_for('user.dashboard'))
        else:
            flash('Something went wrong. Please try logging in.', 'info')
            return redirect(url_for('auth.login'))
            
    return render_template('auth/register.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))
