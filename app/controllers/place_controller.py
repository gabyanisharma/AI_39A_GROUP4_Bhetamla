from flask import (render_template, request, redirect,
                   url_for, flash, jsonify, session)
from app.models.meetup import Meetup, MeetupMember, PlaceSuggestion
from app.models.base_model import Friend
from app.models.user import User
from app.auth import get_current_user_id, is_logged_in
from app.controllers.notification_controller import send_notification
from app.models.place import Restaurant, RestaurantReview
import math


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
def plan_meetup():
    if not is_logged_in():
        return redirect(url_for('auth.login'))

    user_id  = get_current_user_id()
    friends  = Friend.get_friends(user_id)
    meetups  = Meetup.get_by_user(user_id)

    return render_template('meetup/plan.html',
                           friends=friends,
                           meetups=meetups)


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

        user_id    = get_current_user_id()
        meetup_id  = Meetup.create(title, description, user_id,
                                   meetup_date, meetup_time)

        # Add creator as member with their location
        MeetupMember.add(meetup_id, user_id,
                         user_lat, user_lng, user_address,
                         status='accepted')

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
                link=f'/meetup/view/{meetup_id}'
            )

        flash('Meetup created successfully!', 'success')
        return redirect(url_for('meetup.view_meetup_route',
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
    user_id     = get_current_user_id()

    # Check if current user is a member
    is_member = any(m['user_id'] == user_id for m in members)
    is_creator = meetup['created_by'] == user_id

    # Get member locations for midpoint display
    locations = MeetupMember.get_locations(meetup_id)

    # Recalculate midpoint if locations available
    midpoint_lat = midpoint_lng = None
    if len(locations) >= 2:
        midpoint_lat, midpoint_lng = calculate_midpoint(locations)
        Meetup.update_midpoint(meetup_id, midpoint_lat, midpoint_lng, '')

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
                           is_member=is_member,
                           is_creator=is_creator,
                           user_id=user_id)


# ── Update member location ─────────────────────────────────────────
def update_location(meetup_id):
    if not is_logged_in():
        return jsonify({'success': False}), 401

    data    = request.get_json(silent=True) or {}
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
            return redirect(url_for('meetup.view_meetup_route',
                                    meetup_id=meetup_id))

        PlaceSuggestion.add(
            meetup_id, place_name, address,
            lat, lng, rating, get_current_user_id()
        )
        flash('Place suggestion added!', 'success')

    return redirect(url_for('meetup.view_meetup_route',
                            meetup_id=meetup_id))


# ── Accept/Decline meetup invite ───────────────────────────────────
def respond_meetup(meetup_id):
    if not is_logged_in():
        return redirect(url_for('auth.login'))

    action  = request.form.get('action')
    user_id = get_current_user_id()

    if action == 'accept':
        MeetupMember.accept(meetup_id, user_id)
        flash('You joined the meetup!', 'success')
    elif action == 'decline':
        MeetupMember.decline(meetup_id, user_id)
        flash('Meetup declined.', 'info')

    return redirect(url_for('meetup.view_meetup_route',
                            meetup_id=meetup_id))


# ── Saved places page ──────────────────────────────────────────────
def saved_places():
    if not is_logged_in():
        return redirect(url_for('auth.login'))

    from app.database import execute_query
    user_id = get_current_user_id()
    places  = execute_query(
        "SELECT * FROM saved_places WHERE user_id=%s ORDER BY created_at DESC",
        (user_id,), fetch=True
    )
    return render_template('place/saved.html', places=places)


# ── Restaurant list page ───────────────────────────────────────────
def restaurants():
    if not is_logged_in():
        return redirect(url_for('auth.login'))

    # Get filters from query string
    filters = {}
    cuisine     = request.args.get('cuisine')
    price_range = request.args.get('price_range')
    ambience    = request.args.get('ambience')
    min_rating  = request.args.get('min_rating')
    meetup_id   = request.args.get('meetup_id')
    search_q    = request.args.get('q')

    if cuisine:     filters['cuisine']     = cuisine
    if price_range: filters['price_range'] = price_range
    if ambience:    filters['ambience']    = ambience
    if min_rating:  filters['min_rating']  = float(min_rating)

    # If meetup_id provided, get restaurants near midpoint
    midpoint_lat = midpoint_lng = None
    restaurant_list = []

    if meetup_id:
        meetup = Meetup.get_by_id(meetup_id)
        if meetup and meetup['midpoint_lat']:
            midpoint_lat = float(meetup['midpoint_lat'])
            midpoint_lng = float(meetup['midpoint_lng'])
            radius       = float(request.args.get('radius', 3.0))
            restaurant_list = Restaurant.get_near_midpoint(
                midpoint_lat, midpoint_lng, radius, filters
            )
        elif request.args.get('midpoint_lat') and request.args.get('midpoint_lng'):
            midpoint_lat = float(request.args.get('midpoint_lat'))
            midpoint_lng = float(request.args.get('midpoint_lng'))
            radius       = float(request.args.get('radius', 3.0))
            restaurant_list = Restaurant.get_near_midpoint(
                midpoint_lat, midpoint_lng, radius, filters
            )
    elif search_q:
        restaurant_list = Restaurant.search(search_q)
    else:
        restaurant_list = Restaurant.get_all(filters)

    cuisines = Restaurant.get_cuisines()

    return render_template('place/restaurants.html',
                           restaurants=restaurant_list,
                           cuisines=cuisines,
                           filters=filters,
                           midpoint_lat=midpoint_lat,
                           midpoint_lng=midpoint_lng,
                           meetup_id=meetup_id,
                           search_q=search_q or '')


# ── Restaurant detail page ─────────────────────────────────────────
def restaurant_detail(restaurant_id):
    if not is_logged_in():
        return redirect(url_for('auth.login'))

    restaurant = Restaurant.get_by_id(restaurant_id)
    if not restaurant:
        flash('Restaurant not found.', 'error')
        return redirect(url_for('place.saved'))

    reviews      = RestaurantReview.get_by_restaurant(restaurant_id)
    user_review  = RestaurantReview.get_by_user(
        get_current_user_id(), restaurant_id
    )

    return render_template('place/restaurant_detail.html',
                           restaurant=restaurant,
                           reviews=reviews,
                           user_review=user_review)


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
