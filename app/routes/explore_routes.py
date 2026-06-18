from flask import Blueprint
from app.routes.user_routes import login_required
from app.controllers.trending_controller import (
    explore_feed, spot_detail, toggle_interaction,
    saved_spots, dismiss_recommendation
)

explore_bp = Blueprint('explore', __name__, url_prefix='/explore')


@explore_bp.route('/')
@login_required
def feed():
    return explore_feed()


@explore_bp.route('/saved')
@login_required
def saved():
    return saved_spots()


@explore_bp.route('/spot/<int:spot_id>')
@login_required
def spot(spot_id):
    return spot_detail(spot_id)


@explore_bp.route('/spot/<int:spot_id>/interact', methods=['POST'])
@login_required
def interact(spot_id):
    return toggle_interaction(spot_id)


@explore_bp.route('/recommendation/<int:spot_id>/dismiss', methods=['POST'])
@login_required
def dismiss(spot_id):
    return dismiss_recommendation(spot_id)
