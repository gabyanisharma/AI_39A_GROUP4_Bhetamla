from flask import Blueprint, render_template, session, redirect, url_for
from app.routes.user_routes import login_required

meetup_bp = Blueprint('meetup', __name__, url_prefix='/meetup')

@meetup_bp.route('/plan')
@login_required
def plan():
    return render_template('meetup/plan.html')

@meetup_bp.route('/groups')
@login_required
def groups():
    return render_template('meetup/groups.html')
