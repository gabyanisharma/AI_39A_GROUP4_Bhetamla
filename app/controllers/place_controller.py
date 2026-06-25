from flask import (render_template, request, redirect,
                   url_for, flash, jsonify, session, Response)
import datetime as _dt
from app.models.meetup import Meetup, MeetupMember, PlaceSuggestion
from app.models.meetup_preference import MeetupPlanPreference
from app.models.base_model import Friend
from app.models.user import User
from app.auth import get_current_user_id, is_logged_in
from app.controllers.notification_controller import send_notification
from app.models.place import Restaurant, RestaurantReview
from app.models.meetup_route import MeetupRoute
from app.database import execute_query
import math
from datetime import datetime

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
                        'user_id': member.get('user_id'),
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
            return redirect(url_for('meetup.plan'))
        
        if not user_lat or not user_lng:
            flash('Please detect your location before creating a meetup.', 'error')
            return redirect(url_for('meetup.plan'))

        if not meetup_date or not meetup_time:
            flash('Date and time are required.', 'error')
            return redirect(url_for('meetup.plan'))
        
        try:
            meetup_datetime = datetime.strptime(
                f"{meetup_date} {meetup_time}", "%Y-%m-%d %H:%M"
            )
        except ValueError:
            flash('Invalid date or time format.', 'error')
            return redirect(url_for('meetup.plan'))

        if meetup_datetime < datetime.now():
            flash('Meetup date and time cannot be in the past.', 'error')
            return redirect(url_for('meetup.plan'))

        if not invite_ids:
            flash('Please invite at least one friend.', 'error')
            return redirect(url_for('meetup.plan'))

        user_id    = get_current_user_id()
        meetup_id  = Meetup.create(title, description, user_id,
                                   meetup_date, meetup_time)

        # Add creator as member with their location — creator is auto-accepted
        MeetupMember.add(meetup_id, user_id,
                         user_lat, user_lng, user_address, status='accepted')

        # Invite friends — send a rich notification with meetup details
        current_user = User.get_by_id(user_id)
        venue_hint = ''
        if meetup_date:
            from datetime import datetime as _dt
            try:
                d = _dt.strptime(meetup_date, '%Y-%m-%d')
                venue_hint = f' on {d.strftime("%a, %b %d")}'
                if meetup_time:
                    t = _dt.strptime(meetup_time, '%H:%M')
                    venue_hint += f' at {t.strftime("%I:%M %p").lstrip("0")}'
            except ValueError:
                pass

        for friend_id in invite_ids:
            MeetupMember.add(meetup_id, int(friend_id))
            friend = User.get_by_id(friend_id)
            send_notification(
                int(friend_id),
                f'📅 Meetup Invitation: {title}',
                (
                    f'{current_user["full_name"]} invited you to '
                    f'"{title}"{venue_hint}. '
                    f'Tap to view details, accept or decline.'
                ),
                type='meetup',
                link=f'/meetup/view/{meetup_id}'
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
    for loc in locations:
        if loc.get('latitude') is not None:
            loc['latitude'] = float(loc['latitude'])
        if loc.get('longitude') is not None:
            loc['longitude'] = float(loc['longitude'])

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

    # Fetch planning preferences (for the meeting summary sidebar)
    from app.models.meetup_preference import MeetupPlanPreference
    plan_prefs = MeetupPlanPreference.get(meetup_id, user_id) or {}
    # Also try creator's preferences as fallback for venue/budget
    if not plan_prefs and not is_creator:
        plan_prefs = MeetupPlanPreference.get(meetup_id, meetup['created_by']) or {}

    return render_template('meetup/view.html',
                           meetup=meetup,
                           members=members,
                           suggestions=suggestions,
                           locations=locations,
                           map_points=[{
                               'full_name': loc.get('full_name'),
                               'latitude': loc.get('latitude'),
                               'longitude': loc.get('longitude'),
                               'distance_to_mid': loc.get('distance_to_mid'),
                           } for loc in locations],
                           midpoint_lat=midpoint_lat,
                           midpoint_lng=midpoint_lng,
                           route_waypoints=saved_route['waypoints'] if saved_route else [],
                           is_member=is_member,
                           is_creator=is_creator,
                           can_edit_route=can_edit_route,
                           user_id=user_id,
                           plan_prefs=plan_prefs)


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
        return redirect(url_for('user.dashboard'))

    return redirect(url_for('meetup.view_meetup',
                            meetup_id=meetup_id))


# ── Saved places page ──────────────────────────────────────────────
def saved_places():
    if not is_logged_in():
        return redirect(url_for('auth.login'))

    from app.database import execute_query
    from app.models.place import RestaurantOffer
    from app.models.trending_spot import SpotInteraction
    user_id = get_current_user_id()
    places  = execute_query(
        "SELECT * FROM saved_places WHERE user_id=%s ORDER BY created_at DESC",
        (user_id,), fetch=True
    )
    offers = RestaurantOffer.get_saved_by_user(user_id)
    # Also fetch trending spots the user has saved via the Explore page
    saved_spots = SpotInteraction.get_user_interactions(user_id, 'save') or []
    return render_template('place/saved.html', places=places, offers=offers,
                           saved_spots=saved_spots)


def _build_filters(args):
    """Helper to build filter dictionary from request args."""
    filters = {}
    cuisines = args.getlist('cuisine') or args.getlist('cuisine[]')
    if args.get('cuisine') and not cuisines:
        cuisines = [args.get('cuisine')]
    if cuisines:
        filters['cuisine'] = [c for c in cuisines if c]
    if args.get('price_range'): filters['price_range'] = args.get('price_range')
    ambiences = args.getlist('ambience') or args.getlist('ambience[]')
    if args.get('ambience') and not ambiences:
        ambiences = [args.get('ambience')]
    if ambiences:
        filters['ambience'] = [a for a in ambiences if a]
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
            radius = float(request.args.get('radius', 100.0))
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

# ── Offers page ───────────────────────────────────────────────────
def offers():
    if not is_logged_in():
        return redirect(url_for('auth.login'))

    from app.database import execute_query
    search_q = (request.args.get('q') or '').strip()
    cuisine_filter = (request.args.get('cuisine') or '').strip()

    base_query = """
        SELECT o.*, r.name as restaurant_name, r.cuisine, r.rating,
               r.avg_cost_per_person, r.latitude, r.longitude
        FROM restaurant_offers o
        JOIN restaurants r ON o.restaurant_id = r.id
        WHERE o.is_active = TRUE AND o.valid_until >= CURDATE()
    """
    params = []

    if search_q:
        base_query += " AND (o.title LIKE %s OR o.description LIKE %s OR r.name LIKE %s)"
        like = f"%{search_q}%"
        params.extend([like, like, like])

    if cuisine_filter:
        base_query += " AND LOWER(r.cuisine) LIKE %s"
        params.append(f"%{cuisine_filter.lower()}%")

    base_query += " ORDER BY o.discount_percent DESC, o.valid_until ASC"

    offer_rows = execute_query(base_query, tuple(params) if params else None, fetch=True) or []

    # Build unique cuisine list from all active offers for the filter dropdown
    cuisine_rows = execute_query(
        """
        SELECT DISTINCT r.cuisine
        FROM restaurant_offers o
        JOIN restaurants r ON o.restaurant_id = r.id
        WHERE o.is_active = TRUE AND o.valid_until >= CURDATE()
          AND r.cuisine IS NOT NULL
        ORDER BY r.cuisine
        """,
        fetch=True
    ) or []
    cuisines = [row['cuisine'] for row in cuisine_rows if row.get('cuisine')]

    return render_template(
        'place/offers.html',
        offers=offer_rows,
        cuisines=cuisines,
        search_q=search_q,
    )


# ── API for AJAX filtering ─────────────────────────────────────────
def api_filter_restaurants():
    """AJAX endpoint to return JSON list of restaurants."""
    filters = _build_filters(request.args)
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)
    radius = request.args.get('radius', default=100.0, type=float)
    if lat is not None and lng is not None:
        rows = Restaurant.get_nearby(lat, lng, radius, filters)
    else:
        rows = Restaurant.get_all(filters=filters, limit=200)

    def serialize(r):
        return {
            'id': int(r.get('id')),
            'name': r.get('name'),
            'description': r.get('description'),
            'address': r.get('address'),
            'latitude': float(r['latitude']) if r.get('latitude') is not None else None,
            'longitude': float(r['longitude']) if r.get('longitude') is not None else None,
            'category': r.get('category'),
            'cuisine': r.get('cuisine'),
            'price_range': r.get('price_range'),
            'avg_cost_per_person': float(r.get('avg_cost_per_person') or 0),
            'rating': float(r.get('rating') or 0),
            'review_count': int(r.get('review_count') or 0),
            'ambience': r.get('ambience'),
            'distance_km': float(r.get('distance_km') or 0),
            'thumbnail_url': r.get('thumbnail_url')
        }

    return jsonify([serialize(r) for r in (rows or [])])

# ── API: restaurants near a given midpoint (500m default) ──────────
def api_nearby_midpoint():
    """AJAX endpoint: restaurants within a radius (km) of a lat/lng."""
    if not is_logged_in():
        return jsonify({'success': False}), 401

    try:
        lat = float(request.args.get('lat'))
        lng = float(request.args.get('lng'))
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'Missing or invalid lat/lng.'}), 400

    radius_km = float(request.args.get('radius', 100.0))  # default 100km

    rows = Restaurant.get_near_midpoint(lat, lng, radius_km) or []

    def serialize(r):
        return {
            'id': int(r.get('id')),
            'name': r.get('name'),
            'rating': float(r.get('rating') or 0),
            'distance_km': float(r.get('distance_km') or 0),
            'avg_cost_per_person': float(r.get('avg_cost_per_person') or 0),
            'cuisine': r.get('cuisine'),
        }

    return jsonify({
        'success': True,
        'restaurants': [serialize(r) for r in rows]
    })

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
    saved_offers_dict = {o['id']: o for o in RestaurantOffer.get_saved_by_user(user_id)}
    
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


def complete_meetup_plan(meetup_id):
    if not is_logged_in():
        return jsonify({'success': False, 'message': 'Login required.'}), 401

    meetup = Meetup.get_by_id(meetup_id)
    if not meetup:
        return jsonify({'success': False, 'message': 'Meetup not found.'}), 404

    user_id = get_current_user_id()
    if meetup['created_by'] != user_id:
        return jsonify({
            'success': False,
            'message': 'Only the meetup creator can mark this complete.'
        }), 403

    Meetup.update_status(meetup_id, 'completed')

    from app.services import achievement_service
    current_user = User.get_by_id(user_id)
    members = MeetupMember.get_by_meetup(meetup_id)
    completed_user_ids = {user_id}
    completed_user_ids.update(
        member['user_id']
        for member in members
        if member.get('status') == 'accepted'
    )

    # Award achievements + notify every member
    for uid in completed_user_ids:
        achievement_service.on_meetup_completed(uid)
        if uid != user_id:
            send_notification(
                uid,
                f'✅ Meetup Completed: {meetup["title"]}',
                (
                    f'{current_user["full_name"]} marked "{meetup["title"]}" as complete. '
                    f'Check your History & Analytics for a recap!'
                ),
                type='meetup',
                link='/analytics/history'
            )

    return jsonify({
        'success': True,
        'message': 'Meetup marked complete!',
        'analytics_url': url_for('analytics.history')
    })

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


# ── Calendar sync: download a meetup as an .ics file (US29) ─────────
def _ics_escape(text):
    """Escape text per RFC 5545 (commas, semicolons, backslashes, newlines)."""
    return (str(text or '')
            .replace('\\', '\\\\')
            .replace(';', '\\;')
            .replace(',', '\\,')
            .replace('\r\n', '\\n')
            .replace('\n', '\\n'))


def _meetup_event_times(meetup):
    """Return (dtstart_line, dtend_line) for the VEVENT.

    Uses a timed 2-hour event when a meetup_time is set, otherwise an
    all-day event. meetup_time arrives from MySQL as a timedelta.
    """
    day = meetup.get('meetup_date')
    time_val = meetup.get('meetup_time')

    if time_val is None:
        start = day
        end = day + _dt.timedelta(days=1)
        return (
            'DTSTART;VALUE=DATE:' + start.strftime('%Y%m%d'),
            'DTEND;VALUE=DATE:' + end.strftime('%Y%m%d'),
        )

    if isinstance(time_val, _dt.timedelta):
        secs = int(time_val.total_seconds())
        hour, minute = secs // 3600, (secs % 3600) // 60
    else:  # datetime.time
        hour, minute = time_val.hour, time_val.minute

    start_dt = _dt.datetime(day.year, day.month, day.day, hour, minute)
    end_dt = start_dt + _dt.timedelta(hours=2)
    return (
        'DTSTART:' + start_dt.strftime('%Y%m%dT%H%M%S'),
        'DTEND:' + end_dt.strftime('%Y%m%dT%H%M%S'),
    )


def meetup_calendar(meetup_id):
    """Serve a meetup as a downloadable .ics calendar event."""
    if not is_logged_in():
        return redirect(url_for('auth.login'))

    meetup = Meetup.get_by_id(meetup_id)
    if not meetup:
        flash('Meetup not found.', 'error')
        return redirect(url_for('meetup.plan'))

    user_id = get_current_user_id()
    if not _can_access_meetup(meetup, user_id):
        flash('You are not part of this meetup.', 'error')
        return redirect(url_for('meetup.plan'))

    if not meetup.get('meetup_date'):
        flash('Set a meetup date before adding it to your calendar.', 'error')
        return redirect(url_for('meetup.plan', meetup_id=meetup_id))

    dtstart, dtend = _meetup_event_times(meetup)
    location = meetup.get('winning_venue_name') or meetup.get('midpoint_address') or ''
    stamp = _dt.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')

    lines = [
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//Bhetamla//Meetup Planner//EN',
        'CALSCALE:GREGORIAN',
        'METHOD:PUBLISH',
        'BEGIN:VEVENT',
        f'UID:meetup-{meetup_id}@bhetamla',
        f'DTSTAMP:{stamp}',
        dtstart,
        dtend,
        'SUMMARY:' + _ics_escape(meetup.get('title') or 'Bhetamla Meetup'),
        'DESCRIPTION:' + _ics_escape(meetup.get('description') or 'Planned with Bhetamla.'),
        'LOCATION:' + _ics_escape(location),
        'STATUS:CONFIRMED',
        'END:VEVENT',
        'END:VCALENDAR',
    ]
    ics = '\r\n'.join(lines) + '\r\n'

    return Response(
        ics,
        mimetype='text/calendar',
        headers={
            'Content-Disposition': f'attachment; filename="meetup-{meetup_id}.ics"'
        }
    )


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

# ── New API endpoints for dynamic planner modals ─────────────────────

def api_cuisines():
    if not is_logged_in():
        return jsonify({'success': False}), 401
    return jsonify({'success': True, 'cuisines': Restaurant.get_cuisines()})


def api_budget_range():
    if not is_logged_in():
        return jsonify({'success': False}), 401
    min_cost, max_cost = Restaurant.get_budget_range()
    return jsonify({'success': True, 'min': min_cost, 'max': max_cost})


def api_ambiences():
    if not is_logged_in():
        return jsonify({'success': False}), 401
    rows = execute_query(
        "SELECT DISTINCT ambience FROM restaurants WHERE is_active = TRUE AND ambience IS NOT NULL ORDER BY ambience",
        fetch=True
    ) or []
    ambiences = [r['ambience'] for r in rows if r['ambience']]
    return jsonify({'success': True, 'ambiences': ambiences})


def api_offers():
    if not is_logged_in():
        return jsonify({'success': False}), 401
    from app.models.place import RestaurantOffer
    # Get all active offers with restaurant info
    rows = execute_query(
        """
        SELECT o.*, r.name as restaurant_name, r.address as restaurant_address,
               r.latitude, r.longitude, r.cuisine, r.rating, r.avg_cost_per_person
        FROM restaurant_offers o
        JOIN restaurants r ON o.restaurant_id = r.id
        WHERE o.is_active = TRUE AND o.valid_until >= CURDATE()
        ORDER BY o.discount_percent DESC, o.valid_until ASC
        LIMIT 20
        """,
        fetch=True
    ) or []
    offers = []
    for r in rows:
        offers.append({
            'id': r['id'],
            'restaurant_id': r['restaurant_id'],
            'restaurant_name': r['restaurant_name'],
            'title': r['title'],
            'description': r['description'] or '',
            'discount_percent': r['discount_percent'] or 0,
            'valid_until': str(r['valid_until']) if r['valid_until'] else None,
            'cuisine': r['cuisine'] or '',
            'rating': float(r['rating'] or 0),
            'latitude': float(r['latitude']) if r.get('latitude') else None,
            'longitude': float(r['longitude']) if r.get('longitude') else None,
            'avg_cost_per_person': float(r['avg_cost_per_person'] or 0) if r.get('avg_cost_per_person') else 0,
        })
    return jsonify({'success': True, 'offers': offers})


def api_nearby_restaurants():
    if not is_logged_in():
        return jsonify({'success': False}), 401
    lat = request.args.get('lat')
    lng = request.args.get('lng')
    radius = float(request.args.get('radius', 100.0))
    filters = _build_filters(request.args)
    if lat and lng:
        restaurants = Restaurant.get_nearby(float(lat), float(lng), radius, filters)
    else:
        restaurants = Restaurant.get_all(filters, limit=20)
    return jsonify({'success': True, 'restaurants': [{
        'id': r['id'],
        'name': r['name'],
        'address': r.get('address', ''),
        'cuisine': r.get('cuisine', ''),
        'rating': float(r.get('rating') or 0),
        'avg_cost_per_person': float(r.get('avg_cost_per_person') or 0),
        'distance_km': r.get('distance_km'),
        'ambience': r.get('ambience', ''),
    } for r in (restaurants or [])]})