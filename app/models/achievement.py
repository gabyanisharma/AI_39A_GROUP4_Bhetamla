from app.database import execute_query


class Achievement:

    @staticmethod
    def get_all():
        return execute_query(
            "SELECT * FROM achievements ORDER BY id",
            fetch=True
        ) or []

    @staticmethod
    def get_by_key(unlock_key):
        rows = execute_query(
            "SELECT * FROM achievements WHERE unlock_key = %s",
            (unlock_key,), fetch=True
        )
        return rows[0] if rows else None

    @staticmethod
    def get_user_achievements(user_id):
        return execute_query(
            """
            SELECT a.*, ua.unlocked_at
            FROM achievements a
            LEFT JOIN user_achievements ua
              ON ua.achievement_id = a.id AND ua.user_id = %s
            ORDER BY a.id
            """,
            (user_id,), fetch=True
        ) or []

    @staticmethod
    def has_unlocked(user_id, unlock_key):
        rows = execute_query(
            """
            SELECT ua.id FROM user_achievements ua
            JOIN achievements a ON a.id = ua.achievement_id
            WHERE ua.user_id = %s AND a.unlock_key = %s
            """,
            (user_id, unlock_key), fetch=True
        )
        return bool(rows)

    @staticmethod
    def unlock(user_id, unlock_key):
        if Achievement.has_unlocked(user_id, unlock_key):
            return None
        ach = Achievement.get_by_key(unlock_key)
        if not ach:
            return None
        return execute_query(
            """
            INSERT INTO user_achievements (user_id, achievement_id)
            VALUES (%s, %s)
            """,
            (user_id, ach['id'])
        )

    @staticmethod
    def count_for_user(user_id):
        rows = execute_query(
            "SELECT COUNT(*) AS cnt FROM user_achievements WHERE user_id = %s",
            (user_id,), fetch=True
        )
        return rows[0]['cnt'] if rows else 0
