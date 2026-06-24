from flask import Blueprint
from app.routes.user_routes import login_required
from app.controllers.place_controller import (
    saved_places, restaurants, restaurant_detail,
    add_review, save_place, remove_saved_place,
    api_filter_restaurants, api_cuisines, api_budget_range,
    api_ambiences, api_offers, api_nearby_restaurants
)

place_bp = Blueprint('place', __name__, url_prefix='/place')

@place_bp.route('/saved')
@login_required
def saved():
    return saved_places()

@place_bp.route('/restaurants')
@login_required
def restaurants_page():
    return restaurants()

@place_bp.route('/offers')
@login_required
def offers_page():
    from app.controllers.place_controller import offers
    return offers()

@place_bp.route('/restaurant/<int:restaurant_id>')
@login_required
def restaurant_detail_page(restaurant_id):
    return restaurant_detail(restaurant_id)

@place_bp.route('/restaurant/<int:restaurant_id>/review', methods=['POST'])
@login_required
def add_review_page(restaurant_id):
    return add_review(restaurant_id)

@place_bp.route('/save', methods=['POST'])
@login_required
def save():
    return save_place()

@place_bp.route('/remove/<int:place_id>')
@login_required
def remove(place_id):
    return remove_saved_place(place_id)

@place_bp.route('/api/restaurants')
@login_required
def api_restaurants():
    from app.controllers.place_controller import api_filter_restaurants
    return api_filter_restaurants()

@place_bp.route('/api/nearby-midpoint')
@login_required
def api_nearby_midpoint_route():
    from app.controllers.place_controller import api_nearby_midpoint
    return api_nearby_midpoint()

@place_bp.route('/offer/<int:offer_id>/save', methods=['POST'])
@login_required
def save_offer_route(offer_id):
    from app.controllers.place_controller import save_restaurant_offer
    return save_restaurant_offer(offer_id)

@place_bp.route('/offer/<int:offer_id>/reminder', methods=['POST'])
@login_required
def toggle_reminder_route(offer_id):
    from app.controllers.place_controller import toggle_offer_reminder
    return toggle_offer_reminder(offer_id)

@place_bp.route('/api/cuisines')
@login_required
def api_cuisines_route():
    return api_cuisines()

@place_bp.route('/api/budget-range')
@login_required
def api_budget_range_route():
    return api_budget_range()

@place_bp.route('/api/ambiences')
@login_required
def api_ambiences_route():
    return api_ambiences()

@place_bp.route('/api/offers')
@login_required
def api_offers_route():
    return api_offers()

@place_bp.route('/api/nearby')
@login_required
def api_nearby_route():
    return api_nearby_restaurants()