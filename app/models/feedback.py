from app.database import execute_query


class Feedback:
    """App-level rating & feedback (US27), distinct from restaurant reviews."""

    @staticmethod
    def create(user_id, rating, message='', category='general'):
        return execute_query(
            """
            INSERT INTO app_feedback (user_id, rating, category, message)
            VALUES (%s, %s, %s, %s)
            """,
            (user_id, rating, category, message)
        )

    @staticmethod
    def get_by_user(user_id):
        rows = execute_query(
            """
            SELECT * FROM app_feedback
            WHERE user_id = %s
            ORDER BY created_at DESC
            """,
            (user_id,), fetch=True
        )
        return rows or []

    @staticmethod
    def average_rating():
        rows = execute_query(
            "SELECT AVG(rating) AS avg_rating, COUNT(*) AS total FROM app_feedback",
            fetch=True
        )
        if rows and rows[0]['total']:
            return {'average': round(float(rows[0]['avg_rating']), 2),
                    'total': int(rows[0]['total'])}
        return {'average': 0, 'total': 0}
