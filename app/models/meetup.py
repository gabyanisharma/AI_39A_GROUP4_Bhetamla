import secrets

from app.database import execute_query

class Meetup:

    @staticmethod
    def get_or_create_invite_code(meetup_id):
        """Return the meetup's shareable invite code, generating one if needed."""
        row = execute_query(
            "SELECT invite_code FROM meetups WHERE id = %s", (meetup_id,), fetch=True
        )
        if not row:
            return None
        code = row[0].get('invite_code')
        if not code:
            code = secrets.token_urlsafe(9)
            execute_query(
                "UPDATE meetups SET invite_code = %s WHERE id = %s", (code, meetup_id)
            )
        return code

    @staticmethod
    def get_by_invite_code(code):
        rows = execute_query(
            "SELECT * FROM meetups WHERE invite_code = %s", (code,), fetch=True
        )
        return rows[0] if rows else None

    @staticmethod
    def create(title, description, created_by, meetup_date=None, meetup_time=None):
        query = """
            INSERT INTO meetups (title, description, created_by, meetup_date, meetup_time)
            VALUES (%s, %s, %s, %s, %s)
        """
        # Ensure date and time are None if empty
        if not meetup_date:
            meetup_date = None
        if not meetup_time:
            meetup_time = None
        return execute_query(query, (title, description, created_by, meetup_date, meetup_time))

    @staticmethod
    def get_by_id(meetup_id):
        query = "SELECT * FROM meetups WHERE id = %s"
        results = execute_query(query, (meetup_id,), fetch=True)
        return results[0] if results else None

    @staticmethod
    def get_by_user(user_id, include_hidden=True):
        hidden_filter = ""
        if not include_hidden:
            hidden_filter = """
               AND COALESCE((
                   SELECT mm.hidden_from_groups FROM meetup_members mm
                   WHERE mm.meetup_id = m.id AND mm.user_id = %s
               ), 0) = 0
            """
        query = f"""
            SELECT m.*, u.full_name as creator_name
            FROM meetups m
            JOIN users u ON m.created_by = u.id
            WHERE (m.created_by = %s
               OR m.id IN (
                   SELECT meetup_id FROM meetup_members
                   WHERE user_id = %s
               ))
            {hidden_filter}
            ORDER BY m.created_at DESC
        """
        params = (user_id, user_id)
        if not include_hidden:
            params = (user_id, user_id, user_id)
        return execute_query(query, params, fetch=True)

    @staticmethod
    def update_midpoint(meetup_id, lat, lng, address=''):
        query = """
            UPDATE meetups
            SET midpoint_lat = %s, midpoint_lng = %s, midpoint_address = %s
            WHERE id = %s
        """
        return execute_query(query, (lat, lng, address, meetup_id))

    @staticmethod
    def update_status(meetup_id, status):
        query = """
            UPDATE meetups
            SET status = %s
            WHERE id = %s
        """
        return execute_query(query, (status, meetup_id))
    
    @staticmethod
    def hide_from_groups(meetup_id, user_id):
        execute_query(
            """
            UPDATE meetup_members SET hidden_from_groups = TRUE
            WHERE meetup_id = %s AND user_id = %s
            """,
            (meetup_id, user_id)
        )

    @staticmethod
    def delete_by_creator(meetup_id, user_id):
        query = """
            DELETE FROM meetups
            WHERE id = %s AND created_by = %s
        """
        return execute_query(query, (meetup_id, user_id))


class MeetupMember:

    @staticmethod
    def add(meetup_id, user_id, latitude=None, longitude=None, address=None, status='invited'):
        query = """
            INSERT INTO meetup_members (meetup_id, user_id, latitude, longitude, address, status)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            status = VALUES(status)
        """
        if not latitude:
            latitude = None
        if not longitude:
            longitude = None
        if not address:
            address = None
        return execute_query(query, (meetup_id, user_id, latitude, longitude, address, status))

    @staticmethod
    def get_by_meetup(meetup_id):
        query = """
            SELECT mm.*, u.full_name, u.email, u.profile_pic
            FROM meetup_members mm
            JOIN users u ON mm.user_id = u.id
            WHERE mm.meetup_id = %s
        """
        return execute_query(query, (meetup_id,), fetch=True)

    @staticmethod
    def get_locations(meetup_id):
        query = """
            SELECT mm.*, u.full_name
            FROM meetup_members mm
            JOIN users u ON mm.user_id = u.id
            WHERE mm.meetup_id = %s AND mm.latitude IS NOT NULL AND mm.longitude IS NOT NULL
        """
        return execute_query(query, (meetup_id,), fetch=True)

    @staticmethod
    def update_location(meetup_id, user_id, latitude, longitude, address=None):
        query = """
            INSERT INTO meetup_members (meetup_id, user_id, latitude, longitude, address, status)
            VALUES (%s, %s, %s, %s, %s, 'accepted')
            ON DUPLICATE KEY UPDATE
            latitude = VALUES(latitude),
            longitude = VALUES(longitude),
            address = VALUES(address),
            status = 'accepted'
        """
        return execute_query(query, (meetup_id, user_id, latitude, longitude, address))

    @staticmethod
    def accept(meetup_id, user_id):
        query = """
            UPDATE meetup_members
            SET status = 'accepted'
            WHERE meetup_id = %s AND user_id = %s
        """
        return execute_query(query, (meetup_id, user_id))

    @staticmethod
    def decline(meetup_id, user_id):
        query = """
            UPDATE meetup_members
            SET status = 'declined'
            WHERE meetup_id = %s AND user_id = %s
        """
        return execute_query(query, (meetup_id, user_id))


class PlaceSuggestion:

    @staticmethod
    def add(meetup_id, place_name, address=None, latitude=None, longitude=None, rating=0, suggested_by=None):
        query = """
            INSERT INTO place_suggestions (meetup_id, place_name, address, latitude, longitude, rating, suggested_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        if not rating or rating == '':
            rating = 0
        if not latitude or latitude == '':
            latitude = None
        if not longitude or longitude == '':
            longitude = None
        return execute_query(query, (meetup_id, place_name, address, latitude, longitude, rating, suggested_by))

    @staticmethod
    def get_by_meetup(meetup_id):
        query = """
            SELECT ps.*, u.full_name as suggested_by_name
            FROM place_suggestions ps
            LEFT JOIN users u ON ps.suggested_by = u.id
            WHERE ps.meetup_id = %s
            ORDER BY ps.suggested_at DESC
        """
        return execute_query(query, (meetup_id,), fetch=True)
