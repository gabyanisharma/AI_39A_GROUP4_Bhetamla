from flask import Blueprint
from app.routes.user_routes import login_required
from app.controllers.analytics_controller import meeting_history, analytics_data

analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')


@analytics_bp.route('/')
@login_required
def history():
    return meeting_history()


@analytics_bp.route('/data')
@login_required
def data():
    return analytics_data()
