from flask import Blueprint
from app.routes.user_routes import login_required
from app.controllers.place_controller import (
    saved_places, restaurants, restaurant_detail,
    add_review, save_place, remove_saved_place
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

