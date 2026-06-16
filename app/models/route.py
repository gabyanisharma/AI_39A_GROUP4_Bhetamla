import json
from app.database import execute_query


class SavedRoute:
    """Model for multi-stop saved routes."""

    # ── Save a new route ────────────────────────────────────────────
    @staticmethod
    def save(user_id, route_name, waypoints, optimize_by='time',
             total_distance_km=0, total_duration_min=0):
        waypoints_json = json.dumps(waypoints)
        execute_query(
            """
            INSERT INTO saved_routes
                (user_id, route_name, waypoints_json, optimize_by,
                 total_distance_km, total_duration_min)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (user_id, route_name, waypoints_json, optimize_by,
             total_distance_km, total_duration_min)
        )

    # ── Fetch all routes for a user ─────────────────────────────────
    @staticmethod
    def get_by_user(user_id):
        rows = execute_query(
            "SELECT * FROM saved_routes WHERE user_id = %s ORDER BY created_at DESC",
            (user_id,), fetch=True
        ) or []
        for row in rows:
            try:
                row['waypoints'] = json.loads(row['waypoints_json'])
            except Exception:
                row['waypoints'] = []
        return rows

    # ── Fetch a single route ─────────────────────────────────────────
    @staticmethod
    def get_by_id(route_id, user_id=None):
        sql = "SELECT * FROM saved_routes WHERE id = %s"
        params = [route_id]
        if user_id:
            sql += " AND user_id = %s"
            params.append(user_id)
        row = execute_query(sql, params, fetch=True, single=True)
        if row:
            try:
                row['waypoints'] = json.loads(row['waypoints_json'])
            except Exception:
                row['waypoints'] = []
        return row

    # ── Delete a route ───────────────────────────────────────────────
    @staticmethod
    def delete(route_id, user_id):
        execute_query(
            "DELETE FROM saved_routes WHERE id = %s AND user_id = %s",
            (route_id, user_id)
        )
