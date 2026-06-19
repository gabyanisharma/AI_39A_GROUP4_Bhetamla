from flask import (render_template, request,
                   redirect, url_for, flash, jsonify, session)
from app.auth import get_current_user_id, is_logged_in
from app.models.meetup import Meetup, MeetupMember
from app.models.user import User
from app.models.route import SavedRoute
from app.database import execute_query
import math
from datetime import datetime



# ── Kathmandu ride pricing constants ──────────────────────────────
PATHAO_BIKE_BASE   = 25    # NPR
PATHAO_BIKE_PER_KM = 18    # NPR/km

PATHAO_CAR_BASE    = 50    # NPR
PATHAO_CAR_PER_KM  = 35    # NPR/km

TAXI_BASE          = 50    # NPR (flag fall)
TAXI_PER_KM        = 45    # NPR/km
WALK_SPEED_KMH     = 4.5   # average walking speed
BIKE_SPEED_KMH     = 22    # motorbikes weave through Kathmandu traffic
CAR_SPEED_KMH      = 16    # cars/taxis are slower in city congestion

# Peak hours: 8-10 AM and 5-8 PM on weekdays
PEAK_HOUR_RANGES   = [(8, 10), (17, 20)]
PEAK_MULTIPLIER    = 1.3   # 30% surge
PEAK_SPEED_PENALTY = 0.7   # traffic slows everyone ~30% more during peak


# ── Helper: distance ──────────────────────────────────────────────
def _haversine_km(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(math.radians,
                                  [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


def _is_peak_hour(dt=None):
    if dt is None:
        dt = datetime.now()
    if dt.weekday() >= 5:          # Saturday / Sunday
        return False
    hour = dt.hour
    return any(start <= hour < end for start, end in PEAK_HOUR_RANGES)


def _calculate_costs(distance_km, peak=False):
    mult = PEAK_MULTIPLIER if peak else 1.0
    speed_mult = PEAK_SPEED_PENALTY if peak else 1.0

    bike = round((PATHAO_BIKE_BASE + PATHAO_BIKE_PER_KM * distance_km) * mult)
    car  = round((PATHAO_CAR_BASE  + PATHAO_CAR_PER_KM  * distance_km) * mult)
    taxi = round((TAXI_BASE        + TAXI_PER_KM         * distance_km) * mult)
    walk = int((distance_km / WALK_SPEED_KMH) * 60)   # minutes

    # Real travel time estimates — slower during peak traffic.
    bike_mins = max(2, round((distance_km / (BIKE_SPEED_KMH * speed_mult)) * 60))
    car_mins  = max(2, round((distance_km / (CAR_SPEED_KMH  * speed_mult)) * 60))

    return bike, car, taxi, walk, bike_mins, car_mins


# ── Main page ──────────────────────────────────────────────────────
def ride_estimate_page(meetup_id):
    if not is_logged_in():
        return redirect(url_for('auth.login'))

    meetup  = Meetup.get_by_id(meetup_id)
    if not meetup:
        flash('Meetup not found.', 'error')
        return redirect(url_for('meetup.plan'))

    user_id = get_current_user_id()
    members = MeetupMember.get_by_meetup(meetup_id)
    is_peak = _is_peak_hour()

    # Fetch saved estimates for all members
    estimates = execute_query(
        "SELECT * FROM ride_estimates WHERE meetup_id = %s",
        (meetup_id,), fetch=True
    ) or []

    est_map = {e['user_id']: e for e in estimates}

    # Current user's location
    my_member = next(
        (m for m in members if m['user_id'] == user_id), None
    )

    return render_template(
        'ride/estimate.html',
        meetup=meetup,
        members=members,
        est_map=est_map,
        my_member=my_member,
        is_peak=is_peak,
        user_id=user_id
    )


# ── Calculate & save estimate (AJAX) ──────────────────────────────
def calculate_estimate(meetup_id):
    if not is_logged_in():
        return jsonify({'success': False, 'message': 'Not logged in'}), 401

    user_id = get_current_user_id()
    data    = request.get_json() or {}

    from_lat  = data.get('from_lat')
    from_lng  = data.get('from_lng')
    from_addr = data.get('from_address', '')
    to_lat    = data.get('to_lat')
    to_lng    = data.get('to_lng')
    to_addr   = data.get('to_address', '')

    if not all([from_lat, from_lng, to_lat, to_lng]):
        return jsonify({
            'success': False,
            'message': 'Both origin and destination coordinates required.'
        })

    distance_km = round(
        _haversine_km(
            float(from_lat), float(from_lng),
            float(to_lat),   float(to_lng)
        ), 3
    )

    is_peak = _is_peak_hour()
    bike, car, taxi, walk, bike_mins, car_mins = _calculate_costs(distance_km, is_peak)

    # Upsert estimate
    execute_query(
        """
        INSERT INTO ride_estimates
            (meetup_id, user_id, from_lat, from_lng, from_address,
             to_lat, to_lng, to_address, distance_km,
             pathao_bike_cost, pathao_car_cost, taxi_cost,
             walk_minutes, bike_minutes, car_minutes, is_peak_hour)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE
            from_lat          = VALUES(from_lat),
            from_lng          = VALUES(from_lng),
            from_address      = VALUES(from_address),
            to_lat            = VALUES(to_lat),
            to_lng            = VALUES(to_lng),
            to_address        = VALUES(to_address),
            distance_km       = VALUES(distance_km),
            pathao_bike_cost  = VALUES(pathao_bike_cost),
            pathao_car_cost   = VALUES(pathao_car_cost),
            taxi_cost         = VALUES(taxi_cost),
            walk_minutes      = VALUES(walk_minutes),
            bike_minutes      = VALUES(bike_minutes),
            car_minutes       = VALUES(car_minutes),
            is_peak_hour      = VALUES(is_peak_hour),
            calculated_at     = CURRENT_TIMESTAMP
        """,
        (meetup_id, user_id,
         from_lat, from_lng, from_addr,
         to_lat, to_lng, to_addr,
         distance_km, bike, car, taxi, walk, bike_mins, car_mins, is_peak)
    )

    return jsonify({
        'success':     True,
        'distance_km': distance_km,
        'is_peak':     is_peak,
        'costs': {
            'pathao_bike': bike,
            'pathao_car':  car,
            'taxi':        taxi,
            'walk_minutes': walk,
            'bike_minutes': bike_mins,
            'car_minutes': car_mins
        }
    })


# ── Budget split (US2) ─────────────────────────────────────────────
def budget_split(meetup_id):
    if not is_logged_in():
        return jsonify({'success': False}), 401

    estimates = execute_query(
        """
        SELECT re.*, u.full_name
        FROM ride_estimates re
        JOIN users u ON re.user_id = u.id
        WHERE re.meetup_id = %s
        """,
        (meetup_id,), fetch=True
    ) or []

    if not estimates:
        return jsonify({'success': False, 'message': 'No estimates yet.'})

    # Calculate totals and averages
    total_bike = sum(float(e['pathao_bike_cost'] or 0) for e in estimates)
    total_car  = sum(float(e['pathao_car_cost']  or 0) for e in estimates)
    total_taxi = sum(float(e['taxi_cost']        or 0) for e in estimates)
    count      = len(estimates)

    split_data = {
        'member_count':    count,
        'total_bike_cost': round(total_bike),
        'total_car_cost':  round(total_car),
        'total_taxi_cost': round(total_taxi),
        'avg_bike':        round(total_bike / count) if count else 0,
        'avg_car':         round(total_car  / count) if count else 0,
        'avg_taxi':        round(total_taxi / count) if count else 0,
        'members': [{
            'user_id':    e['user_id'],
            'name':       e['full_name'],
            'distance':   float(e['distance_km'] or 0),
            'bike_cost':  float(e['pathao_bike_cost'] or 0),
            'car_cost':   float(e['pathao_car_cost']  or 0),
            'taxi_cost':  float(e['taxi_cost']        or 0),
            'walk_mins':  e['walk_minutes'],
            'bike_mins':  e.get('bike_minutes'),
            'car_mins':   e.get('car_minutes'),
            'is_peak':    bool(e['is_peak_hour'])
        } for e in estimates]
    }

    return jsonify({'success': True, 'data': split_data})



# ── Record budget split → unlocks Penny Pincher badge (US2) ───────
def record_budget_split(meetup_id):
    """
    POST /meetup/budget-split/<meetup_id>/record
    Called by the planner "Send Split" button.
    Persists the split event so the Penny Pincher achievement
    can be awarded on the next badge evaluation pass.
    """
    if not is_logged_in():
        return jsonify({'success': False, 'message': 'Not logged in'}), 401

    user_id = get_current_user_id()
    data    = request.get_json() or {}

    total_bill    = data.get('total_bill', 0)
    split_summary = data.get('split_summary', '')

    # Fetch member count for the split denominator
    member_rows = execute_query(
        "SELECT COUNT(*) AS cnt FROM meetup_members WHERE meetup_id = %s",
        (meetup_id,), fetch=True
    )
    member_count = (member_rows[0]['cnt'] if member_rows else 1) or 1
    per_person   = round(float(total_bill) / member_count, 2) if total_bill else 0

    execute_query(
        """
        INSERT INTO budget_split_records
            (meetup_id, recorded_by, total_bill, member_count,
             per_person_amount, split_summary, recorded_at)
        VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
        ON DUPLICATE KEY UPDATE
            total_bill          = VALUES(total_bill),
            member_count        = VALUES(member_count),
            per_person_amount   = VALUES(per_person_amount),
            split_summary       = VALUES(split_summary),
            recorded_at         = CURRENT_TIMESTAMP
        """,
        (meetup_id, user_id, total_bill, member_count,
         per_person, split_summary)
    )

    return jsonify({
        'success':        True,
        'per_person':     per_person,
        'member_count':   member_count,
        'badge_hint':     'penny_pincher'   # client can optimistically show unlock
    })



def route_planner_page():
    if not is_logged_in():
        return redirect(url_for('auth.login'))
    user_id = get_current_user_id()
    saved_routes = SavedRoute.get_by_user(user_id)
    return render_template('ride/route_planner.html', saved_routes=saved_routes)


# ── Save a multi-stop route (AJAX POST) ───────────────────────────
def save_route():
    if not is_logged_in():
        return jsonify({'success': False, 'message': 'Not logged in'}), 401

    user_id = get_current_user_id()
    data = request.get_json() or {}

    route_name        = data.get('route_name', 'My Route').strip() or 'My Route'
    waypoints         = data.get('waypoints', [])
    optimize_by       = data.get('optimize_by', 'time')
    total_distance_km = data.get('total_distance_km', 0)
    total_duration_min= data.get('total_duration_min', 0)

    if len(waypoints) < 2:
        return jsonify({'success': False, 'message': 'Need at least 2 stops.'}), 400

    SavedRoute.save(
        user_id=user_id,
        route_name=route_name,
        waypoints=waypoints,
        optimize_by=optimize_by,
        total_distance_km=round(float(total_distance_km), 2),
        total_duration_min=int(total_duration_min)
    )
    return jsonify({'success': True, 'message': f'Route "{route_name}" saved!'})


# ── Delete a saved route (AJAX POST) ──────────────────────────────
def delete_route(route_id):
    if not is_logged_in():
        return jsonify({'success': False}), 401
    user_id = get_current_user_id()
    SavedRoute.delete(route_id, user_id)
    return jsonify({'success': True})