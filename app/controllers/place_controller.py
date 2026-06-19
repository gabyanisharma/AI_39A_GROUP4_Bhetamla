from flask import (render_template, request, redirect,
                   url_for, flash, jsonify, session)
from app.models.meetup import Meetup, MeetupMember, PlaceSuggestion
from app.models.meetup_preference import MeetupPlanPreference
from app.models.base_model import Friend
from app.models.user import User
from app.auth import get_current_user_id, is_logged_in
from app.controllers.notification_controller import send_notification
from app.models.place import Restaurant, RestaurantReview
from app.models.meetup_route import MeetupRoute
import math
from flask import render_template, request, redirect, url_for, flash, jsonify

# ── Midpoint calculation ───────────────────────────────────────────
def calculate_midpoint(locations):
    """
    Calculate geographic midpoint from a list of
    (latitude, longitude) pairs.
    """
    if not locations:
        return None, None

    x = y = z = 0.0

    for loc in locations:
        lat = math.radians(float(loc['latitude']))
        lng = math.radians(float(loc['longitude']))

        x += math.cos(lat) * math.cos(lng)
        y += math.cos(lat) * math.sin(lng)
        z += math.sin(lat)

    total = len(locations)
    x /= total
    y /= total
    z /= total

    lng = math.atan2(y, x)
    hyp = math.sqrt(x * x + y * y)
    lat = math.atan2(z, hyp)

    return math.degrees(lat), math.degrees(lng)


def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance in km between two coordinates."""
    R = 6371
    lat1, lon1, lat2, lon2 = map(math.radians,
                                  [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = (math.sin(dlat/2)**2 +
         math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2)
    c = 2 * math.asin(math.sqrt(a))
    return R * c


# ── Plan Meetup page ───────────────────────────────────────────────
def plan_meetup(created_meetup_id=None):
    if not is_logged_in():
        return redirect(url_for('auth.login'))

    user_id  = get_current_user_id()
    friends  = Friend.get_friends(user_id)
    meetups  = Meetup.get_by_user(user_id)

    created_meetup = None
    created_members = []
    created_map_points = []
    created_midpoint = None

    if created_meetup_id:
        try:
            created_meetup_id = int(created_meetup_id)
        except (TypeError, ValueError):
            created_meetup_id = None

    if created_meetup_id:
        candidate = Meetup.get_by_id(created_meetup_id)
        if candidate:
            members = MeetupMember.get_by_meetup(created_meetup_id)
            is_member = any(m['user_id'] == user_id for m in members)
            if candidate['created_by'] == user_id or is_member:
                created_meetup = candidate
                created_members = members
                for member in members:
                    if member.get('latitude') is None or member.get('longitude') is None:
                        continue
                    created_map_points.append({
                        'name': member.get('full_name') or 'Member',
                        'lat': float(member['latitude']),
                        'lng': float(member['longitude']),
                        'address': member.get('address') or '',
                    })
                if candidate.get('midpoint_lat') and candidate.get('midpoint_lng'):
                    created_midpoint = {
                        'lat': float(candidate['midpoint_lat']),
                        'lng': float(candidate['midpoint_lng']),
                        'address': candidate.get('midpoint_address') or 'Smart midpoint',
                    }
                elif len(created_map_points) >= 2:
                    midpoint_lat, midpoint_lng = calculate_midpoint([
                        {'latitude': point['lat'], 'longitude': point['lng']}
                        for point in created_map_points
                    ])
                    if midpoint_lat is not None and midpoint_lng is not None:
                        created_midpoint = {
                            'lat': midpoint_lat,
                            'lng': midpoint_lng,
                            'address': 'Calculated geographic midpoint',
                        }

    return render_template('meetup/plan.html',
                           friends=friends,
                           meetups=meetups,
                           created_meetup_id=created_meetup_id,
                           created_meetup=created_meetup,
                           created_members=created_members,
                           created_map_points=created_map_points,
                           created_midpoint=created_midpoint,
                           current_user_id=user_id)


# ── Create new meetup ──────────────────────────────────────────────
def create_meetup():
    if not is_logged_in():
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        title        = request.form.get('title', '').strip()
        description  = request.form.get('description', '').strip()
        meetup_date  = request.form.get('meetup_date')
        meetup_time  = request.form.get('meetup_time')
        invite_ids   = request.form.getlist('invite_friends')
        user_lat     = request.form.get('user_lat')
        user_lng     = request.form.get('user_lng')
        user_address = request.form.get('user_address', '')

        if not title:
            flash('Meetup title is required.', 'error')
            return redirect(url_for('meetup.plan', meetup_id=meetup_id))

        user_id    = get_current_user_id()
        meetup_id  = Meetup.create(title, description, user_id,
                                   meetup_date, meetup_time)

        # Add creator as member with their location
        MeetupMember.add(meetup_id, user_id,
                         user_lat, user_lng, user_address)

        # Invite friends
        for friend_id in invite_ids:
            MeetupMember.add(meetup_id, int(friend_id))
            friend = User.get_by_id(friend_id)
            current_user = User.get_by_id(user_id)
            send_notification(
                int(friend_id),
                'Meetup Invitation',
                f'{current_user["full_name"]} invited you to "{title}"!',
                type='meetup',
                link=f'/meetup/plan?meetup_id={meetup_id}'
            )

        flash('Meetup created successfully!', 'success')
        from app.services import achievement_service
        achievement_service.on_meetup_created(user_id)
        return redirect(url_for('meetup.plan',
                                meetup_id=meetup_id))

    return redirect(url_for('meetup.plan'))


# ── View meetup ────────────────────────────────────────────────────
def view_meetup(meetup_id):
    if not is_logged_in():
        return redirect(url_for('auth.login'))

    meetup      = Meetup.get_by_id(meetup_id)
    if not meetup:
        flash('Meetup not found.', 'error')
        return redirect(url_for('meetup.plan'))

    members     = MeetupMember.get_by_meetup(meetup_id)
    suggestions = PlaceSuggestion.get_by_meetup(meetup_id)
    saved_route = MeetupRoute.get_by_meetup(meetup_id)
    user_id     = get_current_user_id()

    # Check if current user is a member
    is_member = any(m['user_id'] == user_id for m in members)
    is_creator = meetup['created_by'] == user_id
    can_edit_route = is_creator or any(
        m['user_id'] == user_id and m['status'] == 'accepted'
        for m in members
    )

    # Get member locations for midpoint display
    locations = MeetupMember.get_locations(meetup_id)

    # Recalculate midpoint if locations available
    midpoint_lat = midpoint_lng = None
    if len(locations) >= 2:
        midpoint_lat, midpoint_lng = calculate_midpoint(locations)

        # Calculate distance from midpoint for each member
        for loc in locations:
            if loc['latitude'] and loc['longitude']:
                loc['distance_to_mid'] = round(
                    calculate_distance(
                        float(loc['latitude']),
                        float(loc['longitude']),
                        midpoint_lat, midpoint_lng
                    ), 2
                )

    return render_template('meetup/view.html',
                           meetup=meetup,
                           members=members,
                           suggestions=suggestions,
                           locations=locations,
                           midpoint_lat=midpoint_lat,
                           midpoint_lng=midpoint_lng,
                           route_waypoints=saved_route['waypoints'] if saved_route else [],
                           is_member=is_member,
                           is_creator=is_creator,
                           can_edit_route=can_edit_route,
                           user_id=user_id)


# ── Update member location ─────────────────────────────────────────
def update_location(meetup_id):
    if not is_logged_in():
        return jsonify({'success': False}), 401

    data    = request.get_json()
    lat     = data.get('latitude')
    lng     = data.get('longitude')
    address = data.get('address', '')

    MeetupMember.update_location(
        meetup_id, get_current_user_id(),
        lat, lng, address
    )

    # Recalculate midpoint
    locations = MeetupMember.get_locations(meetup_id)
    midpoint_lat = midpoint_lng = None

    if len(locations) >= 2:
        midpoint_lat, midpoint_lng = calculate_midpoint(locations)
        Meetup.update_midpoint(
            meetup_id, midpoint_lat, midpoint_lng, ''
        )

    return jsonify({
        'success':      True,
        'midpoint_lat': midpoint_lat,
        'midpoint_lng': midpoint_lng,
        'member_count': len(locations)
    })


# ── Get midpoint API ───────────────────────────────────────────────
def get_midpoint(meetup_id):
    if not is_logged_in():
        return jsonify({'success': False}), 401

    locations = MeetupMember.get_locations(meetup_id)

    if len(locations) < 2:
        return jsonify({
            'success': False,
            'message': 'Need at least 2 member locations.'
        })

    midpoint_lat, midpoint_lng = calculate_midpoint(locations)

    members_data = []
    for loc in locations:
        dist = calculate_distance(
            float(loc['latitude']), float(loc['longitude']),
            midpoint_lat, midpoint_lng
        )
        members_data.append({
            'name':     loc['full_name'],
            'lat':      float(loc['latitude']),
            'lng':      float(loc['longitude']),
            'distance': round(dist, 2)
        })

    return jsonify({
        'success':      True,
        'midpoint_lat': midpoint_lat,
        'midpoint_lng': midpoint_lng,
        'members':      members_data
    })


# ── Add place suggestion ───────────────────────────────────────────
def add_suggestion(meetup_id):
    if not is_logged_in():
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        place_name = request.form.get('place_name', '').strip()
        address    = request.form.get('address', '').strip()
        lat        = request.form.get('latitude')
        lng        = request.form.get('longitude')
        rating     = request.form.get('rating', 0)

        if not place_name:
            flash('Place name is required.', 'error')
            return redirect(url_for('meetup.view_meetup',
                                    meetup_id=meetup_id))

        PlaceSuggestion.add(
            meetup_id, place_name, address,
            lat, lng, rating, get_current_user_id()
        )
        flash('Place suggestion added!', 'success')

    return redirect(url_for('meetup.view_meetup',
                            meetup_id=meetup_id))


# ── Accept/Decline meetup invite ───────────────────────────────────
def respond_meetup(meetup_id):
    if not is_logged_in():
        return redirect(url_for('auth.login'))

    action  = request.form.get('action')
    user_id = get_current_user_id()

    if action == 'accept':
        MeetupMember.accept(meetup_id, user_id)
        from app.services import achievement_service
        achievement_service.on_meetup_joined(user_id)
        flash('You joined the meetup!', 'success')
    elif action == 'decline':
        MeetupMember.decline(meetup_id, user_id)
        flash('Meetup declined.', 'info')

    return redirect(url_for('meetup.view_meetup',
                            meetup_id=meetup_id))


# ── Saved places page ──────────────────────────────────────────────
def saved_places():
    if not is_logged_in():
        return redirect(url_for('auth.login'))

    from app.database import execute_query
    from app.models.place import RestaurantOffer
    user_id = get_current_user_id()
    places  = execute_query(
        "SELECT * FROM saved_places WHERE user_id=%s ORDER BY created_at DESC",
        (user_id,), fetch=True
    )
    offers = RestaurantOffer.get_saved_by_user(user_id)
    return render_template('place/saved.html', places=places, offers=offers)


def _build_filters(args):
    """Helper to build filter dictionary from request args."""
    filters = {}
    if args.get('cuisine'): filters['cuisine'] = args.get('cuisine')
    if args.get('price_range'): filters['price_range'] = args.get('price_range')
    if args.get('ambience'): filters['ambience'] = args.get('ambience')
    if args.get('min_rating'): filters['min_rating'] = float(args.get('min_rating'))
    if args.get('max_budget'):
        try:
            filters['max_budget'] = float(args.get('max_budget'))
        except (ValueError, TypeError):
            pass
    return filters

# ── Restaurant list page ───────────────────────────────────────────
def restaurants():
    if not is_logged_in():
        return redirect(url_for('auth.login'))

    filters = _build_filters(request.args)
    meetup_id = request.args.get('meetup_id')
    search_q = request.args.get('q')

    # Get budget info for UI
    budget_min, budget_max = Restaurant.get_budget_range()
    group_budget = None
    
    midpoint_lat = midpoint_lng = None
    restaurant_list = []

    # Handle Meetup context
    if meetup_id:
        meetup = Meetup.get_by_id(meetup_id)
        group_budget = meetup.get('group_budget') if meetup else None
        if meetup and meetup.get('midpoint_lat'):
            midpoint_lat = float(meetup['midpoint_lat'])
            midpoint_lng = float(meetup['midpoint_lng'])
            radius = float(request.args.get('radius', 3.0))
            restaurant_list = Restaurant.get_near_midpoint(
                midpoint_lat, midpoint_lng, radius, filters
            )
        else:
            restaurant_list = Restaurant.get_all(filters)
    elif search_q:
        restaurant_list = Restaurant.search(search_q)
    else:
        restaurant_list = Restaurant.get_all(filters)

    return render_template('place/restaurants.html',
                           restaurants=restaurant_list,
                           cuisines=Restaurant.get_cuisines(),
                           filters=filters,
                           midpoint_lat=midpoint_lat,
                           midpoint_lng=midpoint_lng,
                           meetup_id=meetup_id,
                           search_q=search_q or '',
                           budget_min=budget_min,
                           budget_max=budget_max,
                           group_budget=group_budget)

# ── API for AJAX filtering ─────────────────────────────────────────
def api_filter_restaurants():
    """AJAX endpoint to return JSON list of restaurants."""
    filters = _build_filters(request.args)
    rows = Restaurant.get_all(filters=filters, limit=200)

    def serialize(r):
        return {
            'id': int(r.get('id')),
            'name': r.get('name'),
            'description': r.get('description'),
            'avg_cost_per_person': float(r.get('avg_cost_per_person') or 0),
            'rating': float(r.get('rating') or 0),
            'thumbnail_url': r.get('thumbnail_url')
        }

    return jsonify([serialize(r) for r in (rows or [])])

# ── Restaurant detail page ─────────────────────────────────────────
def restaurant_detail(restaurant_id):
    if not is_logged_in():
        return redirect(url_for('auth.login'))

    restaurant = Restaurant.get_by_id(restaurant_id)
    if not restaurant:
        flash('Restaurant not found.', 'error')
        return redirect(url_for('place.saved'))

    reviews      = RestaurantReview.get_by_restaurant(restaurant_id)
    user_id      = get_current_user_id()
    user_review  = RestaurantReview.get_by_user(
        user_id, restaurant_id
    )

    from app.models.place import RestaurantOffer
    active_offers = RestaurantOffer.get_active_by_restaurant(restaurant_id)
    saved_offers_dict = {o['offer_id']: o for o in RestaurantOffer.get_saved_by_user(user_id)}
    
    for offer in active_offers:
        if offer['id'] in saved_offers_dict:
            offer['is_saved'] = True
            offer['remind_me'] = saved_offers_dict[offer['id']]['remind_me']
        else:
            offer['is_saved'] = False
            offer['remind_me'] = False

    return render_template('place/restaurant_detail.html',
                           restaurant=restaurant,
                           reviews=reviews,
                           user_review=user_review,
                           offers=active_offers)


# ── Add review ─────────────────────────────────────────────────────
def add_review(restaurant_id):
    if not is_logged_in():
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        rating = request.form.get('rating')
        review = request.form.get('review', '').strip()

        if not rating:
            flash('Rating is required.', 'error')
            return redirect(url_for('place.restaurant_detail_page',
                                    restaurant_id=restaurant_id))

        RestaurantReview.add(
            restaurant_id, get_current_user_id(),
            float(rating), review
        )
        flash('Review submitted!', 'success')

    return redirect(url_for('place.restaurant_detail_page',
                            restaurant_id=restaurant_id))


# ── Save place ─────────────────────────────────────────────────────
def save_place():
    if not is_logged_in():
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        place_name = request.form.get('place_name', '').strip()
        address    = request.form.get('address', '').strip()
        lat        = request.form.get('latitude')
        lng        = request.form.get('longitude')

        if not place_name:
            flash('Place name is required.', 'error')
            return redirect(url_for('place.saved'))

        from app.database import execute_query
        execute_query(
            """INSERT INTO saved_places
               (user_id, place_name, address, latitude, longitude)
               VALUES (%s, %s, %s, %s, %s)""",
            (get_current_user_id(), place_name, address, lat, lng)
        )
        flash('Place saved!', 'success')

    return redirect(url_for('place.saved'))


# ── Remove saved place ─────────────────────────────────────────────
def remove_saved_place(place_id):
    if not is_logged_in():
        return redirect(url_for('auth.login'))

    from app.database import execute_query
    execute_query(
        "DELETE FROM saved_places WHERE id=%s AND user_id=%s",
        (place_id, get_current_user_id())
    )
    flash('Place removed.', 'info')
    return redirect(url_for('place.saved'))

# ── Offers ─────────────────────────────────────────────────────────
def save_restaurant_offer(offer_id):
    if not is_logged_in():
        return redirect(url_for('auth.login'))
    from app.models.place import RestaurantOffer
    RestaurantOffer.save_offer(get_current_user_id(), offer_id)
    flash('Offer saved!', 'success')
    return redirect(request.referrer or url_for('place.restaurants_page'))

def toggle_offer_reminder(offer_id):
    if not is_logged_in():
        return redirect(url_for('auth.login'))
    from app.models.place import RestaurantOffer
    remind_me = request.form.get('remind_me') == '1'
    RestaurantOffer.toggle_reminder(get_current_user_id(), offer_id, remind_me)
    flash('Reminder preferences updated.', 'success')
    return redirect(request.referrer or url_for('place.restaurants_page'))

def confirm_meetup_plan(meetup_id):
    if not is_logged_in():
        return jsonify({'success': False, 'message': 'Login required.'}), 401

    meetup = Meetup.get_by_id(meetup_id)
    if not meetup:
        return jsonify({'success': False, 'message': 'Meetup not found.'}), 404

    user_id = get_current_user_id()
    if meetup['created_by'] != user_id:
        return jsonify({
            'success': False,
            'message': 'Only the meetup creator can confirm this plan.'
        }), 403

    current_user = User.get_by_id(user_id)
    members = MeetupMember.get_by_meetup(meetup_id)
    notified = 0
    payload = request.get_json(silent=True) or {}
    midpoint = payload.get('midpoint') or {}

    try:
        midpoint_lat = float(midpoint.get('lat'))
        midpoint_lng = float(midpoint.get('lng'))
        midpoint_address = (midpoint.get('address') or '').strip()
    except (TypeError, ValueError):
        midpoint_lat = midpoint_lng = None
        midpoint_address = ''

    if midpoint_lat is not None and midpoint_lng is not None:
        Meetup.update_midpoint(
            meetup_id,
            midpoint_lat,
            midpoint_lng,
            midpoint_address
        )

    for member in members:
        if member['user_id'] == user_id:
            continue
        send_notification(
            member['user_id'],
            'Meetup Plan Confirmed',
            f'{current_user["full_name"]} confirmed the plan for "{meetup["title"]}".',
            type='meetup',
            link=f'/meetup/plan?meetup_id={meetup_id}'
        )
        notified += 1

    return jsonify({
        'success': True,
        'message': 'Meetup plan confirmed.',
        'notified': notified
    })


def delete_meetup_plan(meetup_id):
    if not is_logged_in():
        return redirect(url_for('auth.login'))

    meetup = Meetup.get_by_id(meetup_id)
    if not meetup:
        flash('Meetup plan not found.', 'error')
        return redirect(url_for('meetup.plan'))

    user_id = get_current_user_id()
    if meetup['created_by'] != user_id:
        flash('Only the meetup creator can delete this plan.', 'error')
        return redirect(url_for('meetup.plan', meetup_id=meetup_id))

    Meetup.delete_by_creator(meetup_id, user_id)
    flash('Meetup plan deleted.', 'success')
    return redirect(url_for('meetup.plan'))


# ── Plan popup preferences (cuisine, budget, ambience, venue, ride) ──
def _can_access_meetup(meetup, user_id):
    """A meetup creator or any of its members may save planning choices."""
    if meetup['created_by'] == user_id:
        return True
    members = MeetupMember.get_by_meetup(meetup['id'])
    return any(m['user_id'] == user_id for m in members)


def _pref_to_int(value):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _pref_to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def save_plan_preferences(meetup_id):
    """Persist the choices made in the serial Plan Meetup popups.

    Accepts a JSON body with any subset of the planner fields so each
    popup can save its own slice as the user advances through the flow.
    """
    if not is_logged_in():
        return jsonify({'success': False, 'message': 'Login required.'}), 401

    meetup = Meetup.get_by_id(meetup_id)
    if not meetup:
        return jsonify({'success': False, 'message': 'Meetup not found.'}), 404

    user_id = get_current_user_id()
    if not _can_access_meetup(meetup, user_id):
        return jsonify({
            'success': False,
            'message': 'You are not part of this meetup.'
        }), 403

    payload = request.get_json(silent=True) or {}

    fields = {}
    if 'cuisine' in payload:
        fields['cuisine'] = (str(payload.get('cuisine') or '').strip())[:100]
    if 'ambience' in payload:
        fields['ambience'] = (str(payload.get('ambience') or '').strip())[:100]
    if 'ride_option' in payload:
        fields['ride_option'] = (str(payload.get('ride_option') or '').strip())[:100]
    if 'notes' in payload:
        fields['notes'] = str(payload.get('notes') or '').strip()
    if 'selected_venue' in payload:
        fields['selected_venue'] = (str(payload.get('selected_venue') or '').strip())[:255]
    if 'budget_min' in payload:
        fields['budget_min'] = _pref_to_int(payload.get('budget_min'))
    if 'budget_max' in payload:
        fields['budget_max'] = _pref_to_int(payload.get('budget_max'))
    if 'selected_venue_lat' in payload:
        fields['selected_venue_lat'] = _pref_to_float(payload.get('selected_venue_lat'))
    if 'selected_venue_lng' in payload:
        fields['selected_venue_lng'] = _pref_to_float(payload.get('selected_venue_lng'))

    # Drop keys that failed validation so we never write garbage.
    fields = {k: v for k, v in fields.items() if v is not None and v != ''}

    if not fields:
        return jsonify({
            'success': False,
            'message': 'No valid preferences supplied.'
        }), 400

    MeetupPlanPreference.upsert(meetup_id, user_id, fields)

    return jsonify({
        'success': True,
        'message': 'Preferences saved.',
        'saved': list(fields.keys())
    })


def get_plan_preferences(meetup_id):
    """Return the caller's saved planning choices for a meetup."""
    if not is_logged_in():
        return jsonify({'success': False, 'message': 'Login required.'}), 401

    meetup = Meetup.get_by_id(meetup_id)
    if not meetup:
        return jsonify({'success': False, 'message': 'Meetup not found.'}), 404

    user_id = get_current_user_id()
    if not _can_access_meetup(meetup, user_id):
        return jsonify({'success': False, 'message': 'You are not part of this meetup.'}), 403

    prefs = MeetupPlanPreference.get(meetup_id, user_id) or {}
    return jsonify({'success': True, 'preferences': prefs})


def confirm_meetup_plan(meetup_id):
    if not is_logged_in():
        return jsonify({'success': False, 'message': 'Login required.'}), 401

    meetup = Meetup.get_by_id(meetup_id)
    if not meetup:
        return jsonify({'success': False, 'message': 'Meetup not found.'}), 404

    user_id = get_current_user_id()
    if meetup['created_by'] != user_id:
        return jsonify({
            'success': False,
            'message': 'Only the meetup creator can confirm this plan.'
        }), 403

    current_user = User.get_by_id(user_id)
    members = MeetupMember.get_by_meetup(meetup_id)
    notified = 0
    payload = request.get_json(silent=True) or {}
    midpoint = payload.get('midpoint') or {}

    try:
        midpoint_lat = float(midpoint.get('lat'))
        midpoint_lng = float(midpoint.get('lng'))
        midpoint_address = (midpoint.get('address') or '').strip()
    except (TypeError, ValueError):
        midpoint_lat = midpoint_lng = None
        midpoint_address = ''

    if midpoint_lat is not None and midpoint_lng is not None:
        Meetup.update_midpoint(
            meetup_id,
            midpoint_lat,
            midpoint_lng,
            midpoint_address
        )

    for member in members:
        if member['user_id'] == user_id:
            continue
        send_notification(
            member['user_id'],
            'Meetup Plan Confirmed',
            f'{current_user["full_name"]} confirmed the plan for "{meetup["title"]}".',
            type='meetup',
            link=f'/meetup/plan?meetup_id={meetup_id}'
        )
        notified += 1

    return jsonify({
        'success': True,
        'message': 'Meetup plan confirmed.',
        'notified': notified
    })


def delete_meetup_plan(meetup_id):
    if not is_logged_in():
        return redirect(url_for('auth.login'))

    meetup = Meetup.get_by_id(meetup_id)
    if not meetup:
        flash('Meetup plan not found.', 'error')
        return redirect(url_for('meetup.plan'))

    user_id = get_current_user_id()
    if meetup['created_by'] != user_id:
        flash('Only the meetup creator can delete this plan.', 'error')
        return redirect(url_for('meetup.plan', meetup_id=meetup_id))

    Meetup.delete_by_creator(meetup_id, user_id)
    flash('Meetup plan deleted.', 'success')
    return redirect(url_for('meetup.plan'))