from app.database import execute_query


class MeetupPlanPreference:
    """Per-user planning choices collected from the Plan Meetup popups
    (cuisine, budget range, ambience, selected venue, ride option, notes).

    Each (meetup_id, user_id) pair has at most one row, so saves are
    upserts that only touch the fields supplied by a given popup.
    """

    # Columns the popups are allowed to write. meetup_id / user_id are
    # handled separately as the identity of the row.
    EDITABLE_FIELDS = (
        'cuisine',
        'budget_min',
        'budget_max',
        'ambience',
        'selected_venue',
        'selected_venue_lat',
        'selected_venue_lng',
        'ride_option',
        'notes',
    )

    @staticmethod
    def get(meetup_id, user_id):
        rows = execute_query(
            """
            SELECT * FROM meetup_plan_preferences
            WHERE meetup_id = %s AND user_id = %s
            """,
            (meetup_id, user_id), fetch=True
        )
        return rows[0] if rows else None

    @staticmethod
    def get_for_meetup(meetup_id):
        rows = execute_query(
            """
            SELECT p.*, u.full_name
            FROM meetup_plan_preferences p
            JOIN users u ON u.id = p.user_id
            WHERE p.meetup_id = %s
            ORDER BY p.updated_at DESC
            """,
            (meetup_id,), fetch=True
        )
        return rows or []

    @classmethod
    def upsert(cls, meetup_id, user_id, fields):
        """Insert or update the caller's preferences for a meetup.

        `fields` is a dict that may contain any subset of EDITABLE_FIELDS;
        only the keys present are written, so each popup can save just the
        slice it owns without clobbering the others.
        """
        clean = {k: fields[k] for k in cls.EDITABLE_FIELDS if k in fields}
        if not clean:
            return None

        columns = ['meetup_id', 'user_id'] + list(clean.keys())
        placeholders = ', '.join(['%s'] * len(columns))
        updates = ', '.join(f'{col} = VALUES({col})' for col in clean.keys())
        params = [meetup_id, user_id] + list(clean.values())

        return execute_query(
            f"""
            INSERT INTO meetup_plan_preferences ({', '.join(columns)})
            VALUES ({placeholders})
            ON DUPLICATE KEY UPDATE {updates}
            """,
            tuple(params)
        )
