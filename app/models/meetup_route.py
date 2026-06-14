from app.database import execute_query, get_db_connection


KATHMANDU_BOUNDS = {
    'min_lat': 27.55,
    'max_lat': 27.85,
    'min_lng': 85.15,
    'max_lng': 85.55,
}

ALLOWED_TRAVEL_MODES = {'driving', 'walking', 'cycling'}
ALLOWED_WAYPOINT_SOURCES = {'geocoder', 'map_click', 'manual', 'dragged'}
MAX_WAYPOINTS = 12


def _clean_text(value, max_length):
    if value is None:
        return ''
    return str(value).strip()[:max_length]


def _parse_float(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number


def _parse_positive_int(value):
    number = _parse_float(value)
    if number is None or number < 0:
        return None
    return int(round(number))


def _inside_kathmandu(lat, lng):
    return (
        KATHMANDU_BOUNDS['min_lat'] <= lat <= KATHMANDU_BOUNDS['max_lat']
        and KATHMANDU_BOUNDS['min_lng'] <= lng <= KATHMANDU_BOUNDS['max_lng']
    )


def validate_route_payload(payload):
    """Validate and normalize the JSON route payload before saving."""
    if not isinstance(payload, dict):
        return None, ['Invalid JSON payload.']

    errors = []
    travel_mode = payload.get('travel_mode', 'driving')
    if travel_mode not in ALLOWED_TRAVEL_MODES:
        errors.append('Unsupported travel mode.')

    raw_waypoints = payload.get('waypoints')
    if not isinstance(raw_waypoints, list):
        return None, ['Waypoints must be an array.']

    if len(raw_waypoints) < 2:
        errors.append('Add at least two stops before saving a route.')
    if len(raw_waypoints) > MAX_WAYPOINTS:
        errors.append(f'Routes can have at most {MAX_WAYPOINTS} stops.')

    cleaned_waypoints = []
    for index, raw in enumerate(raw_waypoints):
        if not isinstance(raw, dict):
            errors.append(f'Stop {index + 1} is invalid.')
            continue

        lat = _parse_float(raw.get('latitude', raw.get('lat')))
        lng = _parse_float(raw.get('longitude', raw.get('lng')))

        if lat is None or lng is None:
            errors.append(f'Stop {index + 1} needs valid latitude and longitude.')
            continue

        if not _inside_kathmandu(lat, lng):
            errors.append(f'Stop {index + 1} is outside the Kathmandu planning area.')

        source = raw.get('source') or 'manual'
        if source not in ALLOWED_WAYPOINT_SOURCES:
            source = 'manual'

        cleaned_waypoints.append({
            'sequence_index': index,
            'label': _clean_text(raw.get('label'), 100) or f'Stop {index + 1}',
            'address': _clean_text(raw.get('address'), 255),
            'latitude': lat,
            'longitude': lng,
            'source': source,
        })

    if errors:
        return None, errors

    route_summary = payload.get('route_summary') or payload.get('routeSummary') or {}
    return {
        'travel_mode': travel_mode,
        'distance_m': _parse_positive_int(route_summary.get('distance_m')),
        'duration_s': _parse_positive_int(route_summary.get('duration_s')),
        'waypoints': cleaned_waypoints,
    }, []


class MeetupRoute:
    @staticmethod
    def user_can_access(meetup_id, user_id):
        query = """
            SELECT m.id
            FROM meetups m
            LEFT JOIN meetup_members mm
              ON mm.meetup_id = m.id
             AND mm.user_id = %s
            WHERE m.id = %s
              AND (
                    m.created_by = %s
                 OR mm.status IN ('accepted', 'invited')
              )
            LIMIT 1
        """
        rows = execute_query(query, (user_id, meetup_id, user_id), fetch=True)
        return bool(rows)

    @staticmethod
    def user_can_edit(meetup_id, user_id):
        query = """
            SELECT m.id
            FROM meetups m
            LEFT JOIN meetup_members mm
              ON mm.meetup_id = m.id
             AND mm.user_id = %s
            WHERE m.id = %s
              AND (
                    m.created_by = %s
                 OR mm.status = 'accepted'
              )
            LIMIT 1
        """
        rows = execute_query(query, (user_id, meetup_id, user_id), fetch=True)
        return bool(rows)

    @staticmethod
    def get_by_meetup(meetup_id):
        routes = execute_query(
            "SELECT * FROM meetup_routes WHERE meetup_id = %s LIMIT 1",
            (meetup_id,),
            fetch=True,
        )
        if not routes:
            return None

        route = routes[0]
        waypoints = execute_query(
            """
            SELECT id, sequence_index, label, address, latitude, longitude, source
            FROM meetup_route_waypoints
            WHERE route_id = %s
            ORDER BY sequence_index ASC
            """,
            (route['id'],),
            fetch=True,
        )

        route['waypoints'] = [
            {
                'id': row['id'],
                'sequence_index': row['sequence_index'],
                'label': row['label'],
                'address': row['address'] or '',
                'latitude': float(row['latitude']),
                'longitude': float(row['longitude']),
                'source': row['source'] or 'manual',
            }
            for row in waypoints
        ]
        return route

    @staticmethod
    def replace_for_meetup(meetup_id, user_id, route_data):
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM meetup_routes WHERE meetup_id = %s LIMIT 1",
                    (meetup_id,),
                )
                existing = cursor.fetchone()

                if existing:
                    route_id = existing['id']
                    cursor.execute(
                        """
                        UPDATE meetup_routes
                        SET created_by = %s,
                            travel_mode = %s,
                            distance_m = %s,
                            duration_s = %s
                        WHERE id = %s
                        """,
                        (
                            user_id,
                            route_data['travel_mode'],
                            route_data['distance_m'],
                            route_data['duration_s'],
                            route_id,
                        ),
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO meetup_routes
                            (meetup_id, created_by, travel_mode, distance_m, duration_s)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (
                            meetup_id,
                            user_id,
                            route_data['travel_mode'],
                            route_data['distance_m'],
                            route_data['duration_s'],
                        ),
                    )
                    route_id = cursor.lastrowid

                cursor.execute(
                    "DELETE FROM meetup_route_waypoints WHERE route_id = %s",
                    (route_id,),
                )

                for waypoint in route_data['waypoints']:
                    cursor.execute(
                        """
                        INSERT INTO meetup_route_waypoints
                            (route_id, sequence_index, label, address,
                             latitude, longitude, source)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            route_id,
                            waypoint['sequence_index'],
                            waypoint['label'],
                            waypoint['address'],
                            waypoint['latitude'],
                            waypoint['longitude'],
                            waypoint['source'],
                        ),
                    )

            connection.commit()
            return route_id
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    @staticmethod
    def delete_for_meetup(meetup_id, user_id):
        query = """
            DELETE mr
            FROM meetup_routes mr
            JOIN meetups m ON m.id = mr.meetup_id
            WHERE mr.meetup_id = %s
              AND (m.created_by = %s OR mr.created_by = %s)
        """
        return execute_query(query, (meetup_id, user_id, user_id))
